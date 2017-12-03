import traceback

class CheckpyError(Exception):
	def __init__(self, exception = None, message = "", output = "", stacktrace = ""):
		self._exception = exception
		self._message = message
		self._output = output
		self._stacktrace = stacktrace

	def output(self):
		return self._output

	def stacktrace(self):
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
