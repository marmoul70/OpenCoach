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

## 2 bis. Inventaire quantitatif du socle

L'arbre Git contient environ 1 165 fichiers :
- 503 fichiers Python sous `app/opencoach` ;
- 164 fichiers source frontend sous `frontend/src` ;
- 380 fichiers sous `tests` ;
- 30 documents sous `docs` ;
- 38 fichiers sous `scripts`.

Les principaux ensembles backend sont :
- `planning` : 127 fichiers Python ;
- `database` : 116 ;
- `coaching` : 54 ;
- `training` : 48 ;
- `api` : 27 ;
- `ai` : 22 ;
- `integrations` : 19.

Ce volume confirme que le chantier doit être conduit par domaines avec une cartographie des dépendances. Il ne faut pas interpréter le nombre de fichiers comme une mesure directe de qualité ou de code inutile.

### Gros fichiers à examiner en priorité

Backend :
- `app/opencoach/api/ai.py` (~86 Ko) ;
- `app/opencoach/api/coros.py` (~82 Ko) ;
- `app/opencoach/api/training_sessions.py` (~40 Ko) ;
- `app/opencoach/integrations/coros/workout_mapper.py` (~41 Ko) ;
- `app/opencoach/planning/sessions/prescription/intervals.py` (~36 Ko).

Frontend :
- `frontend/src/modules/profile/AthleteProfileSections.tsx` (~96 Ko) ;
- `frontend/src/modules/weather/WeatherPage.tsx` (~53 Ko) ;
- `frontend/src/modules/training/TrainingDetails.tsx` (~53 Ko) ;
- `frontend/src/modules/activities/ActivityPage.tsx` (~51 Ko) ;
- `frontend/src/modules/races/RaceDetails.tsx` (~51 Ko).

Ces fichiers sont des candidats à une revue de responsabilités et de lisibilité, pas des candidats automatiques à la découpe. Toute extraction doit réduire le couplage et non déplacer simplement des lignes.

### Sauvegarde frontend suivie par Git

Le dépôt contient `.refactor-backup/20260831-231419/`, avec d'anciennes versions de plusieurs écrans frontend (App, Connections, Profile, Settings). Ce répertoire n'est pas une source d'exécution applicative d'après son chemin, mais il est suivi par Git. Il peut être utile comme archive de récupération ; avant suppression, comparer chaque fichier avec son équivalent courant et vérifier qu'aucune fonctionnalité unique n'y subsiste.

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
