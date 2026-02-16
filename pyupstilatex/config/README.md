# Configuration de pyUPSTIlatex

Ce dossier contient les fichiers de configuration par défaut de pyUPSTIlatex.

## Architecture

```text
pyupstilatex/
├── config/
│   ├── pyUPSTIlatex.json      # Données de configuration (versionné)
│   └── config.default.toml    # Configuration par défaut (versionné)
├── custom/
│   ├── .env                    # Secrets (non versionné)
│   ├── .env.template           # Template pour les secrets
│   ├── config.toml             # Overrides locaux (non versionné)
│   ├── config.toml.template    # Template pour les overrides
│   └── pyUPSTIlatex.json       # Overrides des données de configuration (non versionné)
└── config.py                   # Chargement de la configuration
```

pyUPSTIlatex.json peut-être mis à jour avec `pyupstilatex update-config`

## Ordre de chargement

La configuration est chargée dans cet ordre (les valeurs suivantes écrasent les précédentes) :

1. **config.default.toml** : Valeurs par défaut versionnées
2. **custom/config.toml** : Overrides locaux (si existe)
3. **custom/.env** : Secrets et variables d'environnement

## Utilisation

### Dans votre code

```python
from pyupstilatex.config import load_config

cfg = load_config()
print(cfg.meta.auteur)                    # "Emmanuel BIGEARD"
print(cfg.compilation.latex_nombre_compilations)  # 2
print(cfg.ftp.host)                       # Depuis custom/.env
```

### Personnalisation

1. **Copier les templates** :

   ```bash
   cp custom/.env.template custom/.env
   cp custom/config.toml.template custom/config.toml
   ```

2. **Éditer custom/.env** avec vos secrets :

   ```dotenv
   FTP_USER=votre_utilisateur
   FTP_PASSWORD=votre_mot_de_passe
   SITE_SECRET_KEY=votre_clé_secrète
   ```

3. **Éditer custom/config.toml** avec vos overrides :

   ```toml
   [meta.default]
   auteur = "Votre Nom"
   variante = "votre-lycee"
   ```

## Format TOML

Le fichier TOML est structuré en sections :

- `[meta.default]` : Métadonnées par défaut des documents
- `[compilation.defaut]` : Paramètres de compilation
- `[compilation.latex]` : Paramètres LaTeX
- `[os.format]` : Formats de noms de fichiers
- `[os.suffixe]` : Suffixes pour les noms
- `[os.dossier]` : Arborescence des dossiers
- `[traitement_par_lot]` : Traitement par lot
- `[poly]` : Configuration des polys
- `[ftp]` : Configuration FTP
- `[site]` : Configuration du site web
- `[legacy]` : Compatibilité avec anciennes versions

## Notes

- Les fichiers `custom/.env` et `custom/config.toml` ne sont **jamais versionnés**
- Les templates (`.template`) sont versionnés pour faciliter la configuration initiale
- La rétrocompatibilité avec `.env` uniquement est maintenue
- Les variables d'environnement système prennent toujours le dessus sur les fichiers TOML
