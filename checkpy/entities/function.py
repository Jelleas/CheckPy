import os
import sys
import re
import inspect
import io
import typing

import checkpy.entities.exception as exception
import checkpy.lib
import checkpy.lib.io


class Function:
    def __init__(self, function: typing.Callable):
        self._function = function
        self._printOutput = ""

    def __call__(self, *args, **kwargs) -> typing.Any:
        try:
            with checkpy.lib.io.captureStdout() as _outStreamListener:
                outcome = self._function(*args, **kwargs)

                self._printOutput = _outStreamListener.content
                checkpy.lib.addOutput(self._printOutput)

            return outcome
        except Exception as e:
            if isinstance(e,TypeError):
                no_arguments = re.search(r"(\w+\(\)) takes (\d+) positional arguments but (\d+) were given", str(e))
                if no_arguments:
                    raise exception.SourceException(
                        exception=None,
                         message=f"{no_arguments.group(1)} should take {no_arguments.group(3)} arguments but takes {no_arguments.group(2)} instead"
                    )
            argumentNames = self.arguments
            nArgs = len(args) + len(kwargs)

            message = "while trying to execute {}()".format(self.name)
            if nArgs > 0:
                if len(argumentNames) == len(args):
                    argsRepr = ", ".join("{}={}".format(argumentNames[i], args[i]) for i in range(len(args)))
                    kwargsRepr = ", ".join("{}={}".format(kwargName, kwargs[kwargName]) for kwargName in argumentNames[len(args):nArgs])
                    representation = ", ".join(s for s in [argsRepr, kwargsRepr] if s)
                    message = "while trying to execute {}({})".format(self.name, representation)
                else:
                    argsRepr = ','.join(str(arg) for arg in args)
                    message = f"while trying to execute {self.name}({argsRepr})"
            raise exception.SourceException(exception = e, message = message)

    @property
    def name(self) -> str:
        """gives the name of the function"""
        return self._function.__name__

    @property
    def arguments(self) -> typing.List[str]:
        """gives the parameter names of the function"""
        return self.parameters

    @property
    def parameters(self) -> typing.List[str]:
        """gives the parameter names of the function"""
        return inspect.getfullargspec(self._function)[0]

    @property
    def printOutput(self) -> str:
        """stateful function that returns the print (stdout) output of the latest function call as a string"""
        return self._printOutput

    def __repr__(self):
        return self._function.__name__
