from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .exceptions import DocumentParseError
from .file_helpers import check_path_readable, check_path_writable


@dataclass
class DocumentFile:
    """Gestion des aspects système de fichiers d'un document.

    Gère l'existence, la lisibilité, l'écriture, la détection d'encodage
    et de fichiers binaires, avec lecture et fallback d'encodage.

    Paramètres
    ----------
    source : str
        Chemin du fichier source.
    strict : bool, optional
        Si True, lève des exceptions en cas de problème. Défaut : False.
    require_writable : bool, optional
        Si True (et strict=True), exige que le fichier soit modifiable. Défaut : False.
    """

    source: str
    strict: bool = False
    require_writable: bool = False

    # États du fichier
    _file_exists: Optional[bool] = field(default=None, init=False)
    _file_readable: Optional[bool] = field(default=None, init=False)
    _file_readable_reason: Optional[str] = field(default=None, init=False)
    _file_readable_flag: Optional[str] = field(default=None, init=False)
    _file_writable: Optional[bool] = field(default=None, init=False)
    _file_writable_reason: Optional[str] = field(default=None, init=False)
    _read_encoding: Optional[str] = field(default=None, init=False)
    _raw: Optional[str] = field(default=None, init=False)

    def __post_init__(self):
        """Initialise les états du fichier.

        Vérifie l'existence, la lisibilité et l'écritabilité du fichier.
        Détecte les fichiers binaires et les problèmes d'encodage.
        En mode strict, lève des exceptions si les conditions ne sont pas remplies.

        Raises
        ------
        DocumentParseError
            Si le fichier est introuvable, illisible ou non ouvrable en écriture
            en mode strict.
        """
        try:
            p = Path(self.source)
            self._file_exists = p.is_file()

            # Refuse explicitement tout fichier qui n'est pas un .tex ou un .ltx
            if p.suffix.lower() not in [".tex", ".ltx"]:
                self._file_readable = False
                self._file_readable_reason = "Le fichier n'est pas un fichier tex"
                self._file_readable_flag = "fatal_error"
                # Écriture : si le fichier existe on indique l'état,
                # sinon on signale inexistant
                if self._file_exists:
                    ok_w, reason_w, _ = check_path_writable(self.source)
                    self._file_writable = bool(ok_w)
                    self._file_writable_reason = reason_w
                else:
                    self._file_writable = False
                    self._file_writable_reason = "Fichier inexistant"
            else:
                # Petit test heuristique pour repérer les binaires
                try:
                    with p.open("rb") as f:
                        sample = f.read(4096)
                except Exception as e:
                    # Impossible d'ouvrir en binaire -> on considèrera illisible
                    self._file_readable = False
                    self._file_readable_reason = f"Lecture binaire impossible: {e}"
                    self._file_readable_flag = "fatal_error"
                    self._file_writable = None
                    self._file_writable_reason = None
                else:
                    if not sample:
                        # Fichier vide -> considérer lisible (UTF-8)
                        is_binary = False
                    else:
                        # Seuil simple: présence d'un octet nul => binaire
                        is_binary = b"\x00" in sample

                    if is_binary:
                        self._file_readable = False
                        self._file_readable_reason = "Fichier binaire détecté"
                        self._file_readable_flag = "fatal_error"
                        # Écriture : on laisse l'état vérifié si possible
                        if self._file_exists:
                            ok_w, reason_w, _ = check_path_writable(self.source)
                            self._file_writable = bool(ok_w)
                            self._file_writable_reason = reason_w
                        else:
                            self._file_writable = False
                            self._file_writable_reason = "Fichier inexistant"
                    else:
                        # Texte plausible -> faire la vérification d'encodage
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
                            else (False, "Fichier inexistant", "fatal_error")
                        )

            # Mode strict : on lève des erreurs précises si accès impossible
            if self.strict:
                if not self._file_exists:
                    raise DocumentParseError(
                        f"Fichier introuvable ou non fichier: {self.source}"
                    )
                if not self._file_readable:
                    raise DocumentParseError(
                        f"Fichier illisible: {self.source} — "
                        f"{self._file_readable_reason or 'raison inconnue'}"
                    )
                if self.require_writable:
                    if self._file_writable is True:
                        pass
                    elif self._file_writable is False:
                        raise DocumentParseError(
                            f"Fichier non ouvrable en écriture: {self.source} "
                            f"— {self._file_writable_reason or 'raison inconnue'}"
                        )
                    else:
                        raise DocumentParseError(
                            f"Capacité d'écriture non vérifiable pour ce stockage: "
                            f"{self.source}"
                        )
        except DocumentParseError:
            raise
        except Exception:
            # Ne bloque jamais l'instanciation en cas d'erreur inattendue
            pass

    # Propriétés d'accès simples
    @property
    def exists(self) -> bool:
        """Indique si le fichier existe.

        Retourne
        --------
        bool
            True si le fichier existe, False sinon.
        """
        return bool(self._file_exists)

    @property
    def is_readable(self) -> bool:
        """Indique si le fichier est lisible.

        Retourne
        --------
        bool
            True si le fichier est lisible, False sinon.
        """
        return bool(self._file_readable)

    @property
    def is_writable(self) -> bool:
        """Indique si le fichier est ouvert en écriture.

        Retourne
        --------
        bool
            True si le fichier est modifiable, False sinon.
        """
        return bool(self._file_writable)

    @property
    def readable_reason(self) -> Optional[str]:
        """Raison pour laquelle le fichier n'est pas lisible.

        Retourne
        --------
        str, optional
            Message d'erreur si le fichier n'est pas lisible, None sinon.
        """
        return self._file_readable_reason

    @property
    def readable_flag(self) -> Optional[str]:
        """Flag associé à l'état de lisibilité.

        Retourne
        --------
        str, optional
            'warning', 'error' ou 'fatal_error', ou None si lisible.
        """
        return self._file_readable_flag

    @property
    def writable_reason(self) -> Optional[str]:
        """Raison pour laquelle le fichier n'est pas modifiable.

        Retourne
        --------
        str, optional
            Message d'erreur si le fichier n'est pas modifiable, None sinon.
        """
        return self._file_writable_reason

    @property
    def read_encoding(self) -> Optional[str]:
        """Encodage détecté pour la lecture.

        Retourne
        --------
        str, optional
            Encodage à utiliser (ex: 'latin-1'), ou None si UTF-8.
        """
        return self._read_encoding

    @property
    def path(self) -> Path:
        """Retourne le Path du fichier source.

        Retourne
        --------
        Path
            Objet Path du fichier.
        """
        return Path(self.source)

    @property
    def parent(self) -> Path:
        """Retourne le dossier parent du fichier source.

        Retourne
        --------
        Path
            Dossier parent du fichier.
        """
        return Path(self.source).parent

    @property
    def stem(self) -> str:
        """Retourne le nom du fichier sans extension.

        Retourne
        --------
        str
            Nom du fichier sans extension.
        """
        return Path(self.source).stem

    @property
    def suffix(self) -> str:
        """Retourne l'extension du fichier.

        Retourne
        --------
        str
            Extension du fichier avec le point (ex: '.tex').
        """
        return Path(self.source).suffix

    def check_file(self, mode: str = "read") -> tuple[bool, List[List[str]]]:
        """Vérifie l'état du fichier selon le mode demandé.

        Paramètres
        ----------
        mode : str, optional
            Mode de vérification : 'read', 'write' ou 'exists'. Défaut : 'read'.

        Retourne
        --------
        tuple[bool, List[List[str]]]
            Tuple contenant :
            - ok : True si tout est OK pour le mode demandé
            - messages : Liste de messages [message, flag]

        Notes
        -----
        Modes supportés :
        - 'read'  : existence + readable (UTF-8) ; si fallback latin-1 => warning
        - 'write' : existence + writable (test non destructif)
        - 'exists': existence seulement
        """
        mode = (mode or "read").lower()
        if mode not in ("read", "write", "exists"):
            return False, [
                ["Mode doit être 'read', 'write' ou 'exists'.", "fatal_error"]
            ]

        # Existence
        if not self._file_exists:
            return False, [["Fichier introuvable", "fatal_error"]]

        if mode == "exists":
            return True, []

        # Mode lecture
        if mode == "read":
            # readable_flag may be 'warning' when latin-1 fallback used
            if self._file_readable:
                if self._file_readable_flag == "warning":
                    return (
                        True,
                        [
                            [
                                self._file_readable_reason
                                or "Fichier lu avec fallback d'encodage",
                                "warning",
                            ]
                        ],
                    )
                return True, []
            return False, [
                [
                    self._file_readable_reason or "Impossible de lire",
                    self._file_readable_flag or "error",
                ]
            ]

        # Mode écriture
        if self._file_writable is True:
            return True, []
        if self._file_writable is False:
            return (
                False,
                [
                    [
                        self._file_writable_reason or "Impossible d'ouvrir en écriture",
                        "fatal_error",
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
                    "warning",
                ]
            ],
        )

    def read(self) -> str:
        """Lit et retourne le contenu du fichier.

        Utilise l'encodage détecté (UTF-8 ou fallback latin-1).
        Le contenu est mis en cache après la première lecture.

        Retourne
        --------
        str
            Contenu du fichier.

        Raises
        ------
        DocumentParseError
            Si la lecture échoue.
        """
        if self._raw is None:
            try:
                p = Path(self.source)
                encoding = self._read_encoding or "utf-8"
                self._raw = p.read_text(encoding=encoding, errors="strict")
            except Exception as e:
                raise DocumentParseError(f"Unable to read source {self.source}: {e}")
        return self._raw

    def write(
        self, content: str, encoding: str = "utf-8"
    ) -> tuple[bool, List[List[str]]]:
        """Écrit le contenu dans le fichier.

        Paramètres
        ----------
        content : str
            Le contenu à écrire
        encoding : str, optional
            L'encodage à utiliser (défaut: "utf-8")

        Retourne
        --------
        tuple[bool, List[List[str]]]
            (succès, messages)
        """
        try:
            # Vérifier que le fichier est modifiable
            if not self.is_writable:
                return False, [
                    [
                        f"Impossible d'écrire dans le fichier : {self.writable_reason or 'raison inconnue'}",
                        "error",
                    ]
                ]

            # Écrire le fichier
            Path(self.source).write_text(content, encoding=encoding)

            # Invalider le cache de lecture
            self._raw = None

            return True, []

        except Exception as e:
            return False, [[f"Erreur lors de l'écriture du fichier : {e}", "error"]]
