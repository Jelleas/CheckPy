import traceback
from functools import wraps
from checkpy import caches
from checkpy.entities import exception

class Test:
	def __init__(self, 
			fileName,
			priority, 
			onDescriptionChange=lambda self: None, 
			onTimeoutChange=lambda self: None
		):
		self._fileName = fileName
		self._priority = priority

		self._onDescriptionChange = onDescriptionChange
		self._onTimeoutChange = onTimeoutChange

		self._description = ""

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
			return TestResult(False, self.description, self.exception(e), exception = e)
		except Exception as e:
			e = exception.TestError(
				exception = e,
				message = "while testing",
				stacktrace = traceback.format_exc())
			return TestResult(False, self.description, self.exception(e), exception = e)

		return TestResult(hasPassed, self.description, self.success(info) if hasPassed else self.fail(info))

	@staticmethod
	def test():
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
	
	@property
	def description(self):
		return self._description
	
	@description.setter
	def description(self, new_description):
		if callable(new_description):
			self._description = new_description()
		else:
			self._description = new_description

		self._onDescriptionChange(self)

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


def test(priority=None, timeout=None):
	def useDocStringDescription(test, testFunction):
		if testFunction.__doc__ != None:
			test.description = testFunction.__doc__

	def ensureCallable(test, attribute):
		value = getattr(test, attribute)
		if not callable(value):
			setattr(test, attribute, lambda *args, **kwargs: value)

	def testDecorator(testFunction):
		testFunction.isTestCreator = True
		testFunction.priority = priority
		testFunction.dependencies = set()

		@caches.cacheTestFunction
		@wraps(testFunction)
		def testCreator(test):
			if timeout != None:
				test.timeout = lambda: timeout

			useDocStringDescription(test, testFunction)
			run = test.run

			def runMethod():
				testFunction(test)
				for attr in ["success", "fail", "exception"]:
					ensureCallable(test, attr)
				return run()

			test.run = runMethod

			return test
		return testCreator
	
	return testDecorator


def failed(*precondTestCreators):
	def failedDecorator(testCreator):
		testCreator.dependencies = testCreator.dependencies | set(precondTestCreators)

		@wraps(testCreator)
		def testWrapper(test):
			test = testCreator(test)
			dependencies = test.dependencies
			test.dependencies = lambda: dependencies() | set(precondTestCreators)
			run = test.run
			def runMethod():
				testResults = [caches.getCachedTest(t).run() for t in precondTestCreators]
				return run() if not any(t is None for t in testResults) and not any(t.hasPassed for t in testResults) else None
			test.run = runMethod
			return test
		return testWrapper
	return failedDecorator


def passed(*precondTestCreators):
	def passedDecorator(testCreator):
		testCreator.dependencies = testCreator.dependencies | set(precondTestCreators)

		@wraps(testCreator)
		def testWrapper(test):
			test = testCreator(test)
			dependencies = test.dependencies
			test.dependencies = lambda: dependencies() | set(precondTestCreators)
			run = test.run
			def runMethod():
				testResults = [caches.getCachedTest(t).run() for t in precondTestCreators]
				return run() if not any(t is None for t in testResults) and all(t.hasPassed for t in testResults) else None
			test.run = runMethod
			return test
		return testWrapper
	return passedDecorator
