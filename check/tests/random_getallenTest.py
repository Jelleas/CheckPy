import test as t
import lib
import assertlib
import sys

@t.test(0)
def correctMijnRandomGetal(test):
	def testMethod(fileName):
		sys.modules["random_getallen"] = lib.createModule("random_getallen", lib.sourceOfDefinitions(fileName))
		import random_getallen
		if not assertlib.containsOnly([random_getallen.MijnRandomGetal(1,1) for i in range(100)], [1]):
			return False, "Huh? a random number between 1 and 1 gives something unexpected"
		if not assertlib.containsOnly([random_getallen.MijnRandomGetal(0,1) for i in range(100)], [0,1]):
			return False, "Huh? a random number between 0 and 1 can become something other than 0 or 1?!"
		return True, ""
	test.test = testMethod
	
	test.description = lambda : "MijnRandomGetal functions correctly"
	test.fail = lambda info : str(info)


@t.passed(correctMijnRandomGetal)
@t.test(1)
def correctVierkant(test):
	def testMethod(fileName):
		sys.modules["random_getallen"] = lib.createModule("random_getallen", lib.sourceOfDefinitions(fileName))
		import random_getallen
		return -0.05 < 0.5 - random_getallen.Vierkant() < 0.05, ""
	test.test = testMethod
	
	test.description = lambda : "correct distance calculated by Vierkant"
	test.fail = lambda info : str(info)