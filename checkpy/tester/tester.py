import checkpy
from checkpy import printer
from checkpy.entities import exception
from checkpy.tester import discovery
from checkpy.lib.sandbox import sandbox
from checkpy.lib.explanation import explainCompare
from checkpy.tests import Test, TestResult, TestFunction

from dataclasses import dataclass
from types import ModuleType
from typing import Dict, Iterable, List, Optional, Union

import os
import pathlib
import subprocess
import sys
import multiprocessing as mp
import importlib
import time
import traceback
import warnings

import dessert
from halo import Halo

__all__ = ["getActiveTest", "test", "testModule", "TesterResult"]


_activeTest: Optional[Test] = None


def getActiveTest() -> Optional[Test]:
    return _activeTest


def test(
    testName: str,
    module="",
    debugMode=False,
    silentMode=False
) -> Union["TesterResult", "ErroredTesterResult"]:
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

    monitor = Monitor(
        moduleName=testFileName.split(".")[0],
        fileName=path,
        debugMode=debugMode,
        silentMode=silentMode
    )
    testerResult = monitor.run()

    if path.endswith(".ipynb"):
        os.remove(path)

    testerResult.output = result.output + testerResult.output
    return testerResult


def testModule(
    module: str,
    debugMode=False,
    silentMode=False
) -> Optional[List[Union["TesterResult", "ErroredTesterResult"]]]:
    printer.printer.SILENT_MODE = silentMode
    testNames = discovery.getTestNames(module)

    if not testNames:
        printer.displayError("no tests found in module: {}".format(module))
        return None

    return [test(testName, module=module, debugMode=debugMode, silentMode=silentMode) for testName in testNames]


@dataclass
class MonitorState:
    startTime: float
    timeout: float
    isTiming: bool
    description: str
    result: "TesterResult"
    spinner: Halo


class Monitor:
    def __init__(self, moduleName: str, fileName: str, debugMode=False, silentMode=False):
        self.moduleName = moduleName
        self.fileName = fileName
        self.debugMode = debugMode
        self.silentMode = silentMode

    def run(self) -> Union["TesterResult", "ErroredTesterResult"]:
        ctx = mp.get_context("spawn")
        queue: "mp.Queue[Union[_Signal, TestResult, exception.CheckpyError]]" = ctx.Queue()

        tester = _Tester(
            self.moduleName,
            pathlib.Path(self.fileName),
            self.debugMode,
            self.silentMode,
            queue
        )
        p = ctx.Process(target=tester.run, name="Tester")
        p.start()

        state = MonitorState(
            startTime=time.time(),
            timeout=10,
            isTiming=False,
            description="",
            result=TesterResult(pathlib.Path(self.fileName).name),
            spinner=None
        )

        state.result.addOutput(printer.displayTestName(state.result.name))

        while p.is_alive():
            self.processQueue(queue, state)

            if isinstance(state.result, ErroredTesterResult):
                state.spinner.stop()
                state.spinner.clear()
                return state.result

            if state.isTiming and time.time() - state.startTime > state.timeout:
                self.processTimeout(state)
                p.terminate()
                p.join()
                return state.result

            time.sleep(0.1)

        self.processQueue(queue, state)
        state.spinner.stop()
        state.spinner.clear()
        return state.result

    def processQueue(
            self,
            queue: "mp.Queue[Union[_Signal, TestResult, exception.CheckpyError]]",
            state: MonitorState
        ):
        while not queue.empty():
            item = queue.get()
            # print(item)
            if isinstance(item, TestResult):
                self.processResult(item, state)
            elif isinstance(item, exception.CheckpyError):
                self.processError(item, state)
            else:
                self.processSignal(item, state)

    def processResult(self, result: TestResult, state: MonitorState):
        state.isTiming = False
        state.spinner.stop()
        state.spinner.clear()
        state.result.addResult(result)
        state.result.addOutput(printer.display(result))
        
    def processSignal(self, signal: "_Signal", state: MonitorState):
        if signal.description is not None:
            state.description = signal.description
        if signal.isTiming is not None:
            state.isTiming = signal.isTiming
            frames = [
                f"{printer.printer._Colors.PASS}:){printer.printer._Colors.ENDC}",
                f"{printer.printer._Colors.WARNING}:|{printer.printer._Colors.ENDC}",
                f"{printer.printer._Colors.FAIL}:({printer.printer._Colors.ENDC}",
                f"{printer.printer._Colors.WARNING}:|{printer.printer._Colors.ENDC}",
            ] * 10
            frames[10] = f"{printer.printer._Colors.PASS};){printer.printer._Colors.ENDC}"
            frames[21] = f"{printer.printer._Colors.PASS}:D{printer.printer._Colors.ENDC}"

            state.spinner = Halo(text=state.description, spinner={
                'interval': 350,
                'frames': frames
            })
            state.spinner.start()
        if signal.timeout is not None:
            state.timeout = signal.timeout
        if signal.nTests is not None:
            state.result.nTests = signal.nTests
        if signal.resetTimer:
            state.startTime = time.time()

    def processError(self, error: exception.CheckpyError, state: MonitorState):
        state.result.addOutput(printer.displayError(str(error)))
        if self.debugMode:
            state.result.addOutput(printer.displayCustom(error.stacktrace()))
        state.result = ErroredTesterResult(state.result, error) # type: ignore [assignment]

    def processTimeout(self, state: MonitorState):
        msg = f"Timeout ({state.timeout} seconds) reached during: {state.description}"
        state.result.addResult(
            TestResult(
                hasPassed=False,
                description=state.description,
                message=msg
            )
        )
        state.spinner.stop()
        state.spinner.clear()
        state.result.addOutput(printer.displayError(msg))

        nUnrunTests = state.result.nTests - len(state.result.testResults)
        if nUnrunTests > 0:
            s = "s" if nUnrunTests > 1 else ""
            state.result.addOutput(printer.displayWarning(
                f"{nUnrunTests} test{s} could not run due to the timeout"
            ))


class TesterResult:
    def __init__(self, name: str):
        self.name = name
        self.nTests = 0
        self.output: List[str] = []
        self.testResults: List[TestResult] = []

    def addOutput(self, output: str):
        self.output.append(output)

    def addResult(self, testResult: TestResult):
        self.testResults.append(testResult)

    @property
    def nRunTests(self) -> int:
        return len([t for t in self.testResults if t.hasPassed is not None])

    @property
    def nPassedTests(self) -> int:
        return len([t for t in self.testResults if t.hasPassed])

    @property
    def nFailedTests(self) -> int:
        return len([t for t in self.testResults if t.hasPassed is False])

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


class ErroredTesterResult:
    def __init__(self, testerResult: TesterResult, exception: exception.CheckpyError):
        self.name = testerResult.name
        self.output = testerResult.output[:]
        self.error = exception

    def asDict(self) -> Dict[str, Union[str, int, List]]:
        return {
            "name": self.name,
            "output": self.output,
            "error": str(self.error),
            "stacktrace": self.error.stacktrace()
        }


@dataclass
class _Signal:
    isTiming: Optional[bool]=None
    resetTimer: Optional[bool]=None
    description: Optional[str]=None
    timeout: Optional[int]=None
    nTests: Optional[int]=None


class _Tester(object):
    def __init__(
            self, 
            moduleName: str,
            filePath: pathlib.Path,
            debugMode: bool,
            silentMode: bool,
            queue: "mp.Queue[Union[_Signal, TestResult, exception.CheckpyError]]",
        ):
        self.moduleName = moduleName
        self.filePath = filePath.absolute()
        self.debugMode = debugMode
        self.silentMode = silentMode
        self.queue = queue

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

            try:
                with sandbox():
                    module = importlib.import_module(self.moduleName)
                    module._fileName = self.filePath.name # type: ignore [attr-defined]

                    self._runTestsFromModule(module)
            except Exception as e:
                stacktrace = "\n".join(traceback.format_tb(e.__traceback__))
                error = exception.CheckpyError(
                    exception=e,
                    message="while trying to run tests. This is likely a bug in the tests and not in your code. Best contact the course's staff! You can rerun checkpy with --dev to see more details.",
                    stacktrace=stacktrace
                )
                self._send(error)

    def _runTestsFromModule(self, module: ModuleType):
        self._send(_Signal(isTiming=False))

        if hasattr(module, "before"):
            module.before()

        testFunctions = [method for method in module.__dict__.values() if getattr(method, "isTestFunction", False)]

        self._send(_Signal(nTests=len(testFunctions)))

        self._runTests(testFunctions)

        if hasattr(module, "after"):
            module.after()

    def _runTests(self, testFunctions: Iterable[TestFunction]):
        def handleDescriptionChange(test: Test):
            self._send(_Signal(
                description=test.description
            ))

        def handleTimeoutChange(test: Test):
            self._send(_Signal(
                isTiming=True,
                resetTimer=True,
                timeout=test.timeout
            ))

        global _activeTest

        # run tests in noncolliding execution order
        for testFunction in self._getTestFunctionsInExecutionOrder(testFunctions):
            test = Test(
                fileName=self.filePath.name,
                priority=testFunction.priority,
                timeout=testFunction.timeout,
                onDescriptionChange=handleDescriptionChange,
                onTimeoutChange=handleTimeoutChange
            )
            
            _activeTest = test

            run = testFunction(test)

            self._send(_Signal(
                isTiming=True, 
                resetTimer=True, 
                description=test.description, 
                timeout=test.timeout
            ))

            result = run()

            _activeTest = None
            if result is not None:
                self._send(result)
    
    def _send(self, item: Union[_Signal, TestResult, exception.CheckpyError]):
        self.queue.put(item)

    def _getTestFunctionsInExecutionOrder(self, testFunctions: Iterable[TestFunction]) -> List[TestFunction]:
        sortedTFs: List[TestFunction] = []
        for tf in testFunctions:
            dependencies = self._getTestFunctionsInExecutionOrder(tf.dependencies) + [tf]
            sortedTFs.extend([t for t in dependencies if t not in sortedTFs])
        return sortedTFs
