"""Système de registre pour la découverte de classes personnalisées.

Ce module permet de découvrir et charger dynamiquement des classes personnalisées
depuis le dossier custom/ sans modifier le code source du package.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Type

from .document import UPSTILatexDocument


def discover_custom_document_class() -> Optional[Type[UPSTILatexDocument]]:
    """Découvre une classe UPSTILatexDocument personnalisée dans custom/document.py.

    Cherche un fichier custom/document.py (deux niveaux au-dessus de ce module)
    et tente d'importer une classe nommée CustomUPSTILatexDocument.

    Returns
    -------
    Type[UPSTILatexDocument] | None
        La classe personnalisée si trouvée et valide, None sinon.

    Notes
    -----
    - Le fichier custom/document.py ne doit PAS être un package (pas de __init__.py)
    - La classe CustomUPSTILatexDocument doit hériter de UPSTILatexDocument
    - Les erreurs d'import sont silencieuses (retourne None)
    """
    try:
        # Chemin vers custom/document.py
        # (2 niveaux au-dessus : pyupstilatex/ puis pyUPSTIlatex/)
        custom_module_path = (
            Path(__file__).resolve().parents[2] / "custom" / "document.py"
        )

        if not custom_module_path.exists():
            return None

        # Chargement dynamique du module
        spec = importlib.util.spec_from_file_location(
            "custom_document", custom_module_path
        )
        if spec is None or spec.loader is None:
            return None

        custom_module = importlib.util.module_from_spec(spec)
        sys.modules["custom_document"] = custom_module
        spec.loader.exec_module(custom_module)

        # Récupération de la classe CustomUPSTILatexDocument
        custom_class = getattr(custom_module, "CustomUPSTILatexDocument", None)

        if custom_class is None:
            return None

        # Vérification que c'est bien une sous-classe de UPSTILatexDocument
        if not isinstance(custom_class, type) or not issubclass(
            custom_class, UPSTILatexDocument
        ):
            return None

        return custom_class

    except Exception:
        # En cas d'erreur quelconque, on retourne None (fallback sur classe par défaut)
        return None


def get_document_class() -> Type[UPSTILatexDocument]:
    """Retourne la classe de document à utiliser (personnalisée ou par défaut).

    Returns
    -------
    Type[UPSTILatexDocument]
        La classe CustomUPSTILatexDocument si elle existe et est valide,
        sinon la classe UPSTILatexDocument par défaut.

    Examples
    --------
    >>> DocumentClass = get_document_class()
    >>> doc = DocumentClass(source="mon_fichier.tex")
    """
    custom_class = discover_custom_document_class()
    return custom_class if custom_class is not None else UPSTILatexDocument
