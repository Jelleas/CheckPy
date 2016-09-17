import check.test as t
import check.lib as lib
import check.assertlib as assertlib
import sys

@t.test(0)
def correctMijnRandomGetal(test):
	def testMethod():
		MijnRandomGetal = lib.getFunction("MijnRandomGetal", _fileName)
		if not assertlib.containsOnly([MijnRandomGetal(1,1) for i in range(100)], [1]):
			return False, "Huh? a random number between 1 and 1 gives something unexpected"
		if not assertlib.containsOnly([MijnRandomGetal(0,1) for i in range(100)], [0,1]):
			return False, "Huh? a random number between 0 and 1 can become something other than 0 or 1?!"
		return True, ""
	test.test = testMethod
	
	test.description = lambda : "MijnRandomGetal functions correctly"
	test.fail = lambda info : str(info)


@t.passed(correctMijnRandomGetal)
@t.test(1)
def correctVierkant(test):
	test.test = lambda : assertlib.between(lib.getFunction("Vierkant", _fileName)(), 0.45, 0.55)
	test.description = lambda : "correct distance calculated by Vierkant"