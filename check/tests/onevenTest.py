import test as t
import lib
import assertlib

@t.test
def exact(test):
    def testMethod(fileName):
        result = lib.outputOf(fileName)
        testResult = assertlib.exact(result.strip(), "100")
        return testResult, result
    test.test = testMethod
    
    test.description = lambda : "output is exactly 100"
    test.fail = lambda result : "expected: 100, but got \"%s\" instead" %result

@t.failed(exact)
@t.test
def contains(test):
    def testMethod(fileName):
        result = lib.outputOf(fileName)
        testResult = assertlib.contains(result, "100")
        return testResult, result
    test.test = testMethod
    
    test.description = lambda : "contains 100 in the output"
    test.success = lambda result : "the correct answer (100) can be found in the output"
    test.fail = lambda result : "the correct answer (100) cannot be found in the output"