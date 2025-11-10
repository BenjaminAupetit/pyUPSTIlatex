import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .exceptions import DocumentParseError
from .filesystem import check_path_readable, check_path_writable
from .parsers import parse_metadonnees_tex, parse_metadonnees_yaml
from .storage import FileSystemStorage, StorageProtocol
from .utils import check_type_from_str, read_json_config


@dataclass
class UPSTILatexDocument:
    source: str
    storage: StorageProtocol = field(default_factory=FileSystemStorage)
    strict: bool = False
    require_writable: bool = False
    _raw: Optional[str] = field(default=None, init=False)
    _metadata: Optional[Dict] = field(default=None, init=False)
    _commands: Optional[Dict] = field(default=None, init=False)
    _zones: Optional[Dict] = field(default=None, init=False)
    _version: Optional[str] = field(default=None, init=False)
    _file_exists: Optional[bool] = field(default=None, init=False)
    _file_readable: Optional[bool] = field(default=None, init=False)
    _file_readable_reason: Optional[str] = field(default=None, init=False)
    _file_readable_flag: Optional[str] = field(default=None, init=False)
    _file_writable: Optional[bool] = field(default=None, init=False)
    _file_writable_reason: Optional[str] = field(default=None, init=False)
    _read_encoding: Optional[str] = field(default=None, init=False)

    def __post_init__(self):
        """Initialise les états du fichier selon le type de stockage."""
        try:
            # Cas 1 : stockage local — on peut faire des tests système explicites
            if isinstance(self.storage, FileSystemStorage):
                p = Path(self.source)
                self._file_exists = p.is_file()

                # Refuse explicitement tout fichier qui n'est pas un .tex ou un .ltx
                if p.suffix.lower() not in [".tex", ".ltx"]:
                    self._file_readable = False
                    self._file_readable_reason = "extension non-tex/ltx"
                    self._file_readable_flag = "error"
                    # Écriture : si le fichier existe on indique l'état, sinon on signale inexistant
                    if self._file_exists:
                        ok_w, reason_w, _ = check_path_writable(self.source)
                        self._file_writable = bool(ok_w)
                        self._file_writable_reason = reason_w
                    else:
                        self._file_writable = False
                        self._file_writable_reason = "fichier inexistant"
                else:
                    # Petit test heuristique pour repérer les binaires (NUL ou trop d'octets non imprimables)
                    try:
                        with p.open("rb") as f:
                            sample = f.read(4096)
                    except Exception as e:
                        # Impossible d'ouvrir en binaire -> on considèrera comme illisible
                        self._file_readable = False
                        self._file_readable_reason = f"lecture binaire impossible: {e}"
                        self._file_readable_flag = "error"
                        self._file_writable = None
                        self._file_writable_reason = None
                    else:
                        if not sample:
                            # Fichier vide -> considérer lisible (UTF-8)
                            is_binary = False
                        elif b"\x00" in sample:
                            is_binary = True
                        else:
                            # Heuristique : ratio d'octets imprimables
                            printable = 0
                            for b in sample:
                                if b in (9, 10, 13) or 32 <= b <= 126:
                                    printable += 1
                            non_printable_ratio = 1 - (printable / len(sample))
                            is_binary = non_printable_ratio > 0.30

                        if is_binary:
                            self._file_readable = False
                            self._file_readable_reason = "fichier binaire détecté"
                            self._file_readable_flag = "error"
                            # Écriture : on laisse l'état vérifié si possible
                            if self._file_exists:
                                ok_w, reason_w, _ = check_path_writable(self.source)
                                self._file_writable = bool(ok_w)
                                self._file_writable_reason = reason_w
                            else:
                                self._file_writable = False
                                self._file_writable_reason = "fichier inexistant"
                        else:
                            # Texte plausible -> faire la vérification d'encodage habituelle
                            ok_r, reason_r, flag_r = check_path_readable(self.source)
                            self._file_readable = bool(ok_r)
                            self._file_readable_reason = reason_r
                            self._file_readable_flag = flag_r
                            if flag_r == "warning":
                                # mémoriser l'encodage fallback pour read()
                                self._read_encoding = "latin-1"
                            # Écriture
                            self._file_writable, self._file_writable_reason, _ = (
                                check_path_writable(self.source)
                                if self._file_exists
                                else (False, "fichier inexistant", "error")
                            )

            # Cas 2 : stockage distant — on ne peut que tester par lecture réelle
            else:
                try:
                    _ = self.storage.read_text(self.source)
                    self._file_exists = True
                    self._file_readable = True
                    self._file_readable_reason = None
                    self._file_readable_flag = None
                except UnicodeDecodeError as e:
                    self._file_exists = True
                    self._file_readable = False
                    self._file_readable_reason = f"encodage illisible: {e}"
                    self._file_readable_flag = "error"
                except Exception as e:
                    self._file_exists = False
                    self._file_readable = False
                    self._file_readable_reason = f"lecture impossible: {e}"
                    self._file_readable_flag = "error"

                # Écriture non testable pour les storages distants
                self._file_writable = None
                self._file_writable_reason = None

            # Pré-détection de la version si lisible
            if self._file_readable:
                try:
                    v, _msg, _flag = self.get_version()
                    # _version est déjà mis à jour par get_version()
                except Exception:
                    pass

            # Mode strict : on lève des erreurs précises si accès impossible
            if self.strict:
                if not self._file_exists:
                    raise DocumentParseError(
                        f"Fichier introuvable ou non fichier: {self.source}"
                    )
                if not self._file_readable:
                    raise DocumentParseError(
                        f"Fichier illisible: {self.source} — {self._file_readable_reason or 'raison inconnue'}"
                    )
                if self.require_writable:
                    if self._file_writable is True:
                        pass
                    elif self._file_writable is False:
                        raise DocumentParseError(
                            f"Fichier non ouvrable en écriture: {self.source} — {self._file_writable_reason or 'raison inconnue'}"
                        )
                    else:
                        raise DocumentParseError(
                            f"Capacité d'écriture non vérifiable pour ce stockage: {self.source}"
                        )
        except Exception:
            # Ne bloque jamais l’instanciation en cas d’erreur inattendue
            pass

    # Propriétés d'accès simples
    @property
    def exists(self) -> bool:
        return bool(self._file_exists)

    @property
    def is_readable(self) -> bool:
        return bool(self._file_readable)

    @property
    def is_writable(self) -> bool:
        return bool(self._file_writable)

    @property
    def readable_reason(self) -> Optional[str]:
        return self._file_readable_reason

    @property
    def readable_flag(self) -> Optional[str]:
        return self._file_readable_flag

    @property
    def writable_reason(self) -> Optional[str]:
        return self._file_writable_reason

    @property
    def version(self):
        if self._version is not None:
            return self._version
        return self.get_version()[0]

    @property
    def metadata(self) -> Dict:
        if self._metadata is not None:
            return self._metadata
        return self.get_metadata()[0]

    def get_yaml_metadata(self) -> tuple[Optional[Dict], List[List[str]]]:
        """Extrait les métadonnées depuis le front matter YAML.

        Retourne (metadata, [message, flag]).
        """
        try:
            data, errors = parse_metadonnees_yaml(self.read()) or {}
            return data, errors
        except Exception as e:
            return None, [[f"Erreur de lecture des métadonnées YAML: {e}", "error"]]

    def get_tex_metadata(self) -> tuple[Optional[Dict], List[List[str]]]:
        """Extrait les métadonnées depuis les commandes LaTeX (v1).

        Retourne (metadata, [message, flag]).
        """
        try:
            data, parsing_errors = parse_metadonnees_tex(self.read()) or {}
            version_warning = [
                [
                    "Ce document utilise une ancienne version de UPSTI_Document (v1). Si vous souhaitez mettre à jour UPSTI_Document, exécutez : pyupstilatex upgrade",
                    "warning",
                ]
            ]
            return data, version_warning + parsing_errors
        except Exception as e:
            return None, [[f"Erreur de lecture des métadonnées LaTeX: {e}", "error"]]

    def get_metadata(self) -> tuple[Optional[Dict], List[List[str]]]:
        """Retourne (metadata, message, flag) en fonction de la version du document."""
        # Réutiliser le cache si les métadonnées ont déjà été extraites
        if self._metadata is not None:
            return self._metadata, []

        # On reprend la version détectée, et suivant les cas, on exécute le parser qui va bien
        version = self._version or self.version
        if version == "EPB_Document":
            return (
                None,
                [
                    [
                        "Les fichiers EPB_Document ne sont pas pris en charge par pyUPSTIlatex.",
                        "error",
                    ],
                ],
            )

        # Associer chaque version à sa fonction de récupération
        sources = {
            "UPSTI_Document_v1": self.get_tex_metadata,
            "UPSTI_Document_v2": self.get_yaml_metadata,
        }

        if version in sources:
            metadata, errors = sources[version]()

            formatted, formatted_errors = self._format_metadata(
                metadata, source=version
            )
            if formatted is not None:
                self._metadata = formatted
            return formatted, errors + formatted_errors

        # Version non reconnue
        return (
            None,
            [["Type de document non pris en charge par pyUPSTIlatex", "error"]],
        )

    def get_version(self) -> tuple[Optional[str], List[List[str]]]:
        """Détecte la version du document UPSTI/EPB et retourne (version, message, flag).

        Renvoie un tuple (version, message, flag) où `flag` est l'un de:
        - "plain"  : succès standard
        - "warning": version non reconnue
        - "error"  : erreur de lecture
        """
        if self._version is not None:
            # Version déjà détectée (cache)
            return self._version, []

        try:
            content = self.read()
        except Exception as e:
            return None, [[f"Impossible de lire le fichier: {e}", "error"]]

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            # UPSTI_Document v2 (ligne commençant par % mais pas %%)
            if stripped.startswith("%") and not stripped.startswith("%%"):
                if "%### BEGIN metadonnees_yaml ###" in stripped:
                    self._version = "UPSTI_Document_v2"
                    return self._version, []

            # Ignorer lignes commentées pour EPB/v1
            if stripped.startswith("%"):
                continue

            # UPSTI_Document v1
            if "\\newcommand{\\UPSTIidTypeDocument}" in stripped:
                self._version = "UPSTI_Document_v1"
                return self._version, []

            # EPB_Document
            if "\\newcommand{\\EPBIdTypeDocument}" in stripped:
                self._version = "EPB_Document"
                return self._version, []

        self._version = None
        return None, [["Version non reconnue", "warning"]]

    def is_file_ok(self, mode: str = "read") -> tuple[bool, List[List[str]]]:
        """Vérifie rapidement l'état du fichier selon le mode demandé.

        Retourne (ok, raison, flag) où:
        - ok: True si tout est OK pour le mode demandé
        - raison: None si ok, sinon message court expliquant le problème
        - flag: None si ok, sinon 'warning' ou 'error'

        Modes supportés:
        - 'read'  : existence + lecture (UTF-8) ; si fallback latin-1 => warning
        - 'write' : existence + capacité d'écriture (test non destructif pour FileSystemStorage)
        - 'exists': existence seulement
        """
        mode = (mode or "read").lower()
        if mode not in ("read", "write", "exists"):
            raise ValueError("mode must be one of 'read', 'write' or 'exists'")

        # existence
        if not self._file_exists:
            return False, [["Fichier introuvable", "error"]]

        if mode == "exists":
            return True, []

        if mode == "read":
            # readable_flag may be 'warning' when latin-1 fallback used
            if self._file_readable:
                if self._file_readable_flag == "warning":
                    return (
                        False,
                        [
                            [
                                self._file_readable_reason
                                or "fichier lu avec fallback d'encodage",
                                "warning",
                            ]
                        ],
                    )
                return True, []
            return False, [
                [self._file_readable_reason or "impossible de lire", "error"]
            ]

        # mode == 'write'
        if self._file_writable is True:
            return True, []
        if self._file_writable is False:
            return (
                False,
                [
                    [
                        self._file_writable_reason or "impossible d'ouvrir en écriture",
                        "error",
                    ]
                ],
            )
        # None => inconnu pour les storages non locaux
        return (
            False,
            [
                [
                    self._file_writable_reason
                    or "Capacité d'écriture non vérifiable pour ce stockage",
                    "error",
                ]
            ],
        )

    def _format_metadata(
        self, data: Dict, *, source: str
    ) -> Tuple[Dict, List[List[str]]]:
        """Nettoie/normalise les métadonnées parsées avant mise en cache et retour.

        Retourne (dict Python, liste de messages d'erreurs (msg, flag)).
        """
        meta_ok: Dict[str, Dict] = {}
        errors: List[Tuple[str, str]] = []
        cfg = read_json_config()
        cfg_meta = cfg.get("metadonnee") or {}

        # On vérifie s'il y a des champs définis par mégarde
        extra_keys = set(data.keys()) - set(cfg_meta.keys())
        for key in extra_keys:
            errors.append(
                [
                    f"Clé de métadonnée inconnue dans le fichier tex : {key}",
                    'warning',
                ]
            )

        # Vérification des types de données forcées
        for key, value in data.items():
            force_type = (
                cfg_meta.get(key, {}).get("parametres", {}).get("force_type", {})
            )
            if force_type:
                type_to_check = force_type.get("type")

                if check_type_from_str(value, type_to_check):
                    if type_to_check == "dict":
                        if not set(value.keys()).issubset(
                            set(force_type.get("dict_keys", []))
                        ):
                            errors.append(
                                [
                                    f"Il y a des clés non autorisées pour '{key}' : {set(value.keys()) - set(force_type.get('dict_keys', []))}.",
                                    'warning',
                                ]
                            )
                    if type_to_check == "list" and force_type.get("in", ""):
                        valid_values_dict = cfg.get(force_type.get("in", ""), {})
                        if not set(value).issubset(set(valid_values_dict)):
                            errors.append(
                                [
                                    f"Il y a des valeurs non autorisées pour '{key}' : {set(value) - set(valid_values_dict)}.",
                                    'warning',
                                ]
                            )

                    continue

                errors.append(
                    [
                        f"'{key}' devrait être de type '{force_type.get('type')}'.",
                        'warning',
                    ]
                )

        # Préparation des champs déclarés et par défaut
        for key, m in cfg_meta.items():
            params = m.get("parametres", {})
            if key not in data and not params.get("default"):
                continue

            meta_ok[key] = {
                "label": m.get("label", "Erreur"),
                "description": m.get("description", "Erreur"),
                "valeur": "",
                "affichage": "",
                "initiales": "",
                "raw_value": (data or {}).get(key, ""),
                "parametres": params,
            }
            if params.get("default") and key not in data:
                meta_ok[key]["type_meta"] = "default"

        # Valeurs par défaut globales
        epoch = int(time.time())
        prefixe_id = os.getenv("META_DEFAULT_ID_DOCUMENT_PREFIXE", "EB")
        separateur_id = os.getenv("META_DEFAULT_SEPARATEUR_ID_DOCUMENT", ":")

        valeurs_par_defaut = {
            "id_unique": f"{prefixe_id}{separateur_id}{epoch}",
            "variante": os.getenv("META_DEFAULT_VARIANTE", "upsti"),
            "matiere": os.getenv("META_DEFAULT_MATIERE", "S2I"),
            "classe": os.getenv("META_DEFAULT_CLASSE", "PT"),
            "type_document": os.getenv("META_DEFAULT_TYPE_DOCUMENT", "cours"),
            "titre": os.getenv("META_DEFAULT_TITRE", "Titre par défaut"),
            "version": os.getenv("META_DEFAULT_VERSION", "0.1"),
            "auteur": os.getenv("META_DEFAULT_AUTEUR", "Emmanuel BIGEARD"),
        }

        # On nettoie les valeurs existantes
        for key, m in meta_ok.items():
            params = m.get("parametres", {})

            # Cas des boolééens
            if params.get("clean") == "boolean":
                raw = m.get("raw_value", "")
                if raw == "":
                    continue  # on laisse vide
                val = str(raw).strip().lower()
                m["raw_value"] = (
                    raw is True or raw == 1 or val in {"true", "1", "yes", "on"}
                )

            # Cas des valeurs custom
            custom_decl_str = params.get("custom_declaration")
            if custom_decl_str:
                raw = m.get("raw_value", "")
                if isinstance(raw, dict):
                    try:
                        decl_dict = yaml.safe_load(custom_decl_str)
                        if not isinstance(decl_dict, dict):
                            errors.append(
                                [
                                    f"custom_declaration invalide pour {key} dans pyUPSTIlatex.json.",
                                    'error',
                                ]
                            )
                            m["raw_value"] = ""
                            m["type_meta"] = "default"

                        # Comparer les clés
                        if not (set(raw.keys()) == set(decl_dict.keys())):
                            errors.append(
                                [
                                    f"Dictionnaire custom declaration invalide pour {key}. "
                                    "On va utiliser la valeur par défaut.",
                                    'warning',
                                ]
                            )
                            m["raw_value"] = ""
                            m["type_meta"] = "default"

                    except yaml.YAMLError:
                        errors.append(
                            [
                                f"custom_declaration invalide pour {key} dans pyUPSTIlatex.json.",
                                'error',
                            ]
                        )
                        m["type_meta"] = "default"

            # Cas des valeurs avec des relations de clé
            if params.get("join_key", ""):
                raw = m.get("raw_value", "")
                if (
                    not isinstance(raw, dict)
                    and raw != ""
                    and raw not in (cfg.get(key) or {})
                    and not params.get("custom_can_be_not_related", "")
                ):
                    errors.append(
                        [
                            f"Valeur inconnue pour {key}: '{raw}'. "
                            "On va utiliser la valeur par défaut.",
                            'warning',
                        ]
                    )
                    m["raw_value"] = ""
                    m["type_meta"] = "default"

        # Application des valeurs par défaut (pour les champs required mais vides)
        for key, md in meta_ok.items():
            if "type_meta" not in md:
                continue

            default_mode = md.get("parametres", {}).get("default", "")
            if default_mode == ".env":
                md["raw_value"] = valeurs_par_defaut.get(key, "")

            elif default_mode == "calc":
                md["raw_value"] = valeurs_par_defaut.get(key, "")

            elif default_mode == "False":
                md["raw_value"] = bool(md.get("raw_value"))

            elif default_mode == "batch_pedagogie":
                # Gestion groupée
                if not data.get("classe") and not meta_ok["classe"]["raw_value"]:
                    meta_ok["classe"]["raw_value"] = valeurs_par_defaut["classe"]

                if not data.get("matiere") and not meta_ok["matiere"]["raw_value"]:
                    meta_ok["matiere"]["raw_value"] = valeurs_par_defaut["matiere"]

                if not data.get("filiere") and not meta_ok["filiere"]["raw_value"]:
                    cfg_classe = cfg.get("classe") or {}
                    classe_used_for_filiere = meta_ok["classe"]["raw_value"]
                    classe_predefinie = cfg_classe.get(classe_used_for_filiere, {})
                    if not classe_predefinie:
                        classe_used_for_filiere = valeurs_par_defaut["classe"]
                    meta_ok["filiere"]["raw_value"] = cfg_classe.get(
                        classe_used_for_filiere, {}
                    ).get("filiere", "")
                    meta_ok["filiere"]["type_meta"] = (
                        "deducted"
                        if meta_ok["classe"].get("type_meta", "") == ""
                        else "default"
                    )

                if not data.get("programme") and not meta_ok["programme"]["raw_value"]:
                    cfg_filiere = cfg.get("filiere") or {}
                    meta_ok["programme"]["raw_value"] = cfg_filiere.get(
                        meta_ok["filiere"]["raw_value"], {}
                    ).get("dernier_programme", "")

                    meta_ok["programme"]["type_meta"] = (
                        "deducted"
                        if meta_ok["filiere"].get("type_meta", "") in ["", "deducted"]
                        else "default"
                    )

        # Finalisation des métadonnées
        for key, fm in meta_ok.items():
            raw_value = fm.get("raw_value")

            if fm.get("parametres", {}).get("join_key", False):

                # Si c'est une valeur custom
                if isinstance(raw_value, dict):
                    fm["valeur"] = raw_value.get("nom")
                    fm["affichage"] = raw_value.get("affichage", fm["valeur"])
                    fm["initiales"] = raw_value.get("initiales", fm["valeur"])
                    continue

                obj = (cfg.get(key) or {}).get(raw_value, {})
                fm["valeur"] = obj.get("nom", "")
                fm["affichage"] = obj.get("affichage", "")
                fm["initiales"] = obj.get("initiales", "")

            # Valeurs de repli
            fm["valeur"] = fm.get("valeur") or raw_value
            fm["affichage"] = fm.get("affichage") or fm["valeur"]
            fm["initiales"] = fm.get("initiales") or fm["affichage"]

        return meta_ok, errors

    # ================================================================================
    # TOCHECK Tout ce qui suit est généré par IA, à vérifier et comprendre
    # ================================================================================

    def read(self) -> str:
        if self._raw is None:
            try:
                # Si on a détecté un encoding fallback pour le stockage local, l'utiliser
                if isinstance(self.storage, FileSystemStorage) and self._read_encoding:
                    p = Path(self.source)
                    self._raw = p.read_text(
                        encoding=self._read_encoding, errors="strict"
                    )
                else:
                    self._raw = self.storage.read_text(self.source)
            except Exception as e:
                raise DocumentParseError(f"Unable to read source {self.source}: {e}")
        return self._raw

    # def refresh(self):
    #     """Invalidate les caches internes et relire la source."""
    #     self._raw = None
    #     self._metadata = None
    #     self._commands = None
    #     self._zones = None
    #     self._version = None
    #     return self.read()

    # def get_commands(
    #     self, names: Optional[List[str]] = None
    # ) -> Dict[str, List[Optional[str]]]:
    #     if self._commands is None:
    #         self._commands = parse_tex_commands(self.read(), names=names)
    #     return self._commands

    # def list_zones(self) -> List[str]:
    #     if self._zones is None:
    #         self._zones = parse_named_zones(self.read())
    #     return list(self._zones.keys())

    # def get_zone(self, name: str):
    #     if self._zones is None:
    #         self._zones = parse_named_zones(self.read())
    #     vals = self._zones.get(name)
    #     if not vals:
    #         return None
    #     return vals if len(vals) > 1 else vals[0]

    # def to_dict(self):
    #     return {
    #         "source": self.source,
    #         "metadata": self.metadata,
    #         "commands": self.get_commands(),
    #         "zones": self._zones or parse_named_zones(self.read()),
    #     }

    @classmethod
    def from_path(
        cls,
        path: str,
        storage: Optional[StorageProtocol] = None,
        *,
        strict: bool = False,
        require_writable: bool = False,
    ):
        return cls(
            source=path,
            storage=(storage or FileSystemStorage()),
            strict=strict,
            require_writable=require_writable,
        )

    @classmethod
    def from_string(cls, content: str, *, strict: bool = False):
        inst = cls(source="<string>", storage=FileSystemStorage(), strict=strict)
        inst._raw = content
        return inst
