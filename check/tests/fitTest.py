import test as t
import lib
import assertlib

def init():
	lib.neutralizeFunctionFromImport(lib.createModule(_fileName), "show", "matplotlib.pyplot")

@t.test(0)
def correctC(test):
	test.test = lambda : assertlib.contains(lib.outputOf(_fileName).split("\n")[0], "60.")
	test.description = lambda : "correct value of c"

@t.test(1)
def correctUncertainy(test):
	test.test = lambda : assertlib.contains(lib.outputOf(_fileName).split("\n")[1], "1.5")
	test.description = lambda : "correct uncertainty"