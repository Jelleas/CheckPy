import test as t
import lib
import assertlib

@t.test
def correctDistance(test):
	def testMethod(fileName):
		result = lib.outputOf(fileName).split("\n")[0]
		testResult = assertlib.exact(result, "36")
		return testResult, result
	test.test = testMethod

	test.description = lambda : "correct distance"

@t.test
def correctBarriers(test):
	def testMethod(fileName):
		result = lib.outputOf(fileName).split("\n")[1]
		testResult = assertlib.match(result, ".*9551.*9587.*")
		return testResult, result
	test.test = testMethod

	test.description = lambda : "correct bounding primes"
	test.fail = lambda info : "output %s does not contain the correct boundaries" %info