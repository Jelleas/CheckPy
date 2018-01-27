import unittest
import os
import sys
from contextlib import contextmanager
try:
	# Python 2
	import StringIO
except:
	# Python 3
	import io as StringIO
import checkpy
import checkpy.tester as tester
import checkpy.downloader as downloader
import checkpy.caches as caches
import checkpy.entities.exception as exception
import checkpy.tester.discovery as discovery

@contextmanager
def capturedOutput():
	new_out, new_err = StringIO.StringIO(), StringIO.StringIO()
	old_out, old_err = sys.stdout, sys.stderr
	try:
		sys.stdout, sys.stderr = new_out, new_err
		yield sys.stdout, sys.stderr
	finally:
		sys.stdout, sys.stderr = old_out, old_err

class TestTest(unittest.TestCase):
	def setUp(self):
		caches.clearAllCaches()
		self.fileName = "some.py"
		self.source = "print(\"foo\")"
		self.write(self.source)
		if not discovery.testExists(self.fileName):
			downloader.clean()
			downloader.download("jelleas/tests")

	def tearDown(self):
		if os.path.isfile(self.fileName):
			os.remove(self.fileName)
		caches.clearAllCaches()

	def write(self, source):
		with open(self.fileName, "w") as f:
			f.write(source)

	def test_oneTest(self):
		for testerResult in [tester.test(self.fileName), tester.test(self.fileName.split(".")[0])]:
			self.assertTrue(len(testerResult.testResults) == 1)
			self.assertTrue(testerResult.testResults[0].hasPassed)
			self.assertTrue("Testing: some.py".lower() in testerResult.output[0].lower())
			self.assertTrue(":)" in testerResult.output[1])
			self.assertTrue("prints exactly: foo".lower() in testerResult.output[1].lower())

	def test_fileMising(self):
		os.remove(self.fileName)
		testerResult = tester.test(self.fileName)
		self.assertTrue("file not found".lower() in testerResult.output[0].lower())
		self.assertTrue(self.fileName.lower() in testerResult.output[0].lower())

	def test_testMissing(self):
		fileName = "foo.py"
		with open(fileName, "w") as f:
			pass
		testerResult = tester.test(fileName)
		self.assertTrue("No test found for".lower() in testerResult.output[0].lower())
		self.assertTrue(fileName.lower() in testerResult.output[0].lower())
		os.remove(fileName)


class TestTestNotebook(unittest.TestCase):
	def setUp(self):
		caches.clearAllCaches()
		self.fileName = "some.ipynb"
		self.source =  r"""{
"cells": [
{
"cell_type": "code",
"execution_count": null,
"metadata": {},
"outputs": [],
"source": [
"print(\"foo\")"
]
}
],
"metadata": {
"kernelspec": {
"display_name": "Python 3",
"language": "python",
"name": "python3"
},
"language_info": {
"codemirror_mode": {
"name": "ipython",
"version": 3
},
"file_extension": ".py",
"mimetype": "text/x-python",
"name": "python",
"nbconvert_exporter": "python",
"pygments_lexer": "ipython3",
"version": "3.6.2"
}
},
"nbformat": 4,
"nbformat_minor": 2
}"""
		self.write(self.source)
		if not discovery.testExists(self.fileName):
			downloader.clean()
			downloader.download("jelleas/tests")

	def tearDown(self):
		if os.path.isfile(self.fileName):
			os.remove(self.fileName)
		caches.clearAllCaches()

	def write(self, source):
		with open(self.fileName, "w") as f:
			f.write(source)

	def test_oneTest(self):
		for testerResult in [tester.test(self.fileName), tester.test(self.fileName.split(".")[0])]:
			self.assertTrue(len(testerResult.testResults) == 1)
			self.assertTrue(testerResult.testResults[0].hasPassed)
			self.assertTrue("Testing: {}".format(self.fileName.split(".")[0]).lower() in testerResult.output[0].lower())
			self.assertTrue(":)" in testerResult.output[1])
			self.assertTrue("prints exactly: foo".lower() in testerResult.output[1].lower())


class TestTestSandbox(unittest.TestCase):
	def setUp(self):
		caches.clearAllCaches()
		self.fileName = "sandbox.py"
		self.source = "print(\"foo\")"
		self.write(self.source)
		if not discovery.testExists(self.fileName):
			downloader.clean()
			downloader.download("jelleas/tests")

	def tearDown(self):
		if os.path.isfile(self.fileName):
			os.remove(self.fileName)
		caches.clearAllCaches()

	def write(self, source):
		with open(self.fileName, "w") as f:
			f.write(source)

	def test_oneTest(self):
		for testerResult in [tester.test(self.fileName), tester.test(self.fileName.split(".")[0])]:
			self.assertTrue(len(testerResult.testResults) == 2)
			self.assertTrue(testerResult.testResults[0].hasPassed)
			self.assertTrue(testerResult.testResults[1].hasPassed)
			self.assertTrue("Testing: sandbox.py".lower() in testerResult.output[0].lower())
			self.assertTrue(":)" in testerResult.output[1])
			self.assertTrue("prints exactly: foo".lower() in testerResult.output[1].lower())
			self.assertTrue(":)" in testerResult.output[2])
			self.assertTrue("sandbox.py and sandboxTest.py exist".lower() in testerResult.output[2].lower())

if __name__ == '__main__':
	unittest.main()
