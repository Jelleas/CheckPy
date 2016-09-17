import check.test as t
import check.lib as lib
import check.assertlib as assertlib

def before():
	lib.neutralizeFunctionFromImport(lib.module(_fileName), "show", "matplotlib.pyplot")

@t.test(0)
def correctMaxSpeed(test):
	test.test = lambda : assertlib.match(lib.outputOf(_fileName).split("\n")[0], ".*79[0-9][0-9].*")
	test.description = lambda : "correct maximum speed of apple"

@t.test(1)
def correctTimeTillReturn(test):
	test.test = lambda : assertlib.match(lib.outputOf(_fileName).split("\n")[1], ".*50[0-9][0-9].*")
	test.description = lambda : "correct time till return apple"
