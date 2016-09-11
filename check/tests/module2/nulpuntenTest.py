import test as t
import lib
import assertlib
import sys

@t.test(0)
def correct(test):
	def testMethod():
		points = lib.getFunction("Nulpunten", _fileName)(1,2,-10)
		for i, point in enumerate(points):
			points[i] = int(point * 10)
		testResult = 23 in points and -43 in points
		return testResult, ""
	test.test = testMethod
	
	test.description = lambda : "output of Nulpunten is correct for the example a=1, b=2, c=-10"


@t.test(1)
def returnTypeIsList(test):
	test.test = lambda : assertlib.sameType(lib.getFunction("Nulpunten", _fileName)(1,2,-10), [])
	test.description = lambda : "correct return type of Nulpunten"