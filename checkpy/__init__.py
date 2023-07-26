import dessert as _dessert

with _dessert.rewrite_assertions_context():
    from checkpy.lib import builder

from checkpy.tests import test, failed, passed
from checkpy.lib.basic import outputOf, getModule, getFunction
from checkpy.lib.sandbox import only, include, exclude, require
from checkpy.lib import static
from checkpy.lib import monkeypatch
from checkpy.entities.type import Type
from checkpy.entities.abstractsyntaxtree import AbstractSyntaxTree
from pytest import approx

import pathlib as _pathlib

__all__ = [
    "test",
    "failed",
    "passed",
    "outputOf",
    "getModule",
    "getFunction",
    "Type",
    "AbstractSyntaxTree",
    "static",
    "monkeypatch",
    "builder",
    "only",
    "include",
    "exclude",
    "require",
    "file",
    "approx"
]

file: _pathlib.Path = None
