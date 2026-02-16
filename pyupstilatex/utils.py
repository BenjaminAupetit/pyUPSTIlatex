from typing import Any, List, Union


def check_types(obj: Any, expected_types: Union[str, List[str]]) -> bool:
    """
    Vérifie si `obj` est du type indiqué par `expected_types` (str ou liste de str).
    Exemple:
      check_types("abc", "str")         -> True
      check_types(123, "text")          -> True
      check_types(3.14, ["str", "text"]) -> True
    """
    type_map = {
        "str": str,
        "int": int,
        "float": float,
        "dict": dict,
        "list": list,
        "tuple": tuple,
        "bool": bool,
        "set": set,
        "text": (str, int, float),
    }

    if isinstance(expected_types, str):
        expected_types = [expected_types]

    for type_name in expected_types:
        cls = type_map.get(type_name)
        if cls and isinstance(obj, cls):
            return True

    return False
