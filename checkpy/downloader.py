import requests
import zipfile as zf
import StringIO
import os
import shutil
import tinydb
import caches
import printer

class Path(object):
	def __init__(self, path):
		self._path = os.path.normpath(path)

	@property
	def path(self):
		return self._path

	@property
	def fileName(self):
		return os.path.basename(self.path)

	def isPythonFile(self):
		return self.fileName.endswith(".py")

	def exists(self):
		return os.path.exists(self.path)

	def walk(self):
		for path, subdirs, files in os.walk(self.path):
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
		return Path(os.path.join(self.path, other.path))

	def __sub__(self, other):
		my_items = [item for item in self]
		other_items = [item for item in other]
		return Path(reduce(lambda total, i : os.path.join(total, i), my_items[len(other_items):], ""))

	def __iter__(self):
		for item in self._path.split(os.path.sep):
			yield item

	def __repr__(self):
		return self.path

	def __hash__(self):
		return hash(repr(self))

	def __eq__(self, other):
		return isinstance(other, type(self)) and repr(self) == repr(other)

	def __contains__(self, item):
		return item in [item for item in self]

	def __nonzero__ (self):
		return len(self.path) != 0


HERE = Path(os.path.abspath(os.path.dirname(__file__)))
TESTSPATH = HERE + Path("tests")
DBPATH = HERE + Path("storage")
DBFILEPATH = DBPATH + Path("downloadLocations.json")


def download(githubLink):
	if githubLink.endswith("/"):
		githubLink = githubLink[:-1]

	username = githubLink.split("/")[-2]
	repoName = githubLink.split("/")[-1]
	_download(username, repoName)

def update():
	for username, repoName in ((entry["user"], entry["repo"]) for entry in _downloadLocationsDatabase().all()):
		download(username, repoName)

def list():
	for username, repoName in ((entry["user"], entry["repo"]) for entry in _downloadLocationsDatabase().all()):
		printer.displayCustom("{} from {}".format(repoName, username))

def clean():
	shutil.rmtree(TESTSPATH.path, ignore_errors=True)
	os.remove(DBFILEPATH.path)
	printer.displayCustom("Removed all tests")
	return

def _download(githubUserName, githubRepoName):
	githubLink = "https://github.com/{}/{}".format(githubUserName, githubRepoName)
	zipLink = githubLink + "/archive/master.zip"
	r = requests.get(zipLink)
	
	if not r.ok:
		printer.displayError("Failed to download {} because: {}".format(githubLink, r.reason))
		return

	_addToDownloadLocations(githubUserName, githubRepoName)

	with zf.ZipFile(StringIO.StringIO(r.content)) as z:
		dest = TESTSPATH + Path(githubRepoName)
		
		existingTests = set()
		for path, subdirs, files in dest.walk():
			for f in files:
				existingTests.add((path + f) - dest)

		newTests = set()
		for path in [Path(name) for name in z.namelist()]:
			if path.isPythonFile():
				newTests.add(path.pathFromFolder("tests"))

		for filePath in existingTests - newTests:
			printer.displayRemoved(filePath.path)
			os.remove((dest + filePath).path)

		for filePath in newTests - existingTests:
			printer.displayAdded(filePath.path)

		_extractTests(z, dest)

	printer.displayCustom("Finished downloading: {}".format(githubLink))

@caches.cache()
def _downloadLocationsDatabase():
	if not DBPATH.exists():
		os.makedirs(DBPATH.path)
	if not os.path.isfile(DBFILEPATH.path):
		with open(DBFILEPATH.path, 'w') as f:
			pass
	return tinydb.TinyDB(DBFILEPATH.path)

def _isKnownDownloadLocation(username, repoName):
	query = tinydb.Query()
	return _downloadLocationsDatabase().contains((query.user == username) & (query.repo == repoName))

def _addToDownloadLocations(username, repoName):
	if not _isKnownDownloadLocation(username, repoName):
		_downloadLocationsDatabase().insert({"user" : username, "repo" : repoName})
	
def _extractTests(zipfile, destPath):
	if not destPath.exists():
		os.makedirs(destPath.path)

	for path in [Path(name) for name in zipfile.namelist()]:
		_extractTest(zipfile, path, destPath)

def _extractTest(zipfile, path, destPath):
	if "tests" not in path:
		return

	subfolderPath = path.pathFromFolder("tests")
	filePath = destPath + subfolderPath

	if path.isPythonFile():
		_extractFile(zipfile, path, filePath)
	elif subfolderPath and not os.path.exists(filePath.path):
		os.makedirs(filePath.path)
			
def _extractFile(zipfile, path, filePath):
	zipPathString = path.path.replace("\\", "/")
	if os.path.isfile(filePath.path):
		with zipfile.open(zipPathString) as new, file(filePath.path, "r") as existing:
			if existing.read() != new.read():
				printer.displayUpdate(path.path)
				
	with zipfile.open(zipPathString) as source, file(filePath.path, "wb+") as target:
		shutil.copyfileobj(source, target)