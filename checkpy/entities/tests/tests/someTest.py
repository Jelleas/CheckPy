import checkpy.tests as t
import checkpy.lib as lib
import checkpy.assertlib as asserts

@t.test(10)
def exactlyFoo(test):
	def testMethod():
		output = lib.outputOf(_fileName, overwriteAttributes = [("__name__", "__main__")])
		return asserts.exact(output.strip(), "foo")

	test.test = testMethod
	test.description = lambda : "prints exactly: foo"
