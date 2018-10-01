import traceback
from functools import wraps
from checkpy import caches
from checkpy.entities import exception

class Test(object):
	def __init__(self, fileName, priority):
		self._fileName = fileName
		self._priority = priority

	def __lt__(self, other):
		return self._priority < other._priority

	@property
	def fileName(self):
		return self._fileName

	@caches.cache()
	def run(self):
		try:
			result = self.test()

			if type(result) == tuple:
				hasPassed, info = result
			else:
				hasPassed, info = result, ""
		except exception.CheckpyError as e:
			return TestResult(False, self.description(), self.exception(e), exception = e)
		except Exception as e:
			e = exception.TestError(
				exception = e,
				message = "while testing",
				stacktrace = traceback.format_exc())
			return TestResult(False, self.description(), self.exception(e), exception = e)

		return TestResult(hasPassed, self.description(), self.success(info) if hasPassed else self.fail(info))

	@staticmethod
	def test():
		raise NotImplementedError()

	@staticmethod
	def description():
		raise NotImplementedError()

	@staticmethod
	def success(info):
		return ""

	@staticmethod
	def fail(info):
		return info

	@staticmethod
	def exception(exception):
		return exception

	@staticmethod
	def dependencies():
		return set()

	@staticmethod
	def timeout():
		return 10


class TestResult(object):
	def __init__(self, hasPassed, description, message, exception = None):
		self._hasPassed = bool(hasPassed)
		self._description = description
		self._message = message
		self._exception = exception

	@property
	def description(self):
		return self._description

	@property
	def message(self):
		return self._message

	@property
	def hasPassed(self):
		return self._hasPassed

	@property
	def exception(self):
		return self._exception

	def asDict(self):
		return {"passed":self.hasPassed,
				"description":str(self.description),
				"message":str(self.message),
				"exception":str(self.exception)}

def test(priority):
	def testDecorator(testCreator):
		testCreator.isTestCreator = True
		@caches.cache(testCreator)
		@wraps(testCreator)
		def testWrapper(fileName):
			t = Test(fileName, priority)
			testCreator(t)
			return t
		return testWrapper
	return testDecorator


def failed(*precondTestCreators):
	def failedDecorator(testCreator):
		@wraps(testCreator)
		def testWrapper(fileName):
			test = testCreator(fileName)
			dependencies = test.dependencies
			test.dependencies = lambda : dependencies() | set(precondTestCreators)
			run = test.run
			def runMethod():
				testResults = [t(fileName).run() for t in precondTestCreators]
				return run() if not any(t is None for t in testResults) and not any(t.hasPassed for t in testResults) else None
			test.run = runMethod
			return test
		return testWrapper
	return failedDecorator


def passed(*precondTestCreators):
	def passedDecorator(testCreator):
		@wraps(testCreator)
		def testWrapper(fileName):
			test = testCreator(fileName)
			dependencies = test.dependencies
			test.dependencies = lambda : dependencies() | set(precondTestCreators)
			run = test.run
			def runMethod():
				testResults = [t(fileName).run() for t in precondTestCreators]
				return run() if not any(t is None for t in testResults) and all(t.hasPassed for t in testResults) else None
			test.run = runMethod
			return test
		return testWrapper
	return passedDecorator
