import logging
from typing import Callable, Dict, Optional, Tuple

DEFAULT_SEP1 = "════════════════════════════════════════════════════════════════"
DEFAULT_SEP2 = "───────────────────────────────────────────────────────"
DEFAULT_SEP3 = "----------------------------"
DEFAULT_ERR = "********************************"

Formatter = Callable[[str], Tuple[str, int]]


def _fmt_sep1(t: str):
    return (f"{DEFAULT_SEP1}\n{t}\n{DEFAULT_SEP1}", logging.INFO)


def _fmt_sep2(t: str):
    return (f"{DEFAULT_SEP2}\n{t}\n{DEFAULT_SEP2}", logging.INFO)


def _fmt_t3(t: str):
    return (f"{t}\n{DEFAULT_SEP3}", logging.INFO)


def _fmt_t4(t: str):
    return (t, logging.INFO)


def _fmt_info(t: str):
    return (f"  {t}", logging.INFO)


def _fmt_resultat(t: str):
    return (f"    └─> {t}", logging.INFO)


def _fmt_resultat_item(t: str):
    return (f"    │     - {t}", logging.INFO)


def _fmt_conclusion(t: str):
    return (f"│\n└─> {t}", logging.INFO)


def _fmt_warning(t: str):
    return (f"  WARNING => {t}", logging.WARNING)


def _fmt_error(t: str):
    return (f"\n{DEFAULT_ERR}\n  ERREUR => {t}\n{DEFAULT_ERR}", logging.ERROR)


def _fmt_empty(t: str):
    return ("", logging.INFO)


DEFAULT_FORMATTERS: Dict[str, Formatter] = {
    "titre1": _fmt_sep1,
    "titre2": _fmt_sep2,
    "titre3": _fmt_t3,
    "titre4": _fmt_t4,
    "info": _fmt_info,
    "action": _fmt_info,
    "resultat": _fmt_resultat,
    "resultat_item": _fmt_resultat_item,
    "conclusion": _fmt_conclusion,
    "warning": _fmt_warning,
    "error": _fmt_error,
    "saut": _fmt_empty,
    "separateur1": lambda t: (DEFAULT_SEP1, logging.INFO),
    "separateur2": lambda t: (DEFAULT_SEP2, logging.INFO),
    "separateur3": lambda t: (DEFAULT_SEP3, logging.INFO),
}


class MessageHandler:
    def __init__(
        self,
        log_file: Optional[str] = None,
        verbose: bool = True,
        logger_name: str = "pyUPSTIlatex",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        formatters: Optional[Dict[str, Formatter]] = None,
    ):
        self.verbose = bool(verbose)
        self._logger = logging.getLogger(logger_name)
        self._formatters = formatters or DEFAULT_FORMATTERS
        self._configure_logger(log_file, console_level, file_level)

    def _configure_logger(self, log_file, console_level, file_level):
        # avoid removing handlers if other parts of app use same logger:
        if not self._logger.handlers:
            self._logger.setLevel(logging.DEBUG)
            console = logging.StreamHandler()
            console.setLevel(console_level if self.verbose else logging.WARNING)
            console.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(console)
            if log_file:
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setLevel(file_level)
                fh.setFormatter(
                    logging.Formatter(
                        "%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
                    )
                )
                self._logger.addHandler(fh)

    def format_message(self, typ: str, texte: str) -> Tuple[str, int]:
        fmt = self._formatters.get(typ, lambda t: (t, logging.INFO))
        return fmt(texte or "")

    def emit(self, message: dict):
        if not message:
            return
        if "verbose" in message and not message["verbose"]:
            return
        typ = message.get("type", "info")
        if not self.verbose and typ in ("info", "resultat", "resultat_item", "action"):
            return
        texte = message.get("texte", "")
        out, level = self.format_message(typ, texte)
        # guard: avoid emitting empty lines when suppressed
        if out == "" and level == logging.INFO:
            self._logger.info("")
        else:
            self._logger.log(level, out)

    # minimal helpers: thin wrappers calling emit
    def msg(self, typ: str, texte: str, verbose: Optional[bool] = None):
        m = {"type": typ, "texte": texte}
        if verbose is not None:
            m["verbose"] = verbose
        self.emit(m)

    # convenience methods map to msg
    def titre1(self, texte, verbose=None):
        self.msg("titre1", texte, verbose)

    def titre2(self, texte, verbose=None):
        self.msg("titre2", texte, verbose)

    def titre3(self, texte, verbose=None):
        self.msg("titre3", texte, verbose)

    def titre4(self, texte, verbose=None):
        self.msg("titre4", texte, verbose)

    def info(self, texte, verbose=None):
        self.msg("info", texte, verbose)

    def action(self, texte, verbose=None):
        self.msg("action", texte, verbose)

    def resultat(self, texte, verbose=None):
        self.msg("resultat", texte, verbose)

    def resultat_item(self, texte, verbose=None):
        self.msg("resultat_item", texte, verbose)

    def conclusion(self, texte, verbose=None):
        self.msg("conclusion", texte, verbose)

    def warning(self, texte, verbose=None):
        self.msg("warning", texte, verbose)

    def error(self, texte):
        self.msg("error", texte)

    def saut(self):
        self.msg("saut", "")

    def separateur1(self):
        self.msg("separateur1", "")

    def separateur2(self):
        self.msg("separateur2", "")

    def separateur3(self):
        self.msg("separateur3", "")
