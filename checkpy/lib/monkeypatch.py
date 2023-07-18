from typing import Callable as _Callable

from checkpy.entities.function import _Function


__all__ = ["documentFunction", "neutralizeFunction"]


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


class _PrintableFunction(_Function):
    def __init__(self, function, docs):
        super().__init__(self, function)
        self._docs = docs
        
    def __repr__(self):
        return self._docs
