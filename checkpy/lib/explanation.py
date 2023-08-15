import re

from types import ModuleType
from typing import Any, Callable, List, Optional, Union

from dessert.util import assertrepr_compare

import checkpy

__all__ = ["addExplainer"]


_explainers: List[Callable[[str, Any, Any], Optional[str]]] = []


def addExplainer(explainer: Callable[[str, Any, Any], Optional[str]]) -> None:
    _explainers.append(explainer)


def explainCompare(op: str, left: Any, right: Any) -> Optional[str]:
    for explainer in _explainers:
        rep = explainer(op, left, right)
        if rep:
            return rep

    # Custom Type message
    if isinstance(left, checkpy.Type) or isinstance(right, checkpy.Type):
        if isinstance(left, checkpy.Type):
            left, right = right, left
        if isinstance(left, str):
            left = f'"{left}"'
        return f"{left} is of type {right}"

    # Custom AbstractSyntaxTree message
    if isinstance(right, checkpy.static.AbstractSyntaxTree):
        if op == "in":
            return f"'{left.__name__}' is used in the source code"

        prefix = f"'{left.__name__}' is not used in the source code\n~"
        allLines = right.source.split("\n")
        lineNoWidth = len(str(max(n.lineno for n in right.foundNodes)))
        lines = []
        for node in right.foundNodes:
            lines.append(f"On line {str(node.lineno).rjust(lineNoWidth)}: {allLines[node.lineno - 1]}")
        return prefix + "\n~".join(lines)

    # Fall back on pytest (dessert) explanations
    rep = assertrepr_compare(MockConfig(), op, left, right)
    if rep:
        # On how to introduce newlines see:
        # https://github.com/vmalloc/dessert/blob/97616513a9ea600d50d53e9499044b51aeaf037a/dessert/util.py#L32
        return "\n~".join(rep)

    return rep


def simplifyAssertionMessage(assertion: Union[str, AssertionError]) -> str:
    message = str(assertion)

    # Filter out pytest's "Use -v to get the full diff" message
    lines = message.split("\n")
    lines = [line for line in lines if "Use -v to get the full diff" not in line]
    message = "\n".join(lines)

    # Find any substitution lines of the form where ... = ... from pytest
    whereRegex = re.compile(r"\n[\s]*\+(\s*)(where|and)[\s]*(.*) = (.*)")
    whereLines = whereRegex.findall(message)

    # If there are none, nothing to do
    if not whereLines:
        return message

    # Find the line containing assert ..., this is what will be substituted
    match = re.compile(r".*assert .*").search(message)

    # If there is no line starting with "assert ", nothing to do
    if match is None:
        return message
    
    assertLine = match.group(0)

    # Always include any lines before the assert line (a custom message)
    result = message[:match.start()]

    substitutionRegex = re.compile(r"(.*) = (.*)")
    oldIndent = 0
    oldSub = ""
    skipping = False

    # For each where line, apply the substitution on the first match
    for indent, _, left, right in whereLines:
        newIndent = len(indent)

        # If the previous step was skipped, and the next step is more indented, keep skipping
        if skipping and newIndent > oldIndent:
            continue

        # If the new indentation is smaller, there is a new substitution, cut off the old part
        # This prevents previous substitutions from interfering with new substitutions
        # For instance (2 == 1) + where 2 = foo(1) => (foo(1) == 1) where 1 = ...
        if newIndent <= oldIndent:
            cutttingMatch = re.search(re.escape(oldSub), assertLine)
            if cutttingMatch is None:
                raise checkpy.entities.exception.CheckpyError(
                    message=f"parsing the assertion '{message}' failed."
                            f" Please create an issue over at https://github.com/Jelleas/CheckPy/issues"
                            f" and copy-paste this entire message."
                )
            end = cutttingMatch.end()
            result += assertLine[:end]
            assertLine = assertLine[end:]
            oldSub = ""

        # Otherwise, no longer skipping
        oldIndent = newIndent
        skipping = False

        # If the right contains any checkpy function or module, skip
        if _shouldSkip(right):
            skipping = True
            continue

        # Substitute the first match in assertLine
        oldAssertLine = assertLine
        assertLine = re.sub(
            r"([^\w])" + re.escape(left) + r"([^\w\.])",
            r"\1" + right + r"\2",
            assertLine,
            count=1,
            flags=re.S
        )

        # If substitution succeeds, keep track of the sub
        if oldAssertLine != assertLine:
            oldSub = right
        # Else substitution failed, start skipping.
        else:
            skipping = True

        # Ensure all newlines are escaped
        assertLine = assertLine.replace("\n", "\\n")
    return result + assertLine


def _shouldSkip(content):
    modules = [checkpy]
    for elem in checkpy.__all__:
        attr = getattr(checkpy, elem)
        if isinstance(attr, ModuleType):
            modules.append(attr)

    skippedFunctionNames = []
    for module in modules:
        for elem in module.__all__:
            attr = getattr(module, elem)
            if callable(attr):
                skippedFunctionNames.append(elem)

    return any(elem in content for elem in skippedFunctionNames)
    

class MockConfig:
    """This config is only used for config.getoption('verbose')"""
    def getoption(*args, **kwargs):
        return 0
