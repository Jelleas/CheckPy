import test as t
import lib
import assertlib

def exact():
    test = t.Test()

    def testMethod(fileName):
        result = lib.outputOf(fileName).strip()
        testResult = assertlib.exact(result, "[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]")
        return testResult, result
    test.test = testMethod
    
    test.description = lambda : "output is exactly as expected"
    test.fail = lambda result : "output is not exactly as expected, output was: %s" %result
    
    return test

@t.failed(exact)
def numberOfPrimes():
    test = t.Test()

    def testMethod(fileName):
        result = lib.outputOf(fileName).strip()
        
        if not result.startswith("[") or not result.endswith("]"):
            return False, "you seemed to have printed out more than just a list, please follow the assignment!"
        
        expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        primes = list(eval(result))
        testResult = assertlib.sameLength(primes, expected)
        return testResult, "you seem to have printed more or less primes than the %d expected!" %len(expected)
    test.test = testMethod
    
    test.description = lambda : "output contains correct number of primes"
    test.fail = lambda result : "output does not contain all expected primes because %s" %result
    
    return test