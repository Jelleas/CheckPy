import printer
import os
import sys
import importlib
import re

HERE = os.path.abspath(os.path.dirname(__file__))

def test(testName, module = ""):
	fileName = _getFileName(testName)
	filePath = _getFilePath(testName)
	if filePath not in sys.path:
		sys.path.append(filePath)

	testFileName = fileName[:-3] + "Test.py"
	testFilePath = _getTestDirPath(testFileName, module = module)
	if testFilePath is None:
		printer.displayError("No test found for {}".format(fileName))
		return
	
	if testFilePath not in sys.path:
		sys.path.append(testFilePath)
	
	testModule = importlib.import_module(testFileName[:-3])
	testModule._fileName = os.path.join(filePath, fileName)
	
	reservedNames = ["before", "after"]
	testCreators = [\
			method \
			for _, method in testModule.__dict__.iteritems() \
			if callable(method) and method.__name__ not in reservedNames\
		]

	_runTests(testModule, testCreators)

def testModule(module):
	testNames = _getTestNames(module)

	if not testNames:
		printer.displayError("no tests found in module: {}".format(module))
		return

	for testName in testNames:
		test(testName, module = module)

def _runTests(testModule, testCreators):
	printer.displayTestName(testModule.__name__)
	
	if hasattr(testModule, "before"):
		getattr(testModule, "before")()

	for test in sorted(tc() for tc in testCreators):
		printer.display(test.run())

	if hasattr(testModule, "after"):
		getattr(testModule, "after")()

def _getTestNames(moduleName):
	moduleName = _backslashToForwardslash(moduleName)
	for (dirPath, dirNames, fileNames) in os.walk(os.path.join(HERE, "tests")):
		dirPath = _backslashToForwardslash(dirPath)
		if moduleName in dirPath:
			return [fileName[:-7] for fileName in fileNames if fileName.endswith(".py") and not fileName.startswith("_")]

def _getTestDirPath(testFileName, module = ""):
	module = _backslashToForwardslash(module)
	testFileName = _backslashToForwardslash(testFileName)
	for (dirPath, dirNames, fileNames) in os.walk(os.path.join(HERE, "tests")):
		if module in _backslashToForwardslash(dirPath) and testFileName in fileNames:
			return dirPath

def _getFileName(completeFilePath):
	fileName = os.path.basename(completeFilePath)
	if not fileName.endswith(".py"):
		fileName += ".py"
	return fileName
	
def _getFilePath(completeFilePath):
	filePath = os.path.dirname(completeFilePath)
	if not filePath:
		filePath = os.path.dirname(os.path.abspath(_getFileName(completeFilePath)))
	return filePath

def _backslashToForwardslash(text):
	return re.sub("\\\\", "/", text)