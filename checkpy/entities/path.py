import os
import sys
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
		if sys.version_info >= (3,0):
			supportedTypes = [str, bytes, Path]
		else:
			supportedTypes = [str, unicode, Path]

		if not any(isinstance(other, t) for t in supportedTypes):
			raise exception.PathError(message = "can't add {} to Path only {}".format(type(other), supportedTypes))

		if not isinstance(other, Path):
			other = Path(other)

		result = str(self)
		for item in other:
			if item != os.path.sep:
				result = os.path.join(result, item)

		return Path(result)

	def __sub__(self, other):
		if sys.version_info >= (3,0):
			supportedTypes = [str, bytes, Path]
		else:
			supportedTypes = [str, unicode, Path]

		if not any(isinstance(other, t) for t in supportedTypes):
			raise exception.PathError(message = "can't subtract {} from Path only {}".format(type(other), supportedTypes))

		if not isinstance(other, Path):
			other = Path(other)

		myItems = [item for item in self]
		otherItems = [item for item in other]

		for items in (myItems, otherItems):
			if len(items) >= 1 and items[0] != os.path.sep and items[0] != ".":
				items.insert(0, ".")

		for i in range(min(len(myItems), len(otherItems))):
			if myItems[i] != otherItems[i]:
				raise exception.PathError(message = "tried subtracting, but root does not match: {} and {}".format(self, other))

		total = ""
		for item in myItems[len(otherItems):]:
			total = os.path.join(total, item)
		return Path(total)

	def __iter__(self):
		items = str(self).split(os.path.sep)
		if len(items) > 0 and items[0] == "":
			items[0] = os.path.sep
		for item in items:
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
