# pyUPSTIlatex

Utilitaire pour lire, parser et éditer des fichiers UPSTI_LaTeX.

## Install:

```
pip install -e .
```

## Fonctions

### CLI

- version : afficher la version d'un fichier
- infos : afficher les informations d'un fichier (et sa version), depuis YAML ou si absent, depuis LaTeX
- compil : compiler un fichier tex
- quick-compil : compilation rapide
- migrate : migration vers UPSTI_Document v3
- create-poly-td : création d'un poly de TD
- merge-pdf : fusionner plusieurs pdf (avec plusieurs pages ou non)

### A partir du site

```
pyUPSTIlatex inspect path/to/file.tex
```

```
pyUPSTIlatex extract-zone path/to/file.tex zone_name
```
