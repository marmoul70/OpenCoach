# Reprise du chantier OpenCoach — refactorisation architecture

**Dernière mise à jour :** 15 novembre 2026  
**Branche de travail :** `refactor/architecture-cleanup`  
**HEAD de travail au 15 novembre 2026 :** `e87f413e782df882dd64d2a03370d81bdbcbc422`  
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


## 9. Mise à jour du chantier — refactor Coach/IA

**HEAD de travail :** `e87f413e782df882dd64d2a03370d81bdbcbc422`  
**Branche :** `refactor/architecture-cleanup`

### Modifications poussées sur la branche

- `services/training_profile_context.py` : le service Coach construit désormais le contexte physiologique, les zones cardiaques, les champs manquants et les capacités hebdomadaires. `ai/coaching_tools.py` ne reconstruit plus les objets physiologiques et délègue au service.
- `services/race_preparation.py` : l'analyse de préparation d'une course est déplacée hors de l'adaptateur IA. Le service utilise `RaceRepository`, `ProfileService` et `TrainingStatsService`; `ai/race_tools.py` conserve le schéma d'arguments et délègue au service.
- `services/planned_training.py` : la consultation des séances, les agrégats de durée/distance/D+ et la sélection de la prochaine séance planifiée sont centralisés dans le Coach.
- Le registre de `api/ai.py` injecte ces services avec l'identifiant de l'athlète provenant du contexte authentifié.
- Les tests de contrats existants `test_ai_coaching_tools.py` et `test_ai_race_tools.py` ont été adaptés aux nouveaux points d'injection. Les assertions de résultats et de cloisonnement par athlète sont conservées.

### Frontière obtenue

Les adaptateurs `ai/race_tools.py` et les outils de profil/planning dans `ai/coaching_tools.py` ne contiennent plus les calculs métier déplacés et ne font aucune requête SQLAlchemy directe. Ils restent responsables de la validation des arguments, de l'appel du service et de la sérialisation limitée destinée au modèle.

### Points restant à traiter

1. `ai/execution_tools.py` construit encore des repositories SQL à partir d'une `Session` dans l'adaptateur. Déplacer l'orchestration de lecture et le débrief métier dans un service Coach dédié, puis injecter ce service.
2. `ai/data_collection_tools.py` porte la validation de preuve conversationnelle (qui doit rester côté adaptateur) mais appelle directement la persistance des propositions avec une `Session`. Introduire une frontière de service applicatif pour la création de proposition.
3. Auditer les agrégations/états de couverture dans `ai/load_tools.py`, `ai/trend_tools.py` et `ai/recovery_tools.py`. Conserver les règles de couverture et les sémantiques de données manquantes ; les déplacer vers les services Coach lorsque ce sont des règles métier, pas lorsqu'il s'agit seulement de formatage du contexte LLM.
4. Découper `api/ai.py` (API, registre, orchestration, prompts, préférences et propositions) après stabilisation des contrats des services.
5. Refaire un audit global des usages et du code mort sur backend, frontend, scripts, infrastructure, migrations et CI. Aucune suppression supplémentaire ne doit être faite sur une simple intuition.
6. Ajouter des tests unitaires directs pour les nouveaux services, en complément des tests de contrat des adaptateurs.
7. Exécuter la suite complète, le lint/build frontend et la CI sur le HEAD final.

### Validation de ce lot

- Les modifications sont commitées sur `refactor/architecture-cleanup`, pas sur `main`.
- Les appels GitHub de statut combiné et de runs de workflow n'ont retourné aucun statut/run consultable pour le HEAD `e87f413...`. Cela ne prouve ni un succès ni un échec de CI.
- Aucun test Python, lint ou build frontend n'a été exécuté dans un environnement de checkout pendant ce lot. Ne pas présenter la branche comme validée ou prête au déploiement avant ces contrôles.
- Le workflow `.github/workflows/ci.yml` déclenche bien sur les pushes de branches `refactor/**`, mais le connecteur utilisé ici ne fournit pas la liste générale des runs de push.

Le prochain lot doit poursuivre le déplacement des responsabilités métier vers le Coach, puis réaliser l'audit frontend/scripts/infrastructure. Ne pas fusionner, rebaser sur `main`, supprimer de branche ou incrémenter `VERSION` dans ce chantier.


## 10. Règle de non-duplication et état du refactoring — 15 novembre 2026

**Branche de travail :** `refactor/architecture-cleanup`  
**HEAD validé à ce point :** `b65ac998e27337c8106035fbf526732633d61ba1`  
**État de `main` :** `58b962292bdcb134f6e693befa24006f8b5c5136` (restauré à son HEAD antérieur après une écriture GitHub mal ciblée ; les changements du chantier sont réappliqués sur la branche dédiée).

### Règle impérative pour les prochains lots

Avant tout ajout ou modification du Coach :

1. Rechercher la capacité par responsabilité, pas uniquement par nom de classe.
2. Cartographier les services, méthodes, repositories, routes et tests qui la couvrent déjà.
3. Réutiliser la fonction existante si elle répond au besoin.
4. Si une règle manque, étendre la fonction ou le service existant et conserver ses contrats.
5. Ne créer une nouvelle classe/service que si aucun point d'extension existant n'est cohérent ; documenter alors pourquoi les services existants ne conviennent pas.
6. Ajouter des tests de caractérisation et de non-régression avant de considérer le déplacement terminé.

### Modifications validées sur la branche

- Suppression de `TrainingProfileContextService`, qui n'était qu'un wrapper de `ProfileService`. La méthode `ProfileService.build_training_context()` étend désormais le service déjà présent.
- `RacePreparationService` réutilise maintenant les compteurs canoniques de `TrainingStatsService.calculate()` pour le nombre de séances et la couverture des métriques. Il ne relit plus les repositories et ne recalcule plus ces compteurs.
- `TrainingStats.coverage()` centralise les statuts `no_sessions`, `unavailable`, `partial` et `complete`. Les outils charge, tendances et préparation de course réutilisent cette règle.
- `TrainingStats.compare_to()` centralise les comparaisons de périodes et masque les deltas lorsque l'une des périodes a une couverture incomplète. `ai/trend_tools.py` ne calcule plus les deltas.
- `RecentTrainingLoad.planned_sessions_count` centralise le comptage des séances prescrites ; l'adaptateur charge ne le recalcule plus.
- Les outils d'exécution utilisent les repositories injectés et le moteur existant `analyze_session_execution`. Les outils profil/planning et course délèguent leurs traitements métier aux services.
- Les tests utilisent désormais les modèles Coach réels pour les statistiques plutôt que des objets simplifiés qui ne reflétaient pas les contrats réels.

### Justification des services spécifiques conservés

- `RacePreparationService` : capacité spécifique d'analyse d'une course future à partir de son profil de parcours, du profil athlète et des statistiques récentes. L'audit n'a pas trouvé de service existant couvrant ce cas ; les statistiques restent déléguées à `TrainingStatsService`.
- `PlannedTrainingService` : consultation et synthèse des séances planifiées, distinctes des statistiques d'entraînement réalisé. L'audit a trouvé le repository et les routes de séances, mais pas de service Coach existant qui porte les agrégats de séances planifiées et la sélection de la prochaine séance.

### Résultats CI

- Commit `6f746a6ba7a57d4e1d31838a534896f07d6cab35` : Python, Bash et frontend validés.
- Commit `d46615d2c55768f285cafc803c7acbaaf7b5d740` : Python, Bash et frontend validés.
- Commit `b65ac998e27337c8106035fbf526732633d61ba1` : Python 3.13 **3 139 tests passés**, Bash validé et frontend validé.
- Les runs intermédiaires en échec correspondent à des commits partiels qui ont été corrigés ensuite ; ils ne représentent pas le HEAD de travail actuel.
- La CI du HEAD suivant les ajouts de documentation devra être vérifiée avant de déclarer ce point stable.

### Audit restant

- `app/opencoach/ai/data_proposals.py` contient encore la persistance SQL des propositions de données de profil (création, consultation, confirmation, rejet). C'est le principal écart restant à examiner dans la frontière IA/application. Réutiliser le cycle existant et ses règles ; ne pas réécrire le workflow ni dupliquer les validations.
- Auditer les agrégations de `activity_tools.py` et les éventuels helpers existants de résumé des streams avant tout déplacement.
- Découper `api/ai.py` après stabilisation des contrats et de la composition des services.
- Continuer l'audit global frontend, scripts, infrastructure, imports dynamiques, dépendances, migrations et code mort.
- Refaire une suite CI complète sur le HEAD final de la branche.

Ne pas fusionner, rebaser sur `main`, supprimer de branche, déployer ou incrémenter `VERSION` sans accord explicite.


## 11. Suite du refactoring IA et réutilisation des primitives Coach

**HEAD validé :** `7a2ff3161dfece35249d3f09b6db3a242e8ec303`

### Découpage de l'API IA

- Le contenu de l'ancien `get_ai_tool_registry` a été déplacé vers `ai/registry.py`. L'API conserve uniquement la fonction de dépendances HTTP qui délègue au constructeur du registre. Les repositories communs (activité, détails, séances) sont créés une seule fois et réutilisés.
- Les prompts système et leur construction sont dans `ai/prompts.py`.
- Les contrats de conversation et de préférences sont dans `ai/schemas.py`.
- Les fonctions de synthèse, de contrôle de qualité, de garde-fous et de sérialisation sont dans `ai/response_synthesis.py`.
- `api/ai.py` passe d'environ 1 530 lignes à environ 700 lignes ; les routes HTTP et l'orchestration de la requête restent dans l'API, sans déplacer les calculs métier dans le LLM.
- Les noms importés dans `api/ai.py` sont conservés lorsque nécessaire pour préserver les contrats de tests existants.

### Nouvelle réutilisation de primitives existantes

- L'audit de `activity_tools.py` a trouvé `_number` dans `training/session_execution/stream_analysis.py`, qui appliquait déjà la validation des échantillons numériques finis.
- Cette normalisation est maintenant portée par `normalize_stream_number` dans le modèle `ActivityStream` et réutilisée par l'analyse temporelle existante.
- Le résumé min/max/moyenne est une propriété `ActivityStream.summary`. L'adaptateur IA ne recalcule plus ces agrégats ; il sérialise la propriété du modèle Coach.
- Tests ajoutés pour les échantillons manquants, booléens, NaN et infinis, ainsi que pour un stream vide.

### Validation CI du HEAD

- Commit : `7a2ff3161dfece35249d3f09b6db3a242e8ec303`
- Python 3.13 : **3 141 tests passés**, 2 avertissements de dépendances.
- Bash validation : succès.
- Frontend lint et build : succès.

### Prochaines vérifications

1. `ai/data_proposals.py` contient toujours le cycle de persistance SQL des propositions de profil. C'est un workflow applicatif existant : conserver ses validations et son contrat, rechercher les repositories/services existants avant de déplacer quoi que ce soit, et ne pas réécrire le workflow.
2. Continuer la réduction de `api/ai.py` seulement après audit des responsabilités restantes. `AIService` est la façade du fournisseur LLM ; `CoachDecisionService` porte la décision d'entraînement quotidienne. Ne pas les détourner pour y placer une orchestration conversationnelle qui ne leur appartient pas.
3. Achever l'audit du code mort et des dépendances sur backend, frontend, scripts et infrastructure ; chaque suppression doit être justifiée par les usages et imports dynamiques.
4. Vérifier les contrats d'API et les parcours frontend après les extractions.
5. Relancer la CI sur le HEAD final avant la recette.

La règle de non-duplication de la section 10 reste impérative. Aucun merge, déploiement, suppression de branche ou incrément de version n'est autorisé dans ce chantier.


## 12. Déplacement des propositions de données vers le Coach — 16 novembre 2026

**Commit :** `c6f79c5f57684b9c4675c7bfdeec027005a160d8`

- Le cycle de proposition/confirmation a été déplacé de `ai/data_proposals.py` vers `coaching/profile_data_proposals.py`. L'ancien module IA ne contient plus qu'un shim de compatibilité ; l'API et l'outil IA importent directement le module Coach.
- Les modifications confirmées du profil passent maintenant par `ProfileService` et `SqlProfileRepository`. Les champs physiques, physiologiques, d'entraînement et de nutrition utilisent les sections du modèle domaine `AthleteProfile`, au lieu de modifier directement les colonnes SQL.
- Les équipements chaussure/vélo/montre sont ajoutés au modèle `AthleteProfile.equipment`, puis persistés par le mécanisme canonique de synchronisation de `SqlProfileRepository`. La détection des doublons compare les équipements du profil domaine ; aucune seconde implémentation SQL d'inventaire matériel n'est conservée.
- Les check-ins passent par `AthleteDailyCheckIn` et `SqlDailyCheckInRepository`. Le statut de proposition est modifié dans la même session avant l'appel du repository, qui valide la transaction.
- Les validations, l'isolation par profil, l'expiration à 15 minutes, la détection de conflit, la déduplication des propositions en attente et la confirmation explicite sont conservées.
- `ProfileService.build_training_context()` reste l'unique exposition des repères nutritionnels (glucides, hydratation, sodium) au Coach. La politique de cycles reste `planning/trajectory/load_recovery_cycle.py` ; aucun cycle parallèle n'a été ajouté.
- Tests complets : **3 141 passed**, 2 avertissements ; Bash, ShellCheck, bootstrap Debian 13, lint et build frontend validés sur le commit.

La suite de l'audit doit encore vérifier les responsabilités restantes des adaptateurs IA, les accès SQL directs, puis les domaines frontend, scripts, infrastructure, migrations et imports dynamiques. Ce lot ne certifie pas encore l'absence globale de code mort ou de doublons.


## 13. Déplacement de la sérialisation Readiness hors des adaptateurs IA

Le résultat Readiness et ses avertissements sont désormais sérialisés par `readiness_assessment_to_dict()` dans le domaine `opencoach.readiness`. L'adaptateur `ai/recovery_tools.py` se limite à appeler `ReadinessService.calculate()`, traiter l'indisponibilité technique prévue et transmettre le résultat domaine. Les règles de fraîcheur, de fiabilité des baselines et les avertissements ne sont plus reconstruits dans l'IA.

Ce déplacement réutilise le moteur Readiness et son assessment existants ; aucun second service ni calcul n'a été ajouté. La suite ciblée `tests/test_ai_recovery_tools.py` doit confirmer la préservation du contrat de l'outil.



## État de reprise — 16 novembre 2026

Les refactors récents ont déplacé plusieurs responsabilités vers les capacités Coach existantes : statistiques et tendances, charge récente, récupération Wellness, calendrier de courses, contraintes, plan hebdomadaire, débriefing prévu/réalisé et sélection/détail d'activité.

Le package opencoach.ai ne compose plus les repositories SQL : le câblage est effectué dans la composition API. Des tests d'architecture empêchent les dépendances directes entre domaines métier et IA, ainsi que les imports de persistance dans opencoach.ai.

Le moteur IA local est optionnel et désactivé par défaut. Les domaines Coach restent indépendants de son fournisseur.

Non terminé : audit et déplacement des règles de recommandation/restriction présentes dans api/ai.py et ai/response_synthesis.py, puis audit exhaustif des autres adaptateurs IA et de leurs contrats. Ne pas déclarer la règle zéro métier satisfaite avant cette dernière passe et la CI complète.



## État de reprise — mise à jour du 16 novembre 2026

Les fenêtres par défaut et limites de périodes ont été déplacées vers les services Coach. Les schémas IA et le plan conversationnel ne reproduisent plus les limites historiques, de charge, de tendances, de préparation de course ou de calendrier. Les valeurs par défaut (historique/charge, calendrier) sont appliquées par les services métier.

Le plan déterministe transmet les arguments préparés comme fiables ; les appels directs du modèle restent soumis à la validation de preuve utilisateur. Les routes Coach principales ne dépendent pas du package IA, et un garde-fou d'architecture le vérifie.

Le package opencoach.ai n'importe ni SQLAlchemy ni opencoach.database. Les repositories sont composés dans la couche API et les adaptateurs appellent les services Coach existants.

**Non terminé :** la composition des analyses de recommandation et les contrôles d'affirmations de la synthèse IA doivent encore être rapprochés de CoachDecisionService et PlanningContextService. Ne pas déclarer la règle zéro logique métier satisfaite avant ce travail et une CI verte sur le HEAD final.
