"""pyUPSTIlatex package

Chargement automatique des variables d'environnement depuis le fichier .env
situé à la racine du projet Python (dossier parent immédiat du package).

Cette étape permet d'accéder aux paramètres via os.environ partout dans le code
sans avoir à charger explicitement le .env à chaque fois.
"""

from __future__ import annotations

from pathlib import Path

try:
    from dotenv import load_dotenv

    _DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
    if _DOTENV_PATH.exists():
        load_dotenv(_DOTENV_PATH)
except Exception:
    # Ne jamais bloquer l'import du package si python-dotenv n'est pas installé
    # ou si un problème quelconque survient. Dans ce cas, on compte sur
    # l'environnement système pour fournir les variables nécessaires.
    pass
