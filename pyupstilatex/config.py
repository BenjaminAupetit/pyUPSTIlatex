"""Utilities to access configuration from environment variables.

This module assumes `.env` is automatically loaded at package import time
(handled in pyupstilatex/__init__.py). It provides small helpers to fetch
values with proper typing and reasonable defaults.

Usage:
    from pyupstilatex.config import get_str, get_int, get_bool
    ftp_user = get_str("FTP_USER", default="")
    latex_recto = get_bool("POLY_TD_RECTO_VERSO", default=True)
    nb_compil = get_int("COMPILATION_NOMBRE_COMPILATIONS_LATEX", default=2)

Notes:
- All values are read from os.environ at call time (no persistent cache),
  so changing env at runtime is reflected on next call.
- For booleans, accepted values: 1, true, yes, y, on; falsy: 0, false, no, n, off.
- For paths, get_path returns a pathlib.Path (no existence check).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

__all__ = [
    "get_str",
    "get_int",
    "get_bool",
    "get_path",
    "get_list",
    # Dataclasses
    "MetaConfig",
    "CompilationConfig",
    "TraitementParLotConfig",
    "UploadConfig",
    "PolyTDConfig",
    "AppConfig",
    "load_config",
]


def get_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Return an environment variable as string, or default if missing."""
    return os.environ.get(key, default)


def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """Return an environment variable parsed as int, or default if invalid/missing."""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(str(val).strip())
    except (TypeError, ValueError):
        return default


_TRUTHY = {"1", "true", "yes", "y", "on"}
_FALSY = {"0", "false", "no", "n", "off"}


def get_bool(key: str, default: bool = False) -> bool:
    """Return an environment variable parsed as bool, or default if invalid/missing."""
    val = os.environ.get(key)
    if val is None:
        return default
    s = str(val).strip().lower()
    if s in _TRUTHY:
        return True
    if s in _FALSY:
        return False
    # Numeric fallbacks
    try:
        return bool(int(s))
    except ValueError:
        return default


def get_path(key: str, default: Optional[str | Path] = None) -> Path:
    """Return an environment variable as Path. Uses default if missing."""
    val = os.environ.get(key)
    if val is None:
        return Path(default) if default is not None else Path()
    return Path(val)


def get_list(
    key: str, default: Optional[Iterable[str]] = None, sep: str = ";"
) -> list[str]:
    """Return an environment variable as a list of strings, split by `sep`.

    - Trims whitespace around items
    - Filters out empty segments
    - If missing, returns list(default) or []
    """
    val = os.environ.get(key)
    if val is None:
        return list(default) if default is not None else []
    parts = [p.strip() for p in val.split(sep)]
    return [p for p in parts if p]


# =========================
# Section-based dataclasses
# =========================
@dataclass(frozen=True)
class MetaConfig:
    """Valeurs par défaut des métadonnées documents (provenant du .env)."""

    id_document_prefixe: str
    variante: str
    matiere: str
    classe: str
    type_document: str
    titre: str
    version: str
    auteur: str

    @classmethod
    def from_env(cls) -> "MetaConfig":
        return cls(
            id_document_prefixe=get_str("META_DEFAULT_ID_DOCUMENT_PREFIXE", "EB:"),
            variante=get_str("META_DEFAULT_VARIANTE", "upsti"),
            matiere=get_str("META_DEFAULT_MATIERE", "S2I"),
            classe=get_str("META_DEFAULT_CLASSE", "PT"),
            type_document=get_str("META_DEFAULT_TYPE_DOCUMENT", "cours"),
            titre=get_str("META_DEFAULT_TITRE", "Titre par défaut"),
            version=get_str("META_DEFAULT_VERSION", "0.1"),
            auteur=get_str("META_DEFAULT_AUTEUR", "Emmanuel BIGEARD"),
        )


@dataclass(frozen=True)
class CompilationConfig:
    """Valeurs par défaut pour la compilation, provenant du .env"""

    # Valeurs par défaut des paramètres de compilation
    compiler: bool
    renommer_automatiquement: bool
    versions_a_compiler: list[str]
    versions_accessibles_a_compiler: list[str]
    est_un_document_a_trous: bool
    copier_pdf_dans_dossier_cible: bool
    upload: bool
    dossier_ftp: str

    # Paramètres de compilation LaTeX
    nombre_compilations_latex: int

    # Compilation rapide et OS
    nom_fichier_parametres_compilation: str
    extension_fichier_metadonnees: str
    format_nom_fichier: str
    dossier_cible_par_rapport_au_fichier_tex: str
    copier_fichier_version: bool
    format_nom_fichier_version: str
    dossier_sources_latex: str
    dossier_tmp_pour_zip: str
    suffixe_nom_fichier_prof: str
    suffixe_nom_fichier_a_trous: str
    suffixe_nom_diaporama: str
    suffixe_nom_sources: str

    @classmethod
    def from_env(cls) -> "CompilationConfig":
        return cls(
            # Defaults (from COMPILATION_DEFAUT_* env vars)
            compiler=get_bool("COMPILATION_DEFAUT_COMPILER", True),
            renommer_automatiquement=get_bool(
                "COMPILATION_DEFAUT_RENOMMER_AUTOMATIQUEMENT", True
            ),
            versions_a_compiler=get_list(
                "COMPILATION_DEFAUT_VERSIONS_A_COMPILER", default=[], sep=","
            ),
            versions_accessibles_a_compiler=get_list(
                "COMPILATION_DEFAUT_VERSIONS_ACCESSIBLES_A_COMPILER",
                default=[],
                sep=",",
            ),
            est_un_document_a_trous=get_bool(
                "COMPILATION_DEFAUT_EST_UN_DOCUMENT_A_TROUS", False
            ),
            copier_pdf_dans_dossier_cible=get_bool(
                "COMPILATION_DEFAUT_COPIER_PDF_DANS_DOSSIER_CIBLE", True
            ),
            upload=get_bool("COMPILATION_DEFAUT_UPLOAD", True),
            dossier_ftp=get_str("COMPILATION_DEFAUT_DOSSIER_FTP", "/"),
            # Paramètres de compilation LaTeX
            nombre_compilations_latex=get_int(
                "COMPILATION_LATEX_NOMBRE_COMPILATIONS", 2
            ),
            # Compilation rapide et OS
            nom_fichier_parametres_compilation=get_str(
                "COMPILATION_OS_NOM_FICHIER_PARAMETRES_COMPILATION",
                "@parametres.pyUPSTIlatex.yaml",
            ),
            extension_fichier_metadonnees=get_str(
                "COMPILATION_OS_EXTENSION_FICHIER_METADONNEES", ".meta.json"
            ),
            format_nom_fichier=get_str(
                "COMPILATION_OS_FORMAT_NOM_FICHIER",
                "{thematique.code}-{classe.niveau}-{titre}",
            ),
            dossier_cible_par_rapport_au_fichier_tex=get_str(
                "COMPILATION_OS_DOSSIER_CIBLE_PAR_RAPPORT_AU_FICHIER_TEX", ".."
            ),
            copier_fichier_version=get_bool(
                "COMPILATION_OS_COPIER_FICHIER_VERSION", True
            ),
            format_nom_fichier_version=get_str(
                "COMPILATION_OS_FORMAT_NOM_FICHIER_VERSION", "@_v[numero_version].ver"
            ),
            dossier_sources_latex=get_str(
                "COMPILATION_OS_DOSSIER_SOURCES_LATEX", "Src"
            ),
            dossier_tmp_pour_zip=get_str(
                "COMPILATION_OS_DOSSIER_TMP_POUR_ZIP", "tempZip"
            ),
            suffixe_nom_fichier_prof=get_str(
                "COMPILATION_OS_SUFFIXE_NOM_FICHIER_PROF", "-prof"
            ),
            suffixe_nom_fichier_a_trous=get_str(
                "COMPILATION_OS_SUFFIXE_NOM_FICHIER_A_TROUS", "-eleve"
            ),
            suffixe_nom_diaporama=get_str(
                "COMPILATION_OS_SUFFIXE_NOM_DIAPORAMA", "-diaporama"
            ),
            suffixe_nom_sources=get_str(
                "COMPILATION_OS_SUFFIXE_NOM_SOURCES", "-sources"
            ),
        )


@dataclass(frozen=True)
class TraitementParLotConfig:
    """Valeurs par défaut pour les traitements par lot, provenant du .env"""

    dossiers_a_traiter: list[str]
    fichiers_a_exclure: list[str]

    @classmethod
    def from_env(cls) -> "TraitementParLotConfig":
        return cls(
            dossiers_a_traiter=get_list(
                "TRAITEMENT_PAR_LOT_DOSSIERS_A_TRAITER", default=[], sep=";"
            ),
            fichiers_a_exclure=get_list(
                "TRAITEMENT_PAR_LOT_FICHIERS_A_EXCLURE", default=[], sep=";"
            ),
        )


@dataclass(frozen=True)
class UploadConfig:
    """Valeurs par défaut pour la gestion de l'upload, provenant du .env"""

    ftp_user: str
    ftp_password: str
    ftp_host: str
    ftp_port: int
    webhook_url: str

    @classmethod
    def from_env(cls) -> "UploadConfig":
        return cls(
            ftp_user=get_str("UPLOAD_FTP_USER", "ftp_user"),
            ftp_password=get_str("UPLOAD_FTP_PASSWORD", "ftp_pwd"),
            ftp_host=get_str("UPLOAD_FTP_HOST", "ftp_host"),
            ftp_port=get_int("UPLOAD_FTP_PORT", 21),
            webhook_url=get_str("UPLOAD_WEBHOOK_URL", ""),
        )


@dataclass(frozen=True)
class PolyTDConfig:
    nombre_de_pages_par_feuille: int
    recto_verso: bool
    dossier_pour_poly_td: str
    nom_fichier_xml_poly: str
    suffixe_poly_td: str
    template_page_de_garde: Path

    @classmethod
    def from_env(cls) -> "PolyTDConfig":
        return cls(
            nombre_de_pages_par_feuille=get_int(
                "POLY_TD_NOMBRE_DE_PAGES_PAR_FEUILLE", 2
            )
            or 2,
            recto_verso=get_bool("POLY_TD_RECTO_VERSO", True),
            dossier_pour_poly_td=get_str("POLY_TD_DOSSIER_POUR_POLY_TD", "_poly")
            or "_poly",
            nom_fichier_xml_poly=get_str("POLY_TD_NOM_FICHIER_XML_POLY", "poly.xml")
            or "poly.xml",
            suffixe_poly_td=get_str("POLY_TD_SUFFIXE_POLY_TD", "-polyTD") or "-polyTD",
            template_page_de_garde=get_path(
                "POLY_TD_TEMPLATE_PAGE_DE_GARDE",
                "templates/page_de_garde_poly_TD.template.tex",
            ),
        )


@dataclass(frozen=True)
class AppConfig:
    meta: MetaConfig
    compilation: CompilationConfig
    traitement_par_lot: TraitementParLotConfig
    upload: UploadConfig
    poly_td: PolyTDConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            meta=MetaConfig.from_env(),
            compilation=CompilationConfig.from_env(),
            traitement_par_lot=TraitementParLotConfig.from_env(),
            upload=UploadConfig.from_env(),
            poly_td=PolyTDConfig.from_env(),
        )


def load_config() -> AppConfig:
    """Convenience function to build an AppConfig from environment variables."""
    return AppConfig.from_env()
