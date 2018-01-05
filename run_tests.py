import unittest
import argparse

def unittests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/unittests', pattern='*_test.py')
    return test_suite

def integrationtests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/integrationtests', pattern='*_test.py')
    return test_suite

def main():
	parser = argparse.ArgumentParser(description = "tests for checkpy")
	parser.add_argument("-integration", action="store_true", help="run integration tests")
	parser.add_argument("-unit", action="store_true", help="run unittests")
	parser.add_argument("-all", action="store_true", help="run all tests")
	args = parser.parse_args()

	runner = unittest.TextTestRunner(verbosity=1)

	if args.all:
		runner.run(unittests())
		runner.run(integrationtests())
		return

	if args.unit:
		runner.run(unittests())
		return

	if args.integration:
		runner.run(integrationtests())
		return

	parser.print_help()

if __name__ == "__main__":
	main()