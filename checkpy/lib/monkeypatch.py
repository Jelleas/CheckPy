from typing import Callable

from checkpy.entities.function import Function

__all__ = ["documentFunction", "neutralizeFunction"]


def documentFunction(func: Callable, documentation: str) -> "PrintableFunction":
    """Creates a function that shows documentation when its printed / shows up in an error."""
    return PrintableFunction(func, documentation)


def neutralizeFunction(function: Callable):
    """
    Patches the function to do nothing (no op).
    Useful for unblocking blocking functions like time.sleep() or plt.slow()
    """
    def dummy(*args, **kwargs):
        pass
    setattr(function, "__code__", dummy.__code__)


class PrintableFunction(Function):
    def __init__(self, function, docs):
        super().__init__(self, function)
        self._docs = docs
        
    def __repr__(self):
        return self._docs
