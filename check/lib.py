import sys
import re
import StringIO
import contextlib
import importlib
import imp

@contextlib.contextmanager
def _stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = StringIO.StringIO()
	sys.stdout = stdout
	yield stdout
	sys.stdout = old

def getFunction(functionName, fileName):
	moduleName = fileName[:-3] if fileName.endswith(".py") else fileName
	return getattr(createModule(moduleName, sourceOfDefinitions(fileName)), functionName)

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
			exception = e
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
			elif line.startswith("import "):
				newSource += line
			else:
				insideDefinition = False
	return newSource

def createModule(name, source):
	mod = imp.new_module(name)
	exec source in mod.__dict__
	sys.modules[name] = mod
	return mod

def removeWhiteSpace(s):
	return re.sub(r"\s+", "", s, flags=re.UNICODE)

def getPositiveIntegersFromString(s):
	return [int(i) for i in re.findall(r"\d+", s)]