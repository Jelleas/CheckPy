import printer
import os
import sys
import importlib
import re
import caches
import multiprocessing
import time
import dill

HERE = os.path.abspath(os.path.dirname(__file__))
TIMEOUT = 20 # timeout of a module set of tests in seconds

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
	
	_runTests(testModule)

def testModule(module):
	testNames = _getTestNames(module)

	if not testNames:
		printer.displayError("no tests found in module: {}".format(module))
		return

	for testName in testNames:
		test(testName, module = module)
	
def _runTests(testModule):
	def _runner(testModule):
		reservedNames = ["before", "after"]
		testCreators = [method for method in testModule.__dict__.values() if callable(method) and method.__name__ not in reservedNames]

		printer.displayTestName(os.path.basename(testModule._fileName))

		if hasattr(testModule, "before"):
			try:
				testModule.before()
			except Exception as e:
				printer.displayError("Something went wrong at setup:\n{}".format(e))
				return
		
		for test in sorted(tc() for tc in testCreators):
			testResult = test.run()
			if testResult != None:
				printer.display(testResult)
		
		if hasattr(testModule, "after"):
			try:
				testModule.after()
			except Exception as e:
				printer.displayError("Something went wrong at closing:\n{}".format(e))

	reservedNames = ["before", "after"]
	testCreators = [method for method in testModule.__dict__.values() if callable(method) and method.__name__ not in reservedNames]

	p = multiprocessing.Process(target=_runner, name="Run", args=(testModule,))
	p.start()

	start = time.time()
	while p.is_alive():
		if time.time() - start > TIMEOUT:
			printer.displayError("Timeout ({} seconds) reached, stopped testing.".format(TIMEOUT))
			p.terminate()
			p.join()
			return
		time.sleep(0.1)
	
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