import test as t
import lib
import assertlib
import sys

def returnTypeIsList():
	test = t.Test()

	def testMethod(fileName):
		sys.modules["nulpunten"] = lib.createModule("nulpunten", lib.sourceOfDefinitions(fileName))
		import nulpunten
		points = nulpunten.Nulpunten(1,2,-10)
		testResult = assertlib.sameType(points, [])
		return testResult, ""
	test.test = testMethod
	
	test.description = lambda : "correct return type of Nulpunten"
	
	return test

def correct():
	test = t.Test()

	def testMethod(fileName):
		sys.modules["nulpunten"] = lib.createModule("nulpunten", lib.sourceOfDefinitions(fileName))
		import nulpunten
		points = nulpunten.Nulpunten(1,2,-10)
		for i, point in enumerate(points):
			points[i] = int(point * 10)
		testResult = 23 in points and -43 in points
		return testResult, ""
	test.test = testMethod
	
	test.description = lambda : "output of Nulpunten is correct for the example a=1, b=2, c=-10"
	
	return test