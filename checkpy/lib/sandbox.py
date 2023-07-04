import contextlib
import glob
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, List, Set, Union

from checkpy.entities.exception import TooManyFilesError, MissingRequiredFiles


__all__ = ["exclude", "include", "only", "require", "sandbox"]


DEFAULT_FILE_LIMIT = 10000


class Config:
	def __init__(self, onUpdate=lambda config: None):
		self.includedFiles: Set[str] = set()
		self.excludedFiles: Set[str] = set()
		self.missingRequiredFiles: List[str] = []
		self.isSandboxed = False
		self.root = Path.cwd()
		self.onUpdate = onUpdate

	def _initSandbox(self):
		if self.isSandboxed:
			return

		self.includedFiles = _glob("*", root=self.root)
		self.isSandboxed = True

	def exclude(self, *patterns: Iterable[Union[str, Path]]):
		self._initSandbox()

		newExcluded: Set[str] = set()

		for pattern in patterns:
			newExcluded |= _glob(pattern, root=self.root)

		self.includedFiles -= newExcluded
		self.excludedFiles.update(newExcluded)

		self.onUpdate(self)

	def include(self, *patterns: Iterable[Union[str, Path]]):
		self._initSandbox()

		newIncluded: Set[str] = set()

		for pattern in patterns:
			newIncluded |= _glob(pattern, root=self.root)

		self.excludedFiles -= newIncluded
		self.includedFiles.update(newIncluded)

		self.onUpdate(self)

	def only(self, *patterns: Iterable[Union[str, Path]]):
		self._initSandbox()

		allFiles = self.includedFiles | self.excludedFiles
		self.includedFiles = set.union(*[_glob(p, root=self.root) for p in patterns])
		self.excludedFiles = allFiles - self.includedFiles

		self.onUpdate(self)

	def require(self, *filePaths: Iterable[Union[str, Path]]):
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


config = Config()

def exclude(*patterns: Iterable[Union[str, Path]]):
	config.exclude(*patterns)

def include(*patterns: Iterable[Union[str, Path]]):
	config.include(*patterns)

def only(*patterns: Iterable[Union[str, Path]]):
	config.only(*patterns)

def require(*filePaths: Iterable[Union[str, Path]]):
	config.require(*filePaths)


@contextlib.contextmanager
def sandbox(name: Union[str, Path]=""):
	if config.missingRequiredFiles:
		raise MissingRequiredFiles(config.missingRequiredFiles)

	if not config.isSandboxed:
		yield
		return

	with tempfile.TemporaryDirectory() as dir:
		dir = Path(Path(dir) / name)
		dir.mkdir(exist_ok=True)

		for f in config.includedFiles:
			dest = (dir / f).absolute()
			dest.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy(f, dest)

		with cd(dir), sandboxConfig():
			yield


@contextlib.contextmanager
def conditionalSandbox(name: Union[str, Path]=""):
	isSandboxed = False
	tempDir = None
	dir = None

	oldIncluded: Set[str] = set()
	oldExcluded: Set[str] = set()

	def sync(config: Config):
		nonlocal oldIncluded, oldExcluded
		for f in config.excludedFiles - oldExcluded:
			dest = (dir / f).absolute()
			try:
				os.remove(dest)
			except FileNotFoundError:
				pass

		for f in config.includedFiles - oldExcluded:
			dest = (dir / f).absolute()
			dest.parent.mkdir(parents=True, exist_ok=True)
			origin = (config.root / f).absolute()
			shutil.copy(origin, dest)

		oldIncluded = set(config.includedFiles)
		oldExcluded = set(config.excludedFiles)

	def onUpdate(config: Config):
		if config.missingRequiredFiles:
			raise MissingRequiredFiles(config.missingRequiredFiles)

		nonlocal isSandboxed
		if not isSandboxed:
			isSandboxed = True
			nonlocal tempDir
			tempDir = tempfile.TemporaryDirectory()
			nonlocal dir
			dir = Path(Path(tempDir.name) / name)
			dir.mkdir(exist_ok=True)
			os.chdir(dir)
		
		sync(config)

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


def _glob(pattern: Union[str, Path], root: Union[str, Path]=None, skip_dirs: bool=False, limit: int=DEFAULT_FILE_LIMIT) -> Set[str]:
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
				raise TooManyFilesError(limit)

		# Expand dirs
		for file in files:
			if os.path.isdir(file) and not skip_dirs:
				for f in _glob(f"{file}/**/*", skip_dirs=True):
					if not os.path.isdir(f):
						add_file(f)
			else:
				add_file(file)

		return all_files

