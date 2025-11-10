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
- For booleans, accepted truthy values: 1, true, yes, y, on; falsy: 0, false, no, n, off.
- For paths, get_path returns a pathlib.Path (no existence check).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = [
    "get_str",
    "get_int",
    "get_bool",
    "get_path",
    # Dataclasses
    "OSConfig",
    "CompilationConfig",
    "PolyTDConfig",
    "LaTeXConfig",
    "ZipConfig",
    "FTPConfig",
    "DBConfig",
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


# =========================
# Section-based dataclasses
# =========================


@dataclass(frozen=True)
class OSConfig:
    nom_fichier_parametres: str
    chemin_json_annuaire: Path
    dossier_upsti_compilation: Path
    dossier_cible_par_rapport_au_fichier_tex: Path
    nom_dossier_sources_latex: str
    format_nom_fichier_version: str
    extension_fichier_version: str
    extension_diaporama: str
    chemin_fichier_parametres_traitement_par_lot: Path

    @classmethod
    def from_env(cls) -> "OSConfig":
        return cls(
            nom_fichier_parametres=get_str(
                "OS_NOM_FICHIER_PARAMETRES", "@parametres.upsti.ini"
            )
            or "@parametres.upsti.ini",
            chemin_json_annuaire=get_path(
                "OS_CHEMIN_JSON_ANNUAIRE",
                "upsti_annuaire_tex/annuaire_fichiers_tex.json",
            ),
            dossier_upsti_compilation=get_path(
                "OS_DOSSIER_UPSTI_COMPILATION", "upsti_compilation"
            ),
            dossier_cible_par_rapport_au_fichier_tex=get_path(
                "OS_DOSSIER_CIBLE_PAR_RAPPORT_AU_FICHIER_TEX", ".."
            ),
            nom_dossier_sources_latex=get_str("OS_NOM_DOSSIER_SOURCES_LATEX", "Src")
            or "Src",
            format_nom_fichier_version=get_str(
                "OS_FORMAT_NOM_FICHIER_VERSION", "@_v[XXXX]"
            )
            or "@_v[XXXX]",
            extension_fichier_version=get_str("OS_EXTENSION_FICHIER_VERSION", ".ver")
            or ".ver",
            extension_diaporama=get_str("OS_EXTENSION_DIAPORAMA", ".pptx") or ".pptx",
            chemin_fichier_parametres_traitement_par_lot=get_path(
                "OS_CHEMIN_FICHIER_PARAMETRES_TRAITEMENT_PAR_LOT",
                "upsti_outils/parametres_traitement_par_lot.ini",
            ),
        )


@dataclass(frozen=True)
class CompilationConfig:
    nombre_compilations_latex: int
    copier_fichier_version: bool
    mise_a_jour_annuaire_fichiers_tex: bool
    upload_fichier_preview: bool
    suffixe_nom_fichier_prof: str
    suffixe_nom_fichier_a_trous: str
    suffixe_nom_diaporama: str
    suffixe_nom_sources: str

    @classmethod
    def from_env(cls) -> "CompilationConfig":
        return cls(
            nombre_compilations_latex=get_int(
                "COMPILATION_NOMBRE_COMPILATIONS_LATEX", 2
            )
            or 2,
            copier_fichier_version=get_bool("COMPILATION_COPIER_FICHIER_VERSION", True),
            mise_a_jour_annuaire_fichiers_tex=get_bool(
                "COMPILATION_MISE_A_JOUR_ANNUAIRE_FICHIERS_TEX", True
            ),
            upload_fichier_preview=get_bool("COMPILATION_UPLOAD_FICHIER_PREVIEW", True),
            suffixe_nom_fichier_prof=get_str(
                "COMPILATION_SUFFIXE_NOM_FICHIER_PROF", "-Prof"
            )
            or "-Prof",
            suffixe_nom_fichier_a_trous=get_str(
                "COMPILATION_SUFFIXE_NOM_FICHIER_A_TROUS", "-Eleve"
            )
            or "-Eleve",
            suffixe_nom_diaporama=get_str(
                "COMPILATION_SUFFIXE_NOM_DIAPORAMA", "-Diaporama"
            )
            or "-Diaporama",
            suffixe_nom_sources=get_str("COMPILATION_SUFFIXE_NOM_SOURCES", "-Sources")
            or "-Sources",
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
class LaTeXConfig:
    prefixe_id_document: str
    separateur_id_document: str

    @classmethod
    def from_env(cls) -> "LaTeXConfig":
        return cls(
            prefixe_id_document=get_str("LATEX_PREFIXE_ID_DOCUMENT", "EB") or "EB",
            separateur_id_document=get_str("LATEX_SEPARATEUR_ID_DOCUMENT", ":") or ":",
        )


@dataclass(frozen=True)
class ZipConfig:
    dossier_tmp_pour_zip: Path

    @classmethod
    def from_env(cls) -> "ZipConfig":
        return cls(dossier_tmp_pour_zip=get_path("ZIP_DOSSIER_TMP_POUR_ZIP", "tempZip"))


@dataclass(frozen=True)
class FTPConfig:
    user: str
    password: str
    host: str
    port: int
    dossier_ftp_racine: str
    dossier_ftp_preview: str

    @classmethod
    def from_env(cls) -> "FTPConfig":
        return cls(
            user=get_str("FTP_USER", "") or "",
            password=get_str("FTP_PASSWORD", "") or "",
            host=get_str("FTP_HOST", "") or "",
            port=get_int("FTP_PORT", 21) or 21,
            dossier_ftp_racine=get_str("FTP_DOSSIER_FTP_RACINE", "doc_peda")
            or "doc_peda",
            dossier_ftp_preview=get_str("FTP_DOSSIER_FTP_PREVIEW", "_preview")
            or "_preview",
        )


@dataclass(frozen=True)
class DBConfig:
    name: str
    host: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DBConfig":
        return cls(
            name=get_str("DB_NAME", "") or "",
            host=get_str("DB_HOST", "localhost") or "localhost",
            user=get_str("DB_USER", "") or "",
            password=get_str("DB_PASSWORD", "") or "",
        )


@dataclass(frozen=True)
class AppConfig:
    os: OSConfig
    compilation: CompilationConfig
    poly_td: PolyTDConfig
    latex: LaTeXConfig
    zip: ZipConfig
    ftp: FTPConfig
    db: DBConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            os=OSConfig.from_env(),
            compilation=CompilationConfig.from_env(),
            poly_td=PolyTDConfig.from_env(),
            latex=LaTeXConfig.from_env(),
            zip=ZipConfig.from_env(),
            ftp=FTPConfig.from_env(),
            db=DBConfig.from_env(),
        )


def load_config() -> AppConfig:
    """Convenience function to build an AppConfig from environment variables."""
    return AppConfig.from_env()
