# pyUPSTIlatex

Utilitaire pour lire, parser et éditer des fichiers UPSTI_LaTeX.

## Install:

```
pip install -e .
```

## Fonctions

### CLI

#### Fonctionnelles

- version : afficher la version d'un fichier

#### En cours...

- infos : afficher les informations d'un fichier (et sa version), depuis YAML ou si absent, depuis LaTeX (check integrity !!!)

#### ToDev

- liste : liste les documents contenus dans un dossier qui possèdent tels ou tels attributs (options de package, type, etc...)
- change-parametre : change la valeur d'un paramètre ou d'une métadonnée
- compil : compiler un fichier tex
- quick-compil : compilation rapide
- migrate : migration vers UPSTI_Document v3
- create-poly-td : création d'un poly de TD
- create-poly-colles : création d'un ou des polys de colle
- merge-pdf : fusionner plusieurs pdf (avec plusieurs pages ou non)

### A partir du site

```
pyUPSTIlatex inspect path/to/file.tex
```

```
pyUPSTIlatex extract-zone path/to/file.tex zone_name
```
