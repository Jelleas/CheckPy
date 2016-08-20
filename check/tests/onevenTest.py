import test as t
import lib
import assertlib

def exact():
    test = t.Test()
    
    def testMethod(fileName):
        result = lib.outputOf(fileName)
        testResult = assertlib.exact(result, "100")
        return testResult, result
    test.test = testMethod
    
    test.description = lambda : "output is exactly 100"
    test.fail = lambda result : "expected: 100, but got \"%s\" instead" %result
    
    return test

@t.failed(exact)
def contains():
    test = t.Test()
    
    def testMethod(fileName):
        result = lib.outputOf(fileName)
        testResult = assertlib.contains(result, "100")
        return testResult, result
    test.test = testMethod
    
    test.description = lambda : "contains 100 in the output"
    test.success = lambda result : "the correct answer (100) can be found in the output"
    test.fail = lambda result : "the correct answer (100) cannot be found in the output"
    
    return test