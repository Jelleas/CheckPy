import contextlib
import os
import pathlib
import re
import shutil
import sys
import traceback

from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, List, Optional, Tuple, Union
from warnings import warn

import checkpy
import checkpy.tester
from checkpy.entities import path, exception, function
from checkpy import caches
from checkpy.lib.static import getSource
import checkpy.lib.io

__all__ = [
    "getFunction",
    "getModule",
    "outputOf",
    "getModuleAndOutputOf",
]

def getFunction(
        functionName: str,
        fileName: Optional[Union[str, Path]]=None,
        src: Optional[str]=None,
        argv: Optional[List[str]]=None,
        stdinArgs: Optional[List[str]]=None,
        ignoreExceptions: Iterable[Exception]=(),
        overwriteAttributes: Iterable[Tuple[str, Any]]=()
) -> function.Function:
    """Run the file, ignore any side effects, then get the function with functionName"""
    module = _getModuleAndOutputOf(
        fileName=fileName,
        src=src,
        argv=argv,
        stdinArgs=stdinArgs,
        ignoreExceptions=ignoreExceptions,
        overwriteAttributes=overwriteAttributes
    )[0]

    if functionName not in module.__dict__:
        raise AssertionError(
            f"Function '{functionName}' not found in module '{module.__name__}'"
        )

    return getattr(module, functionName)


def outputOf(
        fileName: Optional[Union[str, Path]]=None,
        src: Optional[str]=None,
        argv: Optional[List[str]]=None,
        stdinArgs: Optional[List[str]]=None,
        ignoreExceptions: Iterable[Exception]=(),
        overwriteAttributes: Iterable[Tuple[str, Any]]=()
) -> str:
    """Get the output after running the file."""
    _, output = _getModuleAndOutputOf(
        fileName=fileName,
        src=src,
        argv=argv,
        stdinArgs=stdinArgs,
        ignoreExceptions=ignoreExceptions,
        overwriteAttributes=overwriteAttributes
    )
    checkpy.lib.addOutput(output)
    return output


def getModule(
        fileName: Optional[Union[str, Path]]=None,
        src: Optional[str]=None,
        argv: Optional[List[str]]=None,
        stdinArgs: Optional[List[str]]=None,
        ignoreExceptions: Iterable[Exception]=(),
        overwriteAttributes: Iterable[Tuple[str, Any]]=()
) -> ModuleType:
    """Get the python Module after running the file."""
    mod, output = _getModuleAndOutputOf(
        fileName=fileName,
        src=src,
        argv=argv,
        stdinArgs=stdinArgs,
        ignoreExceptions=ignoreExceptions,
        overwriteAttributes=overwriteAttributes
    )
    checkpy.lib.addOutput(output)
    return mod


def getModuleAndOutputOf(
        fileName: Optional[Union[str, Path]]=None,
        src: Optional[str]=None,
        argv: Optional[List[str]]=None,
        stdinArgs: Optional[List[str]]=None,
        ignoreExceptions: Iterable[Exception]=(),
        overwriteAttributes: Iterable[Tuple[str, Any]]=()
    ) -> Tuple[ModuleType, str]:
    """
    This function handles most of checkpy's under the hood functionality

    fileName (optional): the name of the file to run
    src (optional): the source code to run
    argv (optional): set sys.argv to argv before importing,
    stdinArgs (optional): arguments passed to stdin
    ignoreExceptions (optional): exceptions that will silently pass while importing
    overwriteAttributes (optional): attributes to overwrite in the imported module
    """
    mod, output = _getModuleAndOutputOf(
        fileName=fileName,
        src=src,
        argv=argv,
        stdinArgs=stdinArgs,
        ignoreExceptions=ignoreExceptions,
        overwriteAttributes=overwriteAttributes
    )
    checkpy.lib.addOutput(output)
    return mod, output

@caches.cache()
def _getModuleAndOutputOf(
        fileName: Optional[Union[str, Path]]=None,
        src: Optional[str]=None,
        argv: Optional[List[str]]=None,
        stdinArgs: Optional[List[str]]=None,
        ignoreExceptions: Iterable[Exception]=(),
        overwriteAttributes: Iterable[Tuple[str, Any]]=()
    ) -> Tuple[ModuleType, str]:
    """
    This function handles most of checkpy's under the hood functionality

    fileName (optional): the name of the file to run
    src (optional): the source code to run
    argv (optional): set sys.argv to argv before importing,
    stdinArgs (optional): arguments passed to stdin
    ignoreExceptions (optional): exceptions that will silently pass while importing
    overwriteAttributes (optional): attributes to overwrite in the imported module
    """
    if fileName is None:
        if checkpy.file is None:
            raise checkpy.entities.exception.CheckpyError(
                message=f"Cannot call getModuleAndOutputOf() without passing fileName as argument if not test is running."
            )
        fileName = checkpy.file.name

    if src is None:
        src = getSource(fileName)

    mod = None
    output = ""
    excep = None

    with checkpy.lib.io.captureStdout() as stdoutListener:
        # fill stdin with args
        if stdinArgs:
            for arg in stdinArgs:
                sys.stdin.write(str(arg) + "\n")
            sys.stdin.seek(0)

        # if argv given, overwrite sys.argv
        if argv:
            sys.argv, argv = argv, sys.argv

        if any(name == "__name__" and attr == "__main__" for name, attr in overwriteAttributes):
            moduleName = "__main__"
        else:
            moduleName = str(fileName).split(".")[0]

        mod = ModuleType(moduleName)
        # overwrite attributes
        for attr, value in overwriteAttributes:
            setattr(mod, attr, value)

        try:
            # execute code in mod
            exec(src, mod.__dict__)

            # add resulting module to sys
            sys.modules[moduleName] = mod
        except tuple(ignoreExceptions) as e: # type: ignore
            pass
        except exception.CheckpyError as e:
            excep = e
        except Exception as e:
            checkpy.lib.addOutput(stdoutListener.content)
            excep = exception.SourceException(
                exception = e,
                message = "while trying to import the code",
                output = stdoutListener.content,
                stacktrace = traceback.format_exc())
        except SystemExit as e:
            checkpy.lib.addOutput(stdoutListener.content)
            excep = exception.ExitError(
                message = "exit({}) while trying to import the code".format(int(e.args[0])),
                output = stdoutListener.content,
                stacktrace = traceback.format_exc())

        # wrap every function in mod with Function
        for name, func in [(name, f) for name, f in mod.__dict__.items() if callable(f)]:
            if func.__module__ == moduleName:
                setattr(mod, name, function.Function(func))

        # reset sys.argv
        if argv:
            sys.argv = argv

        output = stdoutListener.content
    if excep:
        raise excep

    return mod, output


def addOutput(output: str):
    """
    Add output to the active test's output.
    If no active test is found, this function does nothing.
    """
    test = checkpy.tester.getActiveTest()
    if test is not None:
        test.addOutput(output)


def removeWhiteSpace(s):
    warn("""checkpy.lib.removeWhiteSpace() is deprecated. Instead use:
    import re
    re.sub(r"\\s+", "", text)	
    """, DeprecationWarning, stacklevel=2)
    return re.sub(r"\s+", "", s, flags=re.UNICODE)


def getPositiveIntegersFromString(s):
    warn("""checkpy.lib.getPositiveIntegersFromString() is deprecated. Instead use:
    import re
    [int(i) for i in re.findall(r"\\d+", text)]
    """, DeprecationWarning, stacklevel=2)
    return [int(i) for i in re.findall(r"\d+", s)]


def getNumbersFromString(s):
    warn("""checkpy.lib.getNumbersFromString() is deprecated. Instead use:
    lib.static.getNumbersFrom(s)
    """, DeprecationWarning, stacklevel=2)
    return [eval(n) for n in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", s)]


def getLine(text, lineNumber):
    warn("""checkpy.lib.getLine() is deprecated. Instead try:
    lines = text.split("\\n")
    assert len(lines) >= lineNumber + 1
    line = lines[lineNumber]
    """, DeprecationWarning, stacklevel=2)
    lines = text.split("\n")
    try:
        return lines[lineNumber]
    except IndexError:
        raise IndexError("Expected to have atleast {} lines in:\n{}".format(lineNumber + 1, text))


def fileExists(fileName):
    warn("""checkpy.lib.fileExists() is deprecated. Use pathlib.Path instead:
    from pathlib import Path
    Path(filename).exists()
    """, DeprecationWarning, stacklevel=2)
    return path.Path(fileName).exists()


def require(fileName, source=None):
    warn("""checkpy.lib.require() is deprecated. Use requests to download files:
    import requests
    url = 'http://google.com/favicon.ico'
    r = requests.get(url, allow_redirects=True)
    with open('google.ico', 'wb') as f:
        f.write(r.content)
    """, DeprecationWarning, stacklevel=2)
    from checkpy.lib import download

    if source:
        download(fileName, source)
        return

    filePath = checkpy.USERPATH / fileName

    if not fileExists(str(filePath)):
        raise exception.CheckpyError(message="Required file {} does not exist".format(fileName))

    shutil.copyfile(filePath, pathlib.Path.cwd() / fileName)
