from pathlib import Path

import click

from .config import load_config
from .document import UPSTILatexDocument
from .filesystem import scan_for_documents
from .logger import (
    COLOR_DARK_GRAY,
    COLOR_GREEN,
    COLOR_LIGHT_BLUE,
    COLOR_LIGHT_GREEN,
    COLOR_ORANGE,
    COLOR_RED,
    COLOR_RESET,
    MessageHandler,
)


@click.group()
@click.option(
    "--log-file", "-L", type=click.Path(), default=None, help="Chemin du fichier de log"
)
@click.option(
    "--no-verbose",
    is_flag=True,
    default=False,
    help="Désactive les messages d'information",
)
@click.pass_context
def main(ctx, log_file, no_verbose):
    """pyUPSTIlatex CLI"""
    handler = MessageHandler(log_file=log_file, verbose=not no_verbose)
    ctx.obj = {"msg": handler}


@main.command()
@click.argument("path", type=click.Path())
@click.pass_context
def version(ctx, path):
    """Affiche la version du document UPSTI/EPB."""

    msg: MessageHandler = ctx.obj["msg"]
    msg.titre1(f"VERSION : {Path(path).name}")

    # Instanciation du document
    doc = UPSTILatexDocument.from_path(path)

    # Vérification du fichier via UPSTILatexDocument.check_file (sans émission auto)
    ok, file_errors = doc.file.check_file("read")
    if not ok:
        # Afficher les erreurs au format 'resultat' comme auparavant
        for err in file_errors:
            msg.info(f"{err[0]}", flag=err[1])
        msg.separateur1()
        return ctx.exit(1)

    # Détection de version
    version, errors = doc.get_version()
    for error in errors:
        msg.info(f"{error[0]}", flag=error[1])
    if version is not None:
        msg.info(f"Version détectée : {COLOR_GREEN}{version}{COLOR_RESET}")
    msg.separateur1()


@main.command()
@click.argument("path", type=click.Path())
@click.pass_context
def infos(ctx, path):
    """Affiche les informations du document UPSTI"""

    msg: MessageHandler = ctx.obj["msg"]
    msg.titre1(f"INFOS : {Path(path).name}")

    # Instanciation du document
    doc = UPSTILatexDocument.from_path(path)

    # Vérification du fichier (lecture)
    fichier_valide, errors = doc.file.check_file("read")

    # Récupération des métadonnées selon la version
    if fichier_valide:
        metadata, meta_errors = doc.get_metadata()
        errors += meta_errors

    # On détecte si on a rencontré une erreur fatale
    for error in errors:
        if error[1] == "fatal_error":
            msg.info(f"{error[0]}", flag=error[1])
            msg.separateur1()
            return ctx.exit(1)

    if metadata:
        # Préparer la liste des éléments affichables et calculer la largeur max
        items = []
        for meta in metadata.values():
            label = meta.get("label")
            valeur = (
                meta.get("valeur")
                if meta.get("valeur") is not None
                else meta.get("raw_value", "")
            )
            initial_value = meta.get("initial_value", "")
            display_flag = meta.get("display_flag", "")

            # type_meta peut être de la forme "default" ou "default:wrong_type"
            tm_raw = meta.get("type_meta") or ""
            tm_parts = tm_raw.split(":", 1)
            main_type = tm_parts[0] if tm_parts and tm_parts[0] else ""
            cause_type = tm_parts[1] if len(tm_parts) > 1 else ""
            items.append(
                (label, valeur, main_type, cause_type, initial_value, display_flag)
            )

        max_label_len = max((len(lbl) for lbl, _, _, _, _, _ in items), default=0)

        # Afficher les lignes avec alignement des ':'
        # Vérifier l'affichage en fonction des nouveaux mots clés
        for label, valeur, type_meta, cause_meta, initial_value, display_flag in items:
            # colorer le label selon s'il s'agit d'une valeur par défaut
            if display_flag == "info":
                separateur_colored = f"{COLOR_LIGHT_BLUE}=>{COLOR_RESET}"
            elif type_meta == "default":
                separateur_colored = f"{COLOR_DARK_GRAY}=>{COLOR_RESET}"
                if cause_meta:
                    separateur_colored = f"{COLOR_ORANGE}=>{COLOR_RESET}"
                    valeur = (
                        f"{COLOR_ORANGE}{valeur} (avant correction: "
                        f"'{initial_value}'){COLOR_RESET}"
                    )
            elif type_meta == "deducted":
                separateur_colored = f"{COLOR_LIGHT_GREEN}=>{COLOR_RESET}"
            elif type_meta == "ignored":
                separateur_colored = f"{COLOR_RED}=>{COLOR_RESET}"
                valeur = f"{COLOR_RED}ignoré: '{initial_value}'{COLOR_RESET}"
            else:
                separateur_colored = f"{COLOR_GREEN}=>{COLOR_RESET}"

            # padding: ajouter des espaces après le label pour aligner ':'
            pad = max_label_len - len(label)
            padding = " " * pad
            msg.info(f"{padding}{label} {separateur_colored} {valeur}")

    # Erreurs rencontrées
    if errors:
        msg.separateur2()
        for error in errors:
            msg.info(f"{error[0]}", flag=error[1])

    # Légende des symboles
    msg.separateur1()
    msg.info(
        f"{COLOR_GREEN}=>{COLOR_RESET} valeur définie dans le fichier tex, "
        f"{COLOR_LIGHT_GREEN}=>{COLOR_RESET} valeur déduite, "
        f"{COLOR_DARK_GRAY}=>{COLOR_RESET} valeur par défaut"
    )
    msg.info(
        f"{COLOR_ORANGE}=>{COLOR_RESET} WARNING, "
        f"{COLOR_RED}=>{COLOR_RESET} ERROR, {COLOR_LIGHT_BLUE}=>{COLOR_RESET} INFO"
    )
    msg.separateur1()


@main.command(name="liste-fichiers")
@click.argument(
    "path",
    nargs=-1,
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.option(
    "--exclude",
    "exclude",
    multiple=True,
    help=(
        "Motifs d'exclusion (glob). Si absent, utilise "
        "OS_TRAITEMENT_PAR_LOT_FICHIERS_A_EXCLURE."
    ),
)
@click.option(
    "--show-full-path",
    is_flag=True,
    default=False,
    help="Affiche le chemin complet au lieu du chemin tronqué à 88 caractères.",
)
@click.pass_context
def liste_fichiers(ctx, path, exclude, show_full_path):
    """Affiche la liste des fichiers UPSTI_document dans un ou plusieurs dossiers."""

    msg: MessageHandler = ctx.obj["msg"]
    cfg = load_config()

    # Déterminer les racines à scanner (priorité: path args > env)
    if path and len(path) > 0:
        roots_to_scan = list(path)
    else:
        roots_to_scan = list(
            cfg.traitement_par_lot.dossiers_a_traiter
        )  # scan_for_documents utilisera le .env

    # Déterminer les motifs d'exclusion (priorité: --exclude > env)
    exclude_patterns = list(exclude) if exclude else None  # None = utiliser .env

    # Titre
    if roots_to_scan:
        nb_dossiers = len(roots_to_scan)
        if nb_dossiers == 1:
            msg.titre1(
                f"LISTE des fichiers UPSTI_document contenus dans : {roots_to_scan[0]}"
            )
        else:
            msg.titre1(
                "LISTE des fichiers UPSTI_document contenus dans :\n  - "
                + "\n  - ".join(roots_to_scan)
            )

    # Scanner les documents
    documents, errors = scan_for_documents(roots_to_scan, exclude_patterns)

    # Gérer les erreurs fatales (aucune racine définie)
    if not documents and errors:
        for e in errors:
            msg.info(e, flag="warning")
        msg.separateur1()
        ctx.exit(1)

    # Afficher les documents trouvés
    if not documents:
        msg.info("Aucun document compatible trouvé.", flag="warning")
    else:
        # Calculer les largeurs de colonnes pour un affichage propre
        display_key = "path" if show_full_path else "display_path"
        max_path = max(len(d[display_key]) for d in documents)
        max_version = max(len(d["version"]) for d in documents)

        # Afficher chaque document
        for doc in sorted(documents, key=lambda x: x["path"]):
            path_padded = doc[display_key].ljust(max_path)
            version_text = doc["version"].ljust(max_version)

            # Colorer la version selon le paramètre compiler
            if doc.get("a_compiler", False):
                version_colored = f"{version_text}"
            else:
                version_colored = f"{COLOR_RED}{version_text}{COLOR_RESET}"

            msg.info(f"{path_padded}  {version_colored}")

        # Total
        nb_documents = len(documents)
        msg.separateur2()
        msg.info(
            f"Total de {COLOR_GREEN}{nb_documents}{COLOR_RESET} "
            "document(s) trouvé(s)."
        )

    # Erreurs rencontrées
    if errors:
        msg.separateur2()
        for e in errors:
            msg.info(e, flag="warning")

    msg.separateur1()


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.pass_context
def compile(ctx, path):
    """Compile un fichier .tex ou tous les fichiers d'un dossier."""

    from pathlib import Path

    chemin = Path(path)
    msg: MessageHandler = ctx.obj["msg"]

    if chemin.is_file():
        # Compilation d'un seul fichier
        msg.titre1(f"COMPILATION de {chemin}")

        # TODO: Appeler la fonction de compilation

    elif chemin.is_dir():
        # Compilation de tous les fichiers .tex du dossier
        msg.titre1(f"COMPILATION des fichiers dans {chemin}")

        # Liste des fichiers contenus dans le dossier passé en paramètres
        msg.info("Recherche de tous les fichiers tex UPSTI_document à compiler")
        documents, errors = scan_for_documents([str(chemin)], None)

        # On récupère les infos de compilation de chaque fichier
        documents_a_compiler: list[dict] = []
        for d in documents:
            try:
                doc = UPSTILatexDocument.from_path(d["path"])
                params, _ = doc.get_compilation_parameters()
                d["parametres_compilation"] = params
                if params and params.get("compiler"):
                    documents_a_compiler.append(d)
            except Exception as e:
                msg.info(
                    f"Erreur lors de la lecture des paramètres de {d['filename']}: {e}",
                    flag="warning",
                )
                continue

        nb_documents = len(documents_a_compiler)
        if nb_documents == 0:
            msg.resultat("Aucun document compatible trouvé.", flag="error")
            msg.separateur1()
            return ctx.exit(1)

        # Affichage de la liste des documents trouvés
        max_name = max(len(d["filename"]) for d in documents_a_compiler)
        max_version = max(len(d["version"]) for d in documents_a_compiler)
        for d in sorted(documents_a_compiler, key=lambda x: x["filename"]):
            msg.resultat_item(
                f"{d['filename']:{max_name}}  {d['version']:>{max_version}}"
            )
        msg.resultat_conclusion(
            f"{COLOR_GREEN}{nb_documents}{COLOR_RESET} document(s) trouvé(s)."
        )

        if nb_documents > 1:
            str_fichiers_a_traiter = (
                f"ces {nb_documents} fichiers (la procédure peut-être très longue)"
            )
        else:
            str_fichiers_a_traiter = "ce fichier"

        msg.titre2(
            f"Souhaitez-vous réellement compiler {str_fichiers_a_traiter} ? (O/N)"
        )

        doit_compiler = input()
        if doit_compiler not in ["O", "o"]:
            msg.separateur1()
            msg.info("Opération annulée.", flag="error")
            msg.separateur1()
            return ctx.exit(1)
        else:
            msg.titre2("Démarrage de la compilation...")

    # TOCONTINUE : il faut continuer la compilation maintenant que j'ai bien accès
    # à tous les fichiers...

    msg.separateur1()


if __name__ == "__main__":
    main()
