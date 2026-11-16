# ADR 0002 — Référentiel athlète centralisé et moteur Coach autonome

- **Statut :** accepté comme cible d'architecture
- **Date :** 15 novembre 2026
- **Branche de préparation :** `refactor/architecture-cleanup`

## Contexte

OpenCoach importe des données depuis plusieurs fournisseurs (notamment COROS et Intervals.icu). Les calculs de coaching ne doivent pas dépendre du fournisseur ni être dupliqués dans les intégrations ou dans l'IA.

L'application dispose déjà de référentiels internes :
- les activités sont persistées via `ActivityRepository` ;
- les données quotidiennes de santé/récupération sont persistées via `WellnessRepository` ;
- les séances planifiées et leurs métadonnées de synchronisation sont gérées par `TrainingSessionRepository` ;
- les courses, profils, contraintes et plans hebdomadaires disposent de repositories dédiés.

Le parcours COROS observé dans `integrations/coros/sync.py` appelle `upsert_coros_activity` pour intégrer les activités et `SqlWellnessRepository.save_wellness_day` pour les données Wellness. Le parcours Intervals.icu observé dans `integrations/intervals/sync.py` utilise `ActivityRepository.save_activity` et `WellnessRepository.save_wellness_day`. Les deux fournisseurs alimentent donc déjà des modèles internes communs pour ces domaines.

## Décision

### 1. Les fournisseurs sont des sources, pas des moteurs métier

COROS, Intervals.icu et les futures intégrations sont responsables de :
- authentification et communication fournisseur ;
- récupération, pagination et reprise des imports ;
- mapping/normalisation du format fournisseur vers les modèles OpenCoach ;
- traçabilité de provenance, identifiants externes, horodatages et erreurs de synchronisation ;
- persistance idempotente dans les repositories canoniques.

Ils ne calculent pas les indicateurs de coaching propres à OpenCoach.

### 2. OpenCoach centralise les données canoniques

Les repositories OpenCoach constituent la frontière de stockage partagée. Les services métier lisent ces données indépendamment de leur fournisseur d'origine.

Principaux domaines :
- activités et détails d'activité ;
- Wellness quotidien et métriques de récupération ;
- séances planifiées et exécutions ;
- profils et paramètres physiologiques ;
- courses et objectifs ;
- contraintes et disponibilités ;
- mesures/tests physiologiques ;
- plans, charge, historique et notifications.

Les données brutes propres aux fournisseurs peuvent être conservées pour audit, synchronisation et reconstruction, mais ne doivent pas devenir une deuxième source de vérité pour les calculs sportifs.

### 3. Le Coach est le seul propriétaire des calculs et décisions

Les services du Coach consomment les repositories canoniques et fournissent des résultats structurés. Cela couvre notamment :
- physiologie et zones ;
- charge réelle, estimée, planifiée et projetée ;
- readiness, récupération, tendances et qualité des données ;
- analyse de l'historique et de l'exécution ;
- calendrier, préparation des objectifs et contraintes ;
- génération et adaptation des plans/séances.

L'interface web et les API métier peuvent appeler ces services sans dépendre du LLM.

### 4. L'IA est un client du Coach

L'IA :
1. comprend la question ;
2. choisit une capacité explicitement autorisée ;
3. appelle le service Coach via un contrat stable ;
4. reçoit un résultat métier calculé et contextualisé ;
5. formule une réponse compréhensible en respectant les limites et avertissements du résultat.

L'IA ne doit pas :
- exécuter des requêtes SQL métier ;
- recalculer les métriques, couvertures ou scores ;
- réinterpréter une règle de décision ou une politique d'entraînement ;
- inventer une donnée absente ;
- écrire directement dans les repositories ou fournisseurs.

Les outils IA restent des adaptateurs minces. Les validations de sécurité, listes blanches, authentification et contrôle de l'athlète restent obligatoires.

## Architecture cible

```text
COROS ─────┐
           ├─> Adaptateurs d'intégration ─> Repositories canoniques OpenCoach
Intervals ─┘                                  │
Autres sources ───────────────────────────────┘
                                              │
                                      Services métier Coach
                                              │
                                  API métier / Interface utilisateur
                                              │
Question utilisateur ─> IA ─> capacités Coach┘
                           │
                           └─> explication des résultats Coach
```

## Règles de migration

- Pas de big-bang risqué sur les tables ou les modèles de données.
- Réutiliser les repositories et services existants avant de créer une nouvelle abstraction.
- Migrer les outils IA un par un, en conservant les noms, arguments et payloads existants autant que possible.
- Tout calcul déplacé vers le Coach doit être couvert par des tests de caractérisation comparant les résultats avant/après.
- Les identifiants d'athlète doivent provenir du contexte authentifié, jamais du modèle.
- Conserver la provenance, la fraîcheur, les conflits et la couverture des données dans les résultats métier.
- Ne pas agréger des métriques partielles comme si elles étaient complètes.
- Préserver les scénarios d'idempotence et de réconciliation COROS/Intervals.icu.
- La CI doit être verte sur le dernier commit ; les tests opérationnels des synchronisations et la VM restent des validations distinctes.

## Conséquences

- Les services Coach deviennent le point de passage unique pour l'analyse sportive.
- Les intégrations restent interchangeables et peuvent être enrichies sans changer les règles de coaching.
- L'IA devient remplaçable (Ollama, autre modèle, ou absence d'IA) sans perte des fonctions métier.
- Les outils IA actuellement couplés à SQLAlchemy sont des écarts d'architecture à migrer, notamment `ai/coaching_tools.py` et `ai/race_tools.py`.
- Le chantier n'est considéré terminé que lorsque les fonctions métier essentielles sont accessibles hors IA et que les outils IA ne contiennent plus de calcul métier ni d'accès SQL direct.


## 5. Frontière stricte : zéro logique métier dans l'IA

Cette règle précise et renforce la décision initiale : **le package `opencoach.ai` ne contient aucune logique métier, même lorsqu'elle ne fait que composer des services existants.** L'objectif n'est pas seulement d'éviter les calculs dupliqués : l'IA ne doit être propriétaire d'aucune règle du Coach.

Un adaptateur IA peut uniquement :
- déclarer et valider le schéma technique des arguments nécessaires à l'appel ;
- récupérer l'identité de l'athlète depuis le contexte authentifié (jamais depuis le LLM) ;
- transmettre les paramètres à une capacité applicative Coach existante ;
- convertir le résultat déjà calculé en contrat de transport, sans réinterpréter son sens ;
- traduire les erreurs techniques en résultats d'outil contrôlés.

Un adaptateur IA ne peut notamment pas :
- calculer des périodes métier, fenêtres, agrégats, moyennes, couvertures, ratios ou scores ;
- sélectionner les métriques ou les fenêtres qui constituent une analyse métier ;
- appliquer des seuils, statuts, règles de complétude, masquage conditionnel ou priorités ;
- construire des avertissements métier à partir des valeurs retournées ;
- agréger plusieurs repositories pour fabriquer une capacité métier ;
- décider qu'une donnée est exploitable, partielle, périmée ou insuffisante ;
- effectuer de lecture ou écriture SQL métier directe.

Ces responsabilités appartiennent à la capacité Coach existante qui les possède déjà. Si une orchestration métier est réellement absente, elle doit être ajoutée au domaine Coach approprié **après recherche de l'équivalent existant** et en étendant celui-ci lorsque c'est cohérent. Il est interdit de créer un second service qui reproduit une capacité déjà disponible.

Les payloads IA ne doivent pas réinventer les règles : le service Coach doit retourner les faits, statuts, avertissements et données de qualité nécessaires. L'adaptateur ne fait que les transporter. Les prompts peuvent expliquer au modèle comment formuler une réponse, mais ne sont jamais l'autorité pour une règle métier.
