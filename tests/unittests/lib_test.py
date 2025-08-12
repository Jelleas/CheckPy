import unittest
from io import StringIO
import os
import shutil
import tempfile

import checkpy.lib as lib
import checkpy.caches as caches
import checkpy.entities.exception as exception


class Base(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempdir)
        os.chdir(self.tempdir)

        self.fileName = "dummy.py"
        self.source = "def f(x):" +\
                      "    return x * 2"
        self.write(self.source)

        stdout_context = lib.io.replaceStdout()
        stdout_context.__enter__()
        self.addCleanup(stdout_context.__exit__, None, None, None)

        stdin_context = lib.io.replaceStdin()
        stdin_context.__enter__()
        self.addCleanup(stdin_context.__exit__, None, None, None)

    def tearDown(self):
        caches.clearAllCaches()

    def write(self, source):
        with open(self.fileName, "w") as f:
            f.write(source)


class TestFileExists(Base):
    def test_fileDoesNotExist(self):
        self.assertFalse(lib.fileExists("idonotexist.random"))

    def test_fileExists(self):
        self.assertTrue(lib.fileExists(self.fileName))


class TestSource(Base):
    def test_expectedOutput(self):
        source = lib.source(self.fileName)
        self.assertEqual(source, self.source)


class TestSourceOfDefinitions(Base):
    def test_noDefinitions(self):
        source = \
"""
height = int(input("Height: "))

#retry while height > 23
while height > 23:
    height = int(input("Height: "))

#prints the # and blanks
for i in range(height):
    for j in range(height - i - 1):
        print(" ", end="")
    for k in range(i + 2):
        print("#", end="")
    print("")
"""
        self.write(source)
        self.assertEqual(lib.sourceOfDefinitions(self.fileName), "")

    def test_oneDefinition(self):
        source = \
"""
def main():
    pass
if __name__ == "__main__":
    main()
"""
        expectedOutcome = \
"""def main():
    pass"""
        self.write(source)
        self.assertEqual(lib.sourceOfDefinitions(self.fileName), expectedOutcome)

    def test_comments(self):
        source = \
"""
# foo
\"\"\"bar\"\"\"
"""
        self.write(source)
        self.assertEqual(lib.sourceOfDefinitions(self.fileName), "")

    @unittest.expectedFailure
    def test_multilineString(self):
        source = \
"""
x = \"\"\"foo\"\"\"
"""
        self.write(source)
        self.assertEqual(lib.sourceOfDefinitions(self.fileName), source)

    def test_import(self):
        source = \
"""import os
from os import path"""
        self.write(source)
        self.assertEqual(lib.sourceOfDefinitions(self.fileName), source)


class TestGetFunction(Base):
    def test_sameName(self):
        func = lib.getFunction("f", self.fileName)
        self.assertEqual(func.name, "f")

    def test_sameArgs(self):
        func = lib.getFunction("f", self.fileName)
        self.assertEqual(func.arguments, ["x"])

    def test_expectedOutput(self):
        func = lib.getFunction("f", self.fileName)
        self.assertEqual(func(2), 4)


class TestOutputOf(Base):
    def test_helloWorld(self):
        source = \
"""
print("Hello, world!")
"""
        self.write(source)
        self.assertEqual(lib.outputOf(self.fileName), "Hello, world!\n")

    def test_function(self):
        source = \
"""
def f(x):
    print(x)
f(1)
"""
        self.write(source)
        self.assertEqual(lib.outputOf(self.fileName), "1\n")

    def test_input(self):
        source = \
"""
x = input("foo")
print(x)
"""
        self.write(source)
        output = lib.outputOf(self.fileName, stdinArgs = ["3"])
        self.assertEqual(int(output), 3)

    def test_noInput(self):
        source = \
"""
x = input("foo")
print(x)
"""
        self.write(source)
        with self.assertRaises(exception.InputError):
            lib.outputOf(self.fileName)

    def test_argv(self):
        source = \
"""
import sys
print(sys.argv[1])
"""
        self.write(source)
        output = lib.outputOf(self.fileName, argv = [self.fileName, "foo"])
        self.assertEqual(output, "foo\n")

    def test_ValueError(self):
        source = \
"""
print("bar")
raise ValueError
print("foo")
"""
        self.write(source)
        with self.assertRaises(exception.SourceException):
            output = lib.outputOf(self.fileName, argv = [self.fileName, "foo"])
            self.assertEqual(output, "bar\n")

    def test_ignoreValueError(self):
        source = \
"""
print("foo")
raise ValueError
print("bar")
"""
        self.write(source)
        output = lib.outputOf(self.fileName, ignoreExceptions = [ValueError])
        self.assertEqual(output, "foo\n")

    def test_ignoreSystemExit(self):
        source = \
"""
import sys
print("foo")
sys.exit(1)
print("bar")
"""
        self.write(source)
        output = lib.outputOf(self.fileName, ignoreExceptions = [SystemExit])
        self.assertEqual(output, "foo\n")

    def test_src(self):
        source = \
"""
print("bar")
"""
        self.write(source)
        output = lib.outputOf(self.fileName, src = "print(\"foo\")")
        self.assertEqual(output, "foo\n")


class TestModule(Base):
    def test_function(self):
        source = \
"""
def f():
    pass
"""
        self.write(source)
        self.assertTrue(hasattr(lib.module(self.fileName), "f"))

    def test_class(self):
        source = \
"""
class C:
    pass
"""
        self.write(source)
        self.assertTrue(hasattr(lib.module(self.fileName), "C"))

    def test_import(self):
        source = \
"""
import os
"""
        self.write(source)
        self.assertTrue(hasattr(lib.module(self.fileName), "os"))

    def test_global(self):
        source = \
"""
x = 3
"""
        self.write(source)
        self.assertTrue(hasattr(lib.module(self.fileName), "x"))

    def test_indirectGlobal(self):
        source = \
"""
def f():
    global x
    x = 3
f()
"""
        self.write(source)
        self.assertTrue(hasattr(lib.module(self.fileName), "x"))

    def test_local(self):
        source = \
"""
def f():
    x = 3
f()
"""
        self.write(source)
        self.assertTrue(not hasattr(lib.module(self.fileName), "x"))


class TestNeutralizeFunction(unittest.TestCase):
    def test_dummy(self):
        def dummy():
            return "foo"
        lib.neutralizeFunction(dummy)
        self.assertEqual(dummy(), None)


class TestDownload(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempdir)
        os.chdir(self.tempdir)

    def test_fileDownload(self):
        fileName = "someTest.py"
        
        with lib.sandbox.sandbox():
            lib.download(fileName, "https://raw.githubusercontent.com/Jelleas/tests/master/tests/{}".format(fileName))
            self.assertTrue(os.path.isfile(fileName))
        
    def test_fileDownloadRename(self):
        fileName = "someRandomFileName.name"


        with lib.sandbox.sandbox():
            lib.download(fileName, "https://raw.githubusercontent.com/Jelleas/tests/master/tests/someTest.py")
            self.assertTrue(os.path.isfile(fileName))

class TestCaptureStdout(unittest.TestCase):
    def test_blank(self):
        with lib.io.replaceStdout():
            with lib.io.captureStdout() as stdout:
                self.assertTrue(len(stdout.content) == 0)

    def test_noOutput(self):
        with lib.io.replaceStdout():
            with lib.io.captureStdout() as stdout:
                print("foo")
                self.assertEqual("foo\n", stdout.content)

    def test_noLeakage(self):
        import sys
        try:
            original_stdout = sys.stdout
            mock_stdout = StringIO()
            sys.stdout = mock_stdout

            with lib.io.replaceStdout():
                with lib.io.captureStdout():
                    print("foo")
            
            self.assertEqual(len(mock_stdout.getvalue()), 0)
            self.assertEqual(len(sys.stdout.getvalue()), 0)
        finally:
            sys.stdout = original_stdout
            mock_stdout.close()

class TestReplaceStdin(unittest.TestCase):
    def test_noInput(self):
        with lib.io.replaceStdin() as stdin:
            with self.assertRaises(exception.InputError):
                input()

    def test_oneInput(self):
        with lib.io.replaceStdin() as stdin:
            stdin.write("foo\n")
            stdin.seek(0)
            self.assertEqual(input(), "foo")
            with self.assertRaises(exception.InputError):
                input()

    def test_noLeakage(self):
        with lib.io.replaceStdout():
            with lib.io.replaceStdin() as stdin, lib.io.captureStdout() as stdout:
                stdin.write("foo\n")
                stdin.seek(0)
                self.assertEqual(input("hello!"), "foo")
                self.assertTrue(len(stdout.content) == 0)


if __name__ == '__main__':
    unittest.main()
