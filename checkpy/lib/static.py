import ast as _ast
import io as _io
import re as _re
import tokenize as _tokenize

from pathlib import Path as _Path
from typing import Optional as _Optional
from typing import Union as _Union
from typing import List as _List

import checkpy as _checkpy
import checkpy.entities.exception as _exception


__all__ = [
    "getSource",
    "getSourceOfDefinitions",
    "removeComments",
    "getNumbersFrom",
    "getFunctionCalls",
    "getFunctionDefinitions",
    "getAstNodes",
    "AbstractSyntaxTree"
]


def getSource(fileName: _Optional[_Union[str, _Path]]=None) -> str:
    """Get the contents of the file."""
    if fileName is None:
        if _checkpy.file is None:
            raise _exception.CheckpyError(
                message=f"Cannot call getSource() without passing fileName as argument if not test is running."
            )
        fileName = _checkpy.file.name

    with open(fileName) as f:
        return f.read()


def getSourceOfDefinitions(fileName: _Optional[_Union[str, _Path]]=None) -> str:
    """Get just the source code inside definitions (def / class) and any imports."""
    if fileName is None:
        if _checkpy.file is None:
            raise _exception.CheckpyError(
                message=f"Cannot call getSourceOfDefinitions() without passing fileName as argument if not test is running."
            )
        fileName = _checkpy.file.name

    source = getSource(fileName)

    class Visitor(_ast.NodeVisitor):
        def __init__(self):
            self.lineNumbers = set()

        def visit_ClassDef(self, node: _ast.ClassDef):
            if node.end_lineno is None:
                self.lineNumbers.add(node.lineno - 1)
            else:
                self.lineNumbers |= set(range(node.lineno - 1, node.end_lineno))
            super().generic_visit(node)
        
        def visit_FunctionDef(self, node: _ast.FunctionDef):
            if node.end_lineno is None:
                self.lineNumbers.add(node.lineno - 1)
            else:
                self.lineNumbers |= set(range(node.lineno - 1, node.end_lineno))
            super().generic_visit(node)

        def visit_Import(self, node: _ast.Import):
            self.lineNumbers.add(node.lineno - 1)
            super().generic_visit(node)

        def visit_ImportFrom(self, node: _ast.ImportFrom):
            self.lineNumbers.add(node.lineno - 1)
            super().generic_visit(node)

    tree = _ast.parse(source)
    visitor = Visitor()
    visitor.visit(tree)

    lines = source.split("\n")
    return "\n".join(lines[n] for n in sorted(visitor.lineNumbers))


def getNumbersFrom(text: str) -> _List[_Union[int, float]]:
    """
    Get all numbers from a string.
    Only the first dot in a number is used:
        7.3.4 produces float(7.3). The 4 is discarded.
    'e' is unsupported and considered a normal seperator:
        1e7 produces int(1) and int(7)
    Whitespace (or generally non-digits) matters:
        7-8 produces int(7) and int(8)
        7 -8 produces int(7) and int(-8)
        7 - 8 produces int(7) and int(8)
    """
    numbers: _List[_Union[int, float]] = []

    n = ""
    for c in text + " ":
        if c.isdigit() or c == "." or (c in "+-" and not n):
            n += c
        elif n:
            # drop everything after the second '.'
            if n.count(".") > 1:
                n = ".".join(n.split(".")[:2])

            numbers.append(float(n) if "." in n else int(n))
            n = ""

    return numbers


# inspiration from http://stackoverflow.com/questions/1769332/script-to-remove-python-comments-docstrings
def removeComments(source: str) -> str:
    """Remove comments from a string containing Python source code."""
    io_obj = _io.StringIO(source)
    out = ""
    last_lineno = -1
    last_col = 0
    indentation = "\t"
    for token_type, token_string, (start_line, start_col), (end_line, end_col), ltext in _tokenize.generate_tokens(io_obj.readline):
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
    """Get all names of function called in source."""
    class CallVisitor(_ast.NodeVisitor):
        def __init__(self):
            self.parts = []

        def visit_Attribute(self, node):
            super().generic_visit(node)
            self.parts.append(node.attr)

        def visit_Name(self, node):
            self.parts.append(node.id)

        @property
        def call(self):
            return ".".join(self.parts)

    class FunctionsVisitor(_ast.NodeVisitor):
        def __init__(self):
            self.functionCalls = []

        def visit_Call(self, node):
            callVisitor = CallVisitor()
            callVisitor.visit(node.func)
            super().generic_visit(node)
            self.functionCalls.append(callVisitor.call)

    if source is None:
        source = getSource()

    tree = _ast.parse(source)
    visitor = FunctionsVisitor()
    visitor.visit(tree)
    return visitor.functionCalls


def getFunctionDefinitions(source: _Optional[str]=None) -> _List[str]:
    """Get all names of Function definitions from source."""
    class FunctionsVisitor(_ast.NodeVisitor):
        def __init__(self):
            self.functionNames = []

        def visit_FunctionDef(self, node: _ast.FunctionDef):
            self.functionNames.append(node.name)
            super().generic_visit(node)

    if source is None:
        source = getSource()

    tree = _ast.parse(source)
    visitor = FunctionsVisitor()
    visitor.visit(tree)
    return visitor.functionNames


def getAstNodes(*types: type, source: _Optional[str]=None) -> _List[_ast.AST]:
    """
    Given ast.AST types find all nodes with those types.
    Every node found will have a `.lineno` attribute to get its line number.
    Some examples:

    ```
    getAstNodes(ast.For) # Will find all for-loops in the source
    getAstNodes(ast.Mult, ast.Add) # Will find all uses of multiplication (*) and addition (+)
    ```
    """
    for type_ in types:
        if type_.__module__ != _ast.__name__:
            raise _exception.CheckpyError(message=f"{type_} passed to getAstNodes() is not of type ast.AST")

    nodes: _List[_ast.AST] = []

    class Visitor(_ast.NodeVisitor):
        def __init__(self):
            self.lineNumber = 0

        def generic_visit(self, node: _ast.AST):
            if hasattr(node, "lineno"):
                self.lineNumber = node.lineno

            if any(isinstance(node, type_) for type_ in types):
                node.lineno = self.lineNumber
                nodes.append(node)

            super().generic_visit(node)

    if source is None:
        source = getSource()

    tree = _ast.parse(source)
    Visitor().visit(tree)
    return nodes


class AbstractSyntaxTree:
    """
    An 'in' and 'not in' comparible AbstractSyntaxTree for any ast.Node (any type of ast.AST).
    For instance:

    ```
    assert ast.For not in AbstractSyntaxTree() # assert that a for-loop is not present
    assert ast.Mult in AbstractSyntaxTree() # assert that multiplication is present
    ```
    """
    def __init__(self, fileName: _Optional[str]=None):
        # Keep track of any nodes found from last search for a pretty assertion message 
        self.foundNodes: _List[_ast.AST] = []

        # Similarly hold on to the source code
        self.source: str = getSource(fileName=fileName)

    def __contains__(self, item: type) -> bool:
        # Python 3.8 and before use "_ast" for ast.Break.__module__
        if item.__module__ not in [_ast.__name__, "_ast"]:
            raise _checkpy.entities.exception.CheckpyError(
                message=f"{item} is not of type {_ast.AST}."
                        f" Can only search for {_ast.AST} types in AbstractSyntaxTree."
            )
        
        self.foundNodes = getAstNodes(item, source=self.source)        
        return bool(self.foundNodes)