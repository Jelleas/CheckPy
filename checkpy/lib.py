import sys
import re
import StringIO
import contextlib
import importlib
import imp
import cStringIO
import tokenize
import exception as excep
import caches

@contextlib.contextmanager
def _stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = StringIO.StringIO()
	sys.stdout = stdout
	yield stdout
	sys.stdout = old

def getFunction(functionName, fileName):
	return getattr(module(fileName), functionName)
	
def outputOf(fileName):
	return outputOfSource(fileName, source(fileName))

def outputOfSource(fileName, source):
	_, output = moduleAndOutputFromSource(fileName, source)
	return output

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

def module(fileName):
	mod, _ = moduleAndOutputFromSource(fileName, sourceOfDefinitions(fileName))
	return mod

@caches.cache()
def moduleAndOutputFromSource(fileName, source):
	mod = None
	output = ""
	exception = None
	
	with _stdoutIO() as s:
		moduleName = fileName[:-3] if fileName.endswith(".py") else fileName
		try:
			mod = imp.new_module(moduleName)
			exec source in mod.__dict__
			sys.modules[moduleName] = mod

		except Exception as e:
			exception = excep.SourceException(e, "while trying to import the code")

		for name, func in [(name, f) for name, f in mod.__dict__.iteritems() if callable(f)]:
			if func.__module__ == moduleName:
				setattr(mod, name, wrapFunctionWithExceptionHandler(func))
		output = s.getvalue()
	if exception:
		raise exception

	return mod, output

def neutralizeFunction(mod, functionName):
	if hasattr(mod, functionName):
		def dummy(*args, **kwargs):
			pass
		setattr(getattr(mod, functionName), "__code__", dummy.__code__)

def neutralizeFunctionFromImport(mod, functionName, importedModuleName):
	for attr in [getattr(mod, name) for name in dir(mod)]:
		if getattr(attr, "__name__", None) == importedModuleName:
			neutralizeFunction(attr, functionName)
		if getattr(attr, "__name__", None) == functionName and getattr(attr, "__module__", None) == importedModuleName:
			neutralizeFunction(mod, functionName)
	
def wrapFunctionWithExceptionHandler(func):
	def exceptionWrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Exception as e:
			argListRepr = reduce(lambda xs, x : xs + ", " + x, ["{}={}".format(func.__code__.co_varnames[i], args[i]) for i in range(len(args))])
			for kwargName in func.__code__.co_varnames[len(args):func.func_code.co_argcount]:
				argListRepr += ", {}={}".format(kwargName, kwargs[kwargName])
			raise excep.SourceException(e, "while trying to execute the function {} with arguments \"{}\"".format(func.__name__, argListRepr))
	return exceptionWrapper

def removeWhiteSpace(s):
	return re.sub(r"\s+", "", s, flags=re.UNICODE)

def getPositiveIntegersFromString(s):
	return [int(i) for i in re.findall(r"\d+", s)]

# inspiration from http://stackoverflow.com/questions/1769332/script-to-remove-python-comments-docstrings
def removeComments(source):
	io_obj = cStringIO.StringIO(source)
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