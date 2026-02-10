"""
Handlers de version pour les documents UPSTI.

Ce module implémente le pattern Strategy pour gérer les opérations
spécifiques à chaque version de document (UPSTI_Document et upsti-latex) sans dupliquer
le code dans la classe principale UPSTILatexDocument.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .file_helpers import read_json_config
from .file_latex_helpers import find_tex_entity, parse_metadata_tex, parse_metadata_yaml

if TYPE_CHECKING:
    from .document import UPSTILatexDocument


class DocumentVersionHandler(ABC):
    """Classe de base abstraite pour les handlers de version.

    Chaque version de document (v1, v2) doit implémenter cette interface
    pour définir ses propres méthodes de manipulation des métadonnées et
    de génération de contenu.
    """

    def __init__(self, document: "UPSTILatexDocument"):
        """Initialise le handler avec une référence au document parent.

        Paramètres
        ----------
        document : UPSTILatexDocument
            Le document parent qui utilise ce handler.
        """
        self.document = document

    @abstractmethod
    def parse_metadata(self) -> Tuple[Optional[Dict], List[List[str]]]:
        """Parse les métadonnées selon le format de la version.

        Retourne
        --------
        Tuple[Optional[Dict], List[List[str]]]
            (metadata_dict, messages) où metadata_dict contient les métadonnées
            brutes extraites du document, et messages contient les erreurs/warnings.
        """
        pass

    @abstractmethod
    def set_metadata(self, key: str, value: any) -> Tuple[bool, List[List[str]]]:
        """Ajoute ou modifie une métadonnée dans le document.

        Paramètres
        ----------
        key : str
            La clé de la métadonnée.
        value : any
            La valeur de la métadonnée.

        Retourne
        --------
        Tuple[bool, List[List[str]]]
            (success, messages) où success indique si l'opération a réussi.
        """
        pass

    @abstractmethod
    def delete_metadata(self, key: str) -> Tuple[bool, List[List[str]]]:
        """Supprime une métadonnée du document.

        Paramètres
        ----------
        key : str
            La clé de la métadonnée à supprimer.

        Retourne
        --------
        Tuple[bool, List[List[str]]]
            (success, messages) où success indique si l'opération a réussi.
        """
        pass

    @abstractmethod
    def get_logo(self) -> Optional[str]:
        """Retourne le chemin ou la valeur du logo d'un cours, par exemple.

        Retourne
        --------
        Optional[str]
            Le chemin ou la valeur du logo, ou None si non défini.
        """
        pass

    @abstractmethod
    def get_metadata_tex_declaration(self) -> str:
        """Génère les déclarations LaTeX des métadonnées du document.

        Pour UPSTI_Document, génère les commandes \\newcommand correspondant
        à chaque métadonnée (en fonction de tex_type et tex_key définis dans
        la configuration JSON).
        Pour upsti-latex, les métadonnées sont déjà dans le front-matter YAML,
        donc retourne une chaîne vide.

        Retourne
        --------
        str
            Les déclarations LaTeX (une par ligne), ou chaîne vide.
        """
        pass


class HandlerUPSTIDocument(DocumentVersionHandler):
    """Handler pour les documents UPSTI_Document.

    Les documents v1 stockent leurs métadonnées directement dans le code LaTeX
    sous forme de commandes personnalisées (\\UPSTImetaXXX{...}).
    """

    def parse_metadata(self) -> Tuple[Optional[Dict], List[List[str]]]:
        """Parse les métadonnées depuis le contenu LaTeX.

        Utilise le parser LaTeX pour extraire les commandes \\UPSTImetaXXX.

        Retourne
        --------
        Tuple[Optional[Dict], List[List[str]]]
            Dictionnaire des métadonnées extraites et liste de messages.
        """
        return parse_metadata_tex(self.document.content)

    def set_metadata(self, key: str, value: any) -> Tuple[bool, List[List[str]]]:
        """Ajoute ou modifie une métadonnée en insérant/modifiant une commande LaTeX.

        Pour les documents v1, recherche la commande correspondant à `key` via
        la configuration JSON (metadonnee[key]["parametres"]["tex_key"]).
        Si la commande existe déjà (ligne non commentée), elle est modifiée.
        Sinon, elle est ajoutée en haut du fichier.

        Paramètres
        ----------
        key : str
            Nom de la métadonnée (ex: "titre", "auteur").
        value : any
            Valeur de la métadonnée (sera convertie en string).

        Retourne
        --------
        Tuple[bool, List[List[str]]]
            (True, messages) si succès, (False, errors) sinon.
        """
        errors: List[List[str]] = []

        try:
            # 1. Charger la config pour obtenir tex_key
            cfg, cfg_errors = read_json_config()
            if cfg_errors:
                return False, cfg_errors
            if cfg is None:
                errors.append(
                    ["Configuration JSON introuvable ou invalide.", "fatal_error"]
                )
                return False, errors

            cfg_meta = cfg.get("metadonnee", {})
            meta_config = cfg_meta.get(key)
            if not meta_config:
                errors.append(
                    [
                        f"La métadonnée '{key}' n'est pas définie "
                        "dans la configuration.",
                        "error",
                    ]
                )
                return False, errors

            params = meta_config.get("parametres", {})
            tex_key = params.get("tex_key")
            if not tex_key:
                errors.append(
                    [
                        f"La métadonnée '{key}' n'a pas de 'tex_key' défini dans "
                        "la configuration.",
                        "error",
                    ]
                )
                return False, errors

            # 2. Vérifier si la commande existe déjà
            content = self.document.content
            existing = find_tex_entity(content, tex_key, kind="command_declaration")

            # 3. Construire la nouvelle déclaration
            new_declaration = f"\\newcommand{{\\{tex_key}}}{{{value}}}\n"

            if existing:
                # La commande existe : on la remplace
                # Trouver la ligne contenant cette déclaration
                lines = content.splitlines(keepends=True)
                new_lines = []
                replaced = False

                for line in lines:
                    # Ignorer les lignes commentées
                    stripped = line.lstrip()
                    if stripped.startswith("%"):
                        new_lines.append(line)
                        continue

                    # Vérifier si la ligne contient la déclaration
                    line_parsed = find_tex_entity(
                        line, tex_key, kind="command_declaration"
                    )
                    if line_parsed and not replaced:
                        # Remplacer cette ligne
                        new_lines.append(new_declaration)
                        replaced = True
                    else:
                        new_lines.append(line)

                new_content = "".join(new_lines)
                message = f"Métadonnée '{key}' (\\{tex_key}) modifiée avec succès."

            else:
                # La commande n'existe pas : on l'insère après \usepackage{...}}
                lines = content.splitlines(keepends=True)
                new_lines = []
                inserted = False

                for line in lines:
                    new_lines.append(line)

                    # Chercher \usepackage ou \RequirePackage{UPSTI_Document}
                    if not inserted and not line.lstrip().startswith("%"):
                        if "\\usepackage" in line or "\\RequirePackage" in line:
                            if "UPSTI_Document" in line:
                                # Insérer la nouvelle commande juste après
                                new_lines.append(new_declaration)
                                inserted = True

                if not inserted:
                    # Si on n'a pas trouvé le package, on insère en haut du fichier
                    new_lines.insert(0, new_declaration)

                new_content = "".join(new_lines)
                message = f"Métadonnée '{key}' (\\{tex_key}) ajoutée avec succès."

            # 4. Écrire le nouveau contenu
            self.document.file.write(new_content)

            # 5. Invalider le cache des métadonnées
            self.document._metadata = None

            errors.append([message, "info"])
            return True, errors

        except Exception as e:
            errors.append(
                [f"Erreur lors de l'ajout/modification de la métadonnée: {e}", "error"]
            )
            return False, errors

    def delete_metadata(self, key: str) -> Tuple[bool, List[List[str]]]:
        """Supprime une métadonnée en retirant la commande LaTeX.

        Paramètres
        ----------
        key : str
            Nom de la métadonnée à supprimer.

        Retourne
        --------
        Tuple[bool, List[List[str]]]
            (True, []) si succès, (False, errors) sinon.
        """
        errors: List[List[str]] = []

        try:
            import re

            content = self.document.content

            # Pattern pour trouver la ligne complète avec \UPSTImeta<key>{valeur}
            pattern = rf"\\UPSTImeta{re.escape(key)}\{{[^}}]*\}}\n?"

            if not re.search(pattern, content):
                errors.append([f"La métadonnée '{key}' n'existe pas.", "error"])
                return False, errors

            # Supprimer la ligne
            new_content = re.sub(pattern, "", content)

            # Écrire le nouveau contenu
            self.document.file.write(new_content)

            # Invalider le cache
            self.document._metadata = None

            errors.append([f"Métadonnée '{key}' supprimée avec succès.", "info"])
            return True, errors

        except Exception as e:
            errors.append(
                [f"Erreur lors de la suppression de la métadonnée: {e}", "error"]
            )
            return False, errors

    def get_logo(self) -> Optional[str]:
        """Retourne le contenu de \\UPSTIlogoPageDeGarde.

        Retourne
        --------
        Optional[str]
            Le contenu de la commande \\UPSTIlogoPageDeGarde, ou None si non définie.
        """
        try:
            content = self.document.content
            parsed = find_tex_entity(content, "UPSTIlogoPageDeGarde", kind="command")

            # parsed est une liste...
            if parsed and len(parsed) > 0:
                first_occurrence = parsed[0]
                args = first_occurrence.get("args", [])
                if args and len(args) > 0:
                    return args[0].get("value")

            return None
        except Exception:
            return None

    def get_metadata_tex_declaration(self) -> str:
        """Génère les déclarations LaTeX des métadonnées pour UPSTI_Document.

        Parcourt toutes les métadonnées du document et génère les commandes
        LaTeX correspondantes en fonction de tex_type et tex_key définis
        dans pyUPSTIlatex.json.

        - tex_type == "command_declaration" : génère \\newcommand{\\<tex_key>}{<valeur>}
          où <valeur> est l'id_upsti_document pour les champs relationnels (join_key),
          ou la raw_value pour les champs simples.
        - tex_type == "package_option_programme" : ignoré (géré au niveau du \\usepackage).

        Retourne
        --------
        str
            Bloc de déclarations \\newcommand, une par ligne.
        """

        print("pouet")

        # Charger la config JSON
        cfg, cfg_errors = read_json_config()
        if cfg is None:
            return ""

        cfg_meta = cfg.get("metadonnee", {})

        # Récupérer les métadonnées du document
        metadata, _ = self.document.get_metadata()
        if metadata is None:
            return ""

        print(metadata)

        declarations = []

        for key, meta_config in cfg_meta.items():
            params = meta_config.get("parametres", {})
            tex_key = params.get("tex_key")
            tex_type = params.get("tex_type", "")

            if not tex_key or tex_type != "command_declaration":
                continue

            # Récupérer les données de la métadonnée dans le document
            meta_data = metadata.get(key)
            if meta_data is None:
                continue

            raw_value = meta_data.get("raw_value", "")
            if raw_value == "" or raw_value is None:
                continue

            # Déterminer la valeur à utiliser pour la déclaration
            join_key = params.get("join_key", "")

            if join_key and not isinstance(raw_value, dict):
                # Valeur relationnelle : récupérer id_upsti_document depuis la config
                cfg_section = cfg.get(key, {})
                entry = cfg_section.get(str(raw_value), {})
                tex_value = entry.get("id_upsti_document", raw_value)
            elif isinstance(raw_value, dict):
                # Valeur custom (dict) : utiliser 0 comme marqueur
                tex_value = 0
            elif isinstance(raw_value, bool):
                tex_value = "1" if raw_value else "0"
            else:
                tex_value = raw_value

            declarations.append(f"\\newcommand{{\\{tex_key}}}{{{tex_value}}}")

            # Gérer les custom_tex_keys pour les valeurs custom (dict)
            custom_tex_keys = params.get("custom_tex_keys", [])
            if isinstance(raw_value, dict) and custom_tex_keys:
                for custom_entry in custom_tex_keys:
                    champ = custom_entry.get("champ", "")
                    custom_key = custom_entry.get("tex_key", "")
                    if custom_key and champ in raw_value:
                        declarations.append(
                            f"\\newcommand{{\\{custom_key}}}{{{raw_value[champ]}}}"
                        )

        print(declarations)
        exit()

        return "\n".join(declarations)


class HandlerUpstiLatex(DocumentVersionHandler):
    """Handler pour les documents upsti-latex.

    Les documents v2 stockent leurs métadonnées dans un bloc YAML
    (front-matter) au début du fichier.
    """

    def parse_metadata(self) -> Tuple[Optional[Dict], List[List[str]]]:
        """Parse les métadonnées depuis le front-matter YAML.

        Utilise le parser YAML pour extraire les métadonnées du bloc
        délimité par --- au début du fichier.

        Retourne
        --------
        Tuple[Optional[Dict], List[List[str]]]
            Dictionnaire des métadonnées extraites et liste de messages.
        """
        return parse_metadata_yaml(self.document.content)

    def set_metadata(self, key: str, value: any) -> Tuple[bool, List[List[str]]]:
        """Ajoute une métadonnée dans le bloc YAML.

        Paramètres
        ----------
        key : str
            Nom de la métadonnée.
        value : any
            Valeur de la métadonnée (doit être sérialisable en YAML).

        Retourne
        --------
        Tuple[bool, List[List[str]]]
            (True, []) si succès, (False, errors) sinon.
        """
        errors: List[List[str]] = []

        try:
            import yaml

            content = self.document.content

            # Extraire le bloc YAML
            if not content.startswith("---"):
                errors.append(
                    [
                        "Le document ne contient pas de front-matter YAML valide.",
                        "error",
                    ]
                )
                return False, errors

            # Trouver la fin du bloc YAML
            parts = content.split("---", 2)
            if len(parts) < 3:
                errors.append(
                    ["Format YAML invalide (manque le délimiteur de fin ---).", "error"]
                )
                return False, errors

            yaml_content = parts[1]
            rest_content = parts[2]

            # Parser le YAML
            metadata = yaml.safe_load(yaml_content) or {}

            # Vérifier si la clé existe déjà
            if key in metadata:
                errors.append(
                    [
                        f"La métadonnée '{key}' existe déjà. "
                        "Utilisez modifier_metadonnee pour la changer.",
                        "error",
                    ]
                )
                return False, errors

            # Ajouter la nouvelle métadonnée
            metadata[key] = value

            # Reconstruire le fichier
            new_yaml = yaml.dump(metadata, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_yaml}---{rest_content}"

            # Écrire le nouveau contenu
            self.document.file.write(new_content)

            # Invalider le cache
            self.document._metadata = None

            errors.append([f"Métadonnée '{key}' ajoutée avec succès.", "info"])
            return True, errors

        except Exception as e:
            errors.append([f"Erreur lors de l'ajout de la métadonnée: {e}", "error"])
            return False, errors

    def delete_metadata(self, key: str) -> Tuple[bool, List[List[str]]]:
        """Supprime une métadonnée du bloc YAML.

        Paramètres
        ----------
        key : str
            Nom de la métadonnée à supprimer.

        Retourne
        --------
        Tuple[bool, List[List[str]]]
            (True, []) si succès, (False, errors) sinon.
        """
        errors: List[List[str]] = []

        try:
            import yaml

            content = self.document.content

            # Extraire et parser le YAML
            if not content.startswith("---"):
                errors.append(
                    [
                        "Le document ne contient pas de front-matter YAML valide.",
                        "error",
                    ]
                )
                return False, errors

            parts = content.split("---", 2)
            if len(parts) < 3:
                errors.append(
                    ["Format YAML invalide (manque le délimiteur de fin ---).", "error"]
                )
                return False, errors

            yaml_content = parts[1]
            rest_content = parts[2]

            metadata = yaml.safe_load(yaml_content) or {}

            # Vérifier si la clé existe
            if key not in metadata:
                errors.append([f"La métadonnée '{key}' n'existe pas.", "error"])
                return False, errors

            # Supprimer la métadonnée
            del metadata[key]

            # Reconstruire le fichier
            new_yaml = yaml.dump(metadata, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_yaml}---{rest_content}"

            # Écrire le nouveau contenu
            self.document.file.write(new_content)

            # Invalider le cache
            self.document._metadata = None

            errors.append([f"Métadonnée '{key}' supprimée avec succès.", "info"])
            return True, errors

        except Exception as e:
            errors.append(
                [f"Erreur lors de la suppression de la métadonnée: {e}", "error"]
            )
            return False, errors

    def get_logo(self) -> Optional[str]:
        """Retourne le logo UPSTI pour la version 2.

        Pour l'instant, cette méthode retourne None car la gestion
        du logo pour v2 n'est pas encore implémentée.

        Retourne
        --------
        Optional[str]
            None (à implémenter ultérieurement).
        """
        # TODO: Implémenter la récupération du logo pour upsti-latex
        return None

    def get_metadata_tex_declaration(self) -> str:
        """Les documents upsti-latex n'utilisent pas de déclarations \\newcommand.

        Les métadonnées sont déjà dans le front-matter YAML, donc aucune
        déclaration LaTeX supplémentaire n'est nécessaire.

        Retourne
        --------
        str
            Chaîne vide.
        """
        return ""
