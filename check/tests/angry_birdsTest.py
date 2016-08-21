import test as t
import lib
import assertlib

def init():
	lib.neutralizeFunctionFromImport(lib.createModule(_fileName), "show", "matplotlib.pyplot")

@t.test(0)
def correctBalBeweging0(test):
	test.test = lambda : (assertlib.exact(lib.getFunction("BalBeweging", _fileName)(16, 79, False), False), "")
	test.description = lambda : "Correct result for BalBeweging with speed = 16, angle = 79"

@t.test(1)
def correctBalBeweging1(test):
	test.test = lambda : (assertlib.exact(lib.getFunction("BalBeweging", _fileName)(3, 30, False), False), "")
	test.description = lambda : "Correct result for BalBeweging with speed = 3, angle = 30"

@t.test(2)
def correctBalBeweging2(test):
	test.test = lambda : (assertlib.exact(lib.getFunction("BalBeweging", _fileName)(11.5, 45, False), True), "")
	test.description = lambda : "Correct result for BalBeweging with speed = 11.5, angle = 45"