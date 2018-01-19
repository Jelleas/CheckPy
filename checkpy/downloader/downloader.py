import requests
import zipfile as zf
import os
import shutil
import tinydb
import time
import checkpy.entities.path as checkpyPath
from checkpy import caches
from checkpy import printer
from checkpy.entities import exception

def download(githubLink):
	if githubLink.endswith("/"):
		githubLink = githubLink[:-1]

	if "/" not in githubLink:
		printer.displayError("{} is not a valid download location".format(githubLink))
		return

	username = githubLink.split("/")[-2].lower()
	repoName = githubLink.split("/")[-1].lower()

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
	shutil.rmtree(str(checkpyPath.TESTSPATH), ignore_errors=True)
	if checkpyPath.DBPATH.exists():
		os.remove(str(checkpyPath.DBPATH))
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
	githubLink = "https://github.com/{}/{}".format(githubUserName, githubRepoName)
	zipLink = githubLink + "/archive/{}.zip".format(_releaseTag(githubUserName, githubRepoName))

	try:
		r = requests.get(zipLink)
	except requests.exceptions.ConnectionError as e:
		raise exception.DownloadError(message = "Oh no! It seems like there is no internet connection available?!")

	if not r.ok:
		raise exception.DownloadError(message = "Failed to download {} because: {}".format(githubLink, r.reason))

	try:
		# Python 2
		import StringIO
		f = StringIO.StringIO(r.content)
	except ImportError:
		# Python 3
		import io
		f = io.BytesIO(r.content)

	with zf.ZipFile(f) as z:
		destPath = checkpyPath.TESTSPATH + githubRepoName

		existingTests = set()
		for path, subdirs, files in destPath.walk():
			for f in files:
				existingTests.add((path + f) - destPath)

		newTests = set()
		for path in [checkpyPath.Path(name) for name in z.namelist()]:
			if path.isPythonFile():
				newTests.add(path.pathFromFolder("tests"))

		for filePath in [fp for fp in existingTests - newTests if fp.isPythonFile()]:
			printer.displayRemoved(str(filePath))

		for filePath in [fp for fp in newTests - existingTests if fp.isPythonFile()]:
			printer.displayAdded(str(filePath))

		for filePath in existingTests - newTests:
			os.remove(str(destPath + filePath))

		_extractTests(z, destPath)

	printer.displayCustom("Finished downloading: {}".format(githubLink))

def _downloadLocationsDatabase():
	if not checkpyPath.DBPATH.containingFolder().exists():
		os.makedirs(str(checkpyPath.DBPATH.containingFolder()))
	if not checkpyPath.DBPATH.exists():
		with open(str(checkpyPath.DBPATH), 'w') as f:
			pass
	return tinydb.TinyDB(str(checkpyPath.DBPATH))

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
				"user" 			: username,
				"repo" 			: repoName,
				"release" 		: releaseId,
				"tag" 			: releaseTag,
				"timestamp" 	: time.time()
			})

def _updateDownloadLocations(username, repoName, releaseId, releaseTag):
	query = tinydb.Query()
	_downloadLocationsDatabase().update(\
		{
			"user" 			: username,
			"repo" 			: repoName,
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

def _extractTests(zipfile, destPath):
	if not destPath.exists():
		os.makedirs(str(destPath))

	for path in [checkpyPath.Path(name) for name in zipfile.namelist()]:
		_extractTest(zipfile, path, destPath)

def _extractTest(zipfile, path, destPath):
	if "tests" not in path:
		return

	subfolderPath = path.pathFromFolder("tests")
	filePath = destPath + subfolderPath

	if path.isPythonFile():
		_extractFile(zipfile, path, filePath)
	elif subfolderPath and not os.path.exists(str(filePath)):
		os.makedirs(str(filePath))

def _extractFile(zipfile, path, filePath):
	zipPathString = str(path).replace("\\", "/")
	if os.path.isfile(str(filePath)):
		with zipfile.open(zipPathString) as new, open(str(filePath), "r") as existing:
			# read file, decode, strip trailing whitespace, remove carrier return
			newText = ''.join(new.read().decode('utf-8').strip().splitlines())
			existingText = ''.join(existing.read().strip().splitlines())
			if newText != existingText:
				printer.displayUpdate(str(path))

	with zipfile.open(zipPathString) as source, open(str(filePath), "wb+") as target:
		shutil.copyfileobj(source, target)
