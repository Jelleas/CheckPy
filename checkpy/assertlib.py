import checkpy.lib as lib
import re
import os

def exact(actual, expected):
	return actual == expected

def exactAndSameType(actual, expected):
	return exact(actual, expected) and sameType(actual, expected)

def between(actual, lower, upper):
	return lower <= actual <= upper

def ignoreWhiteSpace(actual, expected):
	return exact(lib.removeWhiteSpace(actual), lib.removeWhiteSpace(expected))

def contains(actual, expectedElement):
	return expectedElement in actual

def containsOnly(actual, expectedElements):
	return len([el for el in actual if el not in expectedElements]) == 0
	
def sameType(actual, expected):
	return type(actual) is type(expected)

def match(actual, expectedRegEx):
	return True if re.match(expectedRegEx, actual) else False

def sameLength(actual, expected):
	return len(actual) == len(expected)

def fileExists(fileName):
	return os.path.isfile(fileName)

def numberOnLine(number, line, deviation = 0):
	return any(between(n, number - deviation, number + deviation) for n in lib.getNumbersFromString(line))

def fileContainsFunctionCalls(fileName, *functionNames):
	source = lib.removeComments(lib.source(fileName))
	fCallInSrc = lambda fName, src : re.match(re.compile(".*{}[ \\t]*\(.*?\).*".format(fName), re.DOTALL), src)
	return all(fCallInSrc(fName, source) for fName in functionNames)

def fileContainsFunctionDefinitions(fileName, *functionNames):
	source = lib.removeComments(lib.source(fileName))
	fDefInSrc = lambda fName, src : re.match(re.compile(".*def[ \\t]+{}[ \\t]*\(.*?\).*".format(fName), re.DOTALL), src)
	return all(fDefInSrc(fName, source) for fName in functionNames)
