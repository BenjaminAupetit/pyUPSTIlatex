# pyUPSTIlatex

<div align="center">
  <img src="integration/icones_et_logos/pyUPSTIlatex.png" alt="pyUPSTIlatex Logo" width="200"/>
  
  ![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
  ![Version](https://img.shields.io/badge/version-2.0.0-green)
  ![License](https://img.shields.io/badge/license-GPL--3.0-blue)
  ![Status](https://img.shields.io/badge/status-beta-orange)
</div>

## Description

**pyUPSTIlatex** est un outil en ligne de commande complet pour gérer, compiler et automatiser la production de documents LaTeX initialement conçu pour les Sciences Industrielles de l'Ingénieur (S2I) en Classes Préparatoires aux Grandes Écoles (CPGE).

Il peut néanmoins être adapté à n'importe quel niveau ou discipline, moyennant quelques étapes de personnalisation.

Compatible avec les packages LaTeX `upsti-latex` (et `UPSTI_Document`), pyUPSTIlatex simplifie la gestion de documents pédagogiques (cours, TD, TP, colles) en automatisant la compilation, le versionnage, l'upload FTP et la génération de polys.

## ✨ Fonctionnalités principales

- **Compilation intelligente** avec gestion des versions élève/prof/documents à compléter, etc.
- **Versions accessibles** génération automatique de documents accessibles : dys, déficients visuels...
- **Génération de polys** de TD ou de colle
- **Renommage automatique des fichiers tex** selon un pattern configurable
- **Détection automatique** de version et type de document
- **Upload FTP** automatisé avec webhook optionnel pour synchronisation sur un site internet
- **Traitement par lot** de documents (liste des documents compatibles, compilation par lots, etc.)
- **Intégration à l'OS** : affichage de la version, des métadonnées, etc.
- **Personnalisation** possibilité de surcharger la configuration TOML, les templates et différentes classes

### En cours de développement

- **Création des en-têtes et pieds de page LaTeX** à partir de templates générés par pyUPSTIlatex

## Installation

### Prérequis

- **Python** 3.9 ou supérieur
- **LaTeX** (TeX Live, MiKTeX) avec pdflatex
- Packages LaTeX : `upsti-latex` (en cours de développement) ou `UPSTI_Document` ([Télécharger](https://s2i.pinault-bigeard.com/ressources/latex/69-packages-latex-pour-les-sciences-de-l-ingenieur-upsti))

### Installation standard

```bash
# Cloner le dépôt
git clone https://github.com/ebigeard/pyUPSTIlatex.git
cd pyUPSTIlatex

# Installer le package avec toutes ses dépendances (automatique via pyproject.toml)
pip install -e .
```

> **Note** : Cette commande installe automatiquement toutes les dépendances requises (PyYAML, click, python-dotenv, regex, tomli pour Python < 3.11)

## Démarrage rapide

### Configuration initiale

Consulter le wiki [Configuration avancée](https://github.com/ebigeard/pyUPSTIlatex/wiki/Configuration) pour plus de détails.

1. **Créer le fichier de configuration personnalisé :**

```bash
cp custom/.env.template custom/.env
cp custom/config.toml.template  custom/config.toml
```

2. **Configuration TOML** (`custom/config.toml`) :

```toml
[meta.default]
auteur = "Votre Nom"
classe = "MPSI"
matiere = "S2I"

[compilation.defaut]
upload = false  # Désactiver l'upload par défaut

[ftp]
mode_local = true
mode_local_dossier = "C:/tmp/documents"
```

3. **Secrets** (`custom/.env`) :

```bash
FTP_HOST=ftp.example.com
FTP_USER=username
FTP_PASSWORD=password
```

### Utilisation basique

```bash
# Afficher la version d'un document
pyUPSTIlatex version chemin/vers/document.tex

# Afficher les informations complètes (métadonnées)
pyUPSTIlatex infos chemin/vers/document.tex

# Lister les fichiers LaTeX compatibles dans un dossier
pyUPSTIlatex liste-fichiers chemin/vers/dossier

# Compiler un document
pyUPSTIlatex compile chemin/vers/document.tex

# Compiler tous les documents d'un dossier
pyUPSTIlatex compile chemin/vers/dossier

# Créer un poly de TD (en 2 temps)
pyUPSTIlatex poly chemin/vers/dossier
pyUPSTIlatex poly chemin/vers/dossier/_poly/poly.yaml

# Mettre à jour automatiquement le fichier pyUPSTIlatex.json
pyUPSTIlatex update-config
```

## Structure du projet

```text
pyUPSTIlatex/
├── pyupstilatex/               # Code source principal
│   ├── config/                 # Configuration par défaut
│   │   ├── pyUPSTIlatex.json   # Possiblité de mettre à jour par le CLI
│   │   └── config.default.toml # Configuration métier par défaut
│   ├── accessibilite.py        # Configuration des fichiers accessibles
│   ├── cli.py                  # Interface en ligne de commande
│   ├── config.py               # Gestion de la configuration
│   ├── document.py             # Classe principale UPSTILatexDocument
│   ├── document_registery.py   # Pour permettre la surcharge de UPSTILatexDocument
│   ├── exceptions.py           # Gestion des erreurs (pas ouf..)
│   ├── file_helpers.py         # Utilitaires de manipulation de fichiers
│   ├── file_latex_helpers.py   # Parsing LaTeX
│   ├── file_system.py          # Gestion I/O sur le disque
│   ├── handlers.py             # Handlers de version (v1, v2)
│   └── logger.py               # Système de messages dans la console et logger
├── templates/                  # Templates LaTeX par défaut
│   ├── latex/                  # Templates de documents
│   └── yaml/                   # Templates YAML
├── integration/                # Fichiers d'intégration OS
│   ├── commandes_windows/      # Scripts .cmd
│   ├── icones_et_logos/        # Icônes et logos
│   └── yaml/                   # Configs YAML
├── custom/                     # Configuration personnalisée (non versionné)
│   ├── .env                    # Secrets (FTP, etc.)
│   ├── .env.template           # Secrets (Template à dupliquer)
│   ├── config.toml             # Surcharge de configuration
│   ├── config.toml.template    # Surcharge de configuration (Template à dupliquer)
│   ├── document.py.template    # Template de classe personnalisée
│   └── templates/              # Overrides des templates LaTeX et YAML
└── exemples/                   # Exemples
```

## Configuration

pyUPSTIlatex utilise une **configuration en cascade** :

1. **`config.default.toml`** : Configuration par défaut (versionnée)
2. **`custom/config.toml`** : Surcharges locales (non versionnée)
3. **`custom/.env`** : Secrets uniquement (FTP, API keys)

### Sections de configuration

- **`[meta.default]`** : Métadonnées par défaut des documents
- **`[compilation.defaut]`** : Paramètres de compilation
- **`[os.format]`** : Format des noms de fichiers
- **`[os.suffixe]`** : Suffixes (prof, élève, etc.)
- **`[os.dossier]`** : Arborescence des dossiers
- **`[ftp]`** : Configuration FTP
- **`[poly]`** : Paramètres des polys

Consultez le wiki [Configuration avancée](https://github.com/ebigeard/pyUPSTIlatex/wiki/Configuration) pour le guide complet.

## 📚 Documentation

La **documentation complète** est disponible sur le [**Wiki GitHub**](https://github.com/ebigeard/pyUPSTIlatex/wiki) :

- [Guide d'installation détaillé](https://github.com/ebigeard/pyUPSTIlatex/wiki/Installation)
- [Configuration avancée](https://github.com/ebigeard/pyUPSTIlatex/wiki/Configuration)
- [Commandes CLI](https://github.com/ebigeard/pyUPSTIlatex/wiki/CLI)
- [Création de documents](https://github.com/ebigeard/pyUPSTIlatex/wiki/Documents)
- [Génération de polys](https://github.com/ebigeard/pyUPSTIlatex/wiki/Polys)
- [API Python](https://github.com/ebigeard/pyUPSTIlatex/wiki/API)
- [Migration depuis v1](https://github.com/ebigeard/pyUPSTIlatex/wiki/Migration)

## Exemples d'utilisation

### Compilation avec options

```bash
# Compilation en mode "deep" (régénération complète)
pyUPSTIlatex compile document.tex --mode deep

# Simulation (dry-run)
pyUPSTIlatex compile document.tex --dry-run
```

### Traitement par lot

```bash
# Compiler tous les documents d'un dossier
pyUPSTIlatex compile chemin/vers/dossier
```

### Génération de poly

```bash
# Créer le fichier YAML de configuration
pyUPSTIlatex poly chemin/vers/TD

# Le poly.yaml est généré, le modifier si nécessaire, puis compiler
pyUPSTIlatex poly chemin/vers/TD/_poly/poly.yaml
```

### Utilisation programmatique (API Python)

```python
from pyupstilatex import UPSTILatexDocument
from pyupstilatex.config import load_config

# Charger la configuration
cfg = load_config()

# Ouvrir un document
doc, errors = UPSTILatexDocument.from_path("document.tex")

# Extraire les métadonnées
metadata, _ = doc.get_metadata()
titre = doc.get_metadata_value("titre")
classe = doc.get_metadata_value("classe")

# Compiler le document
result, messages = doc.compile(mode="normal")

# Modifier une métadonnée
doc.set_metadata("version", "2.1")
doc.save()
```

## Contribution

Les contributions sont les bienvenues ! Consultez le guide [CONTRIBUTING.md](CONTRIBUTING.md) pour plus de détails.

## License

Ce projet est sous licence **GNU General Public License v3.0**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteur

### Emmanuel Bigeard

- Email : [s2i@bigeard.me](s2i@bigeard.me)
- Site : [s2i.bigeard.me](https://s2i.bigeard.me)
- GitHub : [@ebigeard](https://github.com/ebigeard)

## Remerciements

- [Raphaël Allais](https://allais.eu/), dont les packages LaTeX pour la SI m'ont servi de base pour la création d'`UPSTI_Document`
- Tous les collègues qui utilisent `UPSTI_Document` pour concevoir leurs documents pédagogiques (et qui ont eu la patience de lire mes documentations vaguement rédigées)
- Tous les collègues qui partagent leur travail sur des sites perso
- L'UPSTI et la communauté des enseignants de CPGE S2I

## Changelog

Voir [CHANGELOG.md](CHANGELOG.md) pour l'historique des versions.

## Support

- **Bugs report** : [GitHub Issues](https://github.com/ebigeard/pyUPSTIlatex/issues)
- **Discussions** : [GitHub Discussions](https://github.com/ebigeard/pyUPSTIlatex/discussions)
- **Documentation** : [Wiki](https://github.com/ebigeard/pyUPSTIlatex/wiki)
