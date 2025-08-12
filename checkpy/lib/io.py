import contextlib
import io
import os
import sys
import traceback
import typing

import checkpy.entities.exception as exception

__all__ = [
    # "captureStdin",
    "captureStdout"
]

@contextlib.contextmanager
def captureStdout() -> typing.Generator["_StreamListener", None, None]:
    listener = _StreamListener(sys.stdout)
    try:
        listener.start()
        yield listener
    except:
        raise
    finally:
        listener.stop()


@contextlib.contextmanager
def replaceStdout() -> typing.Generator["_Stream", None, None]:
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    stdout = _Stream()

    try:
        sys.stdout = stdout
        sys.stderr = open(os.devnull)
        yield stdout
    except:
        raise
    finally:
        sys.stderr.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr


@contextlib.contextmanager
def replaceStdin() -> typing.Generator[typing.TextIO, None, None]:
    def newInput(oldInput):
        def input(prompt=None):
            try:
                return oldInput()
            except EOFError:
                e = exception.InputError(
                    message="You requested too much user input",
                    stacktrace=traceback.format_exc())
                raise e
        return input

    oldInput = input
    old = sys.stdin

    stdin = io.StringIO()
 
    try:
        __builtins__["input"] = newInput(oldInput)
        sys.stdin = stdin
        yield stdin
    except:
        raise
    finally:
        sys.stdin = old
        __builtins__["input"] = oldInput


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
        self.content = ""

    def start(self):
        self.stream.register(self)

    def stop(self):
        self.stream.unregister(self)

    def update(self, content: str):
        self.content += content

    @property
    def stream(self) -> _Stream:
        return self._stream