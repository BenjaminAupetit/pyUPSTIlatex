# UPSTI_Document

> [!WARNING]
> La solution `UPSTI_Document` est vouée à être remplacée par `upsti-latex`, qui sera prêt j'espère en 2027.

## Kit de démarrage LaTeX

Ce dossier contient tous les fichiers distribués dans le **Kit de démarrage LaTeX** que j'ai diffusé :

- sur [mon site personnel](https://s2i.pinault-bigeard.com/ressources/latex/69-packages-latex-pour-les-sciences-de-l-ingenieur-upsti)
- sur le [site de l'UPSTI](https://www.upsti.fr/documents-pedagogiques/upsti-kit-de-demarrage-latex)

Je déposerai dans ce dossier leurs versions définitives d'ici fin 2026.

## Contenu de ce dossier

Ce dossier contient :

- un tutoriel d'installation de l'environnement de travail MiKTeX/Texmaker ;
- les packages `UPSTI_Document`, `UPSTI_SI`, `UPSTI_Pedagogique` et `UPSTI_Typographie` (chaque package étant fourni avec sa documentation) ;
- le dossier `UPSTIlatex` regroupant les images génériques utilisées par `UPSTI_Document` ;
- un squelette vierge de document tex basé sur `UPSTI_Document` ;
- quelques exemples de documents pédagogiques rédigés avec `UPSTI_Document` ;
- un fichier regroupant divers extraits de code (snippets) fréquemment utilisés, pour des copier/coller ;
- quelques packages rédigés par des collègues (avec leur documentation) ;
- le VBscript de compilation rapide des fichiers tex (pour générer les sujets et les corrigés en un seul clic) ;
- le script Python de migration EPB_Cours → UPSTI_Document ;
- un tutoriel d'installation d'AMC sous Windows (pour créer des QCM à correction automatique), permettant de rendre AMC entièrement fonctionnel en quelques clics.

Pour ce qui est de l'utilisation de LaTeX en général, internet regorge de ressources de qualité !

Tous ces documents, packages et autres scripts sont fournis tels quels... En espérant que les bugs ne soient pas trop nombreux... Pour toute question, n'hésitez pas à me contacter : [s2i@bigeard.me](s2i@bigeard.me)

## Installation rapide

1. Installer l'environnement MiKTeX/Texmaker (dossier « Installation environnement LaTeX »)
2. Copier le contenu du dossier `Packages` dans votre dossier de packages défini dans MiKTeX Settings (admin)
3. Copier le dossier `UPSTIlatex` à la racine de `C:\`
4. Ouvrir `UPSTI_Snippets.tex` et le compiler (ainsi que les autres fichiers exemples fournis dans ce kit)

Pour des informations détaillées, consulter la documentation dans le dossier « Documentation packages ».

## Changelog

- `1.1` — 23/02/2026 — Mise en ligne d'une version provisoire légèrement modifiée et non documentée, en attendant la version finale
- `1.0` — 23/11/2017 — Mise en ligne de la première version

## Remerciements

- Oriane AUBERT, Florent LE BOURHIS, Pierre MAUBORGNE et Rémi PONCHE pour leur(s) relecture(s) et tests ;
- Raphaël ALLAIS et Robert PAPANICOLA pour le partage de leurs packages.
