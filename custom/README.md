# Templates personnalisés (custom)

Ce dossier permet de surcharger les templates par défaut de pyUPSTIlatex.

## Fonctionnement

Lorsque pyUPSTIlatex cherche un template, il le recherche **d'abord dans ce dossier `custom/templates/`**. Si le fichier n'existe pas ici, il utilise celui du dossier `templates/` par défaut.

## Structure

Conservez la même structure de sous-dossiers que dans `templates/` :

```text
custom/
└── templates/
    ├── yaml/
    │   ├── poly.yaml.j2
    │   └── ...
    ├── latex/
    │   └── ...
    └── ...
```

## Utilisation

1. **Copiez** le template que vous souhaitez modifier depuis `templates/` vers `custom/templates/` en conservant le chemin relatif.
2. **Modifiez** le fichier copié selon vos besoins.
3. pyUPSTIlatex utilisera automatiquement votre version personnalisée.

## Exemple

Pour personnaliser le template YAML des polys :

```bash
# Copier le template par défaut
cp templates/yaml/poly_config.yaml.j2 custom/templates/yaml/poly_config.yaml.j2

# Modifier le fichier copié
# Les modifications seront automatiquement utilisées
```

## Remarques

- Les sous-dossiers de `custom/` doivent être **exclus du contrôle de version** (ajoutez-le à `.gitignore`).
- Vous pouvez ainsi personnaliser vos templates sans risquer de perdre vos modifications lors des mises à jour.
- Si vous supprimez un fichier de `custom/templates/`, pyUPSTIlatex reviendra automatiquement au template par défaut.
