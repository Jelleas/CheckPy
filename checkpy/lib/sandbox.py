import contextlib
import glob
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Set, Union

import requests

from checkpy.entities.exception import TooManyFilesError, MissingRequiredFiles, DownloadError


__all__ = ["exclude", "include", "only", "require"]


DEFAULT_FILE_LIMIT = 10000


def exclude(*patterns: Union[str, Path]):
    """
    Exclude all files matching patterns from the check's sandbox.
    
    If this is the first call to only/include/exclude/require/download initialize the sandbox: 
    * Create a temp dir
    * Copy over all files from current dir (except those files excluded through exclude())

    Patterns are shell globs in the same style as .gitignore.
    """
    config.exclude(*patterns)

def include(*patterns: Union[str, Path]):
    """
    Include all files matching patterns from the check's sandbox.
    
    If this is the first call to only/include/exclude/require/download initialize the sandbox: 
    * Create a temp dir
    * Copy over all files from current dir (except those files excluded through exclude())

    Patterns are shell globs in the same style as .gitignore.
    """
    config.include(*patterns)

def only(*patterns: Union[str, Path]):
    """
    Only files matching patterns will be in the check's sandbox.
    
    If this is the first call to only/include/exclude/require/download initialize the sandbox: 
    * Create a temp dir
    * Copy over all files from current dir (except those files excluded through exclude())

    Patterns are shell globs in the same style as .gitignore.
    """
    config.only(*patterns)

def require(*filePaths: Union[str, Path]):
    """
    Include all files in the check's sandbox. 
    Raises checkpy.entities.exception.MissingRequiredFiles if any required file is missing.
    Note that this function does not accept patterns (globs), but concrete filenames or paths.
    
    If this is the first call to only/include/exclude/require/download initialize the sandbox: 
    * Create a temp dir
    * Copy over all files from current dir (except those files excluded through exclude())

    Patterns are shell globs in the same style as .gitignore.
    """
    config.require(*filePaths)


def download(fileName: str, source: str):
    """
    Download a file from source and store it in fileName.

    If this is the first call to only/include/exclude/require/download initialize the sandbox: 
    * Create a temp dir
    * Copy over all files from current dir (except those files excluded through exclude())
    """
    config.download(fileName, source)


class Config:
    def __init__(self, onUpdate=lambda config: None):
        self.includedFiles: Set[str] = set()
        self.excludedFiles: Set[str] = set()
        self.missingRequiredFiles: List[str] = []
        self.downloads: List[Download] = []
        self.isSandboxed = False
        self.root = Path.cwd()
        self.onUpdate = onUpdate

    def _initSandbox(self):
        if self.isSandboxed:
            return

        self.includedFiles = _glob("*", root=self.root)
        self.isSandboxed = True

    def exclude(self, *patterns: Union[str, Path]):
        self._initSandbox()

        newExcluded: Set[str] = set()

        for pattern in patterns:
            newExcluded |= _glob(pattern, root=self.root)

        self.includedFiles -= newExcluded
        self.excludedFiles.update(newExcluded)

        self.onUpdate(self)

    def include(self, *patterns: Union[str, Path]):
        self._initSandbox()

        newIncluded: Set[str] = set()

        for pattern in patterns:
            newIncluded |= _glob(pattern, root=self.root)

        self.excludedFiles -= newIncluded
        self.includedFiles.update(newIncluded)

        self.onUpdate(self)

    def only(self, *patterns: Union[str, Path]):
        self._initSandbox()

        allFiles = self.includedFiles | self.excludedFiles
        self.includedFiles = set.union(*[_glob(p, root=self.root) for p in patterns])
        self.excludedFiles = allFiles - self.includedFiles

        self.onUpdate(self)

    def require(self, *filePaths: Union[str, Path]):
        self._initSandbox()

        with cd(self.root):
            for fp in filePaths:
                fp = str(fp)
                if not Path(fp).exists():
                    self.missingRequiredFiles.append(fp)
                else:
                    try:
                        self.excludedFiles.remove(fp)
                    except KeyError:
                        pass
                    else:
                        self.includedFiles.add(fp)

        self.onUpdate(self)

    def download(self, fileName: str, source: str):
        self.downloads.append(Download(fileName, source))
        self.onUpdate(self)

config = Config()


class Download:
    def __init__(self, fileName: str, source: str):
        self.fileName: str = str(fileName)
        self.source: str = str(source)
        self._isDownloaded: bool = False

    def download(self):
        if self._isDownloaded:
            return

        try:
            r = requests.get(self.source, allow_redirects=True)
        except requests.exceptions.ConnectionError:
            raise DownloadError(message="Oh no! It seems like there is no internet connection available.")

        if not r.ok:
            raise DownloadError(message=f"Failed to download {self.source} because: {r.reason}")

        with open(self.fileName, "wb+") as target:
            target.write(r.content)

        self._isDownloaded = True


@contextlib.contextmanager
def sandbox(name: Union[str, Path]=""):
    tempDir = None
    dir = None

    oldIncluded: Set[str] = set()
    oldExcluded: Set[str] = set()

    def sync(config: Config, sandboxDir: Path):
        for dl in config.downloads:
            dl.download()

        nonlocal oldIncluded, oldExcluded
        for f in config.excludedFiles - oldExcluded:
            dest = (sandboxDir / f).absolute()
            try:
                os.remove(dest)
            except FileNotFoundError:
                pass

        for f in config.includedFiles - oldExcluded:
            dest = (sandboxDir / f).absolute()
            dest.parent.mkdir(parents=True, exist_ok=True)
            origin = (config.root / f).absolute()
            shutil.copy(origin, dest)

        oldIncluded = set(config.includedFiles)
        oldExcluded = set(config.excludedFiles)

    def onUpdate(config: Config):
        if config.missingRequiredFiles:
            raise MissingRequiredFiles(config.missingRequiredFiles)

        nonlocal tempDir
        nonlocal dir
        if dir is None or tempDir is None:
            tempDir = tempfile.TemporaryDirectory()
            dir = Path(Path(tempDir.name) / name)
            dir.mkdir(exist_ok=True)
            os.chdir(dir)
        
        sync(config, dir)

    with sandboxConfig(onUpdate=onUpdate):
        try:
            yield
        finally:
            os.chdir(config.root)
            if tempDir:
                tempDir.cleanup()


@contextlib.contextmanager
def sandboxConfig(onUpdate=lambda config: None):
    global config
    oldConfig = config
    try:
        config = Config(onUpdate=onUpdate)
        yield config
    finally:
        config = oldConfig


@contextlib.contextmanager
def cd(dest: Union[str, Path]):
    origin = Path.cwd()
    try:
        os.chdir(dest)
        yield dest
    finally:
        os.chdir(origin)


def _glob(
        pattern: Union[str, Path],
        root: Union[str, Path, None]=None,
        skip_dirs: bool=False,
        limit: int=DEFAULT_FILE_LIMIT
    ) -> Set[str]:
    with cd(root) if root else contextlib.nullcontext():
        pattern = str(pattern)

        # Implicit recursive iff no / in pattern and starts with *
        if "/" not in pattern and pattern.startswith("*"):
            pattern = f"**/{pattern}"
        
        files = glob.iglob(pattern, recursive=True)
        
        all_files = set()
        
        def add_file(f):
            fname = str(Path(f))
            all_files.add(fname)
            if len(all_files) > limit:
                raise TooManyFilesError(
                    message=f"found {len(all_files)} files but checkpy only accepts up to {limit} number of files"
                )

        # Expand dirs
        for file in files:
            if os.path.isdir(file) and not skip_dirs:
                for f in _glob(f"{file}/**/*", skip_dirs=True):
                    if not os.path.isdir(f):
                        add_file(f)
            else:
                add_file(file)

        return all_files

