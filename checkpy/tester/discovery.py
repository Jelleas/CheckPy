import os
import re
from checkpy.entities.path import Path, TESTSPATH

def testExists(testName, module = ""):
	testFileName = testName.split(".")[0] + "Test.py"
	testPaths = getTestPaths(testFileName, module = module)
	return len(testPaths) > 0

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
	for (dirPath, subdirs, files) in TESTSPATH.walk():
		if Path(moduleName) in dirPath:
			return [f.fileName[:-7] for f in files if f.fileName.endswith(".py") and not f.fileName.startswith("_")]

def getTestPaths(testFileName, module = ""):
	testFilePaths = []
	for (dirPath, dirNames, fileNames) in TESTSPATH.walk():
		if Path(testFileName) in fileNames and (not module or Path(module) in dirPath):
			testFilePaths.append(dirPath)
	return testFilePaths

def _backslashToForwardslash(text):
	return re.sub("\\\\", "/", text)
