import printer
import caches
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
		
	_runTests(importlib.import_module(testFileName[:-3]), os.path.join(filePath, fileName))

def testModule(module):
	testNames = _getTestNames(module)

	if not testNames:
		printer.displayError("no tests found in module: {}".format(module))
		return

	for testName in testNames:
		test(testName, module = module)

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

class _Signal(object):
	def __init__(self, isTiming = False, resetTimer = False, description = None, timeout = None):
		self.isTiming = isTiming
		self.resetTimer = resetTimer
		self.description = description
		self.timeout = timeout

class _Tester(object):
	def __init__(self, module, fileName, queue):
		self.module = module
		self.fileName = fileName
		self.queue = queue

	def run(self):
		self.module._fileName = self.fileName
		self._sendSignal(_Signal(isTiming = False))

		printer.displayTestName(os.path.basename(self.module._fileName))

		if hasattr(self.module, "before"):
			try:
				self.module.before()
			except Exception as e:
				printer.displayError("Something went wrong at setup:\n{}".format(e))
				return

		reservedNames = ["before", "after"]
		testCreators = [method for method in self.module.__dict__.values() if callable(method) and method.__name__ not in reservedNames]
		self._runTests(testCreators)

		if hasattr(self.module, "after"):
			try:
				self.module.after()
			except Exception as e:
				printer.displayError("Something went wrong at closing:\n{}".format(e))

	def _runTests(self, testCreators):
		cachedResults = {}

		# run tests in noncolliding execution order
		for test in self._getTestsInExecutionOrder([tc() for tc in testCreators]):
			self._sendSignal(_Signal(isTiming = True, resetTimer = True, description = test.description(), timeout = test.timeout())) 
			cachedResults[test] = test.run()
			self._sendSignal(_Signal(isTiming = False))

		# print test results in specified order
		for test in sorted(cachedResults.keys()):
			if cachedResults[test] != None:
				printer.display(cachedResults[test])

	def _sendSignal(self, signal):
		self.queue.put(signal)

	def _getTestsInExecutionOrder(self, tests):
		testsInExecutionOrder = []
		for i, test in enumerate(tests):
			dependencies = self._getTestsInExecutionOrder([tc() for tc in test.dependencies()]) + [test]
			testsInExecutionOrder.extend([t for t in dependencies if t not in testsInExecutionOrder])
		return testsInExecutionOrder
	
def _runTests(module, fileName):
	q = multiprocessing.Queue()
	tester = _Tester(module, fileName, q)
	p = multiprocessing.Process(target=tester.run, name="Tester")
	p.start()

	start = time.time()
	isTiming = False
	
	while p.is_alive():
		while not q.empty():
			signal = q.get()
			isTiming = signal.isTiming
			description = signal.description
			timeout = signal.timeout
			if signal.resetTimer:
				start = time.time()

		if isTiming and time.time() - start > timeout:
			printer.displayError("Timeout ({} seconds) reached during: {}".format(timeout, description))
			p.terminate()
			p.join()
			return
		
		time.sleep(0.1)