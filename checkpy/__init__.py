import pathlib as _pathlib

# Path to the directory checkpy was called from
USERPATH: _pathlib.Path = _pathlib.Path.cwd()

# Path to the directory of checkpy
CHECKPYPATH: _pathlib.Path = _pathlib.Path(__file__).parent

import dessert as _dessert

with _dessert.rewrite_assertions_context():
    from checkpy.lib import builder

from checkpy.tests import test, failed, passed
from checkpy.lib.basic import outputOf, getModule, getFunction
from checkpy.lib.sandbox import only, include, exclude, require
from checkpy.lib import static
from checkpy.lib import monkeypatch
from checkpy.lib.type import Type
from pytest import approx


__all__ = [
    "test",
    "failed",
    "passed",
    "outputOf",
    "getModule",
    "getFunction",
    "Type",
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
