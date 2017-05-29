import requests
import zipfile as zf
import StringIO
import os
import shutil
import tinydb
import time
import caches
import printer
import exception

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
		if isinstance(other, str) or isinstance(other, unicode):
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

	def __nonzero__ (self):
		return len(self.asString()) != 0


HERE = Path(os.path.abspath(os.path.dirname(__file__)))
HEREFOLDER = Folder(HERE.folderName, HERE)
TESTSFOLDER = Folder("tests", HERE + "tests")
DBFOLDER = Folder("storage", HERE + "storage")
DBFILE = File("downloadLocations.json", DBFOLDER.path + "downloadLocations.json")


def download(githubLink):
	if githubLink.endswith("/"):
		githubLink = githubLink[:-1]

	if "/" not in githubLink:
		printer.displayError("{} is not a valid download location".format(githubLink))
		return

	username = githubLink.split("/")[-2]
	repoName = githubLink.split("/")[-1]

	try:
		_syncRelease(username, repoName)
		_download(username, repoName)
	except exception.DownloadError as e:
		printer.displayError(str(e))
	
def update():
	for username, repoName in _forEachUserAndRepo():
		try:
			_syncRelease(username, repoName)
			_download(username, repoName)
		except exception.DownloadError as e:
			printer.displayError(str(e))
		
def list():
	for username, repoName in _forEachUserAndRepo():
		printer.displayCustom("{} from {}".format(repoName, username))

def clean():
	shutil.rmtree(TESTSFOLDER.pathAsString(), ignore_errors=True)
	if (DBFILE.path.exists()):
		os.remove(DBFILE.pathAsString())
	printer.displayCustom("Removed all tests")
	return

def updateSilently():
	for username, repoName in _forEachUserAndRepo():
		# only attempt update if 300 sec have passed
		if time.time() - _timestamp(username, repoName) < 300:
			continue
		
		_setTimestamp(username, repoName)	
		try:
			if _newReleaseAvailable(username, repoName):	
				_download(username, repoName)
		except exception.DownloadError as e:
			pass

def _newReleaseAvailable(githubUserName, githubRepoName):
	githubUserName = githubUserName.lower()
	githubRepoName = githubRepoName.lower()

	# unknown/new download
	if not _isKnownDownloadLocation(githubUserName, githubRepoName):
		return True

	releaseJson = _getReleaseJson(githubUserName, githubRepoName)

	# new release id found
	if releaseJson["id"] != _releaseId(githubUserName, githubRepoName):
		_updateDownloadLocations(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])
		return True

	# no new release found
	return False

def _syncRelease(githubUserName, githubRepoName):
	releaseJson = _getReleaseJson(githubUserName, githubRepoName)

	if _isKnownDownloadLocation(githubUserName, githubRepoName):
		_updateDownloadLocations(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])
	else:
		_addToDownloadLocations(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])
	
# this performs one api call, beware of rate limit!!!
# returns a dictionary representing the json returned by github
# incase of an error, raises an exception.DownloadError
def _getReleaseJson(githubUserName, githubRepoName):
	apiReleaseLink = "https://api.github.com/repos/{}/{}/releases/latest".format(githubUserName, githubRepoName)
	
	try:
		r = requests.get(apiReleaseLink)	
	except requests.exceptions.ConnectionError as e:
		raise exception.DownloadError(message = "Oh no! It seems like there is no internet connection available?!")

	# exceeded rate limit, 
	if r.status_code == 403:
		raise exception.DownloadError(message = "Tried finding new releases from {}/{} but exceeded the rate limit, try again within an hour!".format(githubUserName, githubRepoName))
		
	# no releases found or page not found
	if r.status_code == 404:
		raise exception.DownloadError(message = "Failed to check for new tests from {}/{} because: no releases found (404)".format(githubUserName, githubRepoName))
		
	# random error
	if not r.ok:
		raise exception.DownloadError(message = "Failed to sync releases from {}/{} because: {}".format(githubUserName, githubRepoName, r.reason))
		
	return r.json()

# download tests for githubUserName and githubRepoName from what is known in downloadlocations.json
# use _syncRelease() to force an update in downloadLocations.json
def _download(githubUserName, githubRepoName):
	githubUserName = githubUserName.lower()
	githubRepoName = githubRepoName.lower()

	githubLink = "https://github.com/{}/{}".format(githubUserName, githubRepoName)
	zipLink = githubLink + "/archive/{}.zip".format(_releaseTag(githubUserName, githubRepoName))
	
	try:
		r = requests.get(zipLink)
	except requests.exceptions.ConnectionError as e:
		raise exception.DownloadError(message = "Oh no! It seems like there is no internet connection available?!")

	if not r.ok:
		raise exception.DownloadError(message = "Failed to download {} because: {}".format(githubLink, r.reason))

	with zf.ZipFile(StringIO.StringIO(r.content)) as z:
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

def _forEachUserAndRepo():
	for username, repoName in ((entry["user"], entry["repo"]) for entry in _downloadLocationsDatabase().all()):
		yield username, repoName	

def _isKnownDownloadLocation(username, repoName):
	query = tinydb.Query()
	return _downloadLocationsDatabase().contains((query.user == username) & (query.repo == repoName))

def _addToDownloadLocations(username, repoName, releaseId, releaseTag):
	if not _isKnownDownloadLocation(username, repoName):
		_downloadLocationsDatabase().insert(\
			{
				"user" 		: username,
				"repo" 		: repoName,
				"release" 		: releaseId,
				"tag" 			: releaseTag,
				"timestamp" 	: time.time()
			})

def _updateDownloadLocations(username, repoName, releaseId, releaseTag):
	query = tinydb.Query()
	_downloadLocationsDatabase().update(\
		{
			"user" 		: username,
			"repo" 		: repoName,
			"release" 		: releaseId,
			"tag" 			: releaseTag,
			"timestamp" 	: time.time()
		}, query.user == username and query.repo == repoName)

def _timestamp(username, repoName):
	query = tinydb.Query()
	return _downloadLocationsDatabase().search(query.user == username and query.repo == repoName)[0]["timestamp"]

def _setTimestamp(username, repoName):
	query = tinydb.Query()
	_downloadLocationsDatabase().update(\
		{
			"timestamp" : time.time()
		}, query.user == username and query.repo == repoName)

def _releaseId(username, repoName):
	query = tinydb.Query()
	return _downloadLocationsDatabase().search(query.user == username and query.repo == repoName)[0]["release"]

def _releaseTag(username, repoName):
	query = tinydb.Query()
	return _downloadLocationsDatabase().search(query.user == username and query.repo == repoName)[0]["tag"]

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
			if new.read().strip() != existing.read().strip():
				printer.displayUpdate(path.asString())
				
	with zipfile.open(zipPathString) as source, file(filePath.asString(), "wb+") as target:
		shutil.copyfileobj(source, target)