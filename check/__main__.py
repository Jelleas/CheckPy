import sys
import importlib
import lib
import printer
import os
import re
import argparse
import requests

HERE = os.path.abspath(os.path.dirname(__file__))

def main():
	parser = argparse.ArgumentParser(description="checkPy: a simple python testing framework")
	parser.add_argument('-m', action="store", dest="module")
	parser.add_argument('-d', action="store", dest="githubLink")
	parser.add_argument('file', action="store", nargs="?")
	args = parser.parse_args()
	
	if args.githubLink:
		download(args.githubLink)
		return

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

def download(githubLink):
	downloadAndInstall("https://api.github.com/repos/" + "/".join(githubLink.split("/")[-2:]) + "/contents", "tests")
	
def downloadAndInstall(root, extension):
	r = requests.get(root + "/" + extension)
	json = r.json()

	#print r, root, type(r)
	if type(json) is dict:
		with open(HERE + "/" + extension, "w+") as f:
			f.write(requests.get(json["download_url"]).text)
		return
	else:
		if not os.path.exists(HERE + "/" + extension):
			os.makedirs(HERE + "/" + extension)

	for response in json:
		downloadAndInstall(root, response["path"])

def getTestNames(moduleName):
	for (dirPath, dirNames, fileNames) in os.walk(os.path.dirname(os.path.abspath(__file__)) + "/tests"):
		dirPath = re.sub("\\\\", "/", dirPath)
		if moduleName in dirPath:
			return [fileName[:-7] for fileName in fileNames if fileName.endswith(".py") and not fileName.startswith("_")]

def getTestDirPath(testFileName, module = ""):
	for (dirPath, dirNames, fileNames) in os.walk(os.path.dirname(os.path.abspath(__file__)) + "/tests"):
		dirPath = re.sub("\\\\", "/", dirPath)
		if module in dirPath and testFileName in fileNames:
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

if __name__ == "__main__":
	main()