import inspect
import traceback

from checkpy import caches
from checkpy.entities import exception


__all__ = ["test", "failed", "passed"]


def test(priority=None, timeout=None):
	def testDecorator(testFunction):
		return TestFunction(testFunction, priority=priority, timeout=timeout)
	return testDecorator


def failed(*preconditions, priority=None, timeout=None):
	def failedDecorator(testFunction):
		return FailedTestFunction(testFunction, preconditions, priority=priority, timeout=timeout)
	return failedDecorator


def passed(*preconditions, priority=None, timeout=None):
	def passedDecorator(testFunction):
		return PassedTestFunction(testFunction, preconditions, priority=priority, timeout=timeout)
	return passedDecorator


class Test:
	DEFAULT_TIMEOUT = 10

	def __init__(self, 
			fileName,
			priority,
			timeout=None,
			onDescriptionChange=lambda self: None, 
			onTimeoutChange=lambda self: None
		):
		self._fileName = fileName
		self._priority = priority

		self._onDescriptionChange = onDescriptionChange
		self._onTimeoutChange = onTimeoutChange

		self._description = "placeholder test description"		
		self._timeout = Test.DEFAULT_TIMEOUT if timeout is None else timeout

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

	@property
	def timeout(self):
		return self._timeout
	
	@timeout.setter
	def timeout(self, new_timeout):
		if callable(new_timeout):
			self._timeout = new_timeout()
		else:
			self._timeout = new_timeout
		
		self._onTimeoutChange(self)
	

class TestResult(object):
	def __init__(self, hasPassed, description, message, exception=None):
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


class TestFunction:
	_previousPriority = -1

	def __init__(self, function, priority=None, timeout=None):
		self._function = function
		self.isTestFunction = True
		self.priority = self._getPriority(priority)
		self.dependencies = getattr(self._function, "dependencies", set())
		self.timeout = self._getTimeout(timeout)
		self.__name__ = function.__name__

	def __call__(self, test):
		self._useDocStringDescription(test)

		@caches.cacheTestResult(self)
		def runMethod():
			if inspect.getfullargspec(self._function).args:
				result = self._function(test)
			else:
				result = self._function()

			if result != None:
				test.test = lambda: result

			for attr in ["success", "fail", "exception"]:
				TestFunction._ensureCallable(test, attr)
			return test.run()
		
		return runMethod

	def _useDocStringDescription(self, test):
		if self._function.__doc__ != None:
			test.description = self._function.__doc__

	@staticmethod
	def _ensureCallable(test, attribute):
		value = getattr(test, attribute)
		if not callable(value):
			setattr(test, attribute, lambda *args, **kwargs: value)

	def _getPriority(self, priority):
		if priority != None:
			TestFunction._previousPriority = priority
			return priority
		
		inheritedPriority = getattr(self._function, "priority", None)
		if inheritedPriority:
			TestFunction._previousPriority = inheritedPriority
			return inheritedPriority
		
		TestFunction._previousPriority += 1
		return TestFunction._previousPriority
	
	def _getTimeout(self, timeout):
		if timeout != None:
			return timeout
		
		inheritedTimeout = getattr(self._function, "timeout", None)
		if inheritedTimeout:
			return inheritedTimeout
		
		return Test.DEFAULT_TIMEOUT


class FailedTestFunction(TestFunction):
	def __init__(self, function, preconditions, priority=None, timeout=None):
		super().__init__(function=function, priority=priority, timeout=timeout)
		self.preconditions = preconditions

	def __call__(self, test):
		@caches.cacheTestResult(self)
		def runMethod():
			if getattr(self._function, "isTestFunction", False):
				run = self._function(test)
			else:
				run = TestFunction.__call__(self, test)
			
			testResults = [caches.getCachedTestResult(t) for t in self.preconditions]
			if self.shouldRun(testResults):
				return run()
			return None
		return runMethod
	
	@staticmethod
	def shouldRun(testResults):
		return not any(t is None for t in testResults) and not any(t.hasPassed for t in testResults)


class PassedTestFunction(FailedTestFunction):
	@staticmethod
	def shouldRun(testResults):
		return not any(t is None for t in testResults) and all(t.hasPassed for t in testResults)
