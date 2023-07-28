import os
import sys
import re
import contextlib
import inspect
import io
import typing

import checkpy.entities.exception as exception


class Function(object):
    def __init__(self, function: typing.Callable):
        self._function = function
        self._printOutput = ""

    def __call__(self, *args, **kwargs) -> typing.Any:
        old = sys.stdout
        try:
            with self._captureStdout() as listener:
                outcome = self._function(*args, **kwargs)
                self._printOutput = listener.content
                return outcome
        except Exception as e:
            if isinstance(e,TypeError):
                no_arguments = re.search(r"(\w+\(\)) takes (\d+) positional arguments but (\d+) were given", str(e))
                if no_arguments:
                    raise exception.SourceException(
                        exception=None,
                         message=f"{no_arguments.group(1)} should take {no_arguments.group(3)} arguments but takes {no_arguments.group(2)} instead"
                    )
            sys.stdout = old
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
                    message = f"while trying to exectute {self.name}({argsRepr})"
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

    @contextlib.contextmanager
    def _captureStdout(self) -> typing.Generator["_StreamListener", None, None]:
        """
        capture sys.stdout in _outStream
            (a _Stream that is an instance of StringIO extended with the Observer pattern)
        returns a _StreamListener on said stream
        """
        outStreamListener = _StreamListener(_outStream)
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            outStreamListener.start()
            sys.stdout = outStreamListener.stream
            sys.stderr = open(os.devnull)
            yield outStreamListener
        except:
            raise
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
            sys.stdout = old_stdout
            outStreamListener.stop()

class _Stream(io.StringIO):
    def __init__(self, *args, **kwargs):
        io.StringIO.__init__(self, *args, **kwargs)
        self._listeners: typing.List["_StreamListener"] = []

    def register(self, listener: "_StreamListener"):
        self._listeners.append(listener)

    def unregister(self, listener: "_StreamListener"):
        self._listeners.remove(listener)

    def write(self, text: str):
        """Overwrites StringIO.write to update all listeners"""
        io.StringIO.write(self, text)
        self._onUpdate(text)

    def writelines(self, lines: typing.Iterable):
        """Overwrites StringIO.writelines to update all listeners"""
        io.StringIO.writelines(self, lines)
        for line in lines:
            self._onUpdate(line)

    def _onUpdate(self, content: str):
        for listener in self._listeners:
            listener.update(content)

class _StreamListener:
    def __init__(self, stream: _Stream):
        self._stream = stream
        self._content = ""

    def start(self):
        self.stream.register(self)

    def stop(self):
        self.stream.unregister(self)

    def update(self, content: str):
        self._content += content

    @property
    def content(self) -> str:
        return self._content

    @property
    def stream(self) -> _Stream:
        return self._stream

_outStream = _Stream()
