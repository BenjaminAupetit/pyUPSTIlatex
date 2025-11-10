import click

from .document import UPSTILatexDocument
from .logger import (
    COLOR_GREEN,
    COLOR_LIGHT_GREEN,
    COLOR_LIGHT_ORANGE,
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
    msg.titre1(f"VERSION : {path}")
    msg.action("Détection de la version du document...")

    # Instanciation du document
    doc = UPSTILatexDocument.from_path(path)

    # Vérification du fichier
    if not msg.check_file(doc, mode="read", path=path, emit=False):
        # Récupérer les erreurs et les afficher comme 'resultat' pour garder le
        # format attendu par l'utilisateur
        _ok, file_errors = doc.is_file_ok("read")
        for err in file_errors:
            msg.resultat(f"{err[0]}", flag=err[1])

        msg.separateur1()
        return ctx.exit(1)

    # Détection de version
    version, errors = doc.get_version()
    for error in errors:
        msg.resultat(f"{error[0]}", flag=error[1])
    if version is not None:
        msg.resultat(f"Version détectée : {version}")
    msg.separateur1()


@main.command()
@click.argument("path", type=click.Path())
@click.pass_context
def infos(ctx, path):
    """Affiche les informations du document UPSTI"""

    msg: MessageHandler = ctx.obj["msg"]
    msg.titre1(f"INFOS : {path}")

    # Instanciation du document
    doc = UPSTILatexDocument.from_path(path)

    # Vérification du fichier
    if not msg.check_file(doc, mode="read", path=path):
        return ctx.exit(1)

    # Récupération des métadonnées selon la version
    metadata, errors = doc.get_metadata()

    # On détecte si on a rencontré une erreur
    for error in errors:
        # Si on détecte une erreur, on stoppe ici, si c'est un warning
        # on affichera plus tard
        if error[1] == "error":
            msg.info(f"{error[0]}", flag=error[1])
            msg.separateur1()
            return ctx.exit(1)

    if metadata:
        # Préparer la liste des éléments affichables et calculer la largeur max
        items = []
        for m in metadata.values():
            # TOTEST: on affiche tout pour l'instant
            # if show_in_infos == "if_true" and m.get("raw_value") is False:
            #     continue
            label = m.get("label")
            valeur = (
                m.get("valeur")
                if m.get("valeur") is not None
                else m.get("raw_value") or ""
            )
            type_meta = m.get("type_meta", "")
            items.append((label, valeur, type_meta))

        max_label_len = max((len(lbl) for lbl, _, _ in items), default=0)

        # Afficher les lignes avec alignement des ':'
        for label, valeur, type_meta in items:
            # colorer le label selon s'il s'agit d'une valeur par défaut
            if type_meta == "default":
                separateur_colored = f"{COLOR_ORANGE}=>{COLOR_RESET}"
            elif type_meta == "deducted":
                separateur_colored = f"{COLOR_LIGHT_GREEN}=>{COLOR_RESET}"
            else:
                separateur_colored = f"{COLOR_GREEN}=>{COLOR_RESET}"

            # padding: ajouter des espaces après le label pour aligner ':'
            pad = max_label_len - len(label)
            padding = " " * pad
            msg.info(f"{padding}{label} {separateur_colored} {valeur}")

    msg.separateur2()
    msg.info(
        f"{COLOR_GREEN}=>{COLOR_RESET} valeur définie dans le fichier tex, "
        f"{COLOR_LIGHT_GREEN}=>{COLOR_RESET} valeur déduite, "
        f"{COLOR_ORANGE}=>{COLOR_RESET} valeur par défaut"
    )

    if errors:
        msg.separateur1()
        for error in errors:
            msg.info(f"{error[0]}", flag=error[1])

    msg.separateur1()


# ================================================================================
# TOCHECK Tout ce qui suit est généré par IA, à vérifier et comprendre
# ================================================================================


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("zone", type=str)
@click.option("--stdout/--no-stdout", default=True)
@click.option("--output", "-o", type=click.Path(), default=None)
def extract_zone(path, zone, stdout, output):
    """Extract a named zone. Writes to stdout or file."""
    doc = UPSTILatexDocument.from_path(path)
    content = doc.get_zone(zone)
    if content is None:
        raise click.ClickException(f"Zone '{zone}' not found in {path}")
    if stdout:
        click.echo(content)
    elif output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"Wrote {output}")


if __name__ == "__main__":
    main()
