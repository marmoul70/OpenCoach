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
| MetricCard | Mesure synthétique | label, value, unit, delta optionnel, status, freshness |
| ProgressRing | Progression | value, max, label, valueText, tone |
| PageHeader | En-tête de page | title, description, actions, eyebrow optionnel |
| EmptyState | Absence de contenu | title, description, action optionnelle |
| Skeleton | Chargement | variant, dimensions, aria-busy |
| LineChart | Série temporelle | points horodatés, unité, axes, légende, état vide |
| BarChart | Comparaison | catégories, séries, unité, axes |
| AreaChart | Volume / charge | points, unité, bornes, légende |
| TrainingLoadChart | Charge sportive | CTL/ATL/TSB selon données disponibles, sans calcul implicite non documenté |

Les composants visuels ne font pas d'appels réseau, ne calculent pas de scores physiologiques et ne modifient pas le planning. Les données et règles métier sont injectées par les modules.

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

Les choix d'implémentation (bibliothèque de graphiques, conventions de tests, éventuels déplacements de fichiers) doivent être pris après vérification du code et des dépendances existants. Ne pas ajouter de dépendance si le SVG natif couvre proprement le besoin.
