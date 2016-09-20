import printer
import requests
import zipfile
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

	with zipfile.ZipFile(StringIO.StringIO(r.content)) as z:
		_extractTests(z)

	printer.displayCustom("Finished downloading")

def _extractTests(zipfile):
	destPath = os.path.join(HERE, "tests")
	if not os.path.exists(destPath):
		os.makedirs(destPath)

	getSubfolderName = lambda x : x.split("/tests/")[1]

	for name in zipfile.namelist():
		fileName = os.path.basename(name)

		# extract directories
		if not fileName:
			if "/tests/" in name:
				subfolderName = getSubfolderName(name)
				target = os.path.join(destPath, subfolderName)
				if subfolderName and not os.path.exists(target):
					os.makedirs(target)
			continue

		# extract files
		if "/tests/" in name:
			subfolderName = getSubfolderName(name)
			targetPath = os.path.join(destPath, subfolderName)

			# report updates of existing files
			with zipfile.open(name) as source:
				if os.path.isfile(targetPath):
					with file(targetPath, "r") as existingFile:
						if existingFile.read() != source.read():
							printer.displayUpdate(name)

			# copy zipped file to actual file
			source = zipfile.open(name)
			target = file(os.path.join(destPath, subfolderName), "wb+")
			with source, target:
				shutil.copyfileobj(source, target)
