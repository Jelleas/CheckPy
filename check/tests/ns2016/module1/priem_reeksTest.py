import check.test as t
import check.lib as lib
import check.assertlib as assertlib

@t.test(0)
def correctDistance(test):
	test.test = lambda : assertlib.exact(lib.outputOf(_fileName).split("\n")[0], "36")
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