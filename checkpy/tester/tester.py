from checkpy import printer
from checkpy import caches
from checkpy.entities import exception
from checkpy.tester import discovery
import os
import subprocess
import sys
import importlib
import re
import multiprocessing
import time
import dill

def test(testName, module = "", debugMode = False):
	result = TesterResult()

	path = discovery.getPath(testName)
	if not path:
		result.addOutput(printer.displayError("File not found: {}".format(testName)))
		return result
	path = str(path)

	fileName = os.path.basename(path)
	filePath = os.path.dirname(path)

	if filePath not in sys.path:
		sys.path.append(filePath)

	testFileName = fileName.split(".")[0] + "Test.py"
	testPaths = discovery.getTestPaths(testFileName, module = module)

	if not testPaths:
		result.addOutput(printer.displayError("No test found for {}".format(fileName)))
		return result

	if len(testPaths) > 1:
		result.addOutput(printer.displayWarning("Found {} tests: {}, using: {}".format(len(testPaths), testPaths, testPaths[0])))
	
	testFilePath = str(testPaths[0])

	if testFilePath not in sys.path:
		sys.path.append(testFilePath)

	if path.endswith(".ipynb"):
		if subprocess.call(['jupyter', 'nbconvert', '--to', 'script', path]) != 0:
			result.addOutput(printer.displayError("Failed to convert Jupyter notebook to .py"))
			return result

		path = path.replace(".ipynb", ".py")

		# remove all magic lines from notebook
		with open(path, "r") as f:
			lines = f.readlines()
		with open(path, "w") as f:
			f.write("".join([l for l in lines if "get_ipython" not in l]))

		testerResult = _runTests(testFileName.split(".")[0], path, debugMode = debugMode)

		os.remove(path)
	else:
		testerResult = _runTests(testFileName.split(".")[0], path, debugMode = debugMode)
	
	testerResult.output = result.output + testerResult.output
	return testerResult
		

def testModule(module, debugMode = False):
	testNames = discovery.getTestNames(module)

	if not testNames:
		printer.displayError("no tests found in module: {}".format(module))
		return

	return [test(testName, module = module, debugMode = debugMode) for testName in testNames]

def _runTests(moduleName, fileName, debugMode = False):
	if sys.version_info[:2] >= (3,4):
		ctx = multiprocessing.get_context("spawn")
	else:
		ctx = multiprocessing

	signalQueue = ctx.Queue()
	resultQueue = ctx.Queue()
	tester = _Tester(moduleName, fileName, debugMode, signalQueue, resultQueue)
	p = ctx.Process(target=tester.run, name="Tester")
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

		if not resultQueue.empty():
			p.terminate()
			p.join()
			break

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
		self.testResults = []

	def addOutput(self, output):
		self.output.append(output)

	def addResult(self, testResult):
		self.testResults.append(testResult)

class _Signal(object):
	def __init__(self, isTiming = False, resetTimer = False, description = None, timeout = None):
		self.isTiming = isTiming
		self.resetTimer = resetTimer
		self.description = description
		self.timeout = timeout

class _Tester(object):
	def __init__(self, moduleName, fileName, debugMode, signalQueue, resultQueue):
		self.moduleName = moduleName
		self.fileName = fileName
		self.debugMode = debugMode
		self.signalQueue = signalQueue
		self.resultQueue = resultQueue

	def run(self):
		if self.debugMode:
			printer.DEBUG_MODE = True

		# overwrite argv so that it seems the file was run directly
		sys.argv = [self.fileName]

		module = importlib.import_module(self.moduleName)
		module._fileName = self.fileName

		self._sendSignal(_Signal(isTiming = False))

		result = TesterResult()
		result.addOutput(printer.displayTestName(os.path.basename(self.fileName)))

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
			result.addResult(testResult)
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
		for test in self._getTestsInExecutionOrder([tc(self.fileName) for tc in testCreators]):
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
			dependencies = self._getTestsInExecutionOrder([tc(self.fileName) for tc in test.dependencies()]) + [test]
			testsInExecutionOrder.extend([t for t in dependencies if t not in testsInExecutionOrder])
		return testsInExecutionOrder
