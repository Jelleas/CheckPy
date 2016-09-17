import check.test as t
import check.lib as lib
import check.assertlib as assertlib

def before():
	lib.neutralizeFunctionFromImport(lib.module(_fileName), "show", "matplotlib.pyplot")

@t.test(0)
def correctTimeTillParachute(test):
	test.test = lambda : assertlib.contains(lib.outputOf(_fileName).split("\n")[0], "12.2")
	test.description = lambda : "correct time till opening of parachute"

@t.test(1)
def correctExtraTime(test):
	test.test = lambda : assertlib.contains(lib.outputOf(_fileName).split("\n")[1], "5.1")
	test.description = lambda : "correct extra time with air friction"