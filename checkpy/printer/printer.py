from checkpy.entities import exception
import os
import traceback
import colorama
colorama.init()

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

def display(testResult):
	color, smiley = _selectColorAndSmiley(testResult)
	msg = "{}{} {}{}".format(color, smiley, testResult.description, _Colors.ENDC)
	if testResult.message:
		msg += "\n  - {}".format(testResult.message)

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

def displayTestName(testName):
	msg = "{}Testing: {}{}".format(_Colors.NAME, testName, _Colors.ENDC)
	if not SILENT_MODE:
		print(msg)
	return msg

def displayUpdate(fileName):
	msg = "{}Updated: {}{}".format(_Colors.WARNING, os.path.basename(fileName), _Colors.ENDC)
	if not SILENT_MODE:
		print(msg)
	return msg

def displayRemoved(fileName):
	msg = "{}Removed: {}{}".format(_Colors.WARNING, os.path.basename(fileName), _Colors.ENDC)
	if not SILENT_MODE:
		print(msg)
	return msg

def displayAdded(fileName):
	msg = "{}Added: {}{}".format(_Colors.WARNING, os.path.basename(fileName), _Colors.ENDC)
	if not SILENT_MODE:
		print(msg)
	return msg

def displayCustom(message):
	if not SILENT_MODE:
		print(message)
	return message

def displayWarning(message):
	msg = "{}Warning: {}{}".format(_Colors.WARNING, message, _Colors.ENDC)
	if not SILENT_MODE:
		print(msg)
	return msg

def displayError(message):
	msg = "{}{} {}{}".format(_Colors.WARNING, _Smileys.CONFUSED, message, _Colors.ENDC)
	if not SILENT_MODE:
		print(msg)
	return msg

def _selectColorAndSmiley(testResult):
	if testResult.hasPassed:
		return _Colors.PASS, _Smileys.HAPPY
	if type(testResult.message) is exception.SourceException:
		return _Colors.WARNING, _Smileys.CONFUSED
	if testResult.hasPassed is None:
		return _Colors.WARNING, _Smileys.NEUTRAL
	return _Colors.FAIL, _Smileys.SAD
