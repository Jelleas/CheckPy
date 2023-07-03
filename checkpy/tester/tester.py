import checkpy
from checkpy import printer
from checkpy.entities import exception, path
from checkpy.tester import discovery
from checkpy.tester.sandbox import sandbox
from checkpy.tests import Test

import os
import pathlib
import subprocess
import sys
import importlib
import multiprocessing
import time

def test(testName, module = "", debugMode = False, silentMode = False):
	printer.printer.SILENT_MODE = silentMode

	result = TesterResult(testName)

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

	testerResult = _runTests(testFileName.split(".")[0], path, debugMode = debugMode, silentMode = silentMode)

	if path.endswith(".ipynb"):
		os.remove(path)

	testerResult.output = result.output + testerResult.output
	return testerResult


def testModule(module, debugMode = False, silentMode = False):
	printer.printer.SILENT_MODE = silentMode
	testNames = discovery.getTestNames(module)

	if not testNames:
		printer.displayError("no tests found in module: {}".format(module))
		return

	return [test(testName, module = module, debugMode = debugMode, silentMode = silentMode) for testName in testNames]

def _runTests(moduleName, fileName, debugMode = False, silentMode = False):
	if sys.version_info[:2] >= (3,4):
		ctx = multiprocessing.get_context("spawn")
	else:
		ctx = multiprocessing

	signalQueue = ctx.Queue()
	resultQueue = ctx.Queue()
	tester = _Tester(moduleName, path.Path(fileName).absolutePath(), debugMode, silentMode, signalQueue, resultQueue)
	p = ctx.Process(target=tester.run, name="Tester")
	p.start()

	start = time.time()
	isTiming = False

	while p.is_alive():
		while not signalQueue.empty():
			signal = signalQueue.get()
			
			if signal.description != None:
				description = signal.description
			if signal.isTiming != None:
				isTiming = signal.isTiming
			if signal.timeout != None:
				timeout = signal.timeout
			if signal.resetTimer:
				start = time.time()

		if isTiming and time.time() - start > timeout:
			result = TesterResult(path.Path(fileName).fileName)
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
	
	raise exception.CheckpyError(message="An error occured while testing. The testing process exited unexpectedly.")

class TesterResult(object):
	def __init__(self, name):
		self.name = name
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

	def asDict(self):
		return {"name":self.name,
				"nTests":self.nTests,
			    "nPassed":self.nPassedTests,
				"nFailed":self.nFailedTests,
				"nRun":self.nRunTests,
				"output":self.output,
				"results":[tr.asDict() for tr in self.testResults]}

class _Signal(object):
	def __init__(self, isTiming=None, resetTimer=None, description=None, timeout=None):
		self.isTiming = isTiming
		self.resetTimer = resetTimer
		self.description = description
		self.timeout = timeout

class _Tester(object):
	def __init__(self, moduleName, filePath, debugMode, silentMode, signalQueue, resultQueue):
		self.moduleName = moduleName
		self.filePath = filePath
		self.debugMode = debugMode
		self.silentMode = silentMode
		self.signalQueue = signalQueue
		self.resultQueue = resultQueue

	def run(self):
		printer.printer.DEBUG_MODE = self.debugMode
		printer.printer.SILENT_MODE = self.silentMode

		checkpy.file = pathlib.Path(self.filePath.fileName)

		# overwrite argv so that it seems the file was run directly
		sys.argv = [self.filePath.fileName]

		module = importlib.import_module(self.moduleName)
		module._fileName = self.filePath.fileName

		return self._runTestsFromModule(module)

	def _runTestsFromModule(self, module):
		self._sendSignal(_Signal(isTiming = False))

		result = TesterResult(self.filePath.fileName)
		result.addOutput(printer.displayTestName(self.filePath.fileName))

		if hasattr(module, "before"):
			try:
				module.before()
			except Exception as e:
				result.addOutput(printer.displayError("Something went wrong at setup:\n{}".format(e)))
				return

		testCreators = [method for method in module.__dict__.values() if getattr(method, "isTestFunction", False)]
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

		def handleDescriptionChange(test):
			self._sendSignal(_Signal(
				description=test.description
			))

		def handleTimeoutChange(test):
			self._sendSignal(_Signal(
				isTiming=True,
				resetTimer=True,
				timeout=test.timeout
			))

		# run tests in noncolliding execution order
		for testCreator in self._getTestCreatorsInExecutionOrder(testCreators):
			test = Test(
				self.filePath.fileName,
				testCreator.priority,
				timeout=testCreator.timeout,
				onDescriptionChange=handleDescriptionChange,
				onTimeoutChange=handleTimeoutChange
			)
			
			run = testCreator(test)

			self._sendSignal(_Signal(
				isTiming=True, 
				resetTimer=True, 
				description=test.description, 
				timeout=test.timeout
			))

			with sandbox():
				cachedResults[test] = run()

			self._sendSignal(_Signal(isTiming=False))
		
		# return test results in specified order
		return [cachedResults[test] for test in sorted(cachedResults.keys()) if cachedResults[test] != None]

	def _sendResult(self, result):
		self.resultQueue.put(result)

	def _sendSignal(self, signal):
		self.signalQueue.put(signal)

	def _getTestCreatorsInExecutionOrder(self, testCreators):
		sortedTCs = []
		for tc in testCreators:
			dependencies = self._getTestCreatorsInExecutionOrder(tc.dependencies) + [tc]
			sortedTCs.extend([t for t in dependencies if t not in sortedTCs])
		return sortedTCs
