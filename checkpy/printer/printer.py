import os
import traceback
import typing

import colorama
colorama.init()

from checkpy.entities import exception
import checkpy.tests

DEBUG_MODE = False
SILENT_MODE = False

class _Colors:
    PASS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    NAME = '\033[96m'
    ENDC = '\033[0m'

class _Smileys:
    HAPPY = ":)"
    SAD = ":("
    CONFUSED = ":S"
    NEUTRAL = ":|"

def display(testResult: checkpy.tests.TestResult) -> str:
    color, smiley = _selectColorAndSmiley(testResult)
    msg = "{}{} {}{}".format(color, smiley, testResult.description, _Colors.ENDC)
    if testResult.message:
        msg += "\n   " + "\n   ".join(testResult.message.split("\n"))

    if DEBUG_MODE and testResult.exception:
        exc = testResult.exception
        if hasattr(exc, "stacktrace"):
            stack = str(exc.stacktrace())
        else:
            stack = "".join(traceback.format_tb(testResult.exception.__traceback__))
        msg += "\n" + stack
    if not SILENT_MODE:
        print(msg)
    return msg

def displayTestName(testName: str) -> str:
    msg = "{}Testing: {}{}".format(_Colors.NAME, testName, _Colors.ENDC)
    if not SILENT_MODE:
        print(msg)
    return msg

def displayUpdate(fileName: str) -> str:
    msg = "{}Updated: {}{}".format(_Colors.WARNING, os.path.basename(fileName), _Colors.ENDC)
    if not SILENT_MODE:
        print(msg)
    return msg

def displayRemoved(fileName: str) -> str:
    msg = "{}Removed: {}{}".format(_Colors.WARNING, os.path.basename(fileName), _Colors.ENDC)
    if not SILENT_MODE:
        print(msg)
    return msg

def displayAdded(fileName: str) -> str:
    msg = "{}Added: {}{}".format(_Colors.WARNING, os.path.basename(fileName), _Colors.ENDC)
    if not SILENT_MODE:
        print(msg)
    return msg

def displayCustom(message: str) -> str:
    if not SILENT_MODE:
        print(message)
    return message

def displayWarning(message: str) -> str:
    msg = "{}Warning: {}{}".format(_Colors.WARNING, message, _Colors.ENDC)
    if not SILENT_MODE:
        print(msg)
    return msg

def displayError(message: str) -> str:
    msg = "{}{} {}{}".format(_Colors.WARNING, _Smileys.CONFUSED, message, _Colors.ENDC)
    if not SILENT_MODE:
        print(msg)
    return msg

def _selectColorAndSmiley(testResult: checkpy.tests.TestResult) -> typing.Tuple[str, str]:
    if testResult.hasPassed:
        return _Colors.PASS, _Smileys.HAPPY
    if type(testResult.message) is exception.SourceException:
        return _Colors.WARNING, _Smileys.CONFUSED
    if testResult.hasPassed is None:
        return _Colors.WARNING, _Smileys.NEUTRAL
    return _Colors.FAIL, _Smileys.SAD
