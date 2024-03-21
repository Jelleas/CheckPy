import os
import checkpy.database as database
import pathlib
from typing import Optional, List, Union

def testExists(testName: str, module: str="") -> bool:
    testFileName = testName.split(".")[0] + "Test.py"
    testPaths = getTestPaths(testFileName, module=module)
    return len(testPaths) > 0

def getPath(path: Union[str, pathlib.Path]) -> Optional[pathlib.Path]:
    filePath = os.path.dirname(path)
    if not filePath:
        filePath = os.path.dirname(os.path.abspath(path))

    fileName = os.path.basename(path)

    if "." in fileName:
        path = pathlib.Path(os.path.join(filePath, fileName))
        return path if path.exists() else None

    for extension in [".py", ".ipynb"]:
        path = pathlib.Path(os.path.join(filePath, fileName + extension))
        if path.exists():
            return path

    return None

def getTestNames(moduleName: str) -> Optional[List[str]]:
    for testsPath in database.forEachTestsPath():
        for (dirPath, subdirs, files) in os.walk(testsPath):
            if moduleName in dirPath:
                return [f[:-len("test.py")] for f in files if f.lower().endswith("test.py")]
    return None

def getTestPaths(testFileName: str, module: str="") -> List[pathlib.Path]:
    testFilePaths: List[pathlib.Path] = []
    for testPath in database.forEachTestsPath():
        testFilePaths.extend(getTestPathsFrom(testFileName, testPath, module=module))
    return testFilePaths

def getTestPathsFrom(testFileName: str, path: pathlib.Path, module: str="") -> List[pathlib.Path]:
    """Get all testPaths from a tests folder (path)."""
    testFilePaths: List[pathlib.Path] = []
    for (dirPath, _, fileNames) in os.walk(path):
        if testFileName in fileNames and (not module or module in dirPath):
            testFilePaths.append(pathlib.Path(dirPath))
    return testFilePaths