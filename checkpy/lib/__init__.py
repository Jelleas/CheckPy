from checkpy.lib.basic import *
from checkpy.lib.static import getSource
from checkpy.lib.static import getSourceOfDefinitions
from checkpy.lib.static import removeComments
from checkpy.lib.static import getFunctionDefinitions
from checkpy.lib.static import getFunctionCalls
from checkpy.lib.static import getNumbersFrom
from checkpy.lib.monkeypatch import documentFunction
from checkpy.lib.monkeypatch import neutralizeFunction

# backward-compatible imports (v2 -> v1)
from checkpy.lib.basic import removeWhiteSpace
from checkpy.lib.basic import getPositiveIntegersFromString
from checkpy.lib.basic import getNumbersFromString
from checkpy.lib.basic import getLine
from checkpy.lib.basic import fileExists
from checkpy.lib.sandbox import download
from checkpy.lib.basic import require


# backward-compatible renames (v2 -> v1)
def source(fileName) -> str:
    import warnings
    warnings.warn(
        """source() is deprecated.
        Use getSource() instead.""",
        DeprecationWarning, stacklevel=2
    )
    return getSource(fileName)


def sourceOfDefinitions(fileName) -> str:
    import warnings
    warnings.warn(
        """sourceOfDefinitions() is deprecated.
        Use getSourceOfDefinitions() instead.""",
        DeprecationWarning, stacklevel=2
    )
    return getSourceOfDefinitions(fileName)


def module(*args, **kwargs):
    import warnings
    warnings.warn(
        """module() is deprecated.
        Use getModule() instead.""",
        DeprecationWarning, stacklevel=2
    )
    return getModule(*args, **kwargs)


def moduleAndOutputOf(*args, **kwargs):
    import warnings
    warnings.warn(
        """moduleAndOutputOf() is deprecated.q
        Use getModuleAndOutputOf() instead.""",
        DeprecationWarning, stacklevel=2
    )
    return getModuleAndOutputOf(*args, **kwargs)