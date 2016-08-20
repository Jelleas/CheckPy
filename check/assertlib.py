import lib
import re

def exact(actual, expected):
    return actual == expected
    
def ignoreWhiteSpace(actual, expected):        
    return exact(lib.removeWhiteSpace(actual), lib.removeWhiteSpace(expected))

def contains(actual, expected):
    return expected in actual
    
def sameType(actual, expected):
    return type(actual) is type(expected)

def match(actual, expectedRegEx):
	return True if re.match(expectedRegEx, actual) else False

def sameLength(actual, expected):
	return len(actual) == len(expected)