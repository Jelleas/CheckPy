import printer
import requests
import zipfile as zf
import StringIO
import os
import shutil

HERE = os.path.abspath(os.path.dirname(__file__))

def download(githubLink):
	zipLink = githubLink + "/archive/master.zip"
	r = requests.get(zipLink)
	
	if not r.ok:
		printer.displayError("Failed to download: {}".format(r.reason))
		return

	with zf.ZipFile(StringIO.StringIO(r.content)) as z:
		_extractTests(z)

	printer.displayCustom("Finished downloading")

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