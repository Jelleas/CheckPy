import io as _io
import re as _re
import tokenize as _tokenize

from pathlib import Path as _Path
from typing import Optional as _Optional
from typing import Union as _Union

import checkpy as _checkpy


__all__ = ["getSource", "getSourceOfDefinitions", "removeComments"]


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
	io_obj = io.StringIO(source)
	out = ""
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

		last_col = end_col
		last_lineno = end_line
	return out
