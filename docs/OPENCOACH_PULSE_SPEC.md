# OpenCoach Pulse — cahier des charges

- **Statut :** référence de conception validée, implémentation progressive.
- **Branche de travail :** feature/opencoach-pulse-design-system
- **Branche de référence :** feature/coros-health-recovery
- **Langue :** français.
- **Règle de livraison :** aucune fusion dans la branche Santé ni déploiement VM avant validation explicite.

## 1. Direction produit validée

OpenCoach Pulse est l'évolution visuelle de l'interface OpenCoach. L'interface doit évoquer un outil de coaching sportif sérieux : lisible, précis, moderne et cohérent, sans sacrifier la densité d'information utile.

| Axe | Choix validé |
|---|---|
| Style général | Balanced |
| Densité d'information | Balanced |
| Surfaces | Subtle |
| Graphiques | Technical |
| Navigation | Adaptive |
| Thèmes | Clair, sombre, système |
| Écrans | Mobile, tablette, ordinateur |
| Identité | Anthracite, blanc cassé, vert émeraude |

### 1.1 Surfaces — Subtle

- Fonds de page distincts des surfaces de contenu, avec un contraste doux.
- Cartes à bordure fine et ombre très discrète, sans effet glassmorphism.
- Rayon standard de carte : 16 px ; contrôles compacts : 10 à 12 px.
- Éviter les cartes imbriquées et les aplats colorés décoratifs.
- Les états (succès, vigilance, erreur, information) restent identifiables sans dépendre uniquement de la couleur.

### 1.2 Graphiques — Technical

- Axes, unités, graduations et périodes explicitement identifiables.
- Valeurs numériques alignées avec chiffres tabulaires.
- Légende et tooltip accessibles au clavier et au toucher.
- Grille discrète, séries distinctes et couleurs cohérentes avec la sémantique.
- Afficher les lacunes de données comme des lacunes, jamais comme des zéros.
- Distinguer mesure source, agrégat calculé et interprétation du coach.
- Préserver les séries temporelles et les unités de l'API.

### 1.3 Navigation — Adaptive

- Ordinateur : navigation latérale persistante.
- Mobile : navigation inférieure adaptée aux zones tactiles et aux safe areas iOS.
- Tablette : disposition selon la largeur réellement disponible.
- Conserver toutes les destinations et actions existantes (profil, réglages, météo, courses, ressenti, etc.).
- Ne pas dupliquer la logique de routage ou d'autorisation dans les éléments visuels.

## 2. Principes de conception

- Le coach reste prioritaire ; les métriques expliquent et contextualisent ses recommandations.
- Hiérarchie claire : titre, contexte, indicateur prioritaire, détail.
- Espacement de base : 4 px ; rythme usuel 8 / 12 / 16 / 24 / 32 px.
- Contenu central limité à une largeur confortable sur grand écran.
- Cibles tactiles recommandées : 44–48 px.
- Transitions courtes et sobres ; respecter prefers-reduced-motion.
- Contrastes, focus visible, navigation clavier et libellés accessibles obligatoires.
- Responsive réel : réorganisation des contenus, pas simple réduction du desktop.

## 3. Architecture cible

Le design system centralise les tokens, primitives, composants métier visuels et graphiques. Les modules conservent leurs responsabilités métier et leurs appels API.

    frontend/src/design-system/
      tokens.css
      components/
        Button/
        Card/
        Badge/
        MetricCard/
        ProgressRing/
        PageHeader/
        EmptyState/
        Skeleton/
      charts/
        LineChart/
        BarChart/
        AreaChart/
        TrainingLoadChart/
      layouts/
        AppShell/
        Sidebar/
        BottomNavigation/
      index.ts

Cette arborescence est une cible évolutive, pas une obligation de déplacer immédiatement les composants existants. Avant toute création, rechercher les composants et fonctions équivalents. Réutiliser ou adapter l'existant lorsque c'est pertinent.

## 4. Contrats des composants

| Composant | Responsabilité | Contrat minimal |
|---|---|---|
| Button | Action utilisateur | variant, size, disabled, loading, icon, children |
| Card | Surface de contenu | variant, padding, interactive, children |
| Badge | État / catégorie | tone, label, icon optionnelle |
| MetricCard | Mesure synthétique ou résumé compact | label, value, detail optionnel, icon optionnelle, metadata[], compact |
| ProgressRing | Progression | value, max, label, valueText, tone |
| PageHeader | En-tête de page | title, description, actions, eyebrow optionnel |
| EmptyState | Absence de contenu | title, description, action optionnelle |
| Skeleton | Chargement | variant, dimensions, aria-busy |
| LineChart | Série temporelle | points horodatés, unité, axes, légende, état vide |
| BarChart | Comparaison | catégories, séries, unité, axes |
| AreaChart | Volume / charge | points, unité, bornes, légende |
| TrainingLoadChart | Charge sportive | CTL/ATL/TSB selon données disponibles, sans calcul implicite non documenté |

Les composants visuels ne font pas d'appels réseau, ne calculent pas de scores physiologiques et ne modifient pas le planning. Les données et règles métier sont injectées par les modules.

### 4.1 Contrat de LineChart partagé

- Implémentation SVG native, sans dépendance graphique externe à ce stade.
- Les points portent un identifiant stable, un libellé et une valeur numérique nullable.
- Une valeur `null` représente une absence de mesure : elle crée une rupture visuelle de la ligne et ne devient jamais zéro.
- Le composant reçoit les valeurs déjà formatées et ne connaît ni les unités métier ni les règles de période.
- Le module appelant reste responsable du filtrage temporel, des agrégats métier et de la fraîcheur des données.
- La grille, les repères, les séries et les surfaces utilisent les tokens sémantiques du design system.
- Chaque graphique expose un nom accessible et des détails de points via les éléments SVG.

### 4.2 Widgets de données — contrat partagé

`MetricCard` est la primitive de départ :
- `label` et `value` obligatoires ; `value` accepte un contenu React déjà formaté.
- `detail` et `icon` facultatifs pour une mesure synthétique.
- `metadata[]` permet d'afficher des compléments alignés (moyenne, échantillons, jours couverts, etc.).
- `compact` adapte la densité pour les grilles de métriques.
- `className` permet une adaptation locale sans dupliquer le composant.
- Aucun formatage métier, calcul de delta ou interprétation de statut n'est réalisé dans la carte.

Les widgets de graphiques suivent le même principe : les modules préparent les séries, les unités, les fenêtres et les libellés ; le design system assure uniquement le rendu.

## 5. Règles de données et santé

- Conserver les contrats API et les types existants.
- Ne jamais convertir une valeur absente en zéro.
- Montrer le fournisseur, l'horodatage et la fraîcheur lorsque disponibles.
- Distinguer absence de mesure, synchronisation en cours, données périmées et erreur.
- Ne pas présenter les indicateurs comme un diagnostic médical.
- Ne pas modifier automatiquement le Readiness ou les recommandations du coach dans une refonte purement visuelle.
- Toute évolution métier doit être isolée, documentée et validée séparément.

## 6. Thèmes et responsive

- Tokens sémantiques communs aux thèmes clair et sombre.
- Le thème système suit les changements de préférence OS lorsque le réglage est system.
- Vérifier les safe areas iOS, le scroll, le clavier virtuel et les barres de navigation.
- Breakpoints et layouts basés sur l'espace disponible lorsque possible.
- Aucun texte, graphique ou tableau ne doit déborder à 320 px de largeur.

## 7. Périmètre des sprints

1. Sprint 0 — Préparation : branche dédiée, audit, documentation et garde-fous.
2. Sprint 1 — Tokens : couleurs, surfaces, typographie, espacements, thèmes.
3. Sprint 2 — Primitives : composants génériques réutilisables et harmonisation des composants existants.
4. Sprint 3 — Graphiques : API graphique commune et présentation technique.
5. Sprint 4 — Navigation : sidebar, navigation mobile et comportement adaptatif.
6. Sprint 5 — Adoption : Dashboard puis Santé, sans régression fonctionnelle.
7. Sprint 6 — Validation : lint, build, tests, contrôle visuel et tests sur VM après accord.

## 8. Critères d'acceptation

- Pas de doublon de composant sans justification documentée.
- Pas de changement non demandé des API, schémas, calculs, données COROS ou logique coach.
- Thèmes clair/sombre cohérents sur tous les composants migrés.
- Navigation utilisable au clavier et au tactile.
- Absence de données correctement représentée.
- Build TypeScript et lint sans nouvelle erreur.
- Documentation et journal de développement mis à jour à chaque sprint.
- Branche Santé indépendante ; aucune fusion ni déploiement sans validation explicite de l'utilisateur.

## 9. Décisions techniques ouvertes

La primitive `LineChart` reste en SVG natif pour les séries simples. Pour les graphiques multi-séries, aires, barres, comparaisons et tooltips interactifs, Recharts 3.x est la bibliothèque candidate : composants React composables, SVG, redimensionnement responsive et couche d'accessibilité clavier activée par défaut. La dépendance ne sera ajoutée qu'au premier besoin fonctionnel réel de ces graphiques, après vérification du lockfile et du bundle. Référence : https://recharts.org/.


## 8. Cohérence inter-pages et performance frontend

- Les pages partagent les primitives de structure `oc-app-shell`, `oc-page-content`, `oc-page-header`, `oc-page-eyebrow`, `oc-page-title`, `oc-page-description` et `oc-section`.
- Le composant `PageHeader` standardise le titre, le surtitre, la description et les actions sans imposer le contenu métier.
- Les pages fonctionnelles sont chargées à la demande avec `React.lazy` et `Suspense`. Le shell, les fournisseurs de contexte nécessaires et la navigation restent dans le bundle initial.
- Ne pas ajouter de bibliothèque graphique avant validation explicite de la refonte.
- Préférer les imports ciblés, éviter les barrels qui chargent des modules lourds et ne pas ajouter de dépendance runtime sans cas d'usage démontré.
- Laisser Vite produire les chunks à partir des imports dynamiques. Ne pas fixer de découpage manuel avant d'avoir mesuré les bundles réels.
- Toute évolution doit préserver les routes, les données, les appels API et les règles métier.
- La validation de performance doit suivre les tailles des chunks gzip/brotli, le poids du bundle initial et les temps de build. Les budgets chiffrés seront fixés après une mesure de référence CI, pas inventés.


### Échelle typographique commune

Les rôles typographiques sont définis dans les tokens `--oc-type-*` et appliqués par des classes sémantiques :
- Titre de page : `--oc-type-page-title` (24 à 30 px selon la largeur).
- Titre de section : `--oc-type-section-title` (18 px).
- Titre de carte : `--oc-type-card-title` (16 px).
- Texte courant : `--oc-type-body` (13 px).
- Information secondaire : `--oc-type-secondary` (12 px).
- Libellé : `--oc-type-label` (11 px).
- Légende : `--oc-type-caption` (10 px).

Règle : un même rôle conserve la même taille sur toutes les pages. Les KPI et valeurs de données peuvent utiliser une taille dédiée lorsqu'ils constituent le point focal d'une carte, mais ne doivent pas modifier la hiérarchie des titres et informations.

### 4.3 Contrats visuels effectivement réutilisés

- `Card` : surface neutre, bordure, rayon et ombre issus des tokens ; accepte les attributs HTML et une classe locale via `className`.
- `Button` : variantes `primary`, `secondary` et `ghost` ; conserve les attributs natifs du bouton, `disabled` et l'intégration `asChild`.
- `PageHeader` : `title` obligatoire ; `eyebrow`, `description`, `actions` et `className` optionnels. Le module garde la responsabilité du contenu et des actions.
- `WidgetCard` : reçoit une définition de widget et un callback ; l'accent et le statut sont présentés sans calcul métier dans le composant. Les états de statut restent sémantiquement distincts (neutre, succès, vigilance, alerte).
- `MetricCard` : reste la primitive commune pour les mesures et résumés ; les valeurs sont préparées par le module appelant.
- `oc-interactive-surface` : feedback hover uniquement sur les dispositifs qui le prennent en charge, focus clavier visible et respect de `prefers-reduced-motion`.

Les cartes de l'objectif de course et du résumé hebdomadaire réutilisent maintenant les surfaces interactives Pulse. Les éléments décoratifs (icônes, progressions, statuts) ne doivent pas être transformés en images de fond : l'interface privilégie les icônes vectorielles et les données réelles.
