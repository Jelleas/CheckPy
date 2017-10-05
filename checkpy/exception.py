import traceback

class CheckpyError(Exception):
	def __init__(self, exception = None, message = "", output = ""):
		self._exception = exception
		self._message = message
		self._output = output

	def output(self):
		return self._output

	def __str__(self):
		if self._exception:
			return "\"{}\" occured {}".format(repr(self._exception), self._message)
		return "{} -> {}".format(self.__class__.__name__, self._message)

	def __repr__(self):
		return self.__str__()

class SourceException(CheckpyError):
	pass

class DownloadError(CheckpyError):
	pass

class ExitError(CheckpyError):
	pass
