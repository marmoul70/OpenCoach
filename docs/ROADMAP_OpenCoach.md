# OpenCoach — Feuille de route et état du projet

> Document de référence — mise à jour : 12 août 2026

## 1. Vision du projet

OpenCoach est un coach sportif open source, modulaire et configurable, destiné en priorité au trail.

Architecture fonctionnelle cible :

Suunto Cloud → synchronisation → Raspberry Pi 3 → SQLite → analyse fatigue/progression → calcul de charge → planification → moteur IA → Telegram / interface Web.

Le projet est prévu sous licence MIT et doit rester modulaire, configurable et maintenable.

## 2. Principes de développement

- Architecture modulaire.
- Configuration centralisée.
- Open source / licence MIT.
- Code propre et maintenable selon les standards 2026.
- Documentation en français.
- ADR pour les décisions d'architecture importantes.
- Tests et validation à chaque étape.
- Scripts reproductibles pour installation, développement et maintenance.
- Le développement se fait en binôme : l'assistant intervient comme partenaire technique/architecte et le développeur conserve la maîtrise des changements.

## 3. Environnement actuel

- Hyperviseur : Proxmox.
- Environnement de développement actuel : VM Debian 13.
- RAM VM : 8 Go.
- Poste de développement : Windows.
- Accès prévu : VS Code / environnement distant.
- Déploiement cible à terme : Raspberry Pi 3.
- Base de données cible : SQLite.
- Dépôt GitHub : `marmoul70/OpenCoach`.
- Le dépôt est maintenant public.
- Licence : MIT.

## 4. Architecture cible

### Source de données

Suunto Cloud fournit les données d'activité et d'entraînement.

### Backend / moteur OpenCoach

Le Raspberry Pi héberge progressivement :

1. ingestion et synchronisation Suunto ;
2. stockage SQLite ;
3. analyse de fatigue ;
4. analyse de progression ;
5. calcul de charge d'entraînement ;
6. planification ;
7. moteur IA ;
8. API/services internes.

### Interfaces

- Telegram pour le coaching quotidien.
- Interface Web pour la synthèse, le suivi et le dialogue.
- Une interface multiplateforme pourra ensuite être développée, avec Flutter envisagé et Windows comme première cible.

## 5. État des travaux

### Socle projet

Le dépôt contient notamment :

```text
backend/
docs/
frontend/
infra/
scripts/
  bootstrap/
  dev/
  maintenance/
tests/
README.md
LICENSE
.gitignore
```

Le socle Git/GitHub et la structure initiale ont été réalisés.

### Bootstrap / environnement

La série T0.7 a progressivement construit et fiabilisé :

- détection de Debian ;
- validation de Debian 13 ;
- détection des commandes requises ;
- gestion d'APT ;
- liste centralisée des paquets ;
- détection des paquets manquants ;
- détection des paquets disponibles/installables ;
- installation contrôlée ;
- validation après installation ;
- gestion des privilèges pour `--install` ;
- codes de sortie standardisés ;
- validation finale de l'environnement ;
- contrôles Bash/ShellCheck ;
- tests de bibliothèques ;
- contrôles Git et `git diff --check`.

Les fichiers importants de cette couche sont notamment :

```text
scripts/bootstrap/check-environment.sh
scripts/lib/dependencies.sh
scripts/lib/packages.sh
scripts/lib/package-manager.sh
scripts/lib/exit-codes.sh
```

### Corrections récentes

Une autre analyse du dépôt public a été réalisée dans une conversation séparée. Elle a permis de :

- relire le code existant ;
- corriger certains bugs ;
- installer des paquets nécessaires ;
- ajouter/renforcer des tests de vérification.

Ces modifications doivent être considérées comme faisant partie de l'état réel du dépôt et doivent être vérifiées avant toute nouvelle modification.

### Dernier état connu

Les missions T0.7.x ont été validées progressivement jusqu'à T0.7.14 dans notre suivi de conversation.

Une tentative de démarrage de T0.7.15 a ensuite été faite, mais elle ne doit pas être considérée comme terminée : nous avons constaté que le suivi des missions n'était plus suffisamment fiable.

**Règle de reprise : ne pas inventer l'état d'une mission. Vérifier Git, les tests et les fichiers réellement présents avant de poursuivre.**

## 6. État technique du bootstrap

Le bootstrap dispose maintenant d'une logique séparée entre :

- définition des dépendances ;
- définition des paquets ;
- fonctions de gestionnaire de paquets ;
- codes de sortie ;
- vérification globale de l'environnement ;
- installation des paquets ;
- validation finale.

Le point d'attention historique principal a été la contamination des fichiers Bash par des artefacts Markdown (`\_`, `\*`, blocs ```), qui a provoqué plusieurs erreurs de syntaxe.

**À ne plus reproduire :** les fichiers Bash doivent toujours être fournis sous forme de code brut exploitable, sans artefacts Markdown à l'intérieur du fichier.

Autre problème rencontré : certaines variables de codes de sortie ou de paquets avaient été déclarées `readonly` puis redéfinies lors d'un `source`. La stratégie actuelle doit donc préserver l'idempotence des fichiers de bibliothèque lorsqu'ils sont chargés.

## 7. Roadmap globale

### Phase 0 — Socle et bootstrap

Objectif : disposer d'un environnement reproductible et contrôlé.

- structure du dépôt ;
- Git/GitHub ;
- documentation initiale ;
- scripts bootstrap ;
- dépendances ;
- gestion APT ;
- codes de sortie ;
- tests ;
- ShellCheck ;
- validation CI.

**État : largement réalisé.**

### Phase 1 — Socle backend

Objectif : construire le service OpenCoach.

À réaliser :

1. définir l'architecture backend ;
2. définir la configuration ;
3. définir les modèles de données ;
4. mettre en place SQLite ;
5. créer les migrations/initialisation ;
6. créer les services métier ;
7. créer une API interne propre ;
8. mettre en place les tests unitaires et d'intégration.

### Phase 2 — Ingestion Suunto

Objectif : récupérer et normaliser les données d'entraînement.

À définir précisément :

1. méthode d'accès aux données Suunto ;
2. authentification/jetons ;
3. synchronisation incrémentale ;
4. gestion des doublons ;
5. normalisation ;
6. stockage SQLite ;
7. journalisation ;
8. gestion des erreurs et reprises.

### Phase 3 — Moteur d'analyse

Objectif : transformer les données brutes en indicateurs utiles.

Sous-modules :

- charge d'entraînement ;
- fatigue ;
- progression ;
- historique ;
- tendances ;
- indicateurs spécifiques trail.

Les formules devront être documentées et testées avant intégration au moteur IA.

### Phase 4 — Planification

Objectif : générer un entraînement adapté.

Le moteur devra prendre en compte :

- historique ;
- charge récente ;
- fatigue ;
- progression ;
- objectifs ;
- contraintes ;
- disponibilité ;
- type de séance ;
- spécificités trail.

Le moteur devra être déterministe et testable avant d'ajouter la couche IA.

### Phase 5 — Moteur IA

Objectif : ajouter l'intelligence conversationnelle/adaptative.

L'IA ne doit pas remplacer les calculs métier fondamentaux.

Architecture recommandée :

```text
Données → règles/calculs fiables → contexte structuré → IA → recommandation
```

L'IA interprète et explique les données ; les métriques critiques restent calculées par le backend.

### Phase 6 — Telegram

Objectif : fournir le coaching quotidien.

Fonctions :

- message quotidien ;
- résumé de séance ;
- recommandation ;
- retour utilisateur ;
- adaptation ;
- alertes utiles.

### Phase 7 — Interface Web

Objectif : visualiser l'état du sportif et dialoguer avec OpenCoach.

Premières fonctions :

- tableau de bord ;
- charge ;
- fatigue ;
- progression ;
- calendrier ;
- séances ;
- objectifs ;
- dialogue avec le coach.

### Phase 8 — Interface multiplateforme

Flutter pourra être utilisé pour une interface multiplateforme lorsque l'API et le backend seront suffisamment stables.

Première cible envisagée : Windows.

## 8. Ordre de priorité

L'ordre de construction doit rester :

```text
Infrastructure
    ↓
Backend
    ↓
SQLite / modèle de données
    ↓
Ingestion Suunto
    ↓
Calculs charge/fatigue/progression
    ↓
Planification
    ↓
IA
    ↓
Telegram
    ↓
Interface Web
    ↓
Flutter / multiplateforme
```

Il faut éviter de développer l'interface ou l'IA avant que les données et les calculs métier soient fiables.

## 9. Méthode de travail pour les prochaines missions

Chaque mission doit comporter :

- objectif ;
- prérequis ;
- F01, F02, etc. ;
- fichiers concernés ;
- modifications exactes ;
- tests ;
- résultat attendu ;
- validation ;
- commit Git ;
- mise à jour de cette feuille de route.

Pour limiter les échanges, les fonctionnalités pourront être données par groupes de deux : **F01 + F02**, puis **F03 + F04**, comme demandé.

## 10. Règle de validation

Une mission n'est considérée comme terminée que lorsque :

```text
Code
 ↓
Syntaxe
 ↓
Tests
 ↓
ShellCheck si applicable
 ↓
git diff --check
 ↓
Git commit
 ↓
git push
 ↓
Dépôt propre
```

Le simple fait qu'une commande fonctionne ponctuellement ne suffit pas à clôturer une mission.

## 11. Prochaine étape

Avant de reprendre T0.7.15 ou de créer une nouvelle mission :

1. récupérer l'état réel du dépôt public ;
2. examiner les derniers commits ;
3. examiner les fichiers modifiés ;
4. exécuter/identifier les tests existants ;
5. vérifier les scripts récemment ajoutés par l'autre analyse ;
6. comparer l'état réel avec cette feuille de route ;
7. produire un **état d'avancement réel** ;
8. seulement ensuite définir la prochaine mission.

**T0.7.15 ne doit donc pas être poursuivie à l'aveugle.**

## 12. Objectif final

OpenCoach doit devenir un coach trail personnel capable de :

```text
Suunto
  ↓
Données d'entraînement
  ↓
Historique SQLite
  ↓
Charge / fatigue / progression
  ↓
Analyse
  ↓
Plan d'entraînement
  ↓
Moteur IA
  ↓
┌───────────────┬───────────────┐
│   Telegram    │ Interface Web │
└───────────────┴───────────────┘
```

Le projet doit rester :

- open source ;
- modulaire ;
- configurable ;
- testable ;
- documenté en français ;
- déployable sur Raspberry Pi 3 ;
- extensible vers plusieurs interfaces.
