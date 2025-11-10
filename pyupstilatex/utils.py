import json
from pathlib import Path
from typing import Any, Optional

from .exceptions import DocumentParseError


def check_type_from_str(obj: Any, expected_type: str) -> bool:
    """
    Vérifie si `obj` est du type indiqué par `expected_type` (nom sous forme de str).
    Exemple: check_type_from_str("abc", "str") -> True
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
    }

    cls = type_map.get(expected_type)
    if cls is None:
        return False
    return isinstance(obj, cls)


def read_json_config(path: Optional[Path | str] = None) -> dict:
    """Lit le fichier JSON de configuration et le retourne sous forme de dictionnaire.

    Si 'path' est None, résout le fichier JSON embarqué `pyUPSTIlatex.json` situé à la racine du package (un niveau au-dessus de ce module).
    """
    try:
        if path is None:
            json_path = Path(__file__).resolve().parents[1] / "pyUPSTIlatex.json"
        else:
            json_path = Path(path)
        with json_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise DocumentParseError(
            f"Impossible de lire le fichier JSON de config {json_path}: {e}"
        )
