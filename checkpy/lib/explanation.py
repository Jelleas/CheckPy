from typing import Callable, List, Optional

from dessert.util import assertrepr_compare

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


class MockConfig:
    """This config is only used for config.getoption('verbose')"""
    def getoption(*args, **kwargs):
        return 0
