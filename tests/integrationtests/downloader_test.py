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
import checkpy.interactive
import checkpy.downloader as downloader
import checkpy.caches as caches
import checkpy.entities.exception as exception

@contextmanager
def capturedOutput():
    new_out, new_err = StringIO.StringIO(), StringIO.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

class Base(unittest.TestCase):
    def setUp(self):
        caches.clearAllCaches()

    def tearDown(self):
        caches.clearAllCaches()

class BaseClean(unittest.TestCase):
    def setUp(self):
        caches.clearAllCaches()
        downloader.clean()

    def tearDown(self):
        downloader.clean()
        caches.clearAllCaches()

class TestDownload(BaseClean):
    def setUp(self):
        super(TestDownload, self).setUp()
        self.fileName = "some.py"
        with open(self.fileName, "w") as f:
            f.write("print(\"foo\")")

    def tearDown(self):
        super(TestDownload, self).tearDown()
        if os.path.isfile(self.fileName):
            os.remove(self.fileName)

    def test_spelledOutLink(self):
        downloader.download("https://github.com/jelleas/tests")
        testerResult = checkpy.interactive.test(self.fileName)
        self.assertTrue(len(testerResult.testResults) == 1)
        self.assertTrue(testerResult.testResults[0].hasPassed)

    def test_incompleteLink(self):
        downloader.download("jelleas/tests")
        testerResult = checkpy.interactive.test(self.fileName)
        self.assertTrue(len(testerResult.testResults) == 1)
        self.assertTrue(testerResult.testResults[0].hasPassed)
   
    def test_deadLink(self):
        with capturedOutput() as (out, err):
            downloader.download("jelleas/doesnotexist")
        self.assertTrue("DownloadError" in out.getvalue().strip())
	
class TestUpdate(BaseClean):
    def test_clean(self):
        downloader.update()
        with capturedOutput() as (out, err):
            downloader.list()
        self.assertEqual(out.getvalue().strip(), "")

    def test_oneDownloaded(self):
        downloader.download("jelleas/tests")
        with capturedOutput() as (out, err):
            downloader.update()
        self.assertEqual(\
            out.getvalue().split("\n")[0].strip(),
            "Finished downloading: https://github.com/jelleas/tests"
        )

class TestList(BaseClean):
    def test_clean(self):
        with capturedOutput() as (out, err):
            downloader.list()
        self.assertEqual(out.getvalue().strip(), "")

    def test_oneDownloaded(self):
        downloader.download("jelleas/tests")
        with capturedOutput() as (out, err):
            downloader.list()
        output = out.getvalue()
        self.assertTrue("tests" in output and "jelleas" in output)

class TestClean(Base):
    def test_clean(self):
        downloader.clean()
        with capturedOutput() as (out, err):
            downloader.list()
        self.assertEqual(out.getvalue().strip(), "")

    def test_cleanAfterDownload(self):
        downloader.download("jelleas/tests")
        downloader.clean()
        with capturedOutput() as (out, err):
            downloader.list()
        self.assertEqual(out.getvalue().strip(), "")

if __name__ == '__main__':
    unittest.main()