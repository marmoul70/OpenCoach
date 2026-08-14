# OpenCoach — Réflexion et architecture du frontend

> Document de référence pour conserver les décisions prises lors de la conception du frontend OpenCoach.
>
> **Statut :** réflexion validée / base de conception V1
> **Date :** 13 août 2026

---

## 1. Vision générale

OpenCoach ne doit pas être conçu comme une simple application de coaching, mais comme une **plateforme modulaire et extensible**.

Le coaching sportif constitue le cœur fonctionnel initial, mais l'architecture doit permettre d'ajouter facilement de nouvelles fonctionnalités sans devoir modifier profondément le Core.

Exemples de fonctionnalités futures :

- météo ;
- suivi du sommeil ;
- santé ;
- poids et composition corporelle ;
- balances connectées ;
- nutrition et hydratation ;
- matériel ;
- vélo ;
- nouvelles sources de données ;
- nouvelles fonctionnalités de coaching.

L'objectif est de pouvoir ajouter ces fonctionnalités sous forme de **modules/plugins**.

---

# 2. Principe architectural fondamental

OpenCoach est organisé autour de trois concepts :

```text
                         OPENCOACH
                            │
              ┌─────────────┴─────────────┐
              │                           │
             CORE                       MODULES
              │                           │
     ┌────────┼────────┐       ┌──────────┼──────────┐
     │        │        │       │          │          │
   Auth     UI/API   Config  Coaching   Weather     Health
     │        │        │       │          │          │
     └────────┴────────┘       │          │          │
                               │          │          │
                            Training    Météo      Santé
```

Le **Core doit rester stable et générique**.

Les fonctionnalités métier sont portées par les modules.

---

# 3. Core OpenCoach

Le Core contient les services communs à toute l'application.

## 3.1 Responsabilités du Core

### Infrastructure

- authentification ;
- gestion des utilisateurs ;
- permissions ;
- configuration ;
- communication avec l'API ;
- gestion des erreurs ;
- stockage local ;
- synchronisation ;
- logs ;
- notifications.

### Interface

- layout général ;
- navigation ;
- barre latérale ;
- header ;
- thème clair/sombre ;
- composants UI communs ;
- modales ;
- système de notifications ;
- Dashboard.

### Services transversaux

Le Core doit également fournir :

- gestion des modules/plugins ;
- gestion des widgets ;
- moteur d'alertes ;
- moteur de recommandations ;
- préférences utilisateur ;
- système de notifications.

---

# 4. Architecture des modules

Un module doit être aussi autonome que possible.

Exemple :

```text
modules/
├── coaching/
├── training/
├── activities/
├── analysis/
├── weather/
├── health/
├── sleep/
├── nutrition/
└── equipment/
```

Les modules ne doivent pas créer une chaîne de dépendances complexe.

À éviter :

```text
weather → training → coaching → health → activities
```

À privilégier :

```text
                         CORE
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
     Weather           Training           Health
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                       Coaching
```

Les modules utilisent les contrats et services exposés par le Core.

---

# 5. Module et connecteur : deux concepts différents

Il faut distinguer clairement :

- **module fonctionnel** ;
- **connecteur / source de données**.

Un connecteur fournit des données à un module.

## Exemple

Le module Activités peut recevoir des données depuis :

```text
Suunto
Strava
Garmin
Import GPX
```

Le module Santé peut recevoir :

```text
Withings
Apple Health
Garmin
Saisie manuelle
```

Le module Météo peut utiliser une ou plusieurs API météo.

Ainsi, remplacer une source de données ne nécessite pas de réécrire le module fonctionnel.

---

# 6. Structure conceptuelle d'un module

Un module peut fournir plusieurs éléments :

```text
Module
├── Manifest
├── Pages
├── Dashboard widgets
├── Modales / détails
├── Données
├── Services
├── Settings
├── Connecteurs
├── Événements
├── Alertes potentielles
└── Recommandations potentielles
```

Le module déclare au Core ce qu'il fournit.

Exemple conceptuel :

```text
Nom : Météo
Version : 1.0
Icône : météo
Menu : Météo
Dashboard : oui
Permissions :
  - localisation
```

Le système de plugins définit le contrat technique exact ultérieurement.

---

# 7. Dashboard OpenCoach

## 7.1 Philosophie

Le Dashboard est un **résumé de toute l'application**.

Il doit être :

- simple ;
- lisible ;
- visuel ;
- coloré ;
- compréhensible en quelques secondes ;
- peu chargé ;
- orienté vers les informations importantes.

Le Dashboard ne doit pas afficher une multitude de chiffres ou de graphiques complexes.

### Principe UX

> **Résumé simple → clic → détail → page complète si nécessaire**

Architecture :

```text
             DASHBOARD
                 │
        information simple
                 │
               clic
                 ↓
              MODAL
                 │
       informations détaillées
                 │
               clic
                 ↓
          PAGE COMPLÈTE
                 │
       analyse approfondie
```

---

# 8. Dashboard personnalisable

La V1 reste volontairement simple.

L'utilisateur peut :

- afficher ou masquer un widget ;
- modifier l'ordre des widgets ;
- réinitialiser le Dashboard.

Pas de personnalisation complexe en V1 :

- pas de grille libre ;
- pas de redimensionnement libre ;
- pas de plusieurs dashboards ;
- pas de positionnement pixel-perfect.

L'architecture doit toutefois permettre une évolution future vers davantage de personnalisation.

## Modèle conceptuel d'un widget

```text
Widget
├── id
├── module
├── titre
├── icône
├── ordre
├── enabled
└── configuration
```

---

# 9. Widgets du Dashboard V1

Les widgets retenus lors de la conception sont :

1. 🌦️ Météo
2. 😴 Sommeil
3. 🤖 État de forme
4. 🛌 Repos
5. 🏃 Prochaine séance
6. 🎯 Prochain objectif
7. 💡 Conseil du jour
8. 📊 Résumé depuis le début de l'année

Les widgets restent simples et synthétiques.

Ils peuvent être activés ou désactivés par l'utilisateur.

---

# 10. Widget Météo

Le widget météo doit afficher une information immédiatement compréhensible.

Exemple :

```text
🌦️ Météo

18°C
Conditions favorables 🟢
```

Le widget doit également pouvoir afficher une **alerte météo**.

Exemple :

```text
⚠️ Fortes pluies prévues
Conditions difficiles 🟠
```

Une alerte peut être particulièrement pertinente lorsqu'elle concerne directement une séance prévue.

Exemple :

```text
⚠️ Vent fort prévu pendant votre sortie de demain.
```

Le clic ouvre les prévisions détaillées.

---

# 11. Widget Sommeil

Le widget présente un score simple.

Exemple :

```text
😴 Sommeil

82 / 100 🟢
Bonne récupération
```

Éventuellement :

```text
↗ +6 vs moyenne
```

Le détail est disponible dans une modale.

Le Dashboard ne doit pas afficher toutes les métriques de sommeil.

---

# 12. Widget État de forme

Objectif :

> Répondre rapidement à « Dans quel état suis-je aujourd'hui pour m'entraîner ? »

Exemple :

```text
🤖 État de forme

82 / 100 🟢
Bonne forme

↗ En amélioration
```

Le widget peut afficher quelques indicateurs synthétiques :

- forme ;
- fatigue ;
- récupération ;
- tendance.

Le score est un **indicateur OpenCoach**, pas une vérité médicale.

Le système doit tenir compte des données disponibles et de leur qualité.

Si certaines données manquent, OpenCoach doit pouvoir indiquer un niveau de confiance plutôt que de donner une fausse précision.

---

# 13. Widget Repos

Le widget Repos est distinct du widget Sommeil.

### Sommeil

Décrit principalement ce qui s'est passé pendant la nuit.

### Repos

Indique l'état de récupération et ce qu'OpenCoach recommande actuellement.

Exemple :

```text
🛌 Repos

🟢 BON

Récupération : 82 %

Aujourd'hui
Repos normal

Demain
Entraînement possible
```

Selon les données disponibles, le widget peut également indiquer :

```text
🟠 RÉCUPÉRATION

Repos recommandé aujourd'hui.

OpenCoach recommande de réduire
l'intensité de la séance prévue.
```

---

# 14. Widget Prochaine séance

Le widget doit répondre à :

> « Qu'est-ce que je dois faire ? »

Il affiche uniquement un résumé.

Exemple :

```text
🏃 Prochaine séance

Endurance fondamentale

1h15 • 10 km
75–80 % FC

Voir la séance →
```

Une séance de fractionné peut avoir une présentation différente :

```text
🏃 Fractionné

6 × 4 min / 2 min récupération

Zone 4
1h05

Voir la séance →
```

Une sortie longue trail :

```text
🏔️ Sortie longue

2h45 • 24 km • +1100 m

Endurance + travail en montée

Voir la séance →
```

Le widget est générique ; son contenu dépend des données fournies par les modules Coaching/Training.

---

# 15. Widget Prochain objectif

Le widget doit afficher :

- nom de l'objectif ;
- distance ;
- D+ si pertinent ;
- date ;
- objectif chronométrique si défini ;
- progression ;
- temps restant.

Exemple :

```text
🎯 Trail des Vosges

65 km • 2 800 m D+

███████████████░░░░░ 76 %

Objectif :
Terminer < 10h

18 jours
```

Le clic ouvre la page complète de l'objectif :

- date ;
- distance ;
- D+ ;
- objectif ;
- progression ;
- entraînements réalisés ;
- entraînements restants ;
- analyse OpenCoach.

---

# 16. Widget Conseil du jour

Le Conseil du jour est un élément contextuel et personnalisé.

Il peut concerner :

- entraînement ;
- récupération ;
- repos ;
- nutrition ;
- hydratation ;
- matériel ;
- trail ;
- météo ;
- objectif ;
- préparation de course.

Le système ne doit pas produire un conseil générique répétitif.

Il doit utiliser les données disponibles.

## Exemple

Données :

```text
Météo
+
Prochaine séance
+
Objectif
+
Forme
+
Préférences nutritionnelles
```

Résultat :

```text
💡 Conseil du jour

☀️ Il va faire chaud aujourd'hui.

Pour ta sortie, pars avec 2 flasques
Renoris contenant 30 g de glucides
chacune et prévois 1 barre + 2 gels
Decathlon.

Pense à boire régulièrement dès le début.

Voir pourquoi →
```

Le clic ouvre une modale expliquant la recommandation.

---

# 17. Préférences personnelles

OpenCoach doit pouvoir connaître les préférences de l'utilisateur afin de personnaliser les recommandations.

Les préférences doivent être un **service du Core**, accessible aux modules selon leurs permissions.

Exemples :

## Nutrition

- produits utilisés ;
- gels préférés ;
- barres préférées ;
- compotes ;
- boissons ;
- produits à éviter ;
- préférences d'hydratation ;
- matériel d'hydratation.

## Matériel

- chaussures ;
- sac ;
- bâtons ;
- flasques ;
- montre ;
- lampe ;
- textile ;
- autres équipements.

Le moteur de recommandations doit utiliser les préférences et produits réellement utilisés par l'utilisateur.

---

# 18. Bibliothèque personnelle de produits

OpenCoach pourra proposer une bibliothèque de produits personnels.

Exemple :

```text
🍴 Nutrition
│
├── Gels
│   ├── Decathlon
│   └── ...
│
├── Barres
│   └── ...
│
├── Boissons
│   └── ...
│
└── Compotes
    └── ...
```

Un produit peut posséder :

```text
Produit
├── nom
├── catégorie
├── glucides
├── sodium
├── caféine
├── volume
└── préférence utilisateur
```

Le moteur de recommandations peut ensuite construire un conseil à partir des produits réellement utilisés.

---

# 19. Résumé annuel

Le widget « Mon année » donne une vision globale depuis le 1er janvier.

Exemple :

```text
📊 Mon année 2026

🏃 782 km
⛰️ 28 400 m D+
⏱️ 82 h
🏋️ 67 séances
🏁 14 courses
```

Les statistiques exactes seront définies avec le modèle de données et les modules disponibles.

Une comparaison avec l'année précédente pourra être ajoutée plus tard si les données existent.

Exemple :

```text
🏃 782 km
+12 % vs 2025
```

---

# 20. Système d'alertes transversal

Le Core doit posséder un **Alert Engine** centralisé.

Les modules fournissent des événements ou des valeurs pouvant générer des alertes.

Exemples :

```text
Sommeil
   ↓
Sommeil insuffisant
   ↓
Alert Engine
   ↓
🟠 Alerte
```

```text
Poids
   ↓
Variation inhabituelle
   ↓
Alert Engine
   ↓
🟠 Alerte
```

```text
Météo
   ↓
Fortes chaleurs
   ↓
Alert Engine
   ↓
🔴 Alerte
```

```text
Entraînement
   ↓
Charge élevée
   ↓
Alert Engine
   ↓
🟠 Alerte
```

Le Core ne doit pas avoir besoin de connaître le domaine d'origine de l'alerte.

## Modèle conceptuel

```text
ALERTE
├── id
├── niveau
├── titre
├── description
├── origine
├── date
├── durée
├── action
└── statut
```

---

# 21. Niveaux d'alerte

Le système peut utiliser une hiérarchie simple :

🟢 **Vert** — situation favorable / information positive

🔵 **Bleu** — information neutre

🟠 **Orange** — attention / surveillance

🔴 **Rouge** — problème ou action nécessaire

⚪ **Gris** — donnée indisponible

La couleur doit être utilisée comme information et non comme simple décoration.

---

# 22. Exemple : suivi des chaussures

Le module Matériel doit pouvoir suivre l'utilisation des équipements.

Exemple :

```text
Asics Trabuco
────────────────────────
Date d'achat : 12/03/2026
Kilométrage : 1 200 km
Seuil conseillé : 1 000 km

État : 🔴 À remplacer
```

Le kilométrage doit pouvoir être alimenté automatiquement par les activités :

```text
Activité Suunto
      ↓
Course : 12,4 km
      ↓
Activités OpenCoach
      ↓
Chaussures utilisées
      ↓
+12,4 km
```

## Seuils personnalisables

OpenCoach ne doit pas imposer un kilométrage universel.

L'utilisateur peut définir :

```text
Seuil d'alerte : 800 km
Seuil recommandé : 1 000 km
Seuil critique : 1 200 km
```

Exemple d'alerte :

> 👟 Tes chaussures ont dépassé 1 000 km. Il serait préférable de prévoir leur remplacement.

Puis :

> 🔴 1 200 km — ces chaussures ont fortement dépassé ton seuil défini.

Le même principe pourra être utilisé pour d'autres équipements.

---

# 23. Moteur de recommandations

Le Core doit également posséder un **Recommendation Engine**.

Il combine les informations provenant des modules.

Exemple :

```text
              🌦️ Météo
                  │
              🏃 Séance
                  │
              🎯 Objectif
                  │
              🤖 Forme
                  │
          🍴 Préférences
                  │
                  ▼
       ┌─────────────────────┐
       │ Recommendation      │
       │ Engine              │
       └──────────┬──────────┘
                  │
                  ▼
          💡 Conseil du jour
```

Les recommandations peuvent concerner :

- entraînement ;
- repos ;
- récupération ;
- hydratation ;
- nutrition ;
- matériel ;
- préparation de course.

---

# 24. Architecture transversale

La vision actuelle est donc :

```text
                     OPENCOACH CORE
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       Dashboard       Alert Engine    Recommendation
                                          Engine
          │                │                │
          └────────────────┼────────────────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │
              MODULES            CONNECTEURS
                 │                   │
        ┌────────┼────────┐    ┌─────┼─────┐
        │        │        │    │     │     │
     Coaching  Weather  Health Suunto Strava ...
        │        │        │
     Training  Sleep   Nutrition
        │        │        │
    Activities Equipment Analysis
```

Les modules apportent :

- données ;
- pages ;
- widgets ;
- services ;
- événements ;
- alertes potentielles ;
- recommandations potentielles.

Le Core apporte les mécanismes communs.

---

# 25. Règles UX à conserver

Ces règles doivent guider la conception future du frontend.

### Règle 1 — Simplicité

Le Dashboard est un résumé, pas une page d'analyse.

### Règle 2 — Information progressive

```text
Résumé
  ↓
Modal
  ↓
Page détaillée
```

### Règle 3 — Couleur informative

Les couleurs indiquent l'état ou le niveau d'attention.

### Règle 4 — Personnalisation simple

V1 :

- afficher/masquer ;
- réordonner ;
- réinitialiser.

### Règle 5 — Modularité

Le Dashboard ne doit pas connaître les détails métier des modules.

### Règle 6 — Extensibilité

Ajouter un module doit pouvoir se faire sans réécrire le Core.

### Règle 7 — Données disponibles

OpenCoach ne doit pas inventer une précision lorsque les données nécessaires sont absentes.

### Règle 8 — Personnalisation

Les recommandations doivent tenir compte des préférences de l'utilisateur lorsque les données sont disponibles.

---

# 26. Architecture fonctionnelle cible

La structure fonctionnelle envisagée est :

```text
OPENCOACH
│
├── CORE
│   ├── Auth
│   ├── UI
│   ├── Navigation
│   ├── Settings
│   ├── Notifications
│   ├── Dashboard
│   ├── Module Manager
│   ├── Preferences
│   ├── Alert Engine
│   └── Recommendation Engine
│
├── MODULES
│   ├── Coaching
│   ├── Training
│   ├── Activities
│   ├── Analysis
│   ├── Weather
│   ├── Health
│   ├── Sleep
│   ├── Nutrition
│   └── Equipment
│
└── CONNECTORS
    ├── Suunto
    ├── Strava
    ├── Garmin
    ├── Withings
    ├── Apple Health
    ├── Import GPX
    └── autres à venir
```

---

# 27. Ce qui est volontairement laissé pour plus tard

Cette réflexion ne fige pas encore :

- le framework frontend définitif ;
- le design system ;
- les couleurs exactes ;
- la typographie ;
- les composants graphiques ;
- les contrats techniques exacts des plugins ;
- les API des connecteurs ;
- le modèle de données définitif ;
- les algorithmes de calcul des scores ;
- les algorithmes de recommandations ;
- les règles précises des alertes.

Ces éléments seront définis après la validation de l'architecture fonctionnelle.

---

# 28. Prochaine étape de conception

La prochaine étape consiste à définir la **navigation générale d'OpenCoach**.

Il faudra déterminer :

1. les rubriques principales ;
2. les rubriques appartenant au Core ;
3. les rubriques provenant des modules ;
4. la structure de la barre latérale ;
5. les pages principales ;
6. les pages de détail ;
7. le fonctionnement des modales ;
8. la manière dont les modules apparaissent dans la navigation.

Une fois cette étape définie, nous pourrons commencer à construire la spécification détaillée des écrans du frontend.
