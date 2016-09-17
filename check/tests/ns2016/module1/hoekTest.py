import check.test as t
import check.lib as lib
import check.assertlib as assertlib

@t.test(0)
def correct(test):
	test.test = lambda : assertlib.contains(lib.outputOf(_fileName), "29")
	test.description = lambda : "correct angle calculated"