import test as t
import lib
import assertlib

@t.test(0)
def correct(test):
	def testMethod():
		result = lib.outputOf(_fileName)
		testResult = assertlib.contains(result, "29")
		return testResult, result
	test.test = testMethod

	test.description = lambda : "correct angle calculated"