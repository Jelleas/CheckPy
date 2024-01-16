import typing as _typing

class CheckpyError(Exception):
    def __init__(
            self,
            exception:
            _typing.Optional[Exception]=None,
            message: str="",
            output: str="",
            stacktrace: str=""
        ):
        self._exception = exception
        self._message = message
        self._output = output
        self._stacktrace = stacktrace

    def output(self) -> str:
        return self._output

    def stacktrace(self) -> str:
        return self._stacktrace

    def __str__(self):
        if self._exception:
            return "\"{}\" occured {}".format(repr(self._exception), self._message)
        return "{} -> {}".format(self.__class__.__name__, self._message)

    def __repr__(self):
        return self.__str__()

class SourceException(CheckpyError):
    pass

class InputError(CheckpyError):
    pass

class TestError(CheckpyError):
    pass

class DownloadError(CheckpyError):
    pass

class ExitError(CheckpyError):
    pass

class PathError(CheckpyError):
    pass

class TooManyFilesError(CheckpyError):
    pass

class MissingRequiredFiles(CheckpyError):
    def __init__(self, missingFiles: _typing.List[str]):
        super().__init__(message=f"Missing the following required file{'s' if len(missingFiles) != 1 else ''}: {', '.join(missingFiles)}")
        self.missingFiles = tuple(missingFiles)