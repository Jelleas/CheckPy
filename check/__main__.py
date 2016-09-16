import sys
import importlib
import lib
import printer
import os
import re

def main():
	if not 2 <= len(sys.argv) <= 3:
		printer.displayError("Wrong number of arguments provided to check, usage: check <pyfile> [module]")
		return

	filePath, fileName = getFilePathAndName(sys.argv[1])
	sys.path.append(filePath)
	
	if len(sys.argv) == 3:
		testDirPath = getTestDirPath(fileName[:-3] + "Test.py", module = sys.argv[2])
	else:
		testDirPath =  getTestDirPath(fileName[:-3] + "Test.py")

	if testDirPath is None:
		printer.displayError("No test found for {}".format(fileName))
		return
	
	sys.path.append(testDirPath)
	testModule = importlib.import_module(fileName[:-3] + "Test")
	testModule._fileName = fileName
	
	testCreators = [\
			method \
			for _, method in testModule.__dict__.iteritems() \
			if callable(method) and method.__name__ != "before" and method.__name__ != "after"\
		]

	if hasattr(testModule, "before"):
		getattr(testModule, "before")()

	for test in sorted(tc() for tc in testCreators):
		printer.display(test.run())

	if hasattr(testModule, "after"):
		getattr(testModule, "after")()

def getTestDirPath(testFileName, module = ""):
	for (dirPath, dirNames, fileNames) in os.walk(os.path.dirname(os.path.abspath(__file__)) + "/tests"):
		if dirPath.endswith(module) and testFileName in fileNames:
			return dirPath

def getFilePathAndName(completeFilePath):
	if not completeFilePath.endswith(".py"):
		completeFilePath += ".py"
	
	getFilePath = lambda x : "/".join(re.sub("\\\\", "/", x).split("/")[:-1])
	filePath = getFilePath(completeFilePath)
	fileName = re.sub("\\\\", "/", completeFilePath).split("/")[-1]

	# in case of no path given
	if not filePath:
		filePath = getFilePath(os.path.abspath(fileName))
	
	return filePath, fileName

main()