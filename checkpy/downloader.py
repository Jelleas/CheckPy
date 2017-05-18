import requests
import zipfile as zf
import io
import os
import shutil
import tinydb
from . import caches
from . import printer
from functools import reduce

class Folder(object):
	def __init__(self, name, path):
		self.name = name
		self.path = path

	def pathAsString(self):
		return self.path.asString()

class File(object):
	def __init__(self, name, path):
		self.name = name
		self.path = path

	def pathAsString(self):
		return self.path.asString()

class Path(object):
	def __init__(self, path):
		self._path = os.path.normpath(path)

	@property
	def fileName(self):
		return os.path.basename(self.asString())

	@property
	def folderName(self):
		_, name = os.path.split(os.path.dirname(self.asString()))
		return name

	def asString(self):
		return self._path

	def isPythonFile(self):
		return self.fileName.endswith(".py")

	def exists(self):
		return os.path.exists(self.asString())

	def walk(self):
		for path, subdirs, files in os.walk(self.asString()):
			yield Path(path), [Path(sd) for sd in subdirs], [Path(f) for f in files]

	def pathFromFolder(self, folderName):
		path = ""
		seen = False
		for item in self:
			if seen:
				path = os.path.join(path, item)
			if item == folderName:
				seen = True
		return Path(path)

	def __add__(self, other):
		if isinstance(other, str) or isinstance(other, str):
			return Path(os.path.join(self.asString(), other))
		return Path(os.path.join(self.asString(), other.asString()))

	def __sub__(self, other):
		my_items = [item for item in self]
		other_items = [item for item in other]
		return Path(reduce(lambda total, i : os.path.join(total, i), my_items[len(other_items):], ""))

	def __iter__(self):
		for item in self.asString().split(os.path.sep):
			yield item

	def __repr__(self):
		return self.asString()

	def __hash__(self):
		return hash(repr(self))

	def __eq__(self, other):
		return isinstance(other, type(self)) and repr(self) == repr(other)

	def __contains__(self, item):
		return item in [item for item in self]

	def __bool__ (self):
		return len(self.asString()) != 0


HERE = Path(os.path.abspath(os.path.dirname(__file__)))
HEREFOLDER = Folder(HERE.folderName, HERE)
TESTSFOLDER = Folder("tests", HERE + "tests")
DBFOLDER = Folder("storage", HERE + "storage")
DBFILE = File("downloadLocations.json", DBFOLDER.path + "downloadLocations.json")


def download(githubLink):
	if githubLink.endswith("/"):
		githubLink = githubLink[:-1]

	username = githubLink.split("/")[-2]
	repoName = githubLink.split("/")[-1]
	_download(username, repoName)

def update():
	for username, repoName in ((entry["user"], entry["repo"]) for entry in _downloadLocationsDatabase().all()):
		_download(username, repoName)

def list():
	for username, repoName in ((entry["user"], entry["repo"]) for entry in _downloadLocationsDatabase().all()):
		printer.displayCustom("{} from {}".format(repoName, username))

def clean():
	shutil.rmtree(TESTSFOLDER.pathAsString(), ignore_errors=True)
	if (DBFILE.path.exists()):
		os.remove(DBFILE.pathAsString())
	printer.displayCustom("Removed all tests")
	return

def _download(githubUserName, githubRepoName):
	githubUserName = githubUserName.lower()
	githubRepoName = githubRepoName.lower()

	githubLink = "https://github.com/{}/{}".format(githubUserName, githubRepoName)
	zipLink = githubLink + "/archive/master.zip"
	r = requests.get(zipLink)
	
	if not r.ok:
		printer.displayError("Failed to download {} because: {}".format(githubLink, r.reason))
		return

	_addToDownloadLocations(githubUserName, githubRepoName)

	with zf.ZipFile(io.StringIO(r.content)) as z:
		destFolder = Folder(githubRepoName, TESTSFOLDER.path + githubRepoName)
		
		existingTests = set()
		for path, subdirs, files in destFolder.path.walk():
			for f in files:
				existingTests.add((path + f) - destFolder.path)

		newTests = set()
		for path in [Path(name) for name in z.namelist()]:
			if path.isPythonFile():
				newTests.add(path.pathFromFolder("tests"))

		for filePath in [fp for fp in existingTests - newTests if fp.isPythonFile()]:
			printer.displayRemoved(filePath.asString())

		for filePath in [fp for fp in newTests - existingTests if fp.isPythonFile()]:
			printer.displayAdded(filePath.asString())

		for filePath in existingTests - newTests:
			os.remove((destFolder.path + filePath).asString())

		_extractTests(z, destFolder)

	printer.displayCustom("Finished downloading: {}".format(githubLink))

@caches.cache()
def _downloadLocationsDatabase():
	if not DBFOLDER.path.exists():
		os.makedirs(DBFOLDER.pathAsString())
	if not os.path.isfile(DBFILE.pathAsString()):
		with open(DBFILE.pathAsString(), 'w') as f:
			pass
	return tinydb.TinyDB(DBFILE.pathAsString())

def _isKnownDownloadLocation(username, repoName):
	query = tinydb.Query()
	return _downloadLocationsDatabase().contains((query.user == username) & (query.repo == repoName))

def _addToDownloadLocations(username, repoName):
	if not _isKnownDownloadLocation(username, repoName):
		_downloadLocationsDatabase().insert({"user" : username, "repo" : repoName})
	
def _extractTests(zipfile, destFolder):
	if not destFolder.path.exists():
		os.makedirs(destFolder.pathAsString())

	for path in [Path(name) for name in zipfile.namelist()]:
		_extractTest(zipfile, path, destFolder)

def _extractTest(zipfile, path, destFolder):
	if "tests" not in path:
		return

	subfolderPath = path.pathFromFolder("tests")
	filePath = destFolder.path + subfolderPath

	if path.isPythonFile():
		_extractFile(zipfile, path, filePath)
	elif subfolderPath and not os.path.exists(filePath.asString()):
		os.makedirs(filePath.asString())
			
def _extractFile(zipfile, path, filePath):
	zipPathString = path.asString().replace("\\", "/")
	if os.path.isfile(filePath.asString()):
		with zipfile.open(zipPathString) as new, file(filePath.asString(), "r") as existing:
			if existing.read() != new.read():
				printer.displayUpdate(path.asString())
				
	with zipfile.open(zipPathString) as source, file(filePath.asString(), "wb+") as target:
		shutil.copyfileobj(source, target)