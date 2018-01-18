import os
import shutil
import uuid
import checkpy.entities.path as path

class Sandbox():
	def __init__(self, filePath):
		self.id = "sandbox_" + str(uuid.uuid4())
		self.path = path.Path(os.path.abspath(os.path.dirname(__file__))) + self.id
		self._filePath = filePath
		os.makedirs(str(self.path))

	def _clear(self):
		if self.path.exists():
			shutil.rmtree(str(self.path))

	def __enter__(self):
		self._oldCWD = os.getcwd()
		os.chdir(str(self.path))
		self._filePath.copyTo(self.path + self._filePath.fileName)

	def __exit__(self, exc_type, exc_val, exc_tb):
		os.chdir(str(self._oldCWD))
		self._clear()