import exception as excep
from colorama import init
init()

class Colors:
    PASS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class Smileys:
	HAPPY = ":)"
	SAD = ":("
	CONFUSED = ":S"
    
def display(testResult):
    if testResult == None:
        return

    color, smiley = _selectColorAndSmiley(testResult)
    print "%s%s %s%s" %(color, smiley, testResult.description, Colors.ENDC),
    if testResult.message:
         print "- %s" %testResult.message
    else:
        print

def _selectColorAndSmiley(testResult):
    if testResult.hasPassed:
        return Colors.PASS, Smileys.HAPPY
    if type(testResult.message) is excep.SourceException:
        return Colors.WARNING, Smileys.CONFUSED
    return Colors.FAIL, Smileys.SAD

def displayError(message):
    print "%s%s %s%s" %(Colors.WARNING, Smileys.CONFUSED, message, Colors.ENDC)
