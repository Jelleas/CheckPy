import lib
import re

def exact(actual, expected):
	return actual == expected

def between(actual, lower, upper):
	return lower <= actual <= upper
	
def ignoreWhiteSpace(actual, expected):        
	return exact(lib.removeWhiteSpace(actual), lib.removeWhiteSpace(expected))

def contains(actual, expectedElement):
	return expectedElement in actual

def containsOnly(actual, expectedElements):
	return len(filter(lambda e : e not in expectedElements, actual)) == 0
	
def sameType(actual, expected):
	return type(actual) is type(expected)

def match(actual, expectedRegEx):
	return True if re.match(expectedRegEx, actual) else False

def sameLength(actual, expected):
	return len(actual) == len(expected)

def test():
	print [1,2,3][0]