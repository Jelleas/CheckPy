from . import exception

class Function(object):
	def __init__(self, function):
		self._function = function

	def __call__(self, *args, **kwargs):
		try:
			return self._function(*args, **kwargs)
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

	def name(self):
		return self._function.__name__

	def arguments(self):
		return list(self._function.__code__.co_varnames)