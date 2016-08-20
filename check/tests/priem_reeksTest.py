import test as t
import lib
import assertlib

@t.test(0)
def correctDistance(test):
	def testMethod():
		result = lib.outputOf(_fileName).split("\n")[0]
		testResult = assertlib.exact(result, "36")
		return testResult, result
	test.test = testMethod

	test.description = lambda : "correct distance"

@t.test(1)
def correctBarriers(test):
	def testMethod():
		result = lib.outputOf(_fileName).split("\n")[1]
		testResult = assertlib.match(result, ".*9551.*9587.*")
		return testResult, result
	test.test = testMethod

	test.description = lambda : "correct bounding primes"
	test.fail = lambda info : "output %s does not contain the correct boundaries" %info