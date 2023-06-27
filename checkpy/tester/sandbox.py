import contextlib
import glob
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, Union


@contextlib.contextmanager
def sandbox(files:Iterable[Union[str, Path]]=None, name:Union[str, Path]=""):
	with tempfile.TemporaryDirectory() as dir:
		dir = Path(Path(dir) / name)
		dir.mkdir(exist_ok=True)

		# If no files specified, take all files from cwd
		if files is None:
			cwd = Path.cwd()
			paths = glob.glob(str(cwd / "**"), recursive=True)
			files = [Path(p).relative_to(cwd) for p in paths if os.path.isfile(p)]

		for f in files:
			dest = (dir / f).absolute()
			dest.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy(f, dest)
		
		with cd(dir):
			yield dir


@contextlib.contextmanager
def cd(dest:Union[str, Path]):
	origin = Path.cwd()
	try:
		os.chdir(dest)
		yield dest
	finally:
		os.chdir(origin)
