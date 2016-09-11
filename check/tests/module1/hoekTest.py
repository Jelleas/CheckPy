import test as t
import lib
import assertlib

@t.test(0)
def correct(test):
	test.test = lambda : assertlib.contains(lib.outputOf(_fileName), "29")
	test.description = lambda : "correct angle calculated"