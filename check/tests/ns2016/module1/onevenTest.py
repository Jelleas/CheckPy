import check.test as t
import check.lib as lib
import check.assertlib as assertlib

@t.test(0)
def exact(test):
	def testMethod():
		result = lib.outputOf(_fileName)
		testResult = assertlib.exact(result.strip(), "100")
		return testResult, result
	test.test = testMethod
	
	test.description = lambda : "output is exactly 100"
	test.fail = lambda info : "expected: 100, but got \"%s\" instead" %info


@t.failed(exact)
@t.test(1)
def contains(test):
	test.test = lambda : assertlib.contains(lib.outputOf(_fileName), "100")
	test.description = lambda : "contains 100 in the output"