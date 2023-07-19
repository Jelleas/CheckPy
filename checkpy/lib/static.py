import io as _io
import re as _re
import tokenize as _tokenize

from pathlib import Path as _Path
from typing import Optional as _Optional
from typing import Union as _Union
from typing import List as _List

import checkpy as _checkpy


__all__ = [
	"getSource",
	"getSourceOfDefinitions",
	"removeComments",
	"getFunctionCalls",
	"getFunctionDefinitions"
]


def getSource(fileName: _Optional[_Union[str, _Path]]=None) -> str:
	"""Get the contents of the file."""
	if fileName is None:
		fileName = _checkpy.file.name

	with open(fileName) as f:
		return f.read()


def getSourceOfDefinitions(fileName: _Optional[_Union[str, _Path]]=None) -> str:
	"""Get just the source code inside definitions (def / class)."""
	if fileName is None:
		fileName = _checkpy.file.name

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


# inspiration from http://stackoverflow.com/questions/1769332/script-to-remove-python-comments-docstrings
def removeComments(source: str) -> str:
	"""Remove comments from a string containing Python source code."""
	io_obj = io.StringIO(source)
	out = ""
	last_lineno = -1
	last_col = 0
	indentation = "\t"
	for token_type, token_string, (start_line, start_col), (end_line, end_col), ltext in tokenize.generate_tokens(io_obj.readline):
		if start_line > last_lineno:
			last_col = 0

		# figure out type of indentation used
		if token_type == _tokenize.INDENT:
			indentation = "\t" if "\t" in token_string else " "

		# write indentation
		if start_col > last_col and last_col == 0:
			out += indentation * (start_col - last_col)
		# write other whitespace
		elif start_col > last_col:
			out += " " * (start_col - last_col)

		# ignore comments
		if token_type == _tokenize.COMMENT:
			pass
		# put all docstrings on a single line
		elif token_type == _tokenize.STRING:
			out += _re.sub("\n", " ", token_string)
		else:
			out += token_string

		last_col = end_col
		last_lineno = end_line
	return out


def getFunctionCalls(source: _Optional[str]=None) -> _List[str]:
	"""Get all Function calls from source."""
	import ast

	class CallVisitor(ast.NodeVisitor):
		def __init__(self):
			self.parts = []

		def visit_Attribute(self, node):
			super().generic_visit(node)
			self.parts.append(node.attr)

		def visit_Name(self, node):
			self.parts.append(node.id)

		@property
		def call(self):
			return ".".join(self.parts) + "()"

	class FunctionsVisitor(ast.NodeVisitor):
		def __init__(self):
			self.functionCalls = []

		def visit_Call(self, node):
			callVisitor = CallVisitor()
			callVisitor.visit(node.func)
			super().generic_visit(node)
			self.functionCalls.append(callVisitor.call)

	if source is None:
		source = getSource()

	tree = ast.parse(source)
	visitor = FunctionsVisitor()
	visitor.visit(tree)
	return visitor.functionCalls

def getFunctionDefinitions(
		*functionNames: str,
		source: _Optional[str]=None
	) -> _List[str]:
	"""Get all Function definitions from source."""
	def isFunctionDefIn(functionName, src):
		regex = _re.compile(".*def[ \\t]+{}[ \\t]*\(.*?\).*".format(functionName), _re.DOTALL)
		return regex.match(src)

	if source is None:
		source = getSource()
	source = removeComments(source)
	return all(isFunctionDefIn(fName, source) for fName in functionNames)