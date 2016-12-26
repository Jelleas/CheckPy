import exception as excep
import os
import colorama
colorama.init()

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
	
def display(testResult):
	color, smiley = _selectColorAndSmiley(testResult)
	print "{}{} {}{}".format(color, smiley, testResult.description, _Colors.ENDC)
	if testResult.message:
		print "  - {}".format(testResult.message)

def displayTestName(testName):
	print "{}Testing: {}{}".format(_Colors.NAME, testName, _Colors.ENDC)

def displayUpdate(fileName):
	print "{}Updated: {}{}".format(_Colors.WARNING, os.path.basename(fileName), _Colors.ENDC)

def displayCustom(message):
	print message

def displayError(message):
	print "{}{} {}{}".format(_Colors.WARNING, _Smileys.CONFUSED, message, _Colors.ENDC)

def _selectColorAndSmiley(testResult):
	if testResult.hasPassed:
		return _Colors.PASS, _Smileys.HAPPY
	if type(testResult.message) is excep.SourceException:
		return _Colors.WARNING, _Smileys.CONFUSED
	return _Colors.FAIL, _Smileys.SAD