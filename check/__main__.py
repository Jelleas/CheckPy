import sys
import importlib
import lib
import printer
import os
import re
import argparse
import requests
import zipfile
import StringIO
import shutil

HERE = os.path.abspath(os.path.dirname(__file__))

def main():
	parser = argparse.ArgumentParser(description="checkPy: a simple python testing framework")
	parser.add_argument("-m", action="store", dest="module", help="provide a module name or path to run all tests from the module, or target a module for a specific test")
	parser.add_argument("-d", action="store", dest="githubLink", help="download tests from a Github repository and exit")
	parser.add_argument("-clean", action="store_true", help="remove all tests from the tests folder and exit")
	parser.add_argument("file", action="store", nargs="?", help="name of file to be tested")
	args = parser.parse_args()
	
	if args.clean:
		shutil.rmtree(os.path.join(HERE, "tests"), ignore_errors=True)
		return

	if args.githubLink:
		download(args.githubLink)
		return

	if args.file and args.module:
		runTest(args.file, module = args.module)
	elif args.file and not args.module:
		runTest(args.file)
	elif not args.file and args.module:
		testNames = getTestNames(args.module)
		if not testNames:
			printer.displayError("no tests found in module: {}".format(args.module))
			return
		for testName in testNames:
			runTest(testName, module = args.module)
	else:
		parser.print_help()
		return

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

def download(githubLink):
	zipLink = githubLink + "/archive/master.zip"
	r = requests.get(zipLink)
	
	if not r.ok:
		printer.displayError("Failed to download: {}".format(r.reason))
		return

	with zipfile.ZipFile(StringIO.StringIO(r.content)) as z:
		extractTests(z)

def extractTests(zipfile):
	destPath = os.path.join(HERE, "tests")
	if not os.path.exists(destPath):
		os.makedirs(destPath)

	getSubfolderName = lambda x : x.split("/tests/")[1]

	for name in zipfile.namelist():
		fileName = os.path.basename(name)

		# extract directories
		if not fileName:
			if "/tests/" in name:
				subfolderName = getSubfolderName(name)
				target = os.path.join(destPath, subfolderName)
				if subfolderName and not os.path.exists(target):
					os.makedirs(target)
			continue

		# extract files
		if "/tests/" in name:
			subfolderName = getSubfolderName(name)
			source = zipfile.open(name)
			target = file(os.path.join(destPath, subfolderName), "wb")
			with source, target:
				shutil.copyfileobj(source, target)

def getTestNames(moduleName):
	moduleName = backslashToForwardslash(moduleName)
	for (dirPath, dirNames, fileNames) in os.walk(os.path.join(HERE, "tests")):
		dirPath = backslashToForwardslash(dirPath)
		if moduleName in dirPath:
			return [fileName[:-7] for fileName in fileNames if fileName.endswith(".py") and not fileName.startswith("_")]

def getTestDirPath(testFileName, module = ""):
	module = backslashToForwardslash(module)
	testFileName = backslashToForwardslash(testFileName)
	for (dirPath, dirNames, fileNames) in os.walk(os.path.join(HERE, "tests")):
		dirPath = backslashToForwardslash(dirPath)
		if module in dirPath and testFileName in fileNames:
			return dirPath

def backslashToForwardslash(text):
	return re.sub("\\\\", "/", text)

def getFilePathAndName(completeFilePath):
	if not completeFilePath.endswith(".py"):
		completeFilePath += ".py"
	
	filePath = os.path.dirname(completeFilePath)
	fileName = os.path.basename(completeFilePath)

	# in case of no path given
	if not filePath:
		filePath = os.path.dirname(os.path.abspath(fileName))
	
	return filePath, fileName

if __name__ == "__main__":
	main()