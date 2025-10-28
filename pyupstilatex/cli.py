import click

from .constants import UPSTI_DEFAULT_COMMANDS
from .document import UPSTILatexDocument
from .logger import MessageHandler


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
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--details/--no-details",
    default=False,
    help="Afficher aussi les métadonnées et les zones",
)
@click.pass_context
def inspect(ctx, path, details):
    msg: MessageHandler = ctx.obj["msg"]
    doc = UPSTILatexDocument.from_path(path)
    msg.titre1(f"Inspect {path}")
    # Affichage minimal par défaut: valeurs des commandes UPSTI importantes
    cmds = doc.get_commands(names=UPSTI_DEFAULT_COMMANDS)
    if not cmds:
        msg.info("Aucune des commandes UPSTI attendues n'a été trouvée.")
    else:
        msg.info("Valeurs des commandes UPSTI:")
        for name in UPSTI_DEFAULT_COMMANDS:
            vals = cmds.get(name)
            if not vals:
                msg.resultat(f"{name}: (absent)")
            else:
                # On affiche toutes les occurrences; la plupart n'ont qu'un seul argument
                for i, v in enumerate(vals, start=1):
                    suffix = f" [{i}]" if len(vals) > 1 else ""
                    msg.resultat(f"{name}{suffix}: {v if v is not None else ''}")

    if details:
        meta = doc.metadata
        msg.titre3("Métadonnées")
        if meta:
            for k, v in meta.items():
                msg.resultat(f"{k}: {v}")
        else:
            msg.resultat("(aucune)")
        zones = doc.list_zones()
        msg.titre3("Zones détectées")
        if zones:
            for z in zones:
                msg.resultat(z)
        else:
            msg.resultat("(aucune)")


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
