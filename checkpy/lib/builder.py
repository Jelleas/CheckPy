import checkpy.tests
import checkpy.entities.function
import checkpy.entities.exception
import checkpy
from copy import deepcopy
from uuid import uuid4
from typing import Any, Callable, Dict, Iterable, Optional, List, Tuple, Union


class FunctionBuilder:
    def __init__(self, functionName: str):
        self._state: FunctionState = FunctionState(functionName)
        self._blocks: List[Callable[["FunctionState"], None]] = []

        self.name(functionName)

    def name(self, functionName: str) -> "FunctionBuilder":
        def testName(state: FunctionState):
            state.name = functionName
            state.description = f"defines the function {functionName}()"
            assert functionName in checkpy.static.getFunctionDefinitions(),\
                f'no function found with name {functionName}()'

        self._blocks.append(testName)
        return self

    def params(self, *params: str) -> "FunctionBuilder":
        def testParams(state: FunctionState):
            state.params = params
            state.description = f"defines the function as {state.name}({', '.join(params)})"

            real = state.function.parameters
            expected = state.params

            assert len(real) == len(expected),\
                f"expected {len(expected)} arguments. Your function {state.name}() has"\
                f" {len(real)} arguments"

            assert real == expected,\
                f"parameters should exactly match the requested function definition"

        self._blocks.append(testParams)
        return self

    def returnType(self, type_: type) -> "FunctionBuilder":
        def testType(state: FunctionState):
            state.returnType = type_

            if state.wasCalled:
                state.description = f"{state.getFunctionCallRepr()} returns a value of type {state.returnType}"
                returned = state.returned
                assert returned == checkpy.Type(type_)

        self._blocks.append(testType)
        return self

    def returned(self, expected: Any) -> "FunctionBuilder":
        def testReturned(state: FunctionState):
            actual = state.returned
            state.description = f"{state.getFunctionCallRepr()} should return {expected}"
            assert actual == expected

        self._blocks.append(testReturned)
        return self

    def call(self, *args: Any, **kwargs: Any) -> "FunctionBuilder":
        def testCall(state: FunctionState):
            state.args = args
            state.kwargs = kwargs
            state.description = f"calling function {state.getFunctionCallRepr()}"
            state.returned = state.function(*args, **kwargs)

            state.description = f"{state.getFunctionCallRepr()} returns a value of type {state.returnType}"
            type_ = state.returnType
            returned = state.returned
            assert returned == checkpy.Type(type_)

        self._blocks.append(testCall)
        return self

    def timeout(self, time: int) -> "FunctionBuilder":
        def setTimeout(state: FunctionState):
            state.timeout = time

        self._blocks.append(setTimeout)
        return self

    def description(self, description: str) -> "FunctionBuilder":
        def setDecription(state: FunctionState):
            state.description = description

        self._blocks.append(setDecription)
        return self

    def do(self, function: Callable[["FunctionState"], None]) -> "FunctionBuilder":
        self._blocks.append(function)
        return self

    def build(self) -> checkpy.tests.TestFunction:
        def testFunction():
            self.log: List[FunctionState] = []

            for block in self._blocks:
                self.log.append(deepcopy(self._state))
                block(self._state)

        testFunction.__name__ = f"builder_function_test_{self._state.name}()_{uuid4()}"
        testFunction.__doc__ = self._state.description
        return checkpy.tests.test()(testFunction)


class FunctionState:
    def __init__(self, functionName: str):
        self._description: str = f"defines the function {functionName}()"
        self._name: str = functionName
        self._params: Optional[List[str]] = None
        self._wasCalled: bool = False
        self._returned: Any = None
        self._returnType: type = Any
        self._args: List[Any] = []
        self._kwargs: Dict[str, Any] = {}
        self._timeout: int = 10
        self._descriptionFormatter: Callable[[str, FunctionState], str] =\
            lambda descr, state: f"testing {state.name}() >> {descr}"

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, newName: str):
        self._name = str(newName)

    @property
    def params(self) -> Tuple[str]:
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
        return checkpy.getFunction(self.name)

    @property
    def wasCalled(self) -> bool:
        return self._wasCalled

    @property
    def returned(self) -> Any:
        if not self.wasCalled:
            raise checkpy.entities.exception.CheckpyError(
                f"function was never called for function builder test {self._name}"
            )
        return self._returned

    @returned.setter
    def returned(self, newReturned):
        self._wasCalled = True
        self._returned = newReturned

    @property
    def args(self) -> List[Any]:
        return self._args

    @args.setter
    def args(self, newArgs: Iterable[Any]):
        self._args = newArgs

    @property
    def kwargs(self) -> Dict[str, Any]:
        return self._kwargs

    @kwargs.setter
    def kwargs(self, newKwargs: Dict[str, Any]):
        self._kwargs = newKwargs

    @property
    def returnType(self) -> type:
        return self._returnType

    @returnType.setter
    def returnType(self, newReturnType: type):
        self._returnType = newReturnType

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, newTimeout):
        self._timeout = newTimeout
        checkpy.tester.getActiveTest().timeout = self.timeout

    @property
    def description(self) -> str:
        return self._descriptionFormatter(self._description, self)

    @description.setter
    def description(self, newDescription):
        self._description = newDescription
        checkpy.tester.getActiveTest().description = self.description

    def getFunctionCallRepr(self):
        argsRepr = ", ".join(str(arg) for arg in self.args)
        kwargsRepr = ", ".join(f"{k}={v}" for k, v in self.kwargs.items())
        repr = ', '.join([a for a in (argsRepr, kwargsRepr) if a])
        return f"{self.name}({repr})"

    def setDescriptionFormatter(self, formatter: Callable[[str, "FunctionState"], str]):
        self._descriptionFormatter = formatter
        checkpy.tester.getActiveTest().description = self.description


def function(functionName: str) -> FunctionBuilder:
    return FunctionBuilder(functionName)