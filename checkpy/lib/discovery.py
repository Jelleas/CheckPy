import os
import re
from checkpy.entities.path import Path, TESTSFOLDER

def fileExists(fileName):
	return Path(fileName).exists()

def testExists(testName, module = ""):
	testFileName = testName.split(".")[0] + "Test.py"
	testFilePath = getTestFilePath(testFileName, module = module)
	return bool(testFilePath)

def getPath(path):
	filePath = os.path.dirname(path)
	if not filePath:
		filePath = os.path.dirname(os.path.abspath(path))

	fileName = os.path.basename(path)

	if "." in fileName:
		path = Path(os.path.join(filePath, fileName))
		return path if path.exists() else None

	for extension in [".py", ".ipynb"]:
		path = Path(os.path.join(filePath, fileName + extension))
		if path.exists():
			return path

	return None

def getTestNames(moduleName):
	for (dirPath, subdirs, files) in TESTSFOLDER.path.walk():
		if Path(moduleName) in dirPath:
			return [f.fileName[:-7] for f in files if f.fileName.endswith(".py") and not f.fileName.startswith("_")]

def getTestFilePath(testFileName, module = ""):
	for (dirPath, dirNames, fileNames) in TESTSFOLDER.path.walk():
		if Path(testFileName) in fileNames and (not module or Path(module) in dirPath):
			return dirPath

def _backslashToForwardslash(text):
	return re.sub("\\\\", "/", text)
