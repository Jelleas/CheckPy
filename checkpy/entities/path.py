import os
import shutil
import checkpy.entities.exception as exception

class Path(object):
	def __init__(self, path):
		self._path = os.path.normpath(path)

	@property
	def fileName(self):
		return os.path.basename(str(self))

	@property
	def folderName(self):
		_, name = os.path.split(os.path.dirname(str(self)))
		return name

	def containingFolder(self):
		return Path(os.path.dirname(str(self)))

	def isPythonFile(self):
		return self.fileName.endswith(".py")

	def exists(self):
		return os.path.exists(str(self))

	def walk(self):
		for path, subdirs, files in os.walk(str(self)):
			yield Path(path), [Path(sd) for sd in subdirs], [Path(f) for f in files]

	def copyTo(self, destination):
		shutil.copyfile(str(self), str(destination))

	def pathFromFolder(self, folderName):
		path = ""
		seen = False
		for item in self:
			if seen:
				path = os.path.join(path, item)
			if item == folderName:
				seen = True

		if not seen:
			raise exception.PathError(message = "folder {} does not exist in {}".format(folderName, self))
		return Path(path)

	def __add__(self, other):
		try:
			# Python 3
			if isinstance(other, bytes) or isinstance(other, str):
				return Path(os.path.join(str(self), other))
		except NameError:
			# Python 2
			if isinstance(other, str) or isinstance(other, unicode):
				return Path(os.path.join(str(self), other))
		return Path(os.path.join(str(self), str(other)))

	def __sub__(self, other):
		if isinstance(other, str):
			other = Path(other)
		my_items = [item for item in self]
		other_items = [item for item in other]
		total = ""
		for item in my_items[len(other_items):]:
			total = os.path.join(total, item)
		return Path(total)

	def __iter__(self):
		for item in str(self).split(os.path.sep):
			yield item

	def __hash__(self):
		return hash(repr(self))

	def __eq__(self, other):
		return isinstance(other, type(self)) and repr(self) == repr(other)

	def __contains__(self, item):
		return str(item) in [item for item in self]

	def __nonzero__ (self):
		return len(str(self)) != 0

	def __str__(self):
		return self._path

	def __repr__(self):
		return "/".join([item for item in self])

def current():
	return Path(os.getcwd())

userPath = Path(os.getcwd())

CHECKPYPATH = Path(os.path.abspath(os.path.dirname(__file__))[:-len("/entities")])
TESTSPATH = CHECKPYPATH + "tests"
DBPATH = CHECKPYPATH + "storage" + "downloadLocations.json"
