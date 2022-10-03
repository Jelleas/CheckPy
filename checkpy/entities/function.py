import os
import sys
import re

import contextlib
import inspect
import checkpy.entities.exception as exception

if sys.version_info >= (3,0):
	import io
else:
	import StringIO as io

class Function(object):
	def __init__(self, function):
		self._function = function
		self._printOutput = ""

	def __call__(self, *args, **kwargs):
		old = sys.stdout
		try:
			with self._captureStdout() as listener:
				outcome = self._function(*args, **kwargs)
				self._printOutput = listener.content
				return outcome
		except Exception as e:
			if isinstance(e,TypeError):
				no_arguments = re.search(r"takes (\d+) positional arguments but (\d+) were given", e.__str__())
				if no_arguments:
					raise exception.SourceException(exception = None, message = f"the function should take {no_arguments.group(1)} arguments but does not")
			sys.stdout = old
			argumentNames = self.arguments
			nArgs = len(args) + len(kwargs)

			message = "while trying to execute {}()".format(self.name)
			if nArgs > 0:
				argsRepr = ", ".join("{}={}".format(argumentNames[i], args[i]) for i in range(len(args)))
				kwargsRepr = ", ".join("{}={}".format(kwargName, kwargs[kwargName]) for kwargName in argumentNames[len(args):nArgs])
				representation = ", ".join(s for s in [argsRepr, kwargsRepr] if s)
				message = "while trying to execute {}({})".format(self.name, representation)

			raise exception.SourceException(exception = e, message = message)

	@property
	def name(self):
		"""gives the name of the function"""
		return self._function.__name__

	@property
	def arguments(self):
		"""gives the argument names of the function"""
		return inspect.getfullargspec(self._function)[0]

	@property
	def printOutput(self):
		"""stateful function that returns the print (stdout) output of the latest function call as a string"""
		return self._printOutput

	@contextlib.contextmanager
	def _captureStdout(self):
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
		self._listeners = []

	def register(self, listener):
		self._listeners.append(listener)

	def unregister(self, listener):
		self._listeners.remove(listener)

	def write(self, text):
		"""Overwrites StringIO.write to update all listeners"""
		io.StringIO.write(self, text)
		self._onUpdate(text)

	def writelines(self, sequence):
		"""Overwrites StringIO.writelines to update all listeners"""
		io.StringIO.writelines(self, sequence)
		for item in sequence:
			self._onUpdate(item)

	def _onUpdate(self, content):
		for listener in self._listeners:
			listener.update(content)

class _StreamListener(object):
	def __init__(self, stream):
		self._stream = stream
		self._content = ""

	def start(self):
		self.stream.register(self)

	def stop(self):
		self.stream.unregister(self)

	def update(self, content):
		self._content += content

	@property
	def content(self):
		return self._content

	@property
	def stream(self):
		return self._stream

_outStream = _Stream()
