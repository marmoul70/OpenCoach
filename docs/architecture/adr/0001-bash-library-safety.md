# ADR 0001 — Sécurité et comportement des bibliothèques Bash

- **Statut :** Accepté
- **Date :** 2026-08-08

## Contexte

OpenCoach utilise des bibliothèques Bash partagées par plusieurs
scripts d'installation et de maintenance.

Ces bibliothèques sont chargées avec `source`.

Une bibliothèque Bash modifie potentiellement l'environnement du shell
qui la charge. L'utilisation directe de `set -Eeuo pipefail` dans une
bibliothèque peut donc modifier le comportement du script appelant.

## Décision

Les bibliothèques Bash OpenCoach doivent être conçues pour être
sourcées sans provoquer d'effet de bord inattendu dans le shell appelant.

Les options Bash globales seront configurées au niveau des scripts
exécutables, et non automatiquement dans les bibliothèques partagées,
sauf décision contraire documentée.

Les bibliothèques doivent également pouvoir être chargées plusieurs fois
sans provoquer d'erreur.

## Conséquences

Les scripts exécutables OpenCoach utiliseront une politique stricte
Bash adaptée à leur rôle.

Les bibliothèques devront rester aussi prévisibles et autonomes que
possible.

Cette décision pourra être réévaluée si une bibliothèque nécessite
explicitement une autre stratégie.