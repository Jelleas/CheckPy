import sys
import re
import StringIO
import contextlib
import importlib
import imp
import exception as excep

@contextlib.contextmanager
def _stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = StringIO.StringIO()
	sys.stdout = stdout
	yield stdout
	sys.stdout = old

def getFunction(functionName, fileName):
	return getattr(createModule(fileName), functionName)

def outputOf(fileName):
	exception = None
	with open(fileName) as f:
		try:
			printOutput = outputOfSource(f.read())
		except Exception as e:
			exception = e
	if exception:
		raise exception
	return printOutput

def outputOfSource(source):
	exception = None
	with _stdoutIO() as s:
		try:
			exec source in dict()
		except Exception as e:
			exception = excep.SourceException(e, "while trying to execute the code")
	if exception:
		raise exception
	return s.getvalue()

def sourceOfDefinitions(fileName):
	newSource = ""
	with open(fileName) as f:
		insideDefinition = False
		for line in f.readlines():
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

def createModule(fileName):
	return createModuleFromSource(fileName, sourceOfDefinitions(fileName))

def createModuleFromSource(fileName, source):
	moduleName = fileName[:-3] if fileName.endswith(".py") else fileName
	try:
		mod = imp.new_module(moduleName)
		exec source in mod.__dict__
		sys.modules[moduleName] = mod
	except Exception as e:
		raise excep.SourceException(e, "while trying to import the code")

	for name, func in [(name, f) for name, f in mod.__dict__.iteritems() if callable(f)]:
		if func.__module__ == moduleName:
			setattr(mod, name, wrapFunctionWithExceptionHandler(func))
	return mod

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
			argListRepr = reduce(lambda xs, x : xs + ", " + x, ["%s=%s" %(func.__code__.co_varnames[i], args[i]) for i in range(len(args))])
			for kwargName in func.__code__.co_varnames[len(args):func.func_code.co_argcount]:
				argListRepr += ", %s=%s" %(kwargName, kwargs[kwargName])
			raise excep.SourceException(e, "while trying to execute the function %s with arguments \"%s\"" %(func.__name__, argListRepr))
	return exceptionWrapper

def removeWhiteSpace(s):
	return re.sub(r"\s+", "", s, flags=re.UNICODE)

def getPositiveIntegersFromString(s):
	return [int(i) for i in re.findall(r"\d+", s)]