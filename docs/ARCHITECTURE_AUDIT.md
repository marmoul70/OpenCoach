# Audit architectural OpenCoach — branche de remise à plat

**Branche :** `refactor/architecture-cleanup`  
**Socle initial :** `fix/ai-coach-analysis-semantics`  
**Commit initial :** `a0f90644cd943c16efe1988601bd713b216f2706`  
**Date de l'audit :** 15 novembre 2026  
**Statut :** audit en cours — aucune fonctionnalité supprimée.

## 1. Objectif et règles

Cette branche sert à remettre le dépôt en ordre sans repartir d'un `main` qui ferait perdre les développements métier plus récents.

Règles :
- `main` et les branches sources ne sont pas modifiées par cette mission.
- Aucun comportement métier n'est supprimé sans preuve qu'il est redondant, inutilisé et couvert par un remplacement.
- Toute suppression doit être précédée d'un inventaire des appels, routes API, écrans, migrations, scripts, tests et intégrations concernés.
- Le moteur métier Python reste l'unique source de vérité pour les calculs et décisions sportives.
- Le LLM local ne calcule pas les indicateurs, ne décide pas des adaptations et ne modifie pas le planning ou les fournisseurs.
- Chaque étape de refactoring doit conserver des tests de caractérisation et ajouter des tests de non-régression.

## 2. Socle retenu provisoirement

La branche a été créée à partir du commit `a0f90644cd943c16efe1988601bd713b216f2706`, tête de la PR #37.

Motif : ce socle contient les développements métier et infrastructure présents dans la chaîne de développement récente, en plus des évolutions IA. Repartir directement de `main` ferait perdre des changements identifiés dans COROS, readiness/récupération, wellness, courses, entraînement, déploiement et interface.

Ce choix est provisoire : il ne signifie pas que tout le contenu de cette branche est validé ni qu'il faut conserver toute la couche IA.

## 2 bis. Inventaire quantitatif actualisé

Inventaire calculé sur l'arbre Git du commit `553f518228bc` :
- **1 182 fichiers suivis** au total ;
- **519 fichiers Python** sous `app/opencoach` ;
- **164 fichiers** sous `frontend/src` ;
- **387 fichiers** sous `tests` ;
- **32 fichiers** sous `docs` ;
- **38 fichiers** sous `scripts`.

Principaux ensembles backend (fichiers Python) :
- `planning` : 127 ;
- `database` : 116 ;
- `coaching` : 65 ;
- `training` : 48 ;
- `api` : 27 ;
- `ai` : 24 ;
- `integrations` : 19.

Les décomptes décrivent le volume, pas la qualité ni l'inutilité des fichiers. Ils doivent être recalculés après les suppressions ou déplacements importants.

### Gros fichiers à examiner par responsabilité

Backend :
- `app/opencoach/api/coros.py` (~80 Ko) ;
- `app/opencoach/integrations/coros/workout_mapper.py` (~40 Ko) ;
- `app/opencoach/api/training_sessions.py` (~39 Ko) ;
- `app/opencoach/planning/sessions/prescription/intervals.py` (~35 Ko) ;
- `app/opencoach/api/ai.py` (~27 Ko après le refactoring Coach/IA).

Frontend :
- `frontend/src/modules/profile/AthleteProfileSections.tsx` (~93 Ko) ;
- `frontend/src/modules/weather/WeatherPage.tsx` (~52 Ko) ;
- `frontend/src/modules/training/TrainingDetails.tsx` (~52 Ko) ;
- `frontend/src/modules/activities/ActivityPage.tsx` (~50 Ko) ;
- `frontend/src/modules/races/RaceDetails.tsx` (~50 Ko).

La taille seule ne justifie aucune extraction. Chaque découpage doit isoler une responsabilité cohérente, réduire les dépendances ou rendre les tests plus ciblés, sans déplacer artificiellement du code.

### État des répertoires historiques

- Le répertoire `.refactor-backup/20260831-231419/` cité dans une version antérieure de cet audit **n'existe pas dans l'arbre de cette branche**. Il n'est donc pas une archive à supprimer dans l'état actuel de `refactor/architecture-cleanup`. Ne pas extrapoler cet état à `main`.
- Le répertoire racine `backend/` ne contenait que `.gitkeep`. Après vérification du packaging (`pyproject.toml` pointe sur `app/`) et des scripts d'installation/démarrage, ce marqueur vide a été supprimé : il ne représentait aucun code ni point d'entrée applicatif.
- `config/thresholds.toml` est le fichier de valeurs chargé et validé par `app/opencoach/config/thresholds.py`. Ce module est le parseur/contrat typé, pas une seconde copie de la configuration.
- `app/opencoach/training/session_execution/thresholds.py` définit des tolérances d'évaluation de l'exécution des séances (volume, adhérence et structure). Ces seuils sont d'une autre nature que les seuils Readiness/Coach de `config/thresholds.toml` ; leur présence ne constitue pas en soi une duplication.

## 3. État de validation observé

Au commit initial, les contrôles GitHub Actions visibles sont terminés avec succès :
- Bash validation : success
- Python 3.13 tests : success
- Frontend validation : success

Ces résultats prouvent que les jobs CI de ce commit ont réussi. Ils ne remplacent pas une validation opérationnelle sur la VM Debian 13, une migration de base existante, une synchronisation COROS réelle ou des tests exploratoires de l'interface.

## 4. Fonctionnalités à préserver et auditer

| Domaine | Éléments identifiés | Traitement |
|---|---|---|
| Authentification et profils | comptes, sessions, profils athlètes, paramètres | conserver, auditer sécurité et isolation multi-profil |
| Entraînement | séances, historique, exécution, statistiques | conserver, vérifier source de vérité et contrats |
| Planification | génération, adaptation quotidienne/hebdomadaire, trajectoire, contraintes | conserver, cartographier les services et responsabilités |
| Charge et récupération | charge récente, readiness, wellness, évaluations | conserver, consolider les définitions et éviter les doubles calculs |
| Courses | calendrier, objectifs, préparation, impact sur la trajectoire | conserver |
| COROS | OAuth, synchronisation activités/wellness, push des séances | conserver ; réconcilier explicitement la PR #21 |
| Intervals.icu | import activités, wellness et synchronisation des séances | conserver |
| Notifications | centre persistant, push, rappels | conserver |
| Frontend Pulse | navigation, coach, entraînement, courses, paramètres, PWA | conserver et contrôler les parcours |
| Infrastructure | bootstrap Debian, systemd, Nginx, sauvegarde, migrations, déploiement | conserver, réduire les points d'entrée concurrents |
| IA locale | chat, outils, routage, planification d'exécution, observabilité, évaluateurs | refactoriser après cartographie des usages |

Cette liste est un inventaire de périmètre, pas une validation ligne par ligne.

## 5. Risques et constats concrets

### 5.1 Couche IA

- `app/opencoach/api/ai.py` : 1 532 lignes.
- `app/opencoach/ai/execution_plan.py` : 554 lignes.
- `app/opencoach/ai/tool_routing.py` : environ 230 lignes.
- `app/opencoach/ai/tool_engine.py` : environ 237 lignes.
- `app/opencoach/ai/service.py` : environ 130 lignes.

Le point de vigilance est le cumul des responsabilités : API, assemblage des outils, routage par texte, extraction des périodes, validation, orchestration et synthèse. La cible doit réduire les mécanismes, pas créer de nouvelles couches pour les envelopper.

Cible fonctionnelle :
1. l'application identifie les données et services métier nécessaires ;
2. les services métier OpenCoach calculent et valident les résultats ;
3. le modèle local formule une explication à partir de résultats structurés ;
4. les actions d'écriture restent dans des parcours explicites avec confirmation.

Avant de supprimer un outil, vérifier ses usages, ses routes, ses tests, son exposition frontend et les besoins de conversation qu'il couvre.

### 5.2 Déploiement frontend

Sur le socle retenu :
- `scripts/deploy-frontend.sh` est le point d'entrée canonique et gère les releases atomiques ;
- `scripts/deploy_frontend.sh` est un alias de compatibilité de 10 lignes qui délègue au script canonique.

Il ne s'agit donc plus de deux implémentations concurrentes sur cette branche. Ne pas supprimer l'alias sans rechercher les références dans les documentations, scripts bootstrap et procédures utilisateur.

### 5.3 Version

Sur le socle retenu, `VERSION` et `pyproject.toml` indiquent tous deux `0.8.5`. Le décalage précédemment observé sur `main` n'existe pas sur cette branche. Ne pas incrémenter la version pour un simple audit/refactoring non livré.

### 5.4 PR COROS #21

La PR #21 est encore ouverte et en brouillon. Elle traite un cas de création COROS dont la réponse est incertaine (séance créée à distance mais identifiant non retourné). Le correctif cherche à réconcilier la séance existante avant toute nouvelle création, afin d'éviter les doublons.

Ce comportement est critique pour l'intégrité des données et doit être évalué et intégré dans le plan de préservation. Il ne faut ni l'ignorer ni le fusionner sans revue et tests de non-régression.

### 5.5 PR IA #33 à #37

Les PR forment une chaîne de dépendances et non cinq lots indépendants :
- #33 : observabilité IA ;
- #34 : qualité des analyses ;
- #35 et #36 : conversation, synthèse et comparaisons ;
- #37 : sémantique charge/récupération.

La PR #37 modifie aussi les statistiques d'entraînement. Toute remise à plat doit comparer les contrats et tests de ces statistiques avec le comportement antérieur pour ne pas perdre une correction métier utile.

## 5 bis. Premières vérifications de responsabilités métier

### Policy de saison : séparation justifiée, pas de doublon à supprimer

Les fichiers `policy_evaluation.py`, `policy_evaluator.py` et `policy_evaluators.py` ont des rôles distincts :
- `policy_evaluation.py` définit les objets de résultat et les états d'évaluation ;
- `policy_evaluator.py` orchestre l'évaluation de toutes les règles d'une policy ;
- `policy_evaluators.py` route chaque type de paramètre vers l'évaluateur correspondant.

Leurs imports sont utilisés par `strategy_gate.py`, `planning/__init__.py` et les tests de policy. La similitude des noms ne justifie donc pas une suppression. Une éventuelle simplification devra conserver les contrats publics et les règles de sécurité (notamment une hard limit non évaluable qui bloque la proposition).

### Réconciliation de charge : temporalités différentes

`planning/weekly/load_reconciliation.py` traite l'écart d'une semaine. `planning/history/load_reconciliation.py` analyse plusieurs semaines pour détecter une dérive durable et proposer un réancrage de référence. Le module historique consomme les résultats contextualisés du module hebdomadaire. Ce sont deux niveaux d'analyse complémentaires, pas deux implémentations du même calcul.

### Charge quotidienne, comparaison et projection

Les services observés ont des responsabilités distinctes :
- `DailyTrainingLoadService` calcule la charge réellement effectuée à une date ;
- `TrainingLoadComparisonService` compare le réel au programme OpenCoach ;
- `RecentTrainingLoadService` agrège les comparaisons sur une période ;
- `WeeklyLoadProjectionService` projette le réalisé et les séances restantes de la semaine.

Il ne faut pas fusionner ces services sur la seule base du mot « charge ». En revanche, les chemins de composition FastAPI construisent plusieurs fois la chaîne `DailyTrainingLoadService -> TrainingLoadComparisonService -> RecentTrainingLoadService`. C'est une duplication d'assemblage à mesurer, mais pas une preuve de duplication du calcul métier. Une simplification éventuelle devra centraliser la composition sans ajouter une couche abstraite inutile.

### API Coach : premier nettoyage sans effet fonctionnel

`app/opencoach/api/coach.py` importait deux fois `get_db` depuis `opencoach.database.session`. Le doublon d'import a été supprimé dans un commit dédié. Aucun endpoint, contrat ou calcul métier n'a été modifié.

## 5 ter. Audit ciblé de l'entrée IA et du routage

### Constat sur `api/ai.py`

Le module fait 1 532 lignes et mélange plusieurs responsabilités vérifiées dans le fichier :
- modèles Pydantic de requêtes/réponses et préférences ;
- construction des prompts et budgets de réponse ;
- composition du registre d'outils ;
- endpoints de préférences, statut, propositions de données et chat ;
- orchestration des appels et traitement des réponses ;
- règles de qualité, fallbacks, filtrage et sérialisation des résultats.

C'est un candidat prioritaire pour une réduction de responsabilités, mais une extraction massive immédiate serait risquée : les fallbacks et garde-fous sont directement liés au comportement conversationnel et aux données métier. Le premier lot devra extraire uniquement des blocs autonomes, conserver les routes et fonctions importées par les tests, et vérifier les contrats HTTP.

### Routage et plan d'exécution

`tool_routing.py` sélectionne le catalogue d'outils à présenter au modèle et filtre les outils qui exigent une période explicite. `execution_plan.py` construit des appels déterministes et leurs arguments. Leurs rôles ne sont donc pas identiques.

Les deux modules possèdent toutefois chacun leur fonction de normalisation Unicode, et importent tous deux les fonctions d'extraction de preuves temporelles. Il faut vérifier les différences de normalisation et les usages avant de mutualiser quoi que ce soit. La priorité est d'éviter deux interprétations divergentes d'une même demande, sans perdre les contrôles conservateurs du routeur.

### Registre d'outils

`tool_engine.py` constitue une liste blanche explicite, valide les arguments, limite les outils autorisés, conserve les résultats et gère un cache d'exécution. Ce composant est une frontière de sécurité ; il ne doit pas être fusionné avec le routeur ou l'API. Toute simplification devra préserver l'interdiction d'exécuter une fonction arbitraire fournie par le modèle.

### Nettoyage complémentaire

Dans `api/coach.py`, les deux imports distincts depuis `api.coaching.dependencies` ont été regroupés en un seul bloc. Le contrôle statique des imports exacts ne détecte plus de doublon dans `api/coach.py` ni `api/ai.py`.

Les imports locaux de `api/coaching/dependencies.py` sont volontairement placés dans certaines fonctions de composition. Ils peuvent éviter des imports circulaires ou retarder le chargement de composants optionnels ; ils ne doivent pas être remontés globalement sans analyse des dépendances.

## 5 quater. Suppression de sauvegardes frontend versionnées

Le répertoire `.refactor-backup/20260831-231419/` contenait six anciens fichiers frontend (App, Connections, index Connections, Profile, Settings et SettingsSections). Ils étaient des copies de sauvegarde, pas des sources de build :
- ils vivaient hors de `frontend/src`, qui est le périmètre compilé par Vite/TypeScript ;
- aucune référence à ce répertoire ou à son horodatage n'a été trouvée dans la recherche du dépôt ;
- la règle `.gitignore` `.refactor-backup/` indique explicitement que ces sauvegardes sont locales et ne doivent pas être versionnées.

Les six copies ont donc été supprimées de la branche de nettoyage. L'historique Git conserve les contenus si une comparaison historique est nécessaire. Aucune source frontend active n'a été supprimée.

### Autre sauvegarde accidentellement versionnée

Le fichier `app/opencoach/backup/restore.py.before-rollback-20260831-112557` était une copie pré-rollback de l'implémentation de restauration. Il n'avait aucune référence détectée, était couvert par la règle `.gitignore` `*.before-*`, et différait du module actif `restore.py` (407 lignes contre 528). Il a été retiré de la branche ; l'implémentation active et les données de sauvegarde utilisateur ne sont pas concernées. Le contenu historique reste accessible dans Git.

## 5 quinquies. Vérification des flux de données fournisseurs

Les implémentations consultées confirment un point important de la cible :
- COROS (`integrations/coros/sync.py`) normalise les activités via `upsert_coros_activity` et enregistre les jours Wellness via `SqlWellnessRepository.save_wellness_day`.
- Intervals.icu (`integrations/intervals/sync.py`) enregistre les activités via `ActivityRepository.save_activity` et le Wellness via `WellnessRepository.save_wellness_day`.
- `ReadinessService` lit le référentiel `WellnessRepository`, agrège les imports et calcule les indicateurs indépendamment du fournisseur.
- `TrainingStatsService` lit les `ActivityRepository` et `TrainingSessionRepository` pour construire l'historique d'entraînement.

Cela établit déjà une centralisation effective pour les activités et le Wellness. Il faut préserver cette architecture et étendre le même principe aux autres domaines, plutôt que créer un stockage parallèle spécifique à chaque source.

Un ADR dédié est ajouté : `docs/architecture/adr/0002-coach-central-data-and-ai-boundary.md`.

Écart encore visible : `ai/coaching_tools.py` et `ai/race_tools.py` effectuent plusieurs lectures SQL directes et des agrégations/sérialisations métier. Elles doivent être progressivement converties en adaptateurs de services Coach. La centralisation des activités et Wellness ne signifie donc pas que l'ensemble du moteur est déjà découplé de l'IA.

## 6. Architecture cible minimale

- **API** : authentification, validation des entrées, appel des services, sérialisation des réponses.
- **Services métier** : règles, calculs, décisions et orchestration métier.
- **Intégrations** : adaptateurs COROS/Intervals et synchronisation.
- **IA** : compréhension/rédaction et appels contrôlés aux services nécessaires, sans deuxième moteur métier.
- **Frontend** : présentation et interactions, sans règles métier dupliquées.
- **Infrastructure** : un point d'entrée canonique par opération.

Ne pas créer un module ou une abstraction si une fonction existante, correctement placée et testée, remplit déjà le besoin.

## 7. Plan d'exécution

### Phase A — Inventaire exhaustif
- [ ] cartographier tous les packages Python et leurs dépendances ;
- [ ] cartographier les routes FastAPI et leurs services ;
- [ ] cartographier modèles SQLAlchemy, repositories et migrations Alembic ;
- [ ] cartographier les pages, composants, stores et clients API frontend ;
- [ ] cartographier les intégrations, tâches planifiées, commandes et scripts ;
- [ ] établir la matrice des fonctionnalités et leur couverture de tests.

### Phase B — Audit de qualité
- [ ] rechercher duplications, fonctions mortes, imports inutilisés et cycles ;
- [ ] repérer les modules trop couplés et les responsabilités mixtes ;
- [ ] contrôler la gestion des erreurs, transactions et idempotence ;
- [ ] contrôler isolation multi-athlète et autorisations ;
- [ ] vérifier migrations, sauvegarde/restauration et compatibilité des données ;
- [ ] relever les problèmes de performance et requêtes N+1.

### Phase C — Préservation des fonctions hors IA
- [ ] auditer les PR non fusionnées et leurs dépendances ;
- [ ] revoir la PR #21 COROS et ses scénarios de réconciliation ;
- [ ] établir une matrice de non-régression par domaine ;
- [ ] exécuter la suite complète et comparer les résultats au socle ;
- [ ] valider les parcours sur la VM avant toute intégration vers main.

### Phase D — Simplification
- [ ] supprimer uniquement le code prouvé mort ou redondant ;
- [ ] fusionner les responsabilités réellement dupliquées ;
- [ ] réduire la surface de l'API IA ;
- [ ] conserver les contrats publics et les fonctionnalités existantes ;
- [ ] documenter les décisions structurantes dans des ADR courts.

## 8. Critères d'acceptation

La remise à plat n'est pas terminée tant que :
- toutes les fonctionnalités existantes ont une correspondance dans la matrice de préservation ;
- aucune route, migration, commande ou action frontend utile n'a disparu sans remplacement ;
- les tests métier et d'intégration passent ;
- les synchronisations COROS/Intervals et la réconciliation des créations incertaines sont couvertes ;
- le frontend lint et build ;
- le bootstrap, le déploiement, le rollback et les sauvegardes sont validés ;
- l'architecture IA n'embarque pas de calcul ou de décision métier ;
- le code supprimé est justifié par des preuves d'inutilisation ou de redondance.

## 9. Limites de cet état initial

Ce document est le journal du premier passage. Il ne prétend pas certifier l'ensemble du code. Les analyses statiques et exécutions locales complètes doivent être réalisées avant toute suppression structurelle. Aucune branche source, PR ou branche `main` n'a été modifiée par la création de cette branche d'audit.

## 6. Décision d'architecture confirmée — Coach autonome, IA adaptateur

Décision confirmée le 15 novembre 2026 à la demande de l'utilisateur : les calculs et décisions doivent être directement rattachés au moteur Coach OpenCoach, jamais à l'IA.

Le Coach doit fournir les résultats métier à l'application, même en l'absence d'Ollama. L'IA est une interface conversationnelle qui comprend la demande, appelle les capacités métier existantes et explique leurs résultats. Elle ne recalcule pas les indicateurs, ne prend pas les décisions sportives et ne pilote pas directement les modifications du planning.

Conséquences de conception :
- les services Coach sont les propriétaires des règles et calculs ;
- les API et écrans peuvent appeler ces services sans dépendance à l'IA ;
- les outils IA sont des adaptateurs fins (validation d'entrée, appel du service, sérialisation contrôlée) ;
- les accès SQL directs et agrégations métier dans les modules `opencoach.ai` sont des écarts à corriger progressivement ;
- préserver les noms, schémas d'arguments et payloads des outils durant les refactorings lorsque possible ;
- si aucun service métier existant ne couvre un besoin, créer/compléter un service dans le domaine Coach, avec tests, plutôt que coder le calcul dans l'IA.

Le plan détaillé de reprise, l'état Git et les constats techniques sont consignés dans `docs/REPRISE_REFACTOR_ARCHITECTURE.md`.


## 5 sexies. Propositions de profil : réutilisation des domaines Coach

Le cycle de propositions de données a été déplacé de `opencoach.ai` vers `opencoach.coaching.profile_data_proposals`. L'IA ne porte plus l'implémentation de ce cas d'usage.

- Profil, physiologie, capacité d'entraînement et nutrition : les lectures/écritures confirmées utilisent `ProfileService` et `SqlProfileRepository`.
- Équipements : l'inventaire canonique est `AthleteProfile.equipment`; la persistance passe par la synchronisation existante du repository profil. Le service de proposition d'équipement d'activité `EquipmentProposalService` garde son rôle distinct de sélection d'une chaussure compatible, sans être détourné en CRUD.
- Check-in : le modèle domaine `AthleteDailyCheckIn` et `SqlDailyCheckInRepository` sont réutilisés.
- Nutrition : les repères sont ceux de `AthleteNutrition` et sont exposés par `ProfileService.build_training_context()`. Aucun calcul ou stockage nutritionnel parallèle n'a été ajouté.
- Cycles : `planning/trajectory/load_recovery_cycle.py` demeure la politique de cycle de charge/récupération unique. Les outils IA ne doivent ni la recopier ni produire une deuxième décision de cycle.

L'ancien `ai/data_proposals.py` est conservé comme shim d'import historique uniquement ; l'API et les outils utilisent désormais directement le module Coach. Les tests de caractérisation du cycle de propositions passent dans la suite complète.

**Validation du commit `c6f79c5f57684b9c4675c7bfdeec027005a160d8` :** Python 3.13, 3 141 tests réussis ; Bash et bootstrap Debian 13 réussis ; frontend lint/build réussis. Cela valide ce lot, pas encore l'audit exhaustif du dépôt.


## 13. Renforcement de la frontière IA — 16 novembre 2026

Décision utilisateur : **zéro logique métier dans le package `opencoach.ai`**. La règle s'applique aussi à la composition de services, au choix des fenêtres/métriques, aux conditions de couverture, au masquage des résultats, aux avertissements métier et aux agrégations de repositories. L'IA est un client du Coach, pas un orchestrateur métier.

### Première cartographie des responsabilités restantes

- `ai/race_tools.py` : adaptateur déjà mince vers `RacePreparationService.analyze()`; conserver ce contrat et vérifier les éventuels détails de sérialisation.
- `ai/trend_tools.py` : appelle `TrainingStatsService` et `TrainingStats.compare_to()`; la construction des périodes et leur orchestration doivent être examinées au regard des capacités Coach déjà présentes avant toute modification.
- `ai/load_tools.py` : construit les périodes, combine `RecentTrainingLoadService` et `TrainingStatsService`, applique des règles de complétude/masquage et produit des avertissements. Ces responsabilités ne doivent pas rester dans l'adaptateur. Réutiliser/étendre les capacités Coach de charge et statistiques déjà présentes.
- `ai/recovery_tools.py` : combine des repositories, appelle `aggregate_wellness_days` et `build_recovery_assessment`, choisit la fenêtre de 7 jours, filtre les métriques, interprète la couverture et construit des avertissements. Le moteur `recovery_assessment.py`, l'agrégateur Wellness et `ReadinessService` existent déjà : les responsabilités doivent être rattachées à ces capacités, sans créer un moteur de récupération parallèle.
- `ai/coaching_tools.py` : contient des calculs de période, validations temporelles et transformations conditionnelles de données de planning ; examiner les services `PlannedTrainingService`, repositories de courses et plans hebdomadaires avant d'extraire quoi que ce soit.
- `api/ai.py` : l'orchestration conversationnelle, les préférences IA, le routage des outils et la gestion du fournisseur relèvent de la couche conversation/API ; les routes ne doivent pas contenir de règles sportives.

Cette cartographie est un constat partiel, pas la certification de tout le package. Les autres modules IA, leurs dépendances, leurs appels SQL et leurs tests restent à inventorier. Aucune suppression de code ne sera faite avant la vérification des usages, des contrats et de la couverture de non-régression.

### Ordre de traitement obligatoire

1. Inventorier chaque fonction de `opencoach.ai` et classer ses responsabilités : conversation/transport, sécurité technique ou métier.
2. Pour chaque responsabilité métier, identifier son propriétaire Coach existant, ses routes/API, repositories et tests.
3. Étendre le propriétaire existant si nécessaire ; ne créer un nouveau service que si l'absence de capacité est démontrée et documentée.
4. Déplacer les tests de règles vers le domaine Coach et conserver des tests d'adaptateur limités au contrat d'appel et au transport.
5. Supprimer l'implémentation métier des adaptateurs IA et les imports devenus inutiles.
6. Vérifier qu'aucun accès SQL métier, calcul ou décision ne subsiste dans `opencoach.ai`, puis exécuter la CI complète sur le HEAD final.

Aucun merge, rebase sur `main`, déploiement, suppression de branche ou incrément de version n'est autorisé sans accord explicite.


## 14. Premier retrait de logique Readiness du package IA

La sérialisation du résultat Readiness, notamment les avertissements liés aux conflits d'import, à la fraîcheur des données et à la fiabilité des baselines, est maintenant portée par `opencoach.readiness.readiness_assessment_to_dict()`. `ai/recovery_tools.py` délègue au `ReadinessService` et transmet le résultat. Le contrat de sortie de l'outil est conservé ; aucun service parallèle n'est créé.

Il s'agit d'un premier retrait ciblé. L'outil `recovery_analysis` contient encore une orchestration et des règles de composition qui restent à déplacer vers les capacités Coach existantes après caractérisation de ses contrats.



## 15. Centralisation Coach et indépendance du moteur IA

Les responsabilités suivantes ont été replacées dans les capacités Coach existantes :

- TrainingStatsService possède les fenêtres calendaires et les comparaisons de périodes successives.
- TrainingStats.history_summary() et RecentTrainingLoad.analysis_summary() centralisent les règles de couverture, les sous-totaux partiels, la fiabilité des totaux et les avertissements.
- ReadinessService.describe_recovery() centralise l'accès aux imports Wellness, leur agrégation, le contexte quotidien et le check-in ; l'API Wellness et l'adaptateur conversationnel réutilisent cette même capacité.
- recovery_assessment_to_coach_summary() dans opencoach.recovery_assessment construit la synthèse descriptive métier, notamment la fenêtre récente, les métriques pertinentes, la provenance et les limites de couverture.
- RacePreparationService.list_calendar() porte la consultation du calendrier des courses.
- PlanningContextService.active_constraints() et weekly_plan_context() portent les contraintes et le contexte de plan hebdomadaire.
- PlannedTrainingService.list_between() valide les limites de période des séances planifiées.
- ValidateTrainingSessionService.review() réutilise le moteur d'analyse prévu/réalisé pour un débriefing strictement en lecture seule.
- ActivityDetailService a été ajouté après vérification : les repositories d'activité/détail et la route API COROS existaient, mais aucun service applicatif commun ne résolvait la sélection d'activité et son détail centralisé. Il réutilise les repositories existants et ne crée aucune nouvelle persistance.

La composition des repositories nécessaires aux outils a été déplacée dans api/ai.py. ai/registry.py ne construit plus de repositories SQL ; il assemble uniquement les adaptateurs autour des services Coach injectés.

Deux garde-fous d'architecture vérifient désormais que :
1. les packages métier n'importent pas opencoach.ai ;
2. le package opencoach.ai n'importe ni SQLAlchemy ni opencoach.database.

Le moteur local reste désactivé par défaut (OPENCOACH_AI_ENABLED=false). Les capacités de domaine et leurs API métier ne nécessitent pas qu'un fournisseur LLM soit disponible.

Travaux restant à auditer avant certification zéro métier dans l'IA : les règles de recommandation et de restriction dans api/ai.py et ai/response_synthesis.py, les modules de collecte/proposition de données, ainsi que l'ensemble des adaptateurs et contrats de routage. Aucun retrait global n'est déclaré terminé à ce stade.


Le fallback de rédaction tronquée ne formule plus de recommandation sportive autonome à partir d'une séance planifiée. En cas d'échec de synthèse LLM, l'API renvoie désormais un message technique neutre ; toute décision de séance doit provenir d'une capacité Coach explicite.


Le module mort ai/context.py et ses tests dédiés ont été supprimés après vérification des imports et usages : aucune route, dépendance, composition d'outils ou API de production ne l'appelait. Il reconstruisait une seconde synthèse de statistiques, de charge et de Readiness dans le package IA, avec ses propres règles de couverture et ses propres fenêtres temporelles. Les capacités canoniques sont désormais fournies directement par les services Coach.



## 16. Périodes et valeurs par défaut : propriété du domaine Coach

Les durées maximales et les fenêtres par défaut ont été retirées des schémas IA et du planificateur conversationnel. Elles sont désormais portées par les capacités métier :

- TrainingStatsService.calculate_days() applique la fenêtre historique par défaut de 7 jours et valide sa plage.
- RecentTrainingLoadService.calculate() conserve la fenêtre de charge par défaut du domaine et ses validations.
- TrainingStatsService.compare_adjacent_periods() valide les deux fenêtres de comparaison.
- RacePreparationService.analyze() valide la fenêtre d'historique d'une préparation.
- RacePreparationService.list_calendar() applique le défaut du calendrier et valide son horizon.
- PlannedTrainingService.list_between() valide les fenêtres de séances planifiées.

Les schémas IA transportent des entiers/dates sans reproduire ces politiques. Le plan conversationnel demande une période lorsqu'elle est nécessaire, mais ne décide plus de ses bornes ni de ses valeurs par défaut. Le plan déterministe peut transmettre l'absence de durée au domaine ; les appels directs émis par le LLM restent protégés par le contrôle de preuve utilisateur.

La route /api/coach/today repose sur CoachDecisionService et ses services métier. Un test d'architecture vérifie que les routes Coach principales n'importent pas opencoach.ai. Le moteur IA peut donc être désactivé sans retirer la décision quotidienne du Coach.

La décision de séance n'est plus reconstruite par le parcours conversationnel : `coach_decision` expose désormais `CoachDecisionService`, déjà utilisé par la route Coach quotidienne. Les scénarios de recommandation appellent cette capacité à la place de `next_planned_session` seul ; le service renvoie l'action, la justification, la séance concernée, Readiness et l'évaluation de charge. Le contrôle de restriction s'appuie toujours sur `PlanningContextService.active_constraints()` et sa décision métier structurée.

Les règles restantes dans `ai/execution_plan.py` et `ai/tool_routing.py` concernent l'interprétation du langage utilisateur, la sélection des outils et la collecte de paramètres conversationnels. Elles doivent rester des règles d'interface, sans seuil sportif, calcul, classification ni politique de planification. `ai/response_synthesis.py` conserve uniquement des contrôles de qualité de génération qui vérifient l'étayage des affirmations par les résultats Coach.

**Audit encore ouvert avant certification zéro métier :** vérifier ligne par ligne les derniers contrats du planificateur et de la collecte de données, et confirmer que tous les parcours métier principaux restent disponibles quand `OPENCOACH_AI_ENABLED=false`.


## 17. Suppression de la composition métier dans les adaptateurs IA

Deux compositions restantes ont été retirées des adaptateurs :

- Les dates de référence courantes sont maintenant obtenues par les services Coach (TrainingStatsService, RecentTrainingLoadService, ReadinessService). Les schémas IA transmettent une date explicite lorsqu'elle est demandée, sinon ils laissent le domaine appliquer son horloge. Les outils d'historique, de tendances, de charge et de récupération n'appellent plus date.today() et ne construisent plus leurs fenêtres.
- La synthèse charge + volume réel est maintenant une capacité unique de RecentTrainingLoadService.analysis_summary(). Ce service existant orchestre RecentTrainingLoadService.calculate() et TrainingStatsService.calculate_days() avec la même date de référence, puis délègue le résumé à RecentTrainingLoad.analysis_summary(). ai/load_tools.py ne reçoit plus deux services et ne compose plus les résultats.

La règle de restriction de course est elle aussi fournie par PlanningContextService.active_constraints() dans running_restriction. Le contrôle rédactionnel IA consomme ce résultat structuré et ne réévalue plus running_allowed à partir de chaque contrainte.

Les garde-fous de synthèse qui restent dans ai/response_synthesis.py sont des contrôles de qualité de génération : ils vérifient qu'une affirmation du LLM est étayée par les résultats Coach, sans recalculer de seuil, score ou statut métier. Ils ne sont pas une source de vérité sportive.

**Audit encore ouvert :** terminer la revue des contrats d'outils et du planificateur conversationnel (tool_routing.py, execution_plan.py, argument_evidence.py), vérifier les chemins d'exécution lorsque l'IA est désactivée et recenser les derniers imports/usages publics avant toute suppression. La règle zéro métier n'est pas encore certifiée globalement.


La composition API de la charge a également été factorisée : get_recent_training_load_service() construit le service existant depuis les repositories déjà détenus par TrainingStatsService. PlanningContextService et CoachDecisionService réutilisent cette même chaîne de dépendances. api/ai.py réutilise directement les repositories canoniques de TrainingStatsService pour les outils activité/séance, sans recréer une seconde paire de repositories SQL.

Le schéma de l'outil de proposition de profil hérite maintenant directement de AIDataProposalCreate. Les champs autorisés et validations de valeurs ne sont donc plus redéfinis dans le package IA ; seul le contrôle de preuve conversationnelle reste spécifique à l'adaptateur.


## 14. Mise à jour — frontière du registre Coach/IA (16 novembre 2026)

**HEAD de référence :** `b6c72dcba7e136f271f20ca8beb26868cc653968` (branche `refactor/architecture-cleanup`).

### Changements effectifs

- Le contrat générique d'exécution (`CoachCapability`, `CoachCapabilityResult`, `CoachCapabilityRegistry` et `ToolStatus`) est défini dans `coaching/capabilities/registry.py`. Il ne dépend ni du package IA ni de son observabilité.
- `coaching/capabilities/__init__.py` expose ce contrat comme API publique du domaine.
- `ai/tool_engine.py` est une façade de compatibilité stricte : ses anciens symboles sont des alias des types Coach, y compris le type `ToolStatus` (plus de remplacement permissif par `str`).
- Les adaptateurs conversationnels importent le contrat Coach. L'API enregistre et exécute ces capacités via le registre Coach.
- `ai/data_proposals.py` est déjà un shim de compatibilité ; le cycle de vie des propositions est implémenté dans `coaching/profile_data_proposals.py`.
- `ai/registry.py` reste une composition d'adaptateurs IA autour de services métier injectés. Ce n'est pas un second registre métier et il ne doit pas contenir de calcul ni de décision sportive.

### Vérifications

- CI du commit `aecb23695ef32994c8850e534732d093b63cdc9f` : Python 3.13, Bash et Frontend terminés avec succès.
- Un test de contrat vérifie l'identité des alias historiques avec les types Coach et le caractère strict du type `ToolStatus`.
- La CI du HEAD `b6c72dcba7e136f271f20ca8beb26868cc653968` est en cours au moment de cette mise à jour ; ne pas la considérer comme validée avant la fin des trois jobs.

### Audit restant — points non certifiés

1. Parcourir chaque adaptateur de `ai/*_tools.py` et distinguer strictement validation de transport/sérialisation des règles métier. Une fonction de calcul, un seuil, une interprétation de statut ou une décision individuelle ne doit pas rester dans l'adaptateur.
2. Vérifier les frontières de `api/ai.py` et `ai/response_synthesis.py` : l'orchestration HTTP et la présentation peuvent rester dans la couche IA, mais aucun garde-fou sportif ou choix de recommandation ne doit y être réimplémenté.
3. Confirmer par tests d'intégration que les parcours métier (profil, entraînement, courses, contraintes, récupération, propositions) fonctionnent lorsque le fournisseur IA est désactivé ou absent.
4. Identifier les façades de compatibilité encore importées. Ne les supprimer qu'après inventaire des usages internes, tests, scripts et intégrations externes ; une façade n'est pas une duplication d'implémentation si elle ne contient aucun comportement.
5. Compléter l'audit global des duplications et du code mort hors IA (backend, frontend, scripts, infrastructure et migrations).

**Conclusion provisoire :** le registre et le cycle de propositions ne sont plus des implémentations métier dupliquées dans le package IA. En revanche, l'objectif « zéro logique métier dans l'IA » n'est pas encore certifié ; les points ci-dessus sont des critères bloquants, pas des tâches facultatives.


## 15. Audit des contrôles de synthèse et durcissement des garde-fous — 16 novembre 2026

### Responsabilités examinées

- `ai/response_synthesis.py` : extraction de métadonnées de période, conversion des courses pour le contrat API, limitation de taille des payloads et contrôle de qualité rédactionnelle. Ces opérations relèvent de la présentation et du transport ; elles ne calculent pas d'indicateur sportif et ne choisissent pas de conduite d'entraînement.
- `api/ai.py` : la décision de blocage avant synthèse est appelée via `coaching.assistant.execution_safety`. Les contrôles de risque s'appuient sur `coaching.assistant.response_safety`. Les libellés de proposition et leur rendu sont de la présentation. Aucun seuil sportif ou calcul de recommandation n'a été identifié dans les blocs examinés.
- `ai/execution_plan.py` (désormais dans `coaching/assistant/execution_plan.py`) : interprète l'intention conversationnelle, extrait les dates/périodes explicitement données et prépare les appels. Cette couche est de l'orchestration conversationnelle, pas un moteur de calcul d'entraînement. Les limites et valeurs par défaut des périodes sont appliquées par les services Coach.
- Adaptateurs activité, charge, tendances, récupération, course, contraintes, exécution et profil : validation de schémas d'entrée, appel des services injectés et sérialisation des résultats. Les calculs/états de couverture examinés sont fournis par les modèles et services Coach.

### Correctif concret

Un défaut de regex a été repéré dans `_COACH_ACTIONABLE_GUIDANCE` : la borne de mot finale était échappée deux fois, donc les formulations de conseil n'étaient pas détectées comme prévu. La séparation de la première phrase utilisait également un échappement incorrect de `\s`. Les deux expressions sont corrigées. Des tests ciblés couvrent maintenant :
- une recommandation placée après une phrase de contexte ;
- une réponse purement descriptive qui doit être reformulée ;
- une demande explicite de chiffres qui doit conserver son mode de restitution.

### Renforcement de l'audit statique

Le garde-fou `test_ai_package_does_not_import_persistence_or_sqlalchemy` détecte maintenant aussi les imports dynamiques statiques identifiables via `importlib.import_module("...")` et `__import__("...")`, en plus des imports Python classiques. Il empêche ainsi qu'un accès à la persistance soit masqué derrière ces deux mécanismes.

### Validation et limites

- Le commit `174dd157ee83586c83ab3f314ed1854867b27296` a passé les trois jobs CI.
- Les correctifs regex, les tests ciblés et le durcissement AST sont postérieurs ; leur CI doit être vérifiée sur le HEAD final.
- Cet audit porte sur les fichiers et responsabilités explicitement examinés. Il ne constitue pas encore une certification de chaque module IA ni de l'ensemble des duplications backend/frontend.


## 16. Suppression des dépendances internes aux anciens chemins IA

Les tests métier du routage, du plan conversationnel, des preuves et des propositions utilisent maintenant directement les modules Coach. Le benchmark expérimental importe également le routeur depuis `coaching.assistant`.

Les anciens modules `ai/argument_evidence.py`, `ai/execution_plan.py`, `ai/tool_routing.py` et `ai/data_proposals.py` restent de simples façades de compatibilité. Un test dédié vérifie l'identité des fonctions exportées avec les implémentations Coach : il n'existe donc pas de seconde implémentation à maintenir. Le test du registre vérifie de la même manière les alias historiques `AITool`, `AIToolRegistry` et `ToolStatus`.

Ce choix retire les dépendances internes inutiles aux anciens chemins IA sans casser d'éventuels imports historiques. La suppression définitive de ces façades est différée jusqu'à la décision de rupture de compatibilité ; elles ne portent aucune logique métier.


## 18. Clôture de l'audit de la frontière Coach / IA — 16 novembre 2026

### Résultat

L'audit ciblé de la séparation métier Coach / IA est clôturé sur cette branche. Le contrat d'architecture retenu et vérifié est le suivant :

- Les calculs, validations de données, règles d'entraînement, décisions, contraintes, recommandations et cycle de vie des propositions appartiennent aux services et cas d'usage Coach.
- Le package `opencoach.ai` est un adaptateur de conversation : il valide les entrées de transport, prépare les appels vers les capacités Coach et présente les résultats structurés. Il ne possède ni accès direct à la persistance ni registre métier autonome.
- Les anciens chemins `ai/*` encore exposés pour compatibilité sont des réexports testés, et non des implémentations concurrentes.
- Les routes métier Coach et les autres routes API non IA ne dépendent pas du package IA. La configuration IA est désactivée par défaut ; la construction de l'application ne doit pas initialiser de client Ollama ni contacter un fournisseur.
- Les propositions issues de la conversation restent soumises à une preuve utilisateur exacte et à une confirmation explicite avant toute écriture du profil.

### Derniers contrôles et correction

- La CI du HEAD précédent `4073f189` est verte sur les trois jobs : Python 3.13, Bash et Frontend (run GitHub Actions `43875655025`).
- Un test d'intégration vérifie que l'application répond sur `/api/health` sans construire de client Ollama.
- La validation d'une preuve de proposition exige désormais que la preuve soit contenue dans un seul message utilisateur. Une preuve artificiellement reconstruite en joignant des fragments de messages distincts est rejetée ; un test de régression couvre ce cas.
- Les contrôles AST interdisent les dépendances du domaine vers `opencoach.ai`, les dépendances IA vers SQLAlchemy/la persistance et les imports IA dans les routes métier.

### Limites explicites

Cette clôture certifie la frontière Coach / IA et les responsabilités examinées dans les modules décrits par cet audit. Elle ne prétend pas certifier ligne par ligne les 1 183 fichiers suivis dans le dépôt au HEAD audité, ni l'absence de toute duplication dans l'ensemble du backend, du frontend, des scripts et de l'infrastructure. Les façades historiques restent en place tant qu'une rupture de compatibilité n'est pas décidée. Une validation opérationnelle sur la VM Debian 13, avec base existante et synchronisations COROS/Intervals.icu réelles, reste distincte de la CI et n'est pas remplacée par ces tests.


## 19. Reprise de l'audit global du dépôt — 16 novembre 2026

### Contrôles réalisés

- Recalcul des volumes directement depuis l'arbre Git du HEAD de la branche.
- Vérification de la présence réelle des répertoires d'archives mentionnés dans les anciennes notes.
- Vérification du rôle du répertoire racine `backend/` et du point d'entrée de packaging Python.
- Comparaison des responsabilités entre le chargeur central des seuils et les tolérances propres à l'évaluation d'exécution des séances.
- Revue des tailles des plus gros modules backend et frontend pour établir un ordre d'audit fondé sur le coût de maintenance.

### Décisions

Aucun module métier n'est supprimé sur la base de sa taille ou de son ancienneté. Les premiers candidats à la revue fonctionnelle sont l'API COROS, le mapper de séances COROS, les routes de séances d'entraînement et les gros composants frontend de profil, entraînement et activités. La prochaine étape doit cartographier leurs fonctions, appels, imports et responsabilités avant toute extraction.

Le marqueur vide `backend/.gitkeep` a été retiré après vérification des points d'entrée de packaging et d'installation. L'absence de `.refactor-backup/` sur cette branche est constatée, mais aucune conclusion n'est tirée sur les autres branches.

### Portée

Cette étape est un inventaire reproductible et une clarification des faux positifs de duplication. Elle ne constitue pas encore une revue exhaustive des 1 183 fichiers et ne certifie pas l'absence de code mort dans les modules non examinés.


### Correctif opérationnel identifié pendant l'audit global

Le script de déploiement frontend acceptait `OPENCOACH_WEB_ROOT`, mais le script de rollback utilisait encore systématiquement `/var/www/opencoach`. Avec une racine web personnalisée, le déploiement et le rollback ne ciblaient donc pas le même répertoire. Le rollback utilise maintenant la même variable et rejette les chemins relatifs. Le test shell du déploiement couvre cette cohérence.


### Nettoyage ciblé et validation

- `_extract_scheduled_workouts_for_date()` dans `api/coros.py` n'avait aucun appel de production : il n'était appelé que par un test. Il répétait une partie du parcours de parsing déjà centralisé dans `_extract_scheduled_workout_records_for_date()`. La fonction inutilisée et son assertion dédiée ont été retirées ; les tests conservent la couverture du parseur canonique utilisé par les routes.
- Le script de rollback frontend utilise maintenant `OPENCOACH_WEB_ROOT`, comme le déploiement, et refuse une valeur relative. Le test shell vérifie explicitement cette cohérence.
- CI du commit `4908e8ef` : **3 171 tests Python réussis**, Bash et Frontend réussis (run GitHub Actions `43877822007`). Les deux warnings Python sont des avertissements de dépréciation des dépendances de test.

Ces changements retirent un vrai chemin de parsing mort et corrigent une incohérence de déploiement sans toucher aux règles métier ni à la synchronisation COROS.
