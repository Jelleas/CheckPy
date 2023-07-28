from typing import Callable as _Callable

from checkpy.entities.function import Function as _Function


__all__ = [
    "documentFunction",
    "neutralizeFunction",
    "patchMatplotlib",
    "patchNumpy"
]


def documentFunction(func: _Callable, documentation: str) -> "_PrintableFunction":
    """Creates a function that shows documentation when its printed / shows up in an error."""
    return _PrintableFunction(func, documentation)


def neutralizeFunction(function: _Callable):
    """
    Patches the function to do nothing (no op).
    Useful for unblocking blocking functions like time.sleep() or plt.slow()
    """
    def dummy(*args, **kwargs):
        pass
    setattr(function, "__code__", dummy.__code__)


def patchMatplotlib():
    """
    Patches matplotlib's blocking functions to do nothing.
    Make sure this is called before any matplotlib.pyplot import.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.switch_backend("Agg")
        neutralizeFunction(plt.pause)
        neutralizeFunction(plt.show)
    except ImportError:
        pass


def patchNumpy():
    """
    Always have numpy raise floating-point errors as an error, no warnings.
    """
    try:
        import numpy
        numpy.seterr('raise')
    except ImportError:
        pass


class _PrintableFunction(_Function):
    def __init__(self, function: _Callable, docs: str):
        super().__init__(function)
        self._docs = docs
        
    def __repr__(self):
        return self._docs
