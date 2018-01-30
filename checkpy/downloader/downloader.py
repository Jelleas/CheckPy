import requests
import zipfile as zf
import os
import shutil
import time
from checkpy.entities.path import Path
from checkpy import database
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

def register(localLink):
	path = Path(localLink)

	if not path.exists():
		printer.displayError("{} does not exist")
		return

	database.addToLocalTable(path)

def update():
	for username, repoName in database.forEachUserAndRepo():
		try:
			_syncRelease(username, repoName)
			_download(username, repoName)
		except exception.DownloadError as e:
			printer.displayError(str(e))

def list():
	for username, repoName in database.forEachUserAndRepo():
		printer.displayCustom("Github: {} from {}".format(repoName, username))
	for path in database.forEachLocalPath():
		printer.displayCustom("Local:  {}".format(path))

def clean():
	for path in database.forEachGithubPath():
		shutil.rmtree(str(path), ignore_errors=True)
	database.clean()
	printer.displayCustom("Removed all tests")
	return

def updateSilently():
	for username, repoName in database.forEachUserAndRepo():
		# only attempt update if 300 sec have passed
		if time.time() - database.timestampGithub(username, repoName) < 300:
			continue

		database.setTimestampGithub(username, repoName)
		try:
			if _newReleaseAvailable(username, repoName):
				_download(username, repoName)
		except exception.DownloadError as e:
			pass

def _newReleaseAvailable(githubUserName, githubRepoName):
	# unknown/new download
	if not database.isKnownGithub(githubUserName, githubRepoName):
		return True
	releaseJson = _getReleaseJson(githubUserName, githubRepoName)

	# new release id found
	if releaseJson["id"] != database.releaseId(githubUserName, githubRepoName):
		database.updateGithubTable(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])
		return True

	# no new release found
	return False

def _syncRelease(githubUserName, githubRepoName):
	releaseJson = _getReleaseJson(githubUserName, githubRepoName)

	if database.isKnownGithub(githubUserName, githubRepoName):
		database.updateGithubTable(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])
	else:
		database.addToGithubTable(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])

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
	zipLink = githubLink + "/archive/{}.zip".format(database.releaseTag(githubUserName, githubRepoName))

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
		destPath = database.githubPath(githubUserName, githubRepoName)

		existingTests = set()
		for path, subdirs, files in destPath.walk():
			for f in files:
				existingTests.add((path + f) - destPath)

		newTests = set()
		for path in [Path(name) for name in z.namelist()]:
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

def _extractTests(zipfile, destPath):
	if not destPath.exists():
		os.makedirs(str(destPath))

	for path in [Path(name) for name in zipfile.namelist()]:
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
