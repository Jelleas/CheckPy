"""
A declarative approach to writing checks through method chaining. For example:

```
testSquare = (builder
    .function("square")  # assert function square() is defined
    .params("x")         # assert that square() accepts one parameter called x
    .returnType("int")   # assert that the function always returns an integer
    .call(2)             # call the function with argument 2
    .returns(4)          # assert that the function returns 4
    .call(3)             # now call the function with argument 3
    .returns(9)          # assert that the function returns 9
    .build()             # done, build the test
)
"""

import re

from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, Optional, List, Union
from typing_extensions import Self
from uuid import uuid4

import checkpy.tests
import checkpy.tester
import checkpy.entities.function
import checkpy.entities.exception
import checkpy


__all__ = ["function", "FunctionState"]


class function:
    """
    A declarative approach to writing checks through method chaining.
    Each method adds a part of a test on a stack.
    Upon `.build()` a checkpy test is created that executes each entry in the stack. 

    For example:

    ```
    testSquare = (
        function("square")  # assert function square() is defined
        .params("x")        # assert that square() accepts one parameter called x
        .returnType("int")  # assert that the function always returns an integer
        .call(2)            # call the function with argument 2
        .returns(4)         # assert that the function returns 4
        .call(3)            # now call the function with argument 3
        .returns(9)         # assert that the function returns 9
        .build()            # done, build the test
    )

    # Builders can be reused as long as build() is not called. For example:

    squareBuilder = (
        function("square")
        .params("x")
        .returnType("int")
    )

    testSquare2 = squareBuilder.call(2).returns(4).build() # do remember to call build()!
    testSquare3 = squareBuilder.call(3).returns(9).build() # do remember to call build()!

    # Tests created by this approach can depend and be depended on by other tests like normal:

    testSquare4 = passed(testSquare2, testSquare3)(
        squareBuilder.call(4).returns(16).build()  # testSquare4 will only run if both testSquare2 and 3 pass
    )

    @passed(testSquare2)
    def testSquareError():  # testSquareError will only run if testSquare2 passes.
        \"\"\"square("foo") raises a ValueError\"\"\"
        try:
            square("foo")
        except ValueError:
            return
        return False
    ```
    """
    def __init__(self, functionName: str, fileName: Optional[str]=None): 
        self._state: FunctionState = FunctionState(functionName, fileName=fileName)
        self._blocks: List[Callable[["FunctionState"], None]] = []

        self.name(functionName)

    def name(self, functionName: str) -> Self:
        """Assert that a function with functionName is defined."""
        def testName(state: FunctionState):
            state.name = functionName
            state.description = f"defines the function {functionName}()"

            source = checkpy.static.getSource(state.fileName)
            funcDefs = checkpy.static.getFunctionDefinitions(source)
            assert functionName in funcDefs,\
                f'no function found with name {functionName}()'

        return self.do(testName)

    def params(self, *params: str) -> Self:
        """Assert that the function accepts exactly these parameters."""
        def testParams(state: FunctionState):
            state.params = list(params)
            state.description = f"defines the function as {state.name}({', '.join(params)})"

            real = state.function.parameters
            expected = state.params

            assert len(real) == len(expected),\
                f"expected {len(expected)} arguments. Your function {state.name}() has"\
                f" {len(real)} arguments"

            assert real == expected,\
                f"parameters should exactly match the requested function definition"

        return self.do(testParams)

    def returnType(self, type_: type) -> Self:
        """
        From now on, assert that the function always returns values of type_ when called. 
        Note that type_ can be any typehint. For instance:

        `function("square").returnType(Optional[int]).call(2) # assert that square returns an int or None`
        """
        def testType(state: FunctionState):
            state.returnType = type_

        return self.do(testType)

    def returns(self, expected: Any) -> Self:
        """Assert that the last call returns expected."""
        def testReturned(state: FunctionState):
            state.description = f"{state.getFunctionCallRepr()} should return {expected}"
            assert state.returned == expected

        return self.do(testReturned)
    
    def stdout(self, expected: Any) -> Self:
        """Assert that the last call printed expected."""
        def testStdout(state: FunctionState):
            nonlocal expected
            expected = str(expected)
            descrStr = expected.replace("\n", "\\n")
            if len(descrStr) > 40:
                descrStr = descrStr[:20] + " ... " + descrStr[-20:]
            state.description = f"{state.getFunctionCallRepr()} should print {descrStr}"

            actual = state.function.printOutput
            assert actual == expected

        return self.do(testStdout)

    def stdoutRegex(self, regex: Union[str, re.Pattern], readable: Optional[str]=None) -> Self:
        """
        Assert that the last call printed output matching regex.
        If readable is passed, show that instead of the regex in the test's output.
        """
        def testStdoutRegex(state: FunctionState):
            nonlocal regex
            if isinstance(regex, str):
                regex = re.compile(regex)

            if readable:
                state.description = f"{state.getFunctionCallRepr()} should print {readable}"
            else:
                state.description = f"{state.getFunctionCallRepr()} should print output matching regular expression: {regex}"

            actual = state.function.printOutput

            match = regex.match(actual)
            if not match:
                if readable:
                    raise AssertionError(f"The printed output does not match the expected output. This is expected:\n"
                                         f"{readable}\n"
                                         f"This is what {state.getFunctionCallRepr()} printed:\n"
                                         f"{actual}")
                raise AssertionError(f"The printed output does not match regular expression: {regex}.\n"
                                     f"This is what {state.getFunctionCallRepr()} printed:\n"
                                     f"{actual}")

        return self.do(testStdoutRegex)

    def call(self, *args: Any, **kwargs: Any) -> Self:
        """Call the function with args and kwargs."""
        def testCall(state: FunctionState):
            state.args = list(args)
            state.kwargs = kwargs
            state.description = f"calling function {state.getFunctionCallRepr()}"
            state.returned = state.function(*args, **kwargs)

            state.description = f"{state.getFunctionCallRepr()} returns a value of type {state.returnType}"
            type_ = state.returnType
            returned = state.returned
            assert returned == checkpy.Type(type_)

        return self.do(testCall)

    def timeout(self, time: int) -> Self:
        """Reset the timeout on the check to time."""
        def setTimeout(state: FunctionState):
            state.timeout = time

        return self.do(setTimeout)

    def description(self, description: str) -> Self:
        """
        Fixate the test's description on description. 
        The test's description will not change after a call to this method,
        and can only change by calling this method again.
        """
        def setDecription(state: FunctionState):
            state.setDescriptionFormatter(lambda descr, state: descr)
            state.isDescriptionMutable = True
            state.description = description
            state.isDescriptionMutable = False

        return self.do(setDecription)

    def do(self, function: Callable[["FunctionState"], None]) -> Self:
        """
        Put function on the internal stack and call it after all previous calls have resolved.
        .do serves as an entry point for extensibility. Allowing you, the test writer, to insert
        specific and custom asserts, hints, and the like. For example:

        ```
        def checkDataFileIsUnchanged(state: "FunctionState"):
            with open("data.txt") as f:
                assert f.read() == "42\\n", "make sure not to change the file data.txt"
        
        test = function("process_data").call("data.txt").do(checkDataFileIsUnchanged).build()
        ```
        """
        self._blocks.append(function)
        return self

    def build(self) -> checkpy.tests.TestFunction:
        """
        Build the actual test (checkpy.tests.TestFunction). This should always be the last call.
        Be sure to store the result in a global, to allow checkpy to discover the test. For instance:

        `testSquare = (function("square").call(3).returns(9).build())`
        """
        def testFunction():
            self.log: List[FunctionState] = []

            for block in self._blocks:
                self.log.append(deepcopy(self._state))
                block(self._state)

        testFunction.__name__ = f"builder_function_test_{self._state.name}()_{uuid4()}"
        testFunction.__doc__ = self._state.description
        return checkpy.tests.test()(testFunction)


class FunctionState:
    """
    The state of the current test.
    This object serves as the "single source of truth" for each method in `function`.
    """
    def __init__(self, functionName: str, fileName: Optional[str]=None):
        self._description: str = f"defines the function {functionName}()"
        self._name: str = functionName
        self._fileName: Optional[str] = fileName
        self._params: Optional[List[str]] = None
        self._wasCalled: bool = False
        self._returned: Any = None
        self._returnType: Any = Any
        self._args: List[Any] = []
        self._kwargs: Dict[str, Any] = {}
        self._timeout: int = 10
        self._isDescriptionMutable: bool = True
        self._descriptionFormatter: Callable[[str, FunctionState], str] =\
            lambda descr, state: f"testing {state.name}() >> {descr}"

    @property
    def name(self) -> str:
        """The name of the function to be tested."""
        return self._name

    @name.setter
    def name(self, newName: str):
        self._name = str(newName)

    @property
    def fileName(self) -> Optional[str]:
        """
        The name of the Python file to run and import.
        If this is not set (`None`), the default file (`checkpy.file.name`) is used.
        """
        return self._fileName

    @fileName.setter
    def fileName(self, newFileName: Optional[str]):
        self._fileName = newFileName

    @property
    def params(self) -> List[str]:
        """The exact parameter names and order that the function accepts."""
        if self._params is None:
            raise checkpy.entities.exception.CheckpyError(
                f"params are not set for function builder test {self._name}()"
            )
        return self._params

    @params.setter
    def params(self, parameters: Iterable[str]):
        self._params = list(parameters)

    @property
    def function(self) -> checkpy.entities.function.Function:
        """The executable function."""
        return checkpy.getFunction(self.name, fileName=self.fileName)

    @property
    def wasCalled(self) -> bool:
        """Has the function been called yet?"""
        return self._wasCalled

    @property
    def returned(self) -> Any:
        """What the last function call returned."""
        if not self.wasCalled:
            raise checkpy.entities.exception.CheckpyError(
                f"function was never called for function builder test {self._name}"
            )
        return self._returned

    @returned.setter
    def returned(self, newReturned: Any):
        self._wasCalled = True
        self._returned = newReturned

    @property
    def args(self) -> List[Any]:
        """The args that were given to the last function call (excluding keyword args)"""
        return self._args

    @args.setter
    def args(self, newArgs: Iterable[Any]):
        self._args = list(newArgs)

    @property
    def kwargs(self) -> Dict[str, Any]:
        """The keyword args that were given to the last function call (excluding normal args)"""
        return self._kwargs

    @kwargs.setter
    def kwargs(self, newKwargs: Dict[str, Any]):
        self._kwargs = newKwargs

    @property
    def returnType(self) -> type:
        """
        The typehint of what the function should return according to the test.
        This is not the typehint of the function itself!
        """
        return self._returnType

    @returnType.setter
    def returnType(self, newReturnType: type):
        self._returnType = newReturnType

    @property
    def timeout(self) -> int:
        """
        The timeout of the test in seconds.
        This is not the time left, just the total time available for this test.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, newTimeout: int):
        self._timeout = newTimeout
        checkpy.tester.getActiveTest().timeout = self.timeout

    @property
    def description(self) -> str:
        """The description of the test, what is ultimately shown on the screen."""
        return self._descriptionFormatter(self._description, self)

    @description.setter
    def description(self, newDescription: str):
        if not self.isDescriptionMutable:
            return
        self._description = newDescription
        checkpy.tester.getActiveTest().description = self.description

    @property
    def isDescriptionMutable(self):
        """Can the description be changed (mutated)?"""
        return self._isDescriptionMutable

    @isDescriptionMutable.setter
    def isDescriptionMutable(self, newIsDescriptionMutable: bool):
        self._isDescriptionMutable = newIsDescriptionMutable

    def getFunctionCallRepr(self):
        """
        Helper method to get a formatted string of the function call.
        For instance: foo(2, bar=3)
        Note this method can only be called after a call to the tested function.
        Do be sure to check state.wasCalled! 
        """
        argsRepr = ", ".join(str(arg) for arg in self.args)
        kwargsRepr = ", ".join(f"{k}={v}" for k, v in self.kwargs.items())
        repr = ', '.join([a for a in (argsRepr, kwargsRepr) if a])
        return f"{self.name}({repr})"

    def setDescriptionFormatter(self, formatter: Callable[[str, "FunctionState"], str]):
        """
        The test's description is formatted by a function accepting the new description and the state.
        This method allows you to overwrite that function, for instance:

        `state.setDescriptionFormatter(lambda descr, state: f"Testing your function {state.name}: {descr}")`
        """
        self._descriptionFormatter = formatter
        checkpy.tester.getActiveTest().description = self.description
