# Personnalisation de pyUPSTIlatex (custom)

Ce dossier permet de personnaliser pyUPSTIlatex de trois manières :

1. **Surcharge de templates** : modifier les templates Jinja2
2. **Surcharge de classes** : étendre le comportement de `UPSTILatexDocument`
3. **Surcharge de la config/data** : modifier les définitions de `pyUPSTIlatex.json`

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

---

## 2. Surcharge de la classe UPSTILatexDocument

### Principe

Vous pouvez créer une classe personnalisée qui hérite de `UPSTILatexDocument` pour :

- Ajouter de nouvelles méthodes
- Modifier le comportement existant
- Implémenter des hooks de traitement
- Personnaliser les validations

### Installation

1. **Copiez le template** :

   ```bash
   cp custom/document.py.template custom/document.py
   ```

2. **Modifiez** `custom/document.py` selon vos besoins

3. **Utilisez** pyUPSTIlatex normalement :

   ```python
   from pyupstilatex import UPSTILatexDocument

   # Si custom/document.py existe, UPSTILatexDocument sera votre classe personnalisée
   doc = UPSTILatexDocument(source="fichier.tex")
   ```

### Structure requise

Votre fichier `custom/document.py` doit :

- Définir une classe nommée **exactement** `CustomUPSTILatexDocument`
- Hériter de `UPSTILatexDocument`
- Ne **pas** créer de `__init__.py` dans `custom/`

### Exemple simple

```python
from pyupstilatex.document import UPSTILatexDocument

class CustomUPSTILatexDocument(UPSTILatexDocument):
    """Ma classe personnalisée."""

    def compile(self, version="eleve", clean=False, output_dir=None):
        """Compilation avec log personnalisé."""
        self.msg.info(f"🚀 Compilation de {self.source}")
        super().compile(version=version, clean=clean, output_dir=output_dir)
        self.msg.success("✅ Terminé !")
```

### Désactivation

Pour revenir au comportement par défaut, supprimez ou renommez `custom/document.py`.

---

## 3. Configuration JSON

Le fichier `custom/pyUPSTIlatex.json` permet de surcharger la configuration par défaut avec deux opérations :

- `"remove"` : supprimer des clés de configuration
- `"create_or_modify"` : ajouter ou modifier des valeurs

Voir la documentation principale pour plus de détails.
