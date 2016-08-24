import test as t
import lib
import assertlib

def init():
	lib.neutralizeFunctionFromImport(lib.createModule(_fileName), "show", "matplotlib.pyplot")

@t.test(0)
def correctMaxTemp(test):
	test.test = lambda : (assertlib.match(lib.outputOf(_fileName).split("\n")[0], ".*36[,.]8.*"), "")
	test.description = lambda : "correct maximum temperature"

@t.test(1)
def correctMinTemp(test):
	test.test = lambda : (assertlib.match(lib.outputOf(_fileName).split("\n")[1], ".*24[,.]8.*"), "")
	test.description = lambda : "correct minimum temperature"

@t.test(2)
def correctLongestPeriod(test):
	test.test = lambda : (assertlib.contains(lib.outputOf(_fileName).split("\n")[2], "21"), "")
	test.description = lambda : "correct longest streak of days on which it froze"

@t.test(3)
def correctFinalDayOfLongestPeriod(test):
	test.test = lambda : \
		(assertlib.match(lib.outputOf(_fileName).split("\n")[2], ".*(24|25)-[0]?2-1947.*"),\
		 "note: please provide output in the form of DD-MM-YYYY")
	test.description = lambda : "correct final day of the longest streak of days on which it froze"
	test.fail = lambda info : info

@t.test(4)
def correctHeatWave2015(test):
	test.test = lambda : \
		(assertlib.match(lib.outputOf(_fileName).split("\n")[3], ".*(True|true).*"),\
		 "note: please provide output in the form of true or false")
	test.description = lambda : "correct on whether there was a heatwave in 2015"
	test.fail = lambda info : info