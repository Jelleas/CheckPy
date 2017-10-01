from . import printer
from . import caches
import os
import sys
import importlib
import re
import multiprocessing
import time
import dill

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
		
	return _runTests(testFileName[:-3], os.path.join(filePath, fileName))

def testModule(module):
	testNames = _getTestNames(module)

	if not testNames:
		printer.displayError("no tests found in module: {}".format(module))
		return

	return [test(testName, module = module) for testName in testNames]

def _getTestNames(moduleName):
	moduleName = _backslashToForwardslash(moduleName)
	for (dirPath, dirNames, fileNames) in os.walk(os.path.join(HERE, "tests")):
		dirPath = _backslashToForwardslash(dirPath)
		if moduleName in dirPath.split("/")[-1]:
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

def _runTests(moduleName, fileName):
	signalQueue = multiprocessing.Queue()
	resultQueue = multiprocessing.Queue()
	tester = _Tester(moduleName, fileName, signalQueue, resultQueue)
	p = multiprocessing.Process(target=tester.run, name="Tester")
	p.start()

	start = time.time()
	isTiming = False
	
	while p.is_alive():
		while not signalQueue.empty():
			signal = signalQueue.get()
			isTiming = signal.isTiming
			description = signal.description
			timeout = signal.timeout
			if signal.resetTimer:
				start = time.time()

		if isTiming and time.time() - start > timeout:
			result = TesterResult()
			result.addOutput(printer.displayError("Timeout ({} seconds) reached during: {}".format(timeout, description)))
			p.terminate()
			p.join()
			return result
		
		time.sleep(0.1)

	if not resultQueue.empty():
		return resultQueue.get()

class TesterResult(object):
	def __init__(self):
		self.nTests = 0
		self.nPassedTests = 0
		self.nFailedTests = 0
		self.nRunTests = 0
		self.output = []

	def addOutput(self, output):
		self.output.append(output)

class _Signal(object):
	def __init__(self, isTiming = False, resetTimer = False, description = None, timeout = None):
		self.isTiming = isTiming
		self.resetTimer = resetTimer
		self.description = description
		self.timeout = timeout

class _Tester(object):
	def __init__(self, moduleName, fileName, signalQueue, resultQueue):
		self.moduleName = moduleName
		self.fileName = fileName
		self.signalQueue = signalQueue
		self.resultQueue = resultQueue

	def run(self):
		module = importlib.import_module(self.moduleName)
		result = TesterResult()

		module._fileName = self.fileName
		self._sendSignal(_Signal(isTiming = False))

		result.addOutput(printer.displayTestName(os.path.basename(module._fileName)))

		if hasattr(module, "before"):
			try:
				module.before()
			except Exception as e:
				result.addOutput(printer.displayError("Something went wrong at setup:\n{}".format(e)))
				return

		reservedNames = ["before", "after"]
		testCreators = [method for method in module.__dict__.values() if callable(method) and method.__name__ not in reservedNames]
		
		result.nTests = len(testCreators)

		testResults = self._runTests(testCreators)

		result.nRunTests = len(testResults)
		result.nPassedTests = len([tr for tr in testResults if tr.hasPassed])
		result.nFailedTests = len([tr for tr in testResults if not tr.hasPassed])

		for testResult in testResults:
			result.addOutput(printer.display(testResult))

		if hasattr(module, "after"):
			try:
				module.after()
			except Exception as e:
				result.addOutput(printer.displayError("Something went wrong at closing:\n{}".format(e)))

		self._sendResult(result)

	def _runTests(self, testCreators):
		cachedResults = {}

		# run tests in noncolliding execution order
		for test in self._getTestsInExecutionOrder([tc() for tc in testCreators]):
			self._sendSignal(_Signal(isTiming = True, resetTimer = True, description = test.description(), timeout = test.timeout())) 
			cachedResults[test] = test.run()
			self._sendSignal(_Signal(isTiming = False))

		# return test results in specified order
		return [cachedResults[test] for test in sorted(cachedResults.keys()) if cachedResults[test] != None]
				
	def _sendResult(self, result):
		self.resultQueue.put(result)

	def _sendSignal(self, signal):
		self.signalQueue.put(signal)

	def _getTestsInExecutionOrder(self, tests):
		testsInExecutionOrder = []
		for i, test in enumerate(tests):
			dependencies = self._getTestsInExecutionOrder([tc() for tc in test.dependencies()]) + [test]
			testsInExecutionOrder.extend([t for t in dependencies if t not in testsInExecutionOrder])
		return testsInExecutionOrder