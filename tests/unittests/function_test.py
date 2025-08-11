import unittest
import checkpy.lib as lib
import checkpy.entities.exception as exception
from checkpy.entities.function import Function

class TestFunction(unittest.TestCase):
    def setUp(self):
        context = lib.io.replaceStdout()
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)


class TestFunctionName(TestFunction):
    def test_name(self):
        def foo():
            pass
        self.assertEqual(Function(foo).name, "foo")

class TestFunctionArguments(TestFunction):
    def test_noArgs(self):
        def foo():
            pass
        self.assertEqual(Function(foo).arguments, [])

    def test_args(self):
        def foo(bar, baz):
            pass
        self.assertEqual(Function(foo).arguments, ["bar", "baz"])

    def test_kwargs(self):
        def foo(bar = None, baz = None):
            pass
        self.assertEqual(Function(foo).arguments, ["bar", "baz"])

    def test_argsAndKwargs(self):
        def foo(bar, baz = None):
            pass
        self.assertEqual(Function(foo).arguments, ["bar", "baz"])

class TestFunctionCall(TestFunction):
    def test_dummy(self):
        def foo():
            return None
        f = Function(foo)
        self.assertEqual(f(), None)

    def test_arg(self):
        def foo(bar):
            return bar + 1
        f = Function(foo)
        self.assertEqual(f(1), 2)
        self.assertEqual(f(bar = 1), 2)

    def test_kwarg(self):
        def foo(bar=0):
            return bar + 1
        f = Function(foo)
        self.assertEqual(f(), 1)

        self.assertEqual(f(1), 2)

        self.assertEqual(f(bar = 1), 2)

    def test_exception(self):
        def foo():
            raise ValueError("baz")
        f = Function(foo)
        with self.assertRaises(exception.SourceException):
            f()


class TestFunctionPrintOutput(TestFunction):
    def test_noOutput(self):
        def foo():
            pass
        f = Function(foo)
        f()
        self.assertEqual(f.printOutput, "")

    def test_oneLineOutput(self):
        def foo():
            print("bar")
        f = Function(foo)
        f()
        self.assertEqual(f.printOutput, "bar\n")

    def test_twoLineOutput(self):
        def foo():
            print("bar")
            print("baz")
        f = Function(foo)
        f()
        self.assertEqual(f.printOutput, "bar\nbaz\n")

    def test_indirectPrint(self):
        def foo():
            Function(bar)()
        def bar():
            print("baz")
        foo = Function(foo)
        foo()
        self.assertEqual(foo.printOutput, "baz\n")

    def test_indirectPrintWithOrder(self):
        def foo():
            print("foo")
            Function(bar)()
            print("baz")
        def bar():
            print("bar")
        foo = Function(foo)
        foo()
        self.assertEqual(foo.printOutput, "foo\nbar\nbaz\n")

    def test_multipleCalls(self):
        def foo():
            print("foo")
        foo = Function(foo)
        foo()
        foo()
        self.assertEqual(foo.printOutput, "foo\n")

if __name__ == '__main__':
    unittest.main()
