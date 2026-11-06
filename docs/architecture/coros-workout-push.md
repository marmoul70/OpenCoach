# Envoi des séances OpenCoach vers COROS

## Objectif

Conserver une prescription de coaching complète, la convertir en entraînement structuré COROS et permettre la création ou la mise à jour d'une séance individuelle dans le calendrier COROS.

Le système maître reste OpenCoach. Cette évolution ne déclenche toujours aucun envoi automatique J-1 et ne synchronise jamais une semaine entière. Le déclenchement automatique sera traité séparément après validation du moteur de prescription et du convertisseur.

## Audit de l'existant

### Création des séances OpenCoach

OpenCoach dispose de deux flux distincts :

- La saisie manuelle du calendrier sert principalement à enregistrer une activité déjà réalisée. Elle renseigne les métadonnées générales (sport, durée, distance, D+, intensité et zone cardiaque), mais ne construit pas de structure d'intervalles exploitable par une montre.
- Le moteur de planification et de génération du coach crée des séances planifiées avec une prescription structurée versionnée. Celle-ci conserve les blocs, la structure de travail, les répétitions, les récupérations et les cibles d'intensité.

La prescription est persistée dans `training_sessions.prescription`. Le format version 2 conserve, pour chaque bloc, sa phase métier, sa durée, ses cibles éventuelles et sa prescription d'intensité propre. Les formats version 1 déjà enregistrés restent lisibles.

Les phases générées sont qualifiées : échauffement, travail principal, complément facile et retour au calme. Les phases faciles reçoivent une prescription facile distincte ; elles n'héritent pas artificiellement de l'intensité du bloc principal. Les cibles RPE restent conservées dans OpenCoach même lorsqu'elles ne sont pas pilotables directement par COROS.

### Connecteur COROS existant

Le connecteur OpenCoach réutilise :

- l'autorisation OAuth COROS déjà en place ;
- le stockage chiffré des jetons ;
- le renouvellement des jetons ;
- le client MCP HTTP existant et sa découverte dynamique des outils.

Aucun second compte COROS ni nouveau secret d'API n'est nécessaire.

## Fonctionnement retenu

Le bouton **Envoyer vers COROS** est proposé sur les séances planifiées éligibles depuis les actions de séance du calendrier.

Avant l'écriture, OpenCoach interroge si disponible le calendrier COROS sur la date exacte avec `queryTrainingSchedule`. Les séances déjà présentes sont remontées dans le message de confirmation final ; elles n'empêchent pas l'ajout d'une séance supplémentaire.

L'API appelle ensuite l'outil MCP officiel `createScheduledWorkout` avec :

- la date de la séance au format `yyyyMMdd` ;
- le sport COROS ;
- le nom et la description destinés à l'athlète ;
- les phases et répétitions converties depuis la prescription OpenCoach.

Cette opération ajoute directement une séance autonome à une date du calendrier COROS. Elle ne crée pas de modèle réutilisable dans la bibliothèque COROS et ne modifie pas un plan d'entraînement COROS existant.

Après confirmation du serveur COROS, OpenCoach indique que la séance est ajoutée au calendrier. L'utilisateur doit ensuite synchroniser la montre avec l'application COROS pour récupérer le programme.

## Correspondances prises en charge

| Donnée OpenCoach | COROS |
|---|---|
| Course à pied | Sport 1 |
| Vélo | Sport 2 |
| Trail | Sport 5, sous contraintes de cibles |
| Échauffement | Section 1 |
| Travail principal | Section 2 |
| Complément facile | Section 2 |
| Récupération inter-répétitions | Section 3 |
| Retour au calme | Section 4 |
| Durée | Cible en secondes |
| Distance | Cible en mètres |
| Fréquence cardiaque absolue en bpm | Intensité type 1, plage absolue |
| VMA avec allure dérivée | Intensité type 2, allure absolue en secondes/km |
| Intensité par phase | Cible propre à la section, jamais héritée automatiquement d'une autre phase |
| Répétitions | Groupes d'intervalles COROS (20 répétitions maximum par groupe) |
| Dénivelé positif | Cible trail en mètres si la prescription fournit explicitement un D+ |
| Consignes non pilotables | Description de la séance, sans conversion arbitraire |

La cible d'allure calculée pour une répétition métrique est prioritaire sur la cible générale lorsque cette donnée est explicitement présente dans la prescription. Une cible en réserve de fréquence cardiaque (HRR) n'est jamais assimilée à des bpm : elle est refusée si aucune cible absolue compatible n'est disponible.

## Limites explicites

Le convertisseur refuse une séance lorsqu'une conversion fidèle n'est pas possible. Il ne fabrique pas de cible ou de durée manquante.

- Les séances sans prescription structurée (notamment les saisies manuelles d'activités réalisées) ne sont pas éligibles.
- Les séances de renforcement, natation et autres sports non pris en charge par la création COROS MCP sont refusées.
- Une séance uniquement prescrite en RPE ne peut pas devenir une cible automatique COROS : le RPE n'est pas converti arbitrairement en fréquence cardiaque ou en allure.
- COROS impose des cibles en distance ou en dénivelé pour le trail, pas des cibles en temps. Les phases trail chronométrées et les récupérations trail chronométrées sont donc refusées.
- Les structures techniques, circuits et renforcement ne sont pas aplaties en une séance continue.
- COROS limite la création aux dates comprises entre aujourd'hui et les 90 prochains jours, dans le fuseau du compte COROS ; la validation finale de cette fenêtre est effectuée par le service COROS.
- COROS n'accepte pas les cibles chronométrées en mode Trail : échauffement, retour au calme et récupérations trail doivent disposer d'une cible distance ou dénivelé explicite. Le convertisseur refuse la séance si cette donnée manque.
- Un bloc RPE seul reste visible dans OpenCoach et dans les consignes textuelles, mais ne peut pas être transformé en cible COROS. Si aucune autre cible physiologique compatible n'existe, l'envoi est refusé.
- Une cible D+ et une cible distance ne peuvent pas être simultanément des cibles automatiques d'une même section COROS. La cible structurée prioritaire est transmise et l'autre donnée est conservée dans la description.
- La mise à jour d'une séance autonome déjà envoyée utilise obligatoirement `queryScheduledWorkoutDetails`, vérifie `editable=true`, puis appelle `updateScheduledWorkout` avec le même `idInPlan` et le cours complet. Elle ne crée jamais une seconde séance. Si la mise à jour a un résultat réseau incertain, l'identifiant existant est conservé et la reprise reste une mise à jour, après confirmation.
- Le déplacement et la suppression d'une séance envoyée ne sont pas pris en charge par MCP ; ils doivent être gérés dans l'application COROS.

## Protection contre les doublons

Les colonnes suivantes sont ajoutées à `training_sessions` :

- `coros_workout_id` : identifiant de la copie planifiée COROS (`idInPlan`), conservé en interne ;
- `coros_sync_status` : `pending`, `synced`, `failed` ou `unknown` ;
- `coros_sync_started_at` : date UTC de début de la requête en cours ;
- `coros_last_synced_at` : date de confirmation ;
- `coros_payload_hash` : empreinte du contenu envoyé ;
- `coros_sync_error` : dernier message d'erreur exploitable.

L'intention d'envoi est enregistrée avant l'appel distant. Ainsi, si le processus s'arrête pendant la requête, un second clic n'envoie pas aveuglément une copie supplémentaire.

- `synced` : le même contenu ne peut pas être envoyé une seconde fois ; si le contenu OpenCoach change, l'élément existant est mis à jour via son identifiant COROS ;
- `failed` : le serveur COROS a explicitement refusé la requête, une nouvelle tentative est autorisée ;
- `pending` : un envoi est en cours. Une seconde requête est bloquée pendant cinq minutes.
- `unknown` ou `pending` bloqué depuis plus de cinq minutes : le résultat est incertain. L'utilisateur doit vérifier le calendrier COROS et confirmer que la séance est absente avant d'autoriser une nouvelle tentative. Si le calendrier contient déjà une séance au même titre à cette date, OpenCoach bloque également la nouvelle tentative.

Les identifiants COROS ne sont jamais affichés dans l'interface.

## API

- `POST /api/integrations/coros/workouts/{session_id}/push`
- Le corps accepte `confirmed_no_duplicate: true` uniquement pour autoriser une nouvelle tentative après un résultat incertain et vérification manuelle.

Le serveur vérifie dynamiquement que l'outil `createScheduledWorkout` est disponible dans le catalogue MCP connecté et que son schéma expose les arguments requis.

## Validation

Les tests couvrent :

- la conversion d'une séance continue avec échauffement, complément facile et retour au calme ;
- la conservation et la validation des phases et prescriptions individuelles version 2, avec compatibilité du format version 1 ;
- la conversion des répétitions, distances, allures, récupérations et découpage des séries de plus de 20 répétitions ;
- les plages de fréquence cardiaque et les allures issues de la VMA ;
- le refus des cibles RPE seules, des séances terminées et des sports/structures non compatibles ;
- la lecture préalable du calendrier à la date cible et l'extraction des séances déjà présentes ;
- l'extraction de l'identifiant de la séance planifiée et le filtrage des autres séances du jour ;
- la distinction entre refus explicite de l'outil COROS et résultat réseau incertain ;
- la lecture de l'éditabilité d'une séance existante, la mise à jour sans création d'un doublon et la réservation SQL atomique ;
- l'unicité de la tête Alembic après migration.

Aucun envoi réel à COROS n'est exécuté par les tests automatisés.
