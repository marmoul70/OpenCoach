# Envoi des séances OpenCoach vers COROS

## Objectif

Permettre l'envoi explicite d'une séance planifiée OpenCoach vers le calendrier d'entraînement COROS, afin qu'elle puisse ensuite être synchronisée sur la montre.

L'envoi est individuel : aucune synchronisation automatique de toutes les séances n'est déclenchée.

## Audit de l'existant

### Création des séances OpenCoach

OpenCoach dispose de deux flux distincts :

- La saisie manuelle du calendrier sert principalement à enregistrer une activité déjà réalisée. Elle renseigne les métadonnées générales (sport, durée, distance, D+, intensité et zone cardiaque), mais ne construit pas de structure d'intervalles exploitable par une montre.
- Le moteur de planification et de génération du coach crée des séances planifiées avec une prescription structurée versionnée. Celle-ci conserve les blocs, la structure de travail, les répétitions, les récupérations et les cibles d'intensité.

La prescription est persistée dans `training_sessions.prescription`, mais elle n'était pas incluse dans la réponse de l'API des séances. Le flux d'envoi expose désormais cette donnée au frontend.

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
| Récupération chronométrée | Section 3 |
| Retour au calme | Section 4 |
| Durée | Cible en secondes |
| Distance | Cible en mètres |
| Fréquence cardiaque absolue en bpm | Intensité type 1, plage absolue |
| VMA avec allure dérivée | Intensité type 2, allure absolue en secondes/km |
| Répétitions | Groupe d'intervalles COROS |

La cible d'allure calculée pour une répétition métrique est prioritaire sur la cible générale lorsque cette donnée est explicitement présente dans la prescription. Une cible en réserve de fréquence cardiaque (HRR) n'est jamais assimilée à des bpm : elle est refusée si aucune cible absolue compatible n'est disponible.

## Limites explicites

Le convertisseur refuse une séance lorsqu'une conversion fidèle n'est pas possible. Il ne fabrique pas de cible ou de durée manquante.

- Les séances sans prescription structurée (notamment les saisies manuelles d'activités réalisées) ne sont pas éligibles.
- Les séances de renforcement, natation et autres sports non pris en charge par la création COROS MCP sont refusées.
- Une séance uniquement prescrite en RPE ne peut pas devenir une cible automatique COROS : le RPE n'est pas converti arbitrairement en fréquence cardiaque ou en allure.
- COROS impose des cibles en distance ou en dénivelé pour le trail, pas des cibles en temps. Les phases trail chronométrées et les récupérations trail chronométrées sont donc refusées.
- Les structures techniques, circuits et renforcement ne sont pas aplaties en une séance continue.
- COROS limite la création aux dates comprises entre aujourd'hui et les 90 prochains jours, dans le fuseau du compte COROS ; la validation finale de cette fenêtre est effectuée par le service COROS.
- La mise à jour et la suppression d'une séance déjà envoyée ne sont pas incluses dans cette première version. Le déplacement d'une séance envoyée ou dont le résultat est incertain est bloqué dans OpenCoach ; il doit être géré dans l'application COROS. Une séance envoyée puis modifiée dans OpenCoach ne peut pas être renvoyée comme une nouvelle séance sans créer un risque de doublon.

## Protection contre les doublons

Les colonnes suivantes sont ajoutées à `training_sessions` :

- `coros_workout_id` : identifiant de la copie planifiée COROS (`idInPlan`), conservé en interne ;
- `coros_sync_status` : `pending`, `synced`, `failed` ou `unknown` ;
- `coros_sync_started_at` : date UTC de début de la requête en cours ;
- `coros_last_synced_at` : date de confirmation ;
- `coros_payload_hash` : empreinte du contenu envoyé ;
- `coros_sync_error` : dernier message d'erreur exploitable.

L'intention d'envoi est enregistrée avant l'appel distant. Ainsi, si le processus s'arrête pendant la requête, un second clic n'envoie pas aveuglément une copie supplémentaire.

- `synced` : le même contenu ne peut pas être envoyé une seconde fois ;
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

- la conversion d'une séance continue avec échauffement et retour au calme ;
- la conversion des répétitions, distances, allures et récupérations ;
- les plages de fréquence cardiaque et les allures issues de la VMA ;
- le refus des cibles RPE seules, des séances terminées et des sports/structures non compatibles ;
- la lecture préalable du calendrier à la date cible et l'extraction des séances déjà présentes ;
- l'extraction de l'identifiant de la séance planifiée et le filtrage des autres séances du jour ;
- la distinction entre refus explicite de l'outil COROS et résultat réseau incertain ;
- l'unicité de la tête Alembic après migration.

Aucun envoi réel à COROS n'est exécuté par les tests automatisés.
