import sys
import os
import argparse
from checkpy import downloader
from checkpy import tester
import shutil
import time
import json
import pkg_resources

def main():
	parser = argparse.ArgumentParser(
		description =
			"""
			checkPy: a python testing framework for education.
			You are running Python version {}.{}.{} and checkpy version {}.
			"""
			.format(sys.version_info[0], sys.version_info[1], sys.version_info[2], pkg_resources.get_distribution("checkpy").version)
	)

	parser.add_argument("-module", action="store", dest="module", help="provide a module name or path to run all tests from the module, or target a module for a specific test")
	parser.add_argument("-download", action="store", dest="githubLink", help="download tests from a Github repository and exit")
	parser.add_argument("-register", action="store", dest="localLink", help="register a local folder that contains tests and exit")
	parser.add_argument("-update", action="store_true", help="update all downloaded tests and exit")
	parser.add_argument("-list", action="store_true", help="list all download locations and exit")
	parser.add_argument("-clean", action="store_true", help="remove all tests from the tests folder and exit")
	parser.add_argument("--dev", action="store_true", help="get extra information to support the development of tests")
	parser.add_argument("--silent", action="store_true", help="do not print test results to stdout")
	parser.add_argument("--json", action="store_true", help="return output as json, implies silent")
	parser.add_argument("file", action="store", nargs="?", help="name of file to be tested")
	args = parser.parse_args()

	rootPath = os.sep.join(os.path.abspath(os.path.dirname(__file__)).split(os.sep)[:-1])
	if rootPath not in sys.path:
		sys.path.append(rootPath)

	if args.githubLink:
		downloader.download(args.githubLink)
		return

	if args.localLink:
		downloader.register(args.localLink)
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

	if args.json:
		args.silent = True

	if args.file:
		downloader.updateSilently()

		if args.module:
			result = tester.test(args.file, module = args.module, debugMode = args.dev, silentMode = args.silent)
		else:
			result = tester.test(args.file, debugMode = args.dev, silentMode = args.silent)

		if args.json:
			print(json.dumps(result.asDict(), indent=4))
		return

	if args.module:
		downloader.updateSilently()
		results = tester.testModule(args.module, debugMode = args.dev, silentMode = args.silent)

		if args.json and results:
			print(json.dumps([r.asDict() for r in results], indent=4))
		elif args.json and not results:
			print([])
		return

	parser.print_help()

if __name__ == "__main__":
	main()
