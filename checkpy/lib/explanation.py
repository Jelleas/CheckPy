import re

from typing import Callable, List, Optional, Union

from dessert.util import assertrepr_compare

import checkpy

__all__ = ["addExplainer"]


_explainers: List[Callable[[str, str, str], Optional[str]]] = []


def addExplainer(explainer: Callable[[str, str, str], Optional[str]]) -> None:
    _explainers.append(explainer)


def explainCompare(op: str, left: str, right: str) -> Optional[str]:
    for explainer in _explainers:
        rep = explainer(op, left, right)
        if rep:
            return rep

    # Fall back on pytest (dessert) explanations
    rep = assertrepr_compare(MockConfig(), op, left, right)
    if rep:
        # On how to introduce newlines see:
        # https://github.com/vmalloc/dessert/blob/97616513a9ea600d50d53e9499044b51aeaf037a/dessert/util.py#L32
        return "\n~".join(rep)

    return rep


def simplifyAssertionMessage(assertion: Union[str, AssertionError]) -> str:
    message = str(assertion)

    # Find any substitution lines of the form where ... = ... from pytest
    whereRegex = re.compile(r"\n[\s]*\+(\s*)(where|and)[\s]*(.*)")
    whereLines = whereRegex.findall(message)

    # If there are none, nothing to do
    if not whereLines:
        return message

    # Find the line containing assert ..., this is what will be substituted
    match = re.compile(r".*assert .*").search(message)
    assertLine = match.group(0)

    # Always include any lines before the assert line (a custom message)
    result = message[:match.start()]

    substitutionRegex = re.compile(r"(.*) = (.*)")
    oldIndent = 0
    oldSub = ""
    skipping = False

    # For each where line, apply the substitution on the first match
    for indent, _, substitution in whereLines:
        newIndent = len(indent)

        # If the previous step was skipped, and the next step is more indented, keep skipping
        if skipping and newIndent > oldIndent:
            continue

        # If the new indentation is smaller, there is a new substitution, cut off the old part
        # This prevents previous substitutions from interfering with new substitutions
        # For instance (2 == 1) + where 2 = foo(1) => (foo(1) == 1) where 1 = ...
        if newIndent <= oldIndent:
            end = re.search(re.escape(oldSub), assertLine).end()
            result += assertLine[:end]
            assertLine = assertLine[end:]
            oldSub = ""

        # Otherwise, no longer skipping
        oldIndent = newIndent
        skipping = False

        # Find the left (the original) and the right (the substitute)
        match = substitutionRegex.match(substitution)
        left, right = match.group(1), match.group(2)

        # If the right contains any checkpy function, skip
        if any(elem + "(" in right for elem in checkpy.__all__):
            skipping = True
            continue

        # Substitute the first match in assertLine
        assertLine = re.sub(
            re.escape(left),
            right,
            assertLine,
            count=1,
            flags=re.S
        )

        oldSub = right

        # Ensure all newlines are escaped
        assertLine = assertLine.replace("\n", "\\n")
    return result + assertLine


class MockConfig:
    """This config is only used for config.getoption('verbose')"""
    def getoption(*args, **kwargs):
        return 0
