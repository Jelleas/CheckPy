import check.test as t
import check.lib as lib
import check.assertlib as assertlib
import math

@t.test(0)
def correctFunc1(test):
	test.test = lambda : assertlib.exact(int(lib.getFunction("Riemann", _fileName)(lambda x : x**x, 0, 1, 0.001) * 100), 78)
	test.description = lambda : "correct for x^x from a=0 to b=1 with dx=0.001"

@t.test(1)
def correctFunc2(test):
	test.test = lambda : assertlib.exact(int(lib.getFunction("Riemann", _fileName)(math.sin, 0.1, 2, 0.001) * 100), 74)
	test.description = lambda : "correct for sin(x) from a=0.1 to b=2 with dx=0.001"

@t.test(2)
def correctFunc3(test):
	test.test = lambda : assertlib.exact(int(lib.getFunction("Riemann", _fileName)(lambda x : math.sin(x**2), 0, math.pi, 0.001) * 100), 24)
	test.description = lambda : "correct for sin(x^2) from a=0 to b=pi with dx=0.001"