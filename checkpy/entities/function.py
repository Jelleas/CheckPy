import contextlib
from . import exception

class Function(object):
	def __init__(self, function):
		self._function = function
		self._stdoutOutput = ""

	def __call__(self, *args, **kwargs):
		import checkpy.lib as lib
		try:
			with lib.captureStdout() as stdout:
				outcome = self._function(*args, **kwargs)
				self._stdoutOutput = stdout.getvalue()
				return outcome
		except Exception as e:
			argumentNames = self.arguments()
			nArgs = len(args) + len(kwargs)

			message = "while trying to execute {}()".format(self.name())
			if nArgs > 0:
				argsRepr = ", ".join("{}={}".format(argumentNames[i], args[i]) for i in range(len(args)))	
				kwargsRepr = ", ".join("{}={}".format(kwargName, kwargs[kwargName]) for kwargName in argumentNames[len(args):nArgs])
				representation = ", ".join(s for s in [argsRepr, kwargsRepr] if s)
				message = "while trying to execute {}({})".format(self.name(), representation)
			
			raise exception.SourceException(exception = e, message = message)

	@property
	def name(self):
		"""gives the name of the function"""
		return self._function.__name__

	@property
	def arguments(self):
		"""gives the argument names of the function"""
		return list(self._function.__code__.co_varnames)

	@property
	def printOutput(self):
		"""stateful function that returns the print (stdout) output of the latest function call as a string"""
		return self._stdoutOutput