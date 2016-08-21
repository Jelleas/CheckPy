import sys
import importlib
import lib
import printer

def main():
	if len(sys.argv) != 2:
		printer.displayError("Wrong number of arguments provided to check, usage: check <pyfile>")
		return
		
	fileName = sys.argv[1] if sys.argv[1].endswith(".py") else sys.argv[1] + ".py"
	testName = fileName[:-3] + "Test"

	try:
		testModule = importlib.import_module("tests.%s" %testName)
		testModule._fileName = fileName
	except ImportError as e:
		printer.displayError("No test found for %s" %fileName)
		return

	testCreators = [\
			method \
			for _, method in testModule.__dict__.iteritems() \
			if callable(method)\
		]

	for test in sorted(tc() for tc in testCreators):
		printer.display(test.run())

main()