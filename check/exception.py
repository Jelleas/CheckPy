class SourceException(Exception):
	def __init__(self, exception, message):
		self._exception = exception
		self._message = message

	def __str__(self):
		return "An exception \"%s\" occured" %repr(self._exception) + " " + self._message

	def __repr__(self):
		return "SourceException()"

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