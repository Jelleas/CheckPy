import unittest
import os
import shutil
import sys
import checkpy.lib as lib
import checkpy.caches as caches
import checkpy.entities.exception as exception


class Base(unittest.TestCase):
    def setUp(self):
        self.fileName = "dummy.py"
        self.source = "def f(x):" +\
                      "    return x * 2"
        self.write(self.source)

    def tearDown(self):
        os.remove(self.fileName)
        caches.clearAllCaches()

    def write(self, source):
        with open(self.fileName, "w") as f:
            f.write(source)


class TestFileExists(Base):
    def test_fileDoesNotExist(self):
        self.assertFalse(lib.fileExists("idonotexist.random"))

    def test_fileExists(self):
        self.assertTrue(lib.fileExists(self.fileName))

class TestRequire(Base):
    def setUp(self):
        super(TestRequire, self).setUp()
        self.cwd = os.getcwd()
        self.dirname = "testrequire"
        os.mkdir(self.dirname)

    def tearDown(self):
        super(TestRequire, self).tearDown()
        os.chdir(self.cwd)
        shutil.rmtree(self.dirname)

    def test_fileDownload(self):
        fileName = "inowexist.random"
        lib.require(fileName, "https://raw.githubusercontent.com/Jelleas/tests/master/tests/someTest.py")
        self.assertTrue(os.path.isfile(fileName))
        os.remove(fileName)

    def test_fileLocalCopy(self):
        os.chdir(self.dirname)
        lib.require(self.fileName)
        self.assertTrue(os.path.isfile(self.fileName))


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
    def test_fileDownload(self):
        fileName = "someTest.py"
        lib.download(fileName, "https://raw.githubusercontent.com/Jelleas/tests/master/tests/{}".format(fileName))
        self.assertTrue(os.path.isfile(fileName))
        os.remove(fileName)

    def test_fileDownloadRename(self):
        fileName = "someRandomFileName.name"
        lib.download(fileName, "https://raw.githubusercontent.com/Jelleas/tests/master/tests/someTest.py")
        self.assertTrue(os.path.isfile(fileName))
        os.remove(fileName)


class TestRemoveWhiteSpace(unittest.TestCase):
    def test_remove(self):
        s = lib.removeWhiteSpace("  \t  foo\t\t bar ")
        self.assertEqual(s, "foobar")


class TestGetPositiveIntegersFromString(unittest.TestCase):
    def test_only(self):
        s = "foo1bar 2 baz"
        self.assertEqual(lib.getPositiveIntegersFromString(s), [1,2])

    def test_order(self):
        s = "3 1 2"
        self.assertEqual(lib.getPositiveIntegersFromString(s), [3,1,2])

    def test_negatives(self):
        s = "-2"
        self.assertEqual(lib.getPositiveIntegersFromString(s), [2])

    def test_floats(self):
        s = "2.0"
        self.assertEqual(lib.getPositiveIntegersFromString(s), [2, 0])


class TestGetNumbersFromString(unittest.TestCase):
    def test_only(self):
        s = "foo1bar 2 baz"
        self.assertEqual(lib.getNumbersFromString(s), [1,2])

    def test_order(self):
        s = "3 1 2"
        self.assertEqual(lib.getNumbersFromString(s), [3,1,2])

    def test_negatives(self):
        s = "-2"
        self.assertEqual(lib.getNumbersFromString(s), [-2])

    def test_floats(self):
        s = "2.0"
        self.assertEqual(lib.getNumbersFromString(s), [2.0])


class TestGetLine(unittest.TestCase):
    def test_empty(self):
        s = ""
        with self.assertRaises(IndexError):
            lib.getLine(s, 1)

    def test_oneLine(self):
        s = "foo"
        self.assertEqual(lib.getLine(s, 0), s)

    def test_multiLine(self):
        s = "foo\nbar"
        self.assertEqual(lib.getLine(s, 1), "bar")

    def test_oneLineTooFar(self):
        s = "foo\nbar"
        with self.assertRaises(IndexError):
            lib.getLine(s, 2)


class TestCaptureStdout(unittest.TestCase):
    def test_blank(self):
        with lib.captureStdout() as stdout:
            self.assertTrue(len(stdout.getvalue()) == 0)

    def test_noOutput(self):
        with lib.captureStdout() as stdout:
            print("foo")
            self.assertEqual("foo\n", stdout.getvalue())

    def test_noLeakage(self):
        import sys
        with lib.captureStdout() as stdout:
            print("foo")
        self.assertTrue(len(sys.stdout.getvalue()) == 0)

class TestCaptureStdin(unittest.TestCase):
    def setUp(self):
        self.getInput = lambda : input if sys.version_info >= (3,0) else raw_input

    def test_noInput(self):
        with lib.captureStdin() as stdin:
            with self.assertRaises(exception.InputError):
                self.getInput()()

    def test_oneInput(self):
        with lib.captureStdin() as stdin:
            stdin.write("foo\n")
            stdin.seek(0)
            self.assertEqual(self.getInput()(), "foo")
            with self.assertRaises(exception.InputError):
                self.getInput()()

    def test_noLeakage(self):
        with lib.captureStdin() as stdin, lib.captureStdout() as stdout:
            stdin.write("foo\n")
            stdin.seek(0)
            self.assertEqual(self.getInput()("hello!"), "foo")
            self.assertTrue(len(stdout.read()) == 0)


if __name__ == '__main__':
    unittest.main()
