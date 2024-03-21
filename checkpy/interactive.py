from checkpy.tester import TesterResult
from checkpy.tester import runTests as _runTests
from checkpy.tester import runTestsSynchronously as _runTestsSynchronously
from checkpy import caches as _caches
import checkpy.tester.discovery as _discovery
import pathlib as _pathlib
from typing import List, Optional

__all__ = ["testModule", "test", "testOffline"]


def testModule(moduleName: str, debugMode=False, silentMode=False) -> Optional[List[TesterResult]]:
    """
    Test all files from module
    """
    _caches.clearAllCaches()

    from . import tester
    from . import downloader
    downloader.updateSilently()

    results = tester.testModule(moduleName, debugMode = debugMode, silentMode = silentMode)

    _closeAllMatplotlib()

    return results

def test(fileName: str, debugMode=False, silentMode=False) -> TesterResult:
    """
    Run tests for a single file
    """
    _caches.clearAllCaches()

    from . import tester
    from . import downloader
    downloader.updateSilently()
    
    result = tester.test(fileName, debugMode = debugMode, silentMode = silentMode)

    _closeAllMatplotlib()

    return result

def testOffline(fileName: str, testPath: str | _pathlib.Path, multiprocessing=True, debugMode=False, silentMode=False) -> TesterResult:
    """
    Run a test offline.
    Takes in the name of file to be tested and an absolute path to the tests directory.
    If multiprocessing is True (by default), runs all tests in a seperate process. All tests run in the same process otherwise.
    """
    _caches.clearAllCaches()

    fileStem = fileName.split(".")[0]
    filePath = _discovery.getPath(fileStem)
    
    testModuleName = f"{fileStem}Test"
    testFileName = f"{fileStem}Test.py" 
    testPath = _discovery.getTestPathsFrom(testFileName, _pathlib.Path(testPath))[0]

    if multiprocessing:
        result = _runTests(testModuleName, testPath, filePath, debugMode, silentMode)
    else:
        result = _runTestsSynchronously(testModuleName, testPath, filePath, debugMode, silentMode)

    _closeAllMatplotlib()

    return result

def _closeAllMatplotlib():
    try:
        if __IPYTHON__: # type: ignore [name-defined]
            try:
                import matplotlib.pyplot
                matplotlib.pyplot.close("all")
            except:
                pass
    except:
        pass
