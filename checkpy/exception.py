import traceback

class CheckpyError(Exception):
	def __init__(self, exception = None, message = ""):
		self._exception = exception
		self._message = message

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

"""
def TestException(Exception):
	def __init__(self, exception, message):
		self._exception = exception
		self._message = message

	def __str__(self):
		return "An exception \"%s\" occured in the test itself" %str(self._exception) + " " + self._message

	def __repr__(self):
		return "TestException()"
"""