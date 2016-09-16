import sys
import importlib
import lib
import printer
import os
import re
import argparse

def main():
	parser = argparse.ArgumentParser(description="checkPy: ")
	parser.add_argument('-m', action="store", dest="module")
	parser.add_argument('file', action="store", nargs="?")
	args = parser.parse_args()
	
	if args.file and args.module:
		runTest(args.file, module = args.module)
	elif args.file and not args.module:
		runTest(args.file)
	else:
		for testName in getTestNames(args.module):
			runTest(testName, module = args.module)

def runTest(testName, module = ""):
	filePath, fileName = getFilePathAndName(testName)
	sys.path.append(filePath)

	testPath = getTestDirPath(fileName[:-3] + "Test.py", module = module)
	if testPath is None:
		printer.displayError("No test found for {}".format(fileName))
		return
	
	sys.path.append(testPath)
	testModule = importlib.import_module(fileName[:-3] + "Test")
	testModule._fileName = filePath + "/" + fileName
	
	testCreators = [\
			method \
			for _, method in testModule.__dict__.iteritems() \
			if callable(method) and method.__name__ != "before" and method.__name__ != "after"\
		]

	printer.displayTestName(testName)

	if hasattr(testModule, "before"):
		getattr(testModule, "before")()

	for test in sorted(tc() for tc in testCreators):
		printer.display(test.run())

	if hasattr(testModule, "after"):
		getattr(testModule, "after")()

def getTestNames(moduleName):
	for (dirPath, dirNames, fileNames) in os.walk(os.path.dirname(os.path.abspath(__file__)) + "/tests/" + moduleName):
		return [fileName[:-7] for fileName in fileNames if fileName.endswith(".py")]

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