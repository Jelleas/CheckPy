import printer
import os
import sys
import importlib
import re

HERE = os.path.abspath(os.path.dirname(__file__))

def test(testName, module = ""):
	filePath, fileName = _getFilePathAndName(testName)
	sys.path.append(filePath)

	testPath = _getTestDirPath(fileName[:-3] + "Test.py", module = module)
	if testPath is None:
		printer.displayError("No test found for {}".format(fileName))
		return
	
	sys.path.append(testPath)
	testModule = importlib.import_module(fileName[:-3] + "Test")
	testModule._fileName = os.path.join(filePath, fileName)
	
	testCreators = [\
			method \
			for _, method in testModule.__dict__.iteritems() \
			if callable(method) and method.__name__ != "before" and method.__name__ != "after"\
		]

	printer.displayTestName(testName)

	if hasattr(testModule, "before"):
		getattr(testModule, "before")()

	for test in sorted(tc() for tc in testCreators):
		printer.display(test.run())

	if hasattr(testModule, "after"):
		getattr(testModule, "after")()

def testModule(module):
	testNames = _getTestNames(module)
	if not testNames:
		printer.displayError("no tests found in module: {}".format(module))
		return
	for testName in testNames:
		test(testName, module = module)

def _getTestNames(moduleName):
	moduleName = backslashToForwardslash(moduleName)
	for (dirPath, dirNames, fileNames) in os.walk(os.path.join(HERE, "tests")):
		dirPath = backslashToForwardslash(dirPath)
		if moduleName in dirPath:
			return [fileName[:-7] for fileName in fileNames if fileName.endswith(".py") and not fileName.startswith("_")]

def _getTestDirPath(testFileName, module = ""):
	module = backslashToForwardslash(module)
	testFileName = backslashToForwardslash(testFileName)
	for (dirPath, dirNames, fileNames) in os.walk(os.path.join(HERE, "tests")):
		dirPath = backslashToForwardslash(dirPath)
		if module in dirPath and testFileName in fileNames:
			return dirPath

def _getFilePathAndName(completeFilePath):
	if not completeFilePath.endswith(".py"):
		completeFilePath += ".py"
	
	filePath = os.path.dirname(completeFilePath)
	fileName = os.path.basename(completeFilePath)

	# in case of no path given
	if not filePath:
		filePath = os.path.dirname(os.path.abspath(fileName))
	
	return filePath, fileName

def backslashToForwardslash(text):
	return re.sub("\\\\", "/", text)