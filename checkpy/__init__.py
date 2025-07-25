import pathlib as _pathlib
import typing as _typing

# Path to the directory checkpy was called from
USERPATH: _pathlib.Path = _pathlib.Path.cwd()

# Path to the directory of checkpy
CHECKPYPATH: _pathlib.Path = _pathlib.Path(__file__).parent

# TODO rm me once below is fixed:
#  https://github.com/pytest-dev/pytest/issues/9174
# importing requests before dessert/pytest assert rewrite prevents
# a ValueError on python3.10
import requests as _requests

import dessert as _dessert
with _dessert.rewrite_assertions_context():
    from checkpy.lib import declarative

from checkpy.tests import test, failed, passed
from checkpy.lib.basic import outputOf, getModule, getFunction
from checkpy.lib.sandbox import only, include, includeFromTests, exclude, require, download
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
    "declarative",
    "only",
    "include",
    "includeFromTests",
    "exclude",
    "require",
    "download",
    "file",
    "approx"
]

# To be tested file
file: _typing.Optional[_pathlib.Path] = None

# Path to the tests directory
testPath: _typing.Optional[_pathlib.Path] = None

class _Context:
    def __init__(self, debug=False, json=False, silent=False):
        self.debug = debug
        self.json = json
        self.silent = silent

    def __reduce__(self):
        return (
            _Context,
            (self.debug, self.json, self.silent)
        )

context = _Context()