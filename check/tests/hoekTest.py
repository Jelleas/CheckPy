import test as t
import lib
import assertlib

@t.test
def correct(test):
	def testMethod(fileName):
		result = lib.outputOf(fileName)
		testResult = assertlib.contains(result, "29")
		return testResult, result
	test.test = testMethod

	test.description = lambda : "correct angle calculated"