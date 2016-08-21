import test as t
import lib
import assertlib
import math

@t.test(0)
def correctFunc1(test):
	test.test = lambda : (assertlib.between(lib.getFunction("MonteCarlo", _fileName)(lambda x : x**x, 0, 0, 1, 1), 0.76, 0.80), "")
	test.description = lambda : "correct for x^x from x1=0, y1=0 to x2=1, y2=1"

@t.test(1)
def correctFunc2(test):
	test.test = lambda : (assertlib.between(lib.getFunction("MonteCarlo", _fileName)(math.sin, 0, 0, 1, 1), 0.44, 0.48), "")
	test.description = lambda : "correct for sin(x) from x1=0, y1=0 to x2=1, y2=1"

@t.test(2)
def correctFunc3(test):
	test.test = lambda : (assertlib.between(lib.getFunction("MonteCarlo", _fileName)(lambda x : math.sin(x**2), 0, 0, 1, 1), 0.29, 0.33), "")
	test.description = lambda : "correct for sin(x^2) from x1=0, y1=0 to x2=1, y2=1"