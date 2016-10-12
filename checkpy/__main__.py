import sys
import os
import argparse
import downloader
import printer
import tester
import shutil
import time

HERE = os.path.abspath(os.path.dirname(__file__))

def main():
	parser = argparse.ArgumentParser(description="checkPy: a simple python testing framework")
	parser.add_argument("-m", action="store", dest="module", help="provide a module name or path to run all tests from the module, or target a module for a specific test")
	parser.add_argument("-d", action="store", dest="githubLink", help="download tests from a Github repository and exit")
	parser.add_argument("-clean", action="store_true", help="remove all tests from the tests folder and exit")
	parser.add_argument("file", action="store", nargs="?", help="name of file to be tested")
	args = parser.parse_args()
	
	rootPath = os.sep.join(os.path.abspath(os.path.dirname(__file__)).split(os.sep)[:-1])
	if rootPath not in sys.path:
		sys.path.append(rootPath)	

	if args.clean:
		shutil.rmtree(os.path.join(HERE, "tests"), ignore_errors=True)
		printer.displayCustom("Removed all tests")
		return

	if args.githubLink:
		downloader.download(args.githubLink)
		return

	if args.file and args.module:
		tester.test(args.file, module = args.module)
	elif args.file and not args.module:
		tester.test(args.file)
	elif not args.file and args.module:
		tester.testModule(args.module)
	else:
		parser.print_help()
		return

if __name__ == "__main__":
	main()