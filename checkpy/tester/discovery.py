import os
import re
import checkpy.database as database
from checkpy.entities.path import Path

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
	for testsPath in database.forEachTestsPath():
		for (dirPath, subdirs, files) in testsPath.walk():
			if Path(moduleName) in dirPath:
				return [f[:-len("test.py")] for f in files if f.lower().endswith("test.py")]

def getTestPaths(testFileName, module = ""):
	testFilePaths = []
	for testsPath in database.forEachTestsPath():
		for (dirPath, dirNames, fileNames) in testsPath.walk():
			if testFileName in fileNames and (not module or module in dirPath):
				testFilePaths.append(dirPath)
	return testFilePaths
