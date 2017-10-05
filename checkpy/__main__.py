import sys
import os
import argparse
from . import downloader
from . import tester
import shutil
import time

def main():
	parser = argparse.ArgumentParser(
		description =
			"checkPy: a python testing framework for education. You are running Python version {}.{}.{}."
				.format(*sys.version_info[:3])
	)

	parser.add_argument("-module", action="store", dest="module", help="provide a module name or path to run all tests from the module, or target a module for a specific test")
	parser.add_argument("-download", action="store", dest="githubLink", help="download tests from a Github repository and exit")
	parser.add_argument("-update", action="store_true", help="update all downloaded tests and exit")
	parser.add_argument("-list", action="store_true", help="list all download locations and exit")
	parser.add_argument("-clean", action="store_true", help="remove all tests from the tests folder and exit")
	parser.add_argument("file", action="store", nargs="?", help="name of file to be tested")
	args = parser.parse_args()

	rootPath = os.sep.join(os.path.abspath(os.path.dirname(__file__)).split(os.sep)[:-1])
	if rootPath not in sys.path:
		sys.path.append(rootPath)

	if args.githubLink:
		downloader.download(args.githubLink)
		return

	if args.update:
		downloader.update()
		return

	if args.list:
		downloader.list()
		return

	if args.clean:
		downloader.clean()
		return

	if args.file and args.module:
		downloader.updateSilently()
		tester.test(args.file, module = args.module)
	elif args.file and not args.module:
		downloader.updateSilently()
		tester.test(args.file)
	elif not args.file and args.module:
		downloader.updateSilently()
		tester.testModule(args.module)
	else:
		parser.print_help()
		return

if __name__ == "__main__":
	main()
