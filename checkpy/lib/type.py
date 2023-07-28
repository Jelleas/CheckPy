import typeguard

class Type:
    """
    An equals and not equals comparible type annotation.

    assert [1, 2.0, None] == Type(List[Union[int, float, None]])
    assert [1, 2, 3] == Type(Iterable[int])
    assert {1: "foo"} != Type(Dict[int, str])
    assert (1, "foo", 3) != Type(Tuple[int, str, int])

    This is built on top of typeguard.check_type, see docs @
    https://typeguard.readthedocs.io/en/stable/api.html#typeguard.check_type
    """
    def __init__(self, type_: type):
        self._type = type_

    def __eq__(self, __value: object) -> bool:
        isEq = True
        def callback(err: typeguard.TypeCheckError, memo: typeguard.TypeCheckMemo):
            nonlocal isEq
            isEq = False
        typeguard.check_type(__value, self._type, typecheck_fail_callback=callback)
        return isEq

    def __repr__(self) -> str:
        return (str(self._type)
            .replace("typing.", "")
            .replace("<class 'int'>", "int")
            .replace("<class 'float'>", "float")
            .replace("<class 'bool'>", "bool")
            .replace("<class 'str'>", "str")
            .replace("<class 'list'>", "list")
            .replace("<class 'tuple'>", "tuple")
            .replace("<class 'dict'>", "dict")
            .replace("<class 'set'>", "set")
        )
