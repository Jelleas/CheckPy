import sys
import re
try:
	# Python 2
	import StringIO
except:
	# Python 3
	import io as StringIO
import contextlib
import importlib
import imp
import tokenize
import traceback
import requests
from checkpy.entities import path
from checkpy.entities import exception
from checkpy.entities import function
from checkpy import caches

def require(fileName, source = None):
	fileExists = path.Path(fileName).exists()
	if source and not fileExists:
		download(source, destination = fileName)
		fileExists = True
	return fileExists

def source(fileName):
	source = ""
	with open(fileName) as f:
		source = f.read()
	return source

def sourceOfDefinitions(fileName):
	newSource = ""

	with open(fileName) as f:
		insideDefinition = False
		for line in removeComments(f.read()).split("\n"):
			line += "\n"
			if not line.strip():
				continue

			if (line.startswith(" ") or line.startswith("\t")) and insideDefinition:
				newSource += line
			elif line.startswith("def ") or line.startswith("class "):
				newSource += line
				insideDefinition = True
			elif line.startswith("import ") or line.startswith("from "):
				newSource += line
			else:
				insideDefinition = False
	return newSource


def getFunction(functionName, *args, **kwargs):
	return getattr(module(*args, **kwargs), functionName)

def outputOf(*args, **kwargs):
	_, output = moduleAndOutputOf(*args, **kwargs)
	return output

def module(*args, **kwargs):
	mod, _ = moduleAndOutputOf(*args, **kwargs)
	return mod

@caches.cache()
def moduleAndOutputOf(
		fileName,
		src = None,
		argv = None,
		stdinArgs = None,
		ignoreExceptions = (),
		overwriteAttributes = ()
	):
	"""
	This function handles most of checkpy's under the hood functionality
	fileName: the name of the file to run
	source: the source code to be run
	stdinArgs: optional arguments passed to stdin
	ignoredExceptions: a collection of Exceptions that will silently pass
	overwriteAttributes: a list of tuples [(attribute, value), ...]
	"""
	if src == None:
		src = source(fileName)

	mod = None
	output = ""
	excep = None

	with _stdoutIO() as stdout, _stdinIO() as stdin:
		# fill stdin with args
		if stdinArgs:
			for arg in stdinArgs:
				stdin.write(str(arg) + "\n")
			stdin.seek(0)

		# if argv given, overwrite sys.argv
		if argv:
			sys.argv, argv = argv, sys.argv

		moduleName = fileName.split(".")[0]

		try:
			mod = imp.new_module(moduleName)

			# overwrite attributes
			for attr, value in overwriteAttributes:
				setattr(mod, attr, value)

			# execute code in mod
			if sys.version_info > (3,0):
				exec(src, mod.__dict__)
			else:
				exec(src) in mod.__dict__

			# add resulting module to sys
			sys.modules[moduleName] = mod
		except tuple(ignoreExceptions) as e:
			pass
		except exception.CheckpyError as e:
			excep = e
		except Exception as e:
			excep = exception.SourceException(
				exception = e,
				message = "while trying to import the code",
				output = stdout.getvalue(),
				stacktrace = traceback.format_exc())
		except SystemExit as e:
			excep = exception.ExitError(
				message = "exit({}) while trying to import the code".format(int(e.args[0])),
				output = stdout.getvalue(),
				stacktrace = traceback.format_exc())

		# wrap every function in mod with Function
		for name, func in [(name, f) for name, f in mod.__dict__.items() if callable(f)]:
			if func.__module__ == moduleName:
				setattr(mod, name, function.Function(func))

		# reset sys.argv
		if argv:
			sys.argv = argv

		output = stdout.getvalue()
	if excep:
		raise excep

	return mod, output

def neutralizeFunction(function):
	def dummy(*args, **kwargs):
		pass
	setattr(function, "__code__", dummy.__code__)

def neutralizeFunctionFromImport(mod, functionName, importedModuleName):
	for attr in [getattr(mod, name) for name in dir(mod)]:
		if getattr(attr, "__name__", None) == importedModuleName:
			if hasattr(attr, functionName):
				neutralizeFunction(getattr(attr, functionName))
		if getattr(attr, "__name__", None) == functionName and getattr(attr, "__module__", None) == importedModuleName:
			if hasattr(mod, functionName):
				neutralizeFunction(getattr(mod, functionName))

def download(source, destination = None):
	try:
		r = requests.get(source)
	except requests.exceptions.ConnectionError as e:
		raise exception.DownloadError(message = "Oh no! It seems like there is no internet connection available?!")

	if not r.ok:
		raise exception.DownloadError(message = "Failed to download {} because: {}".format(source, r.reason))

	if not destination:
		destination = path.CWDPATH
	with open(str(destination), "wb+") as target:
		target.write(r.content)

def removeWhiteSpace(s):
	return re.sub(r"\s+", "", s, flags=re.UNICODE)

def getPositiveIntegersFromString(s):
	return [int(i) for i in re.findall(r"\d+", s)]

def getNumbersFromString(s):
	return [eval(n) for n in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", s)]

def getLine(text, lineNumber):
	lines = text.split("\n")
	try:
		return lines[lineNumber]
	except IndexError:
		raise IndexError("Expected to have atleast {} lines in:\n{}".format(lineNumber + 1, text))

# inspiration from http://stackoverflow.com/questions/1769332/script-to-remove-python-comments-docstrings
def removeComments(source):
	io_obj = StringIO.StringIO(source)
	out = ""
	prev_toktype = tokenize.INDENT
	last_lineno = -1
	last_col = 0
	indentation = "\t"
	for token_type, token_string, (start_line, start_col), (end_line, end_col), ltext in tokenize.generate_tokens(io_obj.readline):
		if start_line > last_lineno:
			last_col = 0

		# figure out type of indentation used
		if token_type == tokenize.INDENT:
			indentation = "\t" if "\t" in token_string else " "

		# write indentation
		if start_col > last_col and last_col == 0:
			out += indentation * (start_col - last_col)
		# write other whitespace
		elif start_col > last_col:
			out += " " * (start_col - last_col)

		# ignore comments
		if token_type == tokenize.COMMENT:
			pass
		# put all docstrings on a single line
		elif token_type == tokenize.STRING:
			out += re.sub("\n", " ", token_string)
		else:
			out += token_string

		prev_toktype = token_type
		last_col = end_col
		last_lineno = end_line
	return out

@contextlib.contextmanager
def _stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = StringIO.StringIO()
	sys.stdout = stdout
	yield stdout
	sys.stdout = old

@contextlib.contextmanager
def _stdinIO(stdin=None):
	old_input = input
	def new_input(prompt = None):
		try:
			return old_input()
		except EOFError as e:
			e = exception.InputError(
				message = "You requested too much user input",
				stacktrace = traceback.format_exc())
			raise e

	__builtins__["input"] = new_input

	old = sys.stdin
	if stdin is None:
		stdin = StringIO.StringIO()
	sys.stdin = stdin

	yield stdin

	__builtins__["input"] = old_input
	sys.stdin = old
