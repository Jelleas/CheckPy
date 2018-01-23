import os
import sys
import shutil
import checkpy.entities.exception as exception

class Path(object):
	def __init__(self, path):
		path = os.path.normpath(path)
		self._drive = os.path.splitdrive(path)[0]

		items = str(path).split(os.path.sep)

		# if path started with root, add root
		if len(items) > 0 and items[0] == "":
			items[0] = os.path.sep
		# remove any empty items (for instance because of "/")
		self._items = [item for item in items if item]

	@property
	def fileName(self):
		return list(self)[-1]

	@property
	def folderName(self):
		return list(self)[-2]

	def containingFolder(self):
		return Path(self._join(self._drive, list(self)[:-1]))

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
		items = []
		for item in self:
			if seen:
				items.append(item)
			if item == folderName:
				seen = True

		if not seen:
			raise exception.PathError(message = "folder {} does not exist in {}".format(folderName, self))
		return Path(self._join(self._drive, items))

	def __add__(self, other):
		if sys.version_info >= (3,0):
			supportedTypes = [str, bytes, Path]
		else:
			supportedTypes = [str, unicode, Path]

		if not any(isinstance(other, t) for t in supportedTypes):
			raise exception.PathError(message = "can't add {} to Path only {}".format(type(other), supportedTypes))

		if not isinstance(other, Path):
			other = Path(other)

		# if other path starts with root, throw error
		if list(other)[0] == os.path.sep:
			raise exception.PathError(message = "can't add {} to Path because it starts at root")

		return Path(self._join(self._drive, list(self) + list(other)))

	def __sub__(self, other):
		if sys.version_info >= (3,0):
			supportedTypes = [str, bytes, Path]
		else:
			supportedTypes = [str, unicode, Path]

		if not any(isinstance(other, t) for t in supportedTypes):
			raise exception.PathError(message = "can't subtract {} from Path only {}".format(type(other), supportedTypes))

		if not isinstance(other, Path):
			other = Path(other)

		myItems = list(self)
		otherItems = list(other)

		for items in (myItems, otherItems):
			if len(items) >= 1 and items[0] != os.path.sep and items[0] != ".":
				items.insert(0, ".")

		for i in range(min(len(myItems), len(otherItems))):
			if myItems[i] != otherItems[i]:
				raise exception.PathError(message = "tried subtracting, but subdirs do not match: {} and {}".format(self, other))

		return Path(self._join(self._drive, myItems[len(otherItems):]))

	def __iter__(self):
		for item in self._items:
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
		return self._join(self._drive, list(self))

	def __repr__(self):
		return "/".join([item for item in self])

	def _join(self, drive, items):
		result = drive
		for item in items:
			result = os.path.join(result, item)
		return result


def current():
	return Path(os.getcwd())

userPath = Path(os.getcwd())

CHECKPYPATH = Path(os.path.abspath(os.path.dirname(__file__))[:-len("/entities")])
TESTSPATH = CHECKPYPATH + "tests"
DBPATH = CHECKPYPATH + "storage" + "downloadLocations.json"
