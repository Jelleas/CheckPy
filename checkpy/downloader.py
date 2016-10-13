import requests
import zipfile as zf
import StringIO
import os
import shutil
import tinydb
import caches
import printer

HERE = os.path.abspath(os.path.dirname(__file__))
DBPATH = os.path.join(HERE, "storage")
DBFILEPATH = os.path.join(DBPATH, "downloadLocations.json")

def download(githubLink):	
	zipLink = githubLink + "/archive/master.zip"
	r = requests.get(zipLink)
	
	if not r.ok:
		printer.displayError("Failed to download {} because: {}".format(githubLink, r.reason))
		return

	_addToDownloadLocations(githubLink)

	with zf.ZipFile(StringIO.StringIO(r.content)) as z:
		_extractTests(z)

	printer.displayCustom("Finished downloading: {}".format(githubLink))

def update():
	for loc in (entry["link"] for entry in _downloadLocationsDatabase().all()):
		download(loc)

def list():
	for loc in (entry["link"] for entry in _downloadLocationsDatabase().all()):
		printer.displayCustom(loc)

def clean():
	shutil.rmtree(os.path.join(HERE, "tests"), ignore_errors=True)
	os.remove(DBFILEPATH)
	printer.displayCustom("Removed all tests")
	return

@caches.cache()
def _downloadLocationsDatabase():
	if not os.path.exists(DBPATH):
		os.makedirs(DBPATH)
	if not os.path.isfile(DBFILEPATH):
		with open(DBFILEPATH, 'w') as f:
			pass
	return tinydb.TinyDB(DBFILEPATH)

def _addToDownloadLocations(githubLink):
	query = tinydb.Query()
	if not _downloadLocationsDatabase().contains(query.link == githubLink):
		_downloadLocationsDatabase().insert({"link" : githubLink})

def _extractTests(zipfile):
	destPath = os.path.join(HERE, "tests")
	if not os.path.exists(destPath):
		os.makedirs(destPath)

	for name in zipfile.namelist():
		_extractTest(zipfile, name, destPath)

def _extractTest(zipfile, name, destPath):
	if not "/tests/" in name:
		return

	fileName = os.path.basename(name)
	subfolderName = name.split("/tests/")[1]
	filePath = os.path.join(destPath, subfolderName)

	if fileName:
		_extractFile(zipfile, name, filePath)
	elif subfolderName and not os.path.exists(filePath):
		os.makedirs(filePath)
			
def _extractFile(zipfile, name, filePath):
	if os.path.isfile(filePath):
		with zipfile.open(name) as new, file(filePath, "r") as existing:
			if existing.read() != new.read():
				printer.displayUpdate(name)
				
	with zipfile.open(name) as source, file(filePath, "wb+") as target:
		shutil.copyfileobj(source, target)