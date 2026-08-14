# OpenCoach — Schéma de données

> Document de conception du modèle de données OpenCoach.
>
> Version : 1.0
> Statut : conception
> Base cible : PostgreSQL

---

## 1. Objectif

Ce document définit le modèle de données métier d'OpenCoach.

L'objectif est de disposer d'une structure suffisamment claire pour :

- construire le backend ;
- définir les API ;
- préparer la base PostgreSQL ;
- permettre un stockage temporaire en JSON pendant le développement ;
- conserver l'historique des données importantes ;
- permettre l'évolution future du moteur de coaching.

Le frontend ne doit pas dépendre directement de la structure physique de la base de données.

Le backend constitue la couche responsable de :

- la validation ;
- la persistance ;
- les relations entre données ;
- l'historisation ;
- les règles métier ;
- l'accès aux données.

---

## 2. Principes généraux

### 2.1 Identifiants

Les entités persistantes utilisent un identifiant unique.

Type recommandé : `UUID`.

### 2.2 Dates et heures

- Date et heure : `TIMESTAMPTZ`
- Date seule : `DATE`

### 2.3 Unités

| Donnée | Unité |
|---|---|
| Poids | kg |
| Taille | cm |
| Distance | km |
| Durée | secondes |
| Vitesse | km/h |
| Fréquence cardiaque | bpm |
| VMA | km/h |
| Glucides | g/h |
| Hydratation | ml/h |
| Sodium | mg/h |
| Dénivelé | m |

Les conversions d'affichage sont réalisées par le frontend.

---

## 3. Vue globale

```text
users
  │
  └── athlete_profiles
        │
        ├── athlete_body_metrics
        ├── athlete_physiology
        ├── training_preferences
        ├── athlete_locations
        ├── nutrition_profiles
        ├── equipment
        │     ├── shoes
        │     ├── bikes
        │     └── watches
        ├── activities
        │     └── activity_samples
        ├── training_plans
        │     └── training_sessions
        └── goals
              └── competitions
```

---

## 4. Utilisateur

### Table `users`

Représente le compte utilisateur OpenCoach.

| Champ | Type | Obligatoire | Description |
|---|---|---:|---|
| id | UUID | oui | Identifiant |
| email | VARCHAR | oui | Adresse email |
| password_hash | VARCHAR | non | Hash du mot de passe |
| created_at | TIMESTAMPTZ | oui | Date de création |
| updated_at | TIMESTAMPTZ | oui | Dernière modification |
| last_login_at | TIMESTAMPTZ | non | Dernière connexion |
| active | BOOLEAN | oui | Compte actif |

Contrainte : `email UNIQUE`.

---

## 5. Profil athlète

### Table `athlete_profiles`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| user_id | UUID | Utilisateur associé |
| first_name | VARCHAR | Prénom |
| last_name | VARCHAR | Nom |
| birth_date | DATE | Date de naissance |
| gender | VARCHAR | Sexe/genre renseigné |
| avatar_url | TEXT | Avatar |
| created_at | TIMESTAMPTZ | Création |
| updated_at | TIMESTAMPTZ | Modification |

Relation : `users 1 — 1 athlete_profiles`.

---

## 6. Données corporelles

### Table `athlete_body_metrics`

Les mesures corporelles sont historisées.

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| height_cm | NUMERIC | Taille |
| weight_kg | NUMERIC | Poids |
| recorded_at | TIMESTAMPTZ | Date de mesure |

Exemple :

```text
01/01 → 85.0 kg
15/02 → 84.2 kg
01/03 → 83.8 kg
```

---

## 7. Physiologie

### Table `athlete_physiology`

Contient les paramètres physiologiques utilisés par le moteur de coaching.

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| max_heart_rate | INTEGER | FC maximale |
| resting_heart_rate | INTEGER | FC repos |
| vma | NUMERIC | VMA km/h |
| threshold_heart_rate_1 | INTEGER | SV1 |
| threshold_heart_rate_2 | INTEGER | SV2 |
| effective_from | TIMESTAMPTZ | Début de validité |
| effective_to | TIMESTAMPTZ | Fin de validité |

Les paramètres physiologiques doivent être historisés.

---

## 8. Préférences d'entraînement

### Table `training_preferences`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| weekly_sessions | INTEGER | Séances par semaine |
| weekly_duration_minutes | INTEGER | Durée hebdomadaire |
| weekly_distance_km | NUMERIC | Distance hebdomadaire |
| fatigue_threshold | NUMERIC | Seuil de fatigue |
| experience | VARCHAR | Niveau |
| available_days | JSONB | Jours disponibles |

Valeurs prévues pour `experience` :

- `beginner`
- `intermediate`
- `advanced`
- `expert`

---

## 9. Localisation

### Table `athlete_locations`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| name | VARCHAR | Nom du lieu |
| latitude | NUMERIC | Latitude |
| longitude | NUMERIC | Longitude |
| is_primary | BOOLEAN | Localisation principale |

Une personne pourra posséder plusieurs localisations.

La localisation principale sera utilisée par défaut par le module météo.

---

## 10. Nutrition

### Table `nutrition_profiles`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| carbohydrates_per_hour | NUMERIC | Glucides g/h |
| fluids_per_hour | NUMERIC | Hydratation ml/h |
| sodium_per_hour | NUMERIC | Sodium mg/h |
| effective_from | TIMESTAMPTZ | Début |
| effective_to | TIMESTAMPTZ | Fin |

Ces données pourront être historisées.

---

## 11. Équipement

### Table `equipment`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Propriétaire |
| type | VARCHAR | Type |
| brand | VARCHAR | Marque |
| model | VARCHAR | Modèle |
| active | BOOLEAN | Matériel actif |
| created_at | TIMESTAMPTZ | Création |
| updated_at | TIMESTAMPTZ | Modification |

Types prévus :

- `shoe`
- `bike`
- `watch`

---

## 12. Chaussures

### Table `shoes`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Équipement |
| distance_km | NUMERIC | Kilométrage |
| max_distance_km | NUMERIC | Kilométrage maximal |

Relation : `equipment 1 — 1 shoes`.

---

## 13. Vélos

### Table `bikes`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Équipement |
| distance_km | NUMERIC | Kilométrage |

---

## 14. Montres

### Table `watches`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Équipement |
| device_identifier | VARCHAR | Identifiant externe éventuel |
| integration_provider | VARCHAR | Fournisseur |

Exemples futurs : Suunto, Garmin, Apple, Coros.

---

## 15. Activités sportives

### Table `activities`

Représente les activités réellement effectuées.

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| sport | VARCHAR | Sport |
| activity_type | VARCHAR | Type |
| started_at | TIMESTAMPTZ | Début |
| duration_seconds | INTEGER | Durée |
| distance_km | NUMERIC | Distance |
| elevation_gain_m | NUMERIC | D+ |
| elevation_loss_m | NUMERIC | D- |
| average_heart_rate | INTEGER | FC moyenne |
| max_heart_rate | INTEGER | FC max |
| average_speed_kmh | NUMERIC | Vitesse moyenne |
| calories | INTEGER | Calories |
| source | VARCHAR | Source |
| external_id | VARCHAR | ID externe |

Sources prévues : `manual`, `suunto`, `garmin`, `strava`, `apple`.

---

## 16. Données détaillées d'activité

### Table `activity_samples`

Pour les données volumineuses : GPS, fréquence cardiaque, altitude, cadence, puissance, température et vitesse.

```text
activity_id
sampled_at
latitude
longitude
altitude
heart_rate
speed
cadence
power
temperature
```

Cette table pourra être optimisée selon le volume réel.

---

## 17. Séances planifiées

### Table `training_sessions`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| training_plan_id | UUID | Plan associé |
| planned_at | TIMESTAMPTZ | Date prévue |
| sport | VARCHAR | Sport |
| session_type | VARCHAR | Type |
| title | VARCHAR | Nom |
| description | TEXT | Description |
| duration_seconds | INTEGER | Durée prévue |
| distance_km | NUMERIC | Distance prévue |
| completed | BOOLEAN | Terminée |
| activity_id | UUID | Activité réalisée associée |

---

## 18. Plans d'entraînement

### Table `training_plans`

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| name | VARCHAR | Nom |
| goal | TEXT | Objectif |
| start_date | DATE | Début |
| end_date | DATE | Fin |
| status | VARCHAR | Statut |

Statuts possibles :

- `draft`
- `active`
- `completed`
- `cancelled`

---

## 19. Objectifs

### Table `goals`

Un objectif peut être une course, une distance, une performance, un volume ou un objectif personnel.

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| athlete_id | UUID | Athlète |
| type | VARCHAR | Type |
| name | VARCHAR | Nom |
| target_date | DATE | Date |
| target_distance_km | NUMERIC | Distance |
| target_elevation_gain_m | NUMERIC | D+ |
| target_time_seconds | INTEGER | Temps cible |
| priority | VARCHAR | Priorité |
| status | VARCHAR | Statut |

---

## 20. Compétitions

### Table `competitions`

Une compétition est un cas particulier d'objectif.

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| goal_id | UUID | Objectif associé |
| name | VARCHAR | Nom |
| location | VARCHAR | Lieu |
| date | DATE | Date |
| distance_km | NUMERIC | Distance |
| elevation_gain_m | NUMERIC | D+ |

---

## 21. Météo et alertes

La météo temps réel appartient au domaine météo et ne doit pas être mélangée au profil athlète.

À terme :

- `weather_current`
- `weather_forecast`
- `weather_alerts`

Pour la V1, aucune persistance n'est obligatoire : le module météo peut récupérer les données auprès du fournisseur externe.

Les alertes météo seront développées dans un module séparé.

---

## 22. Paramètres OpenCoach

### Table `user_settings`

Cette table regroupe les préférences générales de l'application.

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant |
| user_id | UUID | Utilisateur |
| language | VARCHAR | Langue |
| units | VARCHAR | Système d'unités |
| timezone | VARCHAR | Fuseau horaire |
| theme | VARCHAR | Thème |
| notifications_enabled | BOOLEAN | Notifications |

Cette table ne doit pas contenir les données sportives de l'athlète.

---

## 23. Historisation

Les données suivantes doivent être historisées :

- poids ;
- FC repos ;
- FC max ;
- VMA ;
- SV1 ;
- SV2 ;
- préférences nutritionnelles.

Les valeurs courantes correspondent à la dernière entrée valide.

---

## 24. Relations principales

```text
users
 │
 └── athlete_profiles
       │
       ├── athlete_body_metrics
       ├── athlete_physiology
       ├── training_preferences
       ├── athlete_locations
       ├── nutrition_profiles
       │
       ├── equipment
       │    ├── shoes
       │    ├── bikes
       │    └── watches
       │
       ├── activities
       │    └── activity_samples
       │
       ├── training_plans
       │    └── training_sessions
       │
       └── goals
            └── competitions
```

---

## 25. Index principaux

Index recommandés :

```text
users.email
athlete_profiles.user_id
athlete_body_metrics.athlete_id
athlete_body_metrics.recorded_at
athlete_physiology.athlete_id
training_preferences.athlete_id
athlete_locations.athlete_id
equipment.athlete_id
activities.athlete_id
activities.started_at
training_sessions.athlete_id
training_sessions.planned_at
training_plans.athlete_id
goals.athlete_id
goals.target_date
activity_samples.activity_id
activity_samples.sampled_at
```

---

## 26. Suppression des données

Les relations appartenant directement à un athlète pourront utiliser `ON DELETE CASCADE`.

Exemple :

```text
users
  ↓
athlete_profiles
  ↓
athlete data
```

La suppression d'un utilisateur pourra supprimer ses données dépendantes.

Les données historiques devront toutefois être traitées avec prudence si une fonctionnalité d'archivage est ajoutée.

---

## 27. JSON de développement

Avant PostgreSQL, le backend pourra utiliser un fichier JSON représentant le même modèle logique.

Exemple :

```json
{
  "athlete": {
    "identity": {},
    "body": {},
    "physiology": {},
    "training": {},
    "location": {},
    "equipment": {
      "shoes": [],
      "bikes": [],
      "watches": []
    },
    "nutrition": {}
  }
}
```

Le JSON est une solution temporaire de développement et ne doit pas devenir le contrat définitif de stockage.

---

## 28. Repository

Le backend doit isoler l'accès aux données derrière une couche repository.

Architecture souhaitée :

```text
API
 │
 ▼
Services
 │
 ▼
Repositories
 │
 ├── JsonRepository
 │
 └── PostgresRepository
```

Pendant le développement :

```text
API
 ↓
Service
 ↓
JsonRepository
 ↓
JSON
```

Après PostgreSQL :

```text
API
 ↓
Service
 ↓
PostgresRepository
 ↓
PostgreSQL
```

Le reste de l'application ne doit pas connaître le type de stockage.

---

## 29. Évolution prévue

Le modèle pourra évoluer avec :

- import Suunto ;
- import Garmin ;
- import Strava ;
- synchronisation Apple Health ;
- récupération automatique des activités ;
- analyse de charge ;
- fatigue ;
- récupération ;
- sommeil ;
- disponibilité ;
- recommandations nutritionnelles ;
- objectifs avancés ;
- moteur de coaching ;
- notifications ;
- alertes météo ;
- recommandations liées aux conditions météo.

Ces fonctionnalités ne doivent pas être ajoutées prématurément aux tables principales.

---

## 30. Priorité d'implémentation

### V1 — Fondation

1. `users`
2. `athlete_profiles`
3. `athlete_body_metrics`
4. `athlete_physiology`
5. `training_preferences`
6. `athlete_locations`
7. `nutrition_profiles`
8. `equipment`
9. `shoes`
10. `bikes`
11. `watches`
12. `user_settings`

### V2 — Activités

13. `activities`
14. `activity_samples`

### V3 — Coaching

15. `training_plans`
16. `training_sessions`
17. `goals`
18. `competitions`

### V4 — Intégrations

- Suunto
- Garmin
- Strava
- Apple Health
- autres fournisseurs

### V5 — Intelligence de coaching

- charge d'entraînement ;
- fatigue ;
- récupération ;
- adaptation automatique ;
- recommandations ;
- nutrition ;
- météo ;
- alertes.

---

## 31. Correspondance avec le frontend actuel

Le frontend possède actuellement la structure métier :

```text
AthleteProfile
├── identity
├── body
├── physiology
├── training
├── location
├── equipment
└── nutrition
```

Cette structure reste le modèle métier frontend.

Le backend exposera une API de profil sans imposer au frontend la structure physique des tables PostgreSQL.

---

## 32. Décision actuelle

La priorité immédiate est de construire le backend autour du profil athlète.

Le stockage JSON sera utilisé comme implémentation temporaire du repository.

PostgreSQL deviendra ensuite l'implémentation persistante définitive.

Le contrat API devra rester stable lors du passage :

```text
JsonRepository
      ↓
PostgresRepository
```

Le frontend ne devra pas être réécrit pour ce changement.

---

## 33. Statut

| Domaine | État |
|---|---|
| Profil athlète | Défini |
| Données corporelles | Défini |
| Physiologie | Défini |
| Entraînement | Défini |
| Localisation | Défini |
| Nutrition | Défini |
| Équipement | Défini |
| Activités | Conception |
| Plans d'entraînement | Conception |
| Objectifs | Conception |
| Météo | Module frontend en cours |
| Alertes météo | À venir |
| PostgreSQL | À implémenter |
| Repository JSON | Prochaine étape |
| API backend | À implémenter |

---

## Conclusion

Le profil athlète constitue la fondation du système OpenCoach.

Les activités, entraînements, objectifs et données physiologiques restent des domaines distincts afin de permettre l'historisation et l'évolution du moteur de coaching.

Le stockage JSON sera utilisé comme implémentation temporaire du repository.

La base PostgreSQL deviendra ensuite l'implémentation persistante définitive.
