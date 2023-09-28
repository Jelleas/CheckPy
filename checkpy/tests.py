import inspect
import traceback

from typing import Any, Dict, Set, Tuple, Union, Callable, Iterable, Optional

from checkpy import caches
from checkpy.entities import exception
from checkpy.lib.sandbox import sandbox
from checkpy.lib.explanation import simplifyAssertionMessage


__all__ = ["test", "failed", "passed"]


def test(
        priority: Optional[int]=None,
        timeout: Optional[int]=None
    ) -> Callable[[Callable], "TestFunction"]:
    def testDecorator(testFunction: Callable) -> TestFunction:
        return TestFunction(testFunction, priority=priority, timeout=timeout)
    return testDecorator


def failed(
        *preconditions: "TestFunction",
        priority: Optional[int]=None,
        timeout: Optional[int]=None,
        hide: bool=True
    ) -> Callable[[Callable], "FailedTestFunction"]:
    def failedDecorator(testFunction: Callable) -> FailedTestFunction:
        return FailedTestFunction(testFunction, preconditions, priority=priority, timeout=timeout, hide=hide)
    return failedDecorator


def passed(
        *preconditions: "TestFunction", 
        priority: Optional[int]=None, 
        timeout: Optional[int]=None, 
        hide: bool=True
    ) -> Callable[[Callable], "PassedTestFunction"]:
    def passedDecorator(testFunction: Callable) -> PassedTestFunction:
        return PassedTestFunction(testFunction, preconditions, priority=priority, timeout=timeout, hide=hide)
    return passedDecorator


class Test:
    DEFAULT_TIMEOUT = 10
    PLACEHOLDER_DESCRIPTION = "placeholder test description"

    def __init__(self, 
            fileName: str,
            priority: int,
            timeout: Optional[int]=None,
            onDescriptionChange: Callable[["Test"], None]=lambda self: None, 
            onTimeoutChange: Callable[["Test"], None]=lambda self: None
        ):
        self._fileName = fileName
        self._priority = priority

        self._onDescriptionChange = onDescriptionChange
        self._onTimeoutChange = onTimeoutChange

        self._description = Test.PLACEHOLDER_DESCRIPTION
        self._timeout = Test.DEFAULT_TIMEOUT if timeout is None else timeout

    def __lt__(self, other):
        return self._priority < other._priority

    @property
    def fileName(self) -> str:
        return self._fileName
    
    @staticmethod
    def test() -> Union[bool, Tuple[bool, str]]:
        raise NotImplementedError()

    @staticmethod
    def success(info: str) -> str:
        return ""

    @staticmethod
    def fail(info: str) -> str:
        return info

    @staticmethod
    def exception(exception: Exception) -> Exception:
        return exception

    @staticmethod
    def dependencies() -> Set["TestFunction"]:
        return set()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, newDescription: Union[str, Callable[[], str]]):
        if callable(newDescription):
            self._description = newDescription()
        else:
            self._description = newDescription

        self._onDescriptionChange(self)

    @property
    def timeout(self) -> int:
        return self._timeout
    
    @timeout.setter
    def timeout(self, new_timeout: Union[int, Callable[[], int]]):
        if callable(new_timeout):
            self._timeout = new_timeout()
        else:
            self._timeout = new_timeout
        
        self._onTimeoutChange(self)

    def __setattr__(self, __name: str, __value: Any) -> None:
        value = __value
        if __name in ["fail", "success", "exception"]:
            if not callable(__value):
                value = lambda *args, **kwargs: __value
        super().__setattr__(__name, value)


class TestResult(object):
    def __init__(
        self,
        hasPassed: Optional[bool],
        description: str,
        message: str,
        exception: Optional[Exception]=None
    ):
        self._hasPassed = hasPassed
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

    def asDict(self) -> Dict[str, Union[bool, None, str]]:
        return {
            "passed": self.hasPassed,
            "description": str(self.description),
            "message": str(self.message),
            "exception": str(self.exception)
        }


class TestFunction:
    _previousPriority = -1

    def __init__(
            self,
            function: Callable,
            priority: Optional[int]=None,
            timeout: Optional[int]=None
        ):
        self._function = function
        self.isTestFunction = True
        self.priority = self._getPriority(priority)
        self.dependencies: Set[TestFunction] = getattr(self._function, "dependencies", set())
        self.timeout = self._getTimeout(timeout)
        self.__name__ = function.__name__

    def __call__(self, test: Test) -> Callable[[], Union["TestResult", None]]:
        self.useDocStringDescription(test)

        @caches.cacheTestResult(self)
        def runMethod():
            with sandbox():
                try:
                    if getattr(self._function, "isTestFunction", False):
                        self._function(test)()
                    elif (len(inspect.getfullargspec(self._function).args) >
                          (1 if inspect.ismethod(self._function) else 0)):
                        self._function(test)
                    else:
                        self._function()

                    # support for old-style tests
                    hasPassed, info = True, ""
                    if test.test != Test.test:
                        result = test.test()

                        if type(result) == tuple:
                            hasPassed, info = result
                        else:
                            hasPassed = result
                except AssertionError as e:
                    # last = traceback.extract_tb(e.__traceback__)[-1]
                    # print(last, dir(last), last.line, last.lineno)

                    assertMsg = simplifyAssertionMessage(str(e))
                    failMsg = test.fail("")
                    if failMsg and not failMsg.endswith("\n"):
                        failMsg += "\n"
                    msg = failMsg + assertMsg

                    return TestResult(False, test.description, msg)
                except exception.CheckpyError as e:
                    return TestResult(False, test.description, str(test.exception(e)), exception=e)
                except Exception as e:
                    e = exception.TestError(
                        exception = e,
                        message = "while testing",
                        stacktrace = traceback.format_exc())
                    return TestResult(False, test.description, str(test.exception(e)), exception=e)

                # Ensure hasPassed is None or a boolean
                # This is needed as boolean operators on np.bool_ return np.bool_
                hasPassed = hasPassed if hasPassed is None else bool(hasPassed)

                return TestResult(hasPassed, test.description, test.success(info) if hasPassed else test.fail(info))
        
        return runMethod

    def useDocStringDescription(self, test: Test) -> None:
        if getattr(self._function, "isTestFunction", False):
            self._function.useDocStringDescription(test) # type: ignore [attr-defined]

        if self._function.__doc__ is not None:
            test.description = self._function.__doc__

    def _getPriority(self, priority: Optional[int]) -> int:
        if priority is not None:
            TestFunction._previousPriority = priority
            return priority
        
        if getattr(self._function, "isTestFunction", False):
            inheritedPriority = getattr(self._function, "priority", None)
            if inheritedPriority:
                TestFunction._previousPriority = inheritedPriority
                return inheritedPriority
            
        TestFunction._previousPriority += 1
        return TestFunction._previousPriority
    
    def _getTimeout(self, timeout: Optional[int]) -> int:
        if timeout is not None:
            return timeout
        
        if getattr(self._function, "isTestFunction", False):
            inheritedTimeout = getattr(self._function, "timeout", None)
            if inheritedTimeout:
                return inheritedTimeout
        
        return Test.DEFAULT_TIMEOUT


class FailedTestFunction(TestFunction):
    HIDE_MESSAGE = "can't check until another check fails"

    def __init__(
            self,
            function: Callable,
            preconditions: Iterable[TestFunction],
            priority: Optional[int]=None,
            timeout: Optional[int]=None,
            hide: Optional[bool]=None
        ):
        super().__init__(function=function, priority=priority, timeout=timeout)

        for precond in preconditions:
            if not isinstance(precond, TestFunction):
                raise exception.CheckpyError(
                    f"{precond} is not a checkpy test and cannot be used as a dependency for test {function}."
                    f" Did you forget to use the @test() decorator for {precond}?"
                )

        self.preconditions = preconditions
        self.shouldHide = self._getHide(hide)

    def __call__(self, test: Test) -> Callable[[], Union["TestResult", None]]:
        self.useDocStringDescription(test)

        @caches.cacheTestResult(self)
        def runMethod():
            if getattr(self._function, "isTestFunction", False):
                run = self._function(test)
            else:
                run = TestFunction.__call__(self, test)

            self.requireDocstringIfNotHidden(test)

            testResults = [caches.getCachedTestResult(t) for t in self.preconditions]
            if self.shouldRun(testResults):
                return run()

            if self.shouldHide:
                return None

            return TestResult(
                None,
                test.description,
                self.HIDE_MESSAGE
            )
        return runMethod
    
    def requireDocstringIfNotHidden(self, test: Test) -> None:
        if not self.shouldHide and test.description == Test.PLACEHOLDER_DESCRIPTION:
            raise exception.TestError(message=f"Test {self.__name__} requires a docstring description if hide=False")

    @staticmethod
    def shouldRun(testResults: Iterable[TestResult]) -> bool:
        return not any(t is None for t in testResults) and not any(t.hasPassed for t in testResults)

    def _getHide(self, hide: Optional[bool]) -> bool:
        if hide is not None:
            return hide

        inheritedHide = getattr(self._function, "hide", None)
        if inheritedHide:
            return inheritedHide

        return True


class PassedTestFunction(FailedTestFunction):
    HIDE_MESSAGE = "can't check until another check passes"

    @staticmethod
    def shouldRun(testResults: Iterable[TestResult]) -> bool:
        return not any(t is None for t in testResults) and all(t.hasPassed for t in testResults)
