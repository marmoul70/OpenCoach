# Reprise du chantier OpenCoach — refactorisation architecture

**Dernière mise à jour :** 15 novembre 2026  
**Branche de travail :** `refactor/architecture-cleanup`  
**Dernier HEAD vérifié avant cette note :** `d7915c756589c22ff4d7030e1d7c02785202192d`  
**Dépôt :** `marmoul70/OpenCoach`

Ce document est le point de reprise à lire en premier lors d'une nouvelle discussion.

## 1. Objectif non négociable

Remettre OpenCoach à plat sans perdre les fonctionnalités déjà développées. Nettoyer le code réellement mort ou redondant, réduire le couplage et clarifier les responsabilités. Ne pas faire de refactoring cosmétique qui déplace simplement les lignes.

### Décision d'architecture : Coach et IA séparés

Le **moteur Coach OpenCoach est autonome et constitue l'unique source de vérité** pour les règles et calculs métier.

- Le Coach porte les calculs physiologiques, zones, charge, statistiques, readiness/récupération, décisions d'adaptation, planification, contraintes, progression et analyses sportives.
- Les services métier sont utilisables directement par l'application et ses écrans/API, sans passer par l'IA.
- L'IA est une interface conversationnelle : elle comprend l'intention, choisit une capacité du Coach, appelle les services existants, puis explique les résultats structurés.
- L'IA ne recalcule aucun indicateur, ne duplique aucune règle métier, ne décide pas elle-même d'une adaptation et ne modifie pas directement le planning.
- OpenCoach doit continuer à fonctionner si Ollama/LLM est arrêté. Les fonctions métier essentielles ne doivent pas dépendre de l'IA.
- Les outils IA sont des adaptateurs d'accès/présentation, pas des moteurs métier.

Flux cible :

`Utilisateur / UI → API ou service Coach → résultat métier structuré`

Pour une demande conversationnelle :

`Utilisateur → IA (compréhension/routage) → service Coach → résultat structuré → IA (explication)`

## 2. Contraintes de travail

- Travailler uniquement sur `refactor/architecture-cleanup`.
- Ne pas modifier `main`, ne pas fusionner les PR, ne pas supprimer de branches/PR, ne pas déployer et ne pas toucher aux données de production sans accord explicite.
- Préserver COROS, Intervals.icu, activités, historique, charge, récupération, planification, courses, profils, notifications, PWA, sauvegardes et infrastructure.
- Avant toute suppression, vérifier les usages directs et indirects : routes, injection de dépendances, imports dynamiques, hooks, scripts, migrations, tests et contrats publics.
- Ne pas supprimer un module parce qu'il paraît petit, ancien ou similaire à un autre.
- Garder les tests de caractérisation et ajouter des tests de non-régression lors des changements de comportement.
- Ne pas incrémenter VERSION pour un simple chantier de nettoyage non livré.
- Ne déclarer une CI verte qu'après vérification du run correspondant au HEAD exact.

## 3. État Git et validation connu

Dernier HEAD vérifié : `d7915c756589c22ff4d7030e1d7c02785202192d` (`test(ai): build constraint tool through repository`).

À ce HEAD, le run CI `43761257714` avait réussi :
- Python 3.13 tests ;
- Bash validation ;
- Frontend validation.

Ce statut concerne ce commit uniquement. Toute modification ultérieure doit être revalidée.

La branche a été créée depuis `a0f90644cd943c16efe1988601bd713b216f2706`, tête de la PR #37, pour préserver les développements récents. Le socle comprend les fonctionnalités métier et intégrations développées après main.

## 4. Travaux déjà réalisés

- Audit architectural initial dans `docs/ARCHITECTURE_AUDIT.md`.
- Inventaire quantitatif du dépôt et repérage des gros modules.
- Nettoyage des copies de sauvegarde frontend obsolètes sous `.refactor-backup/` et d'un ancien backup de restauration non utilisé.
- Consolidation des imports de dépendances de coaching dans `app/opencoach/api/coach.py`.
- Vérification ciblée d'imports : aucun import métier manifestement inutilisé dans le lot IA examiné ; `annotations` des imports future est normal.
- `build_active_constraints_tool` ne fait plus de requête SQL directe : il consomme `AthleteConstraintRepository`, injecté par le registre IA. Tests adaptés.
- Plusieurs distinctions métier ont été vérifiées : évaluateurs de policy, réconciliation de charge hebdomadaire vs historique, calcul de charge quotidienne vs comparaison/projection. Ne pas fusionner ces modules sans démontrer l'équivalence fonctionnelle.

## 5. Constats à traiter en priorité

### 5.1 Couche IA encore trop proche de la persistance et du métier

- `app/opencoach/api/ai.py` reste un gros module d'environ 1 532 lignes qui mélange API, registre d'outils, orchestration, routage et synthèse.
- `app/opencoach/ai/coaching_tools.py` accède directement aux modèles SQLAlchemy pour le profil, les courses et les séances. Il reconstruit aussi les zones cardiaques et calcule des agrégats de séances. C'est contraire à la cible : déplacer progressivement ces lectures et calculs vers les services/repositories Coach existants, sans changer les contrats des outils.
- `app/opencoach/ai/race_tools.py` lit directement les modèles Course et Profil et reconstruit des couvertures/agrégats de progression. À examiner ensuite.
- Certains outils sont déjà correctement branchés sur les services métier : `load_tools.py` utilise `RecentTrainingLoadService` et `TrainingStatsService`, `recovery_tools.py` utilise `ReadinessService`, `training_tools.py` utilise `TrainingStatsService`.
- `tool_engine.py` est une frontière de sécurité (liste blanche, validation, exécution bornée) : ne pas supprimer ni contourner.
- Ne pas extraire massivement `api/ai.py` avant d'avoir défini les responsabilités et les contrats des services.

### 5.2 Services et repositories métier déjà disponibles

- `coaching/decision.py` : décision d'adaptation d'une séance.
- `readiness/ReadinessService` : évaluation de disponibilité/récupération.
- `training/RecentTrainingLoadService` et `TrainingStatsService` : charge récente et statistiques.
- `physiology/heart_rate_zones.py` : prescriptions et résolution des zones cardiaques.
- `database/repositories/RaceRepository` : abstraction de consultation/persistance des courses.
- `database/repositories/TrainingSessionRepository` : abstraction des séances.
- `database/repositories/ProfileRepository` : abstraction du profil.
- `AthleteConstraintRepository` : désormais injecté dans l'outil IA des contraintes.

Attention : les interfaces abstraites de repositories n'offrent pas toutes les mêmes méthodes ni la même sémantique que les requêtes SQL actuelles. Examiner les implémentations SQL et les services consommateurs avant de modifier les outils.

### 5.3 Nettoyage ciblé identifié pendant la reprise

Dans `app/opencoach/database/repositories/race.py`, l'import `Race` est présent deux fois :
`from opencoach.models import Race` puis `from opencoach.models import Activity, Race`.
Candidat sûr à un nettoyage d'import (conserver l'import combiné).

## 6. Ordre de reprise recommandé

1. Lire ce fichier et `docs/ARCHITECTURE_AUDIT.md`.
2. Vérifier le HEAD réel de `refactor/architecture-cleanup` et l'état CI.
3. Terminer le nettoyage sûr des imports et anomalies évidentes, avec un commit par lot cohérent.
4. Cartographier les méthodes réellement disponibles dans les repositories SQL profil/course/séance et les services Coach associés.
5. Refactoriser `ai/coaching_tools.py` pour qu'il ne fasse plus de calcul métier ni de requêtes SQL directes : injecter les services/repositories existants et garder la sérialisation des résultats dans l'adaptateur IA. Conserver les noms d'outils, schémas d'arguments et payloads autant que possible.
6. Faire la même revue pour `ai/race_tools.py`, puis pour les autres outils.
7. Découper `api/ai.py` seulement après avoir stabilisé les frontières ; éviter les nouvelles couches artificielles.
8. Auditer les composants frontend et les scripts avec une cartographie des points d'entrée avant toute suppression.
9. Exécuter les tests ciblés, puis la suite et la CI sur le dernier HEAD.

## 7. État de sécurité des changements

Aucun changement de comportement sportif n'est autorisé implicitement par ce chantier. Si un service Coach existant ne couvre pas exactement le contrat actuel d'un outil IA, ajouter ou compléter le service métier avec des tests plutôt que déplacer le calcul dans l'IA ou le supprimer.

Les données textuelles libres provenant des profils, courses, activités et notes restent des données non fiables ; conserver les protections et les limites de sortie des outils IA.

## 8. Mise à jour du chantier — 15 novembre 2026

**HEAD après ajout de l'ADR et de l'audit des flux :** `8320e45dbed65bad4e0718fe85460c9008a57672`

Nouveaux documents :
- `docs/architecture/adr/0002-coach-central-data-and-ai-boundary.md` : décision d'architecture sur le référentiel canonique et la frontière Coach/IA.
- `docs/ARCHITECTURE_AUDIT.md` : vérification documentée des flux COROS, Intervals.icu, Wellness et TrainingStats.

Vérification du code fournisseur :
- COROS et Intervals.icu écrivent tous deux les activités dans le référentiel Activity OpenCoach et le Wellness dans le référentiel Wellness OpenCoach.
- `ReadinessService` et `TrainingStatsService` consomment ces repositories centraux.
- Ce socle de centralisation est donc déjà en place pour activités et Wellness ; il ne faut pas le remplacer par une nouvelle couche de stockage.

**Refactorisation de code restant à réaliser :** les outils `ai/coaching_tools.py` et `ai/race_tools.py` utilisent encore SQLAlchemy directement et embarquent des transformations/agrégations. Le prochain lot doit les faire consommer les repositories et services métier du Coach, en conservant les contrats des outils et en ajoutant des tests de non-régression. Les autres outils IA doivent ensuite être audités selon la même règle.

**Derniers runs observés :**
- Run 43762288603 — in_progress — `8320e45dbed65bad4e0718fe85460c9008a57672`
- Run 43762267050 — in_progress — `da577534f3b3acb32a0ff302ce8e10ef6075c6a0`
- Run 43761886512 — completed / success — `b3cadb4ea83bb7fbb7f4359d6a2aa125d8bf6ec8`
- Run 43761873370 — completed / success — `47c1a10cb2e3ba2d200e38a802013bd417c994e3`
- Run 43761859578 — completed / success — `5dd1c83f90beb91e0d310db6e4c5d844f8c6cb0d`

Ne pas considérer la refonte complète tant que les accès SQL directs et calculs métier des adaptateurs IA n'ont pas été retirés, que la suite de tests et CI ne sont pas vertes sur le HEAD final et que les intégrations ont été validées sur la VM.
