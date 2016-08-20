import test as t
import lib
import assertlib
import sys
import math

@t.test(0)
def correctFunc1(test):
	def testMethod(fileName):
		sys.modules["riemann"] = lib.createModule("riemann", lib.sourceOfDefinitions(fileName))
		import riemann
		return assertlib.exact(int(riemann.Riemann(lambda x : x**x, 0, 1, 0.001) * 100), 78), ""
	test.test = testMethod
	
	test.description = lambda : "correct for x^x from a=0 to b=1 with dx=0.001"

@t.test(1)
def correctFunc2(test):
	def testMethod(fileName):
		sys.modules["riemann"] = lib.createModule("riemann", lib.sourceOfDefinitions(fileName))
		import riemann
		return assertlib.exact(int(riemann.Riemann(math.sin, 0.1, 2, 0.001) * 100), 74), ""
	test.test = testMethod
	
	test.description = lambda : "correct for sin(x) from a=0.1 to b=2 with dx=0.001"

@t.test(2)
def correctFunc3(test):
	def testMethod(fileName):
		sys.modules["riemann"] = lib.createModule("riemann", lib.sourceOfDefinitions(fileName))
		import riemann
		return assertlib.exact(int(riemann.Riemann(lambda x : math.sin(x**2), 0, math.pi, 0.001) * 100), 24), ""
	test.test = testMethod
	
	test.description = lambda : "correct for sin(x^2) from a=0 to b=pi with dx=0.001"