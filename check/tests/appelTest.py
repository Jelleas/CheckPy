import test as t
import lib
import assertlib

def init():
	mod = lib.createModule("appel", lib.sourceOfDefinitions(_fileName))
	lib.neutralizeFunctionFromImport(mod, "show", "matplotlib.pyplot")

@t.test(0)
def correctTime(test):
	test.test = lambda : (assertlib.contains(lib.outputOf(_fileName).split("\n")[0], "4.5"), "")
	test.description = lambda : "correct time of apple hitting the ground"

@t.test(1)
def correctSpeed(test):
	test.test = lambda : (assertlib.contains(lib.outputOf(_fileName).split("\n")[1], "159"), "")
	test.description = lambda : "correct speed on hitting the ground"

@t.test(2)
def correctSecondsToHit100(test):
	test.test = lambda : (assertlib.contains(lib.outputOf(_fileName).split("\n")[2], "2.8"), "")
	test.description = lambda : "correct time taken to hit 100km/h"