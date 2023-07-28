import checkpy
from checkpy import printer
from checkpy.entities import exception
from checkpy.tester import discovery
from checkpy.lib.sandbox import conditionalSandbox
from checkpy.lib.explanation import explainCompare
from checkpy.tests import Test, TestResult, TestFunction

from types import ModuleType
from typing import Dict, Iterable, List, Optional, Union

import os
import pathlib
import subprocess
import sys
import importlib
import time
import warnings

import dessert
import multiprocessing as mp


__all__ = ["getActiveTest", "test", "testModule", "TesterResult"]


_activeTest: Optional[Test] = None


def getActiveTest() -> Optional[Test]:
    return _activeTest


def test(testName: str, module="", debugMode=False, silentMode=False) -> "TesterResult":
    printer.printer.SILENT_MODE = silentMode

    result = TesterResult(testName)

    discoveredPath = discovery.getPath(testName)
    if discoveredPath is None:
        result.addOutput(printer.displayError("File not found: {}".format(testName)))
        return result
    path = str(discoveredPath)

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


def testModule(module: str, debugMode=False, silentMode=False) -> Optional[List["TesterResult"]]:
    printer.printer.SILENT_MODE = silentMode
    testNames = discovery.getTestNames(module)

    if not testNames:
        printer.displayError("no tests found in module: {}".format(module))
        return None

    return [test(testName, module=module, debugMode=debugMode, silentMode=silentMode) for testName in testNames]

def _runTests(moduleName: str, fileName: str, debugMode=False, silentMode=False) -> "TesterResult":
    ctx = mp.get_context("spawn")
    
    signalQueue: "mp.Queue[_Signal]" = ctx.Queue()
    resultQueue: "mp.Queue[TesterResult]" = ctx.Queue()
    tester = _Tester(moduleName, pathlib.Path(fileName), debugMode, silentMode, signalQueue, resultQueue)
    p = ctx.Process(target=tester.run, name="Tester")
    p.start()

    start = time.time()
    isTiming = False

    while p.is_alive():
        while not signalQueue.empty():
            signal = signalQueue.get()
            
            if signal.description is not None:
                description = signal.description
            if signal.isTiming is not None:
                isTiming = signal.isTiming
            if signal.timeout is not None:
                timeout = signal.timeout
            if signal.resetTimer:
                start = time.time()

        if isTiming and time.time() - start > timeout:
            result = TesterResult(pathlib.Path(fileName).name)
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
    def __init__(self, name: str):
        self.name = name
        self.nTests = 0
        self.nPassedTests = 0
        self.nFailedTests = 0
        self.nRunTests = 0
        self.output: List[str] = []
        self.testResults: List[TestResult] = []

    def addOutput(self, output: str):
        self.output.append(output)

    def addResult(self, testResult: TestResult):
        self.testResults.append(testResult)

    def asDict(self) -> Dict[str, Union[str, int, List]]:
        return {
            "name": self.name,
            "nTests": self.nTests,
            "nPassed": self.nPassedTests,
            "nFailed": self.nFailedTests,
            "nRun": self.nRunTests,
            "output": self.output,
            "results": [tr.asDict() for tr in self.testResults]
        }


class _Signal(object):
    def __init__(
            self, 
            isTiming: Optional[bool]=None, 
            resetTimer: Optional[bool]=None, 
            description: Optional[str]=None, 
            timeout: Optional[int]=None
        ):
        self.isTiming = isTiming
        self.resetTimer = resetTimer
        self.description = description
        self.timeout = timeout


class _Tester(object):
    def __init__(
            self, 
            moduleName: str,
            filePath: pathlib.Path,
            debugMode: bool,
            silentMode: bool,
            signalQueue: "mp.Queue[_Signal]",
            resultQueue: "mp.Queue[TesterResult]"
        ):
        self.moduleName = moduleName
        self.filePath = filePath.absolute()
        self.debugMode = debugMode
        self.silentMode = silentMode
        self.signalQueue = signalQueue
        self.resultQueue = resultQueue

    def run(self):
        printer.printer.DEBUG_MODE = self.debugMode
        printer.printer.SILENT_MODE = self.silentMode

        warnings.filterwarnings("ignore")
        if self.debugMode:
            warnings.simplefilter('always', DeprecationWarning)

        checkpy.file = self.filePath

        # overwrite argv so that it seems the file was run directly
        sys.argv = [self.filePath.name]

        # have pytest (dessert) rewrite the asserts in the AST
        with dessert.rewrite_assertions_context():

            # TODO: should be a cleaner way to inject "pytest_assertrepr_compare"
            dessert.util._reprcompare = explainCompare

            with conditionalSandbox():
                module = importlib.import_module(self.moduleName)
                module._fileName = self.filePath.name # type: ignore [attr-defined]

                self._runTestsFromModule(module)

    def _runTestsFromModule(self, module: ModuleType):
        self._sendSignal(_Signal(isTiming = False))

        result = TesterResult(self.filePath.name)
        result.addOutput(printer.displayTestName(self.filePath.name))

        if hasattr(module, "before"):
            try:
                module.before()
            except Exception as e:
                result.addOutput(printer.displayError("Something went wrong at setup:\n{}".format(e)))
                return

        testFunctions = [method for method in module.__dict__.values() if getattr(method, "isTestFunction", False)]
        result.nTests = len(testFunctions)

        testResults = self._runTests(testFunctions)

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

    def _runTests(self, testFunctions: Iterable[TestFunction]) -> List[TestResult]:
        cachedResults: Dict[Test, Optional[TestResult]] = {}

        def handleDescriptionChange(test: Test):
            self._sendSignal(_Signal(
                description=test.description
            ))

        def handleTimeoutChange(test: Test):
            self._sendSignal(_Signal(
                isTiming=True,
                resetTimer=True,
                timeout=test.timeout
            ))

        global _activeTest

        # run tests in noncolliding execution order
        for testFunction in self._getTestFunctionsInExecutionOrder(testFunctions):
            test = Test(
                self.filePath.name,
                testFunction.priority,
                timeout=testFunction.timeout,
                onDescriptionChange=handleDescriptionChange,
                onTimeoutChange=handleTimeoutChange
            )
            
            _activeTest = test

            run = testFunction(test)
            
            self._sendSignal(_Signal(
                isTiming=True, 
                resetTimer=True, 
                description=test.description, 
                timeout=test.timeout
            ))

            cachedResults[test] = run()

            _activeTest = None

            self._sendSignal(_Signal(isTiming=False))
        
        # return test results in specified order
        sortedResults = [cachedResults[test] for test in sorted(cachedResults)]
        return [result for result in sortedResults if result is not None]
    
    def _sendResult(self, result: TesterResult):
        self.resultQueue.put(result)

    def _sendSignal(self, signal: _Signal):
        #return
        self.signalQueue.put(signal)

    def _getTestFunctionsInExecutionOrder(self, testFunctions: Iterable[TestFunction]) -> List[TestFunction]:
        sortedTFs: List[TestFunction] = []
        for tf in testFunctions:
            dependencies = self._getTestFunctionsInExecutionOrder(tf.dependencies) + [tf]
            sortedTFs.extend([t for t in dependencies if t not in sortedTFs])
        return sortedTFs
