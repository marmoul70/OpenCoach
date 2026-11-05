# OpenCoach Pulse — journal de développement

Ce fichier est le journal append-only des décisions et livraisons du chantier. Chaque sprint doit y ajouter son état, les fichiers touchés, les contrôles exécutés et les points restant à valider.

## 2026-11-05 — Initialisation

### Décisions
- Direction visuelle validée : Balanced / Balanced / Subtle / Technical / Adaptive.
- Branche de travail créée : feature/opencoach-pulse-design-system.
- Base de travail : feature/coros-health-recovery.
- Le chantier reste isolé de la PR Santé #13 ; aucune fusion ou modification de VM sans validation utilisateur.

### Audit technique initial
- Frontend React 19, TypeScript 6, Vite 8, Tailwind CSS 4 et lucide-react.
- Thèmes déjà appliqués via data-theme et préférence persistée dans localStorage.
- Navigation adaptive déjà partiellement présente dans AppNavigation.tsx.
- SidePanel, ToastProvider, WidgetCard, DashboardHeader et DashboardSection existent.
- HealthPage.tsx contient déjà les appels Wellness/Recovery, les métriques, les tendances et les séries physiologiques ; préserver les contrats.
- TrendChart est actuellement local à HealthPage.tsx ; candidat à une abstraction partagée après définition du contrat graphique.
- Les tokens sont partiellement dispersés entre index.css, Dashboard.css et les classes Tailwind des composants.
- package.json indique 0.8.1 et package-lock.json 0.7.0 : incohérence à traiter prudemment, sans mise à jour arbitraire.

### Sprint 0
- [x] Créer la branche dédiée.
- [x] Ajouter le cahier des charges.
- [x] Ajouter le journal de développement.
- [x] Auditer les composants et le socle frontend.
- [ ] Vérifier les builds/lint dans un environnement de travail local ou CI.
- [ ] Compléter l'inventaire des composants et points d'entrée avant migration.

### Sprint 1 — en cours
- [ ] Introduire les tokens sémantiques communs.
- [ ] Importer les tokens globalement sans changer le rendu existant.
- [ ] Valider la compatibilité thèmes clair/sombre et prefers-reduced-motion.

### Contrôles
- Aucun build ni lint local n'a été exécuté à cette étape.
- Aucun fichier de la VM n'a été modifié.
- Aucun changement API, backend, base de données ou COROS n'a été effectué.

## 2026-11-05 — Sprint 1 : première couche de tokens

### Livré
- Ajout de frontend/src/design-system/tokens.css.
- Définition des tokens sémantiques de marque, statuts, typographie, espacements, rayons, transitions, surfaces Subtle et palette de graphiques Technical.
- Déclinaison clair/sombre pilotée par data-theme.
- Ajout des classes utilitaires .oc-surface et .oc-tabular pour les composants migrés.
- Respect de prefers-reduced-motion via les tokens de transition.
- Import global du fichier de tokens depuis frontend/src/index.css.

### Garde-fous
- Les styles existants ne sont pas remplacés en masse : les tokens sont introduits en parallèle afin de permettre une migration progressive.
- Aucun changement aux API, au backend, aux schémas, aux données COROS ou à la logique Santé.
- Aucun composant existant n'a encore été migré vers les nouvelles classes.

### Contrôles
- Vérification statique des fichiers modifiés et correction du sélecteur du thème clair.
- Build et lint non exécutés : aucune exécution locale du dépôt n'est disponible dans cette étape.
- Validation visuelle clair/sombre à faire avant adoption plus large.

### Suite
- Sprint 1 : contrôler le socle CSS et les tokens sur les points d'entrée réels.
- Sprint 2 : inventorier les primitives UI existantes avant de créer de nouveaux composants ; privilégier l'évolution de Card/WidgetCard/MetricTile si elles couvrent déjà le besoin.

## 2026-11-05 — Sprint 2 : premières primitives migrées

### Audit anti-doublon
- Button.tsx existait déjà avec variantes primary/secondary/ghost.
- Card.tsx existait déjà avec CardHeader et CardContent.
- Aucun nouveau Button ou Card n'a donc été créé.
- Badge, MetricCard, EmptyState et Skeleton ne sont pas présents aux chemins UI testés ; leur absence doit encore être confirmée par l'inventaire complet avant toute création.

### Livré
- Card consomme désormais les tokens sémantiques de surface, bordure, texte et ombre.
- Button consomme les tokens d'accent, de surface, de texte et de rayon.
- Hauteur minimale de Button portée à 44 px pour améliorer la cible tactile.
- API publique de Button, Card, CardHeader et CardContent conservée.
- Les classes passées via className restent disponibles pour les cas spécifiques.

### À contrôler
- Vérifier les usages de Card et Button pour repérer d'éventuelles dépendances aux couleurs implicites.
- Vérifier les styles Tailwind compilés et l'ordre de priorité des tokens.
- Migrer ensuite les composants existants (WidgetCard, SidePanel, ToastProvider) après analyse de leurs variantes et usages.
- Ne pas créer MetricCard avant d'avoir vérifié les composants métriques locaux (MetricTile, StatusCard et widgets métier).

### Validation
- Les modifications ont été poussées sur la branche GitHub dédiée.
- Aucun build/lint local exécuté ; validation CI/locale encore requise.
- Aucun merge, déploiement ou changement sur la VM.


## 2026-11-05 — Sprint 2 : migration de WidgetCard

### Audit ciblé
- Le composant métier générique existant est `frontend/src/components/widgets/WidgetCard.tsx` (et non dans `components/ui`).
- Il est utilisé pour les widgets du tableau de bord ; son contrat repose sur `WidgetDefinition` et ses statuts/accents existants.
- Aucun nouveau composant MetricCard ou Badge n'a été créé : le besoin ne justifie pas encore une duplication.

### Livré
- Ajout de la classe partagée `.oc-interactive-surface` aux tokens : élévation discrète au survol, bordure sémantique, focus clavier visible.
- Respect de `prefers-reduced-motion` : suppression de la translation et de la transition.
- Migration de la surface racine de `WidgetCard` vers `.oc-surface` et `.oc-interactive-surface`.
- Conservation des accents, statuts, libellés, icônes, interaction de détail et du contrat `WidgetDefinition`.

### Contrôles et limites
- Contrôle statique du diff : seul le style de la surface racine de WidgetCard a été remplacé.
- Build TypeScript, lint et rendu navigateur non exécutés depuis cette intervention GitHub.
- La page Santé et ses fonctions `fetchRecoveryAssessment` / `fetchWellnessTrends` restent inchangées.
- Aucun backend, schéma, API, calcul physiologique ou planning modifié.

### Suite
- Migrer SidePanel et ToastProvider sur les tokens sémantiques sans toucher à leurs comportements.
- Compléter l'inventaire des primitives réellement utilisées avant de décider si un Badge/EmptyState/Skeleton partagé est nécessaire.
- Vérifier le comportement de la navigation existante avant toute évolution responsive.


## 2026-11-05 — Sprint 2 : migration de SidePanel

### Livré
- Ajout des classes sémantiques `.oc-panel-surface` et `.oc-panel-header`.
- Migration du fond, de la bordure et de l'ombre du panneau vers les tokens clair/sombre.
- Conservation de l'animation d'ouverture/fermeture, de la fermeture Escape, du backdrop, des dimensions responsive et des callbacks.
- Pas de changement de l'API publique de `SidePanel`.

### Contrôle
- Vérification statique : les substitutions portent uniquement sur les classes de surface du panneau et de son en-tête.
- Build/lint et vérification visuelle toujours à exécuter ; ne pas considérer le sprint comme validé visuellement.


### Vérification complémentaire
- Relecture du composant après le premier commit : l'en-tête conservait encore ses anciennes classes de thème.
- Correction appliquée dans un commit distinct : l'en-tête utilise maintenant bien `.oc-panel-header`.
- Le contrôle confirme que les deux surfaces du SidePanel consomment les tokens sémantiques.


## 2026-11-05 — Sprint 2 : migration de ToastProvider

### Audit et livraison
- ToastProvider existait déjà ; aucune nouvelle infrastructure de notification créée.
- Ajout des classes sémantiques `.oc-toast`, `.oc-toast-title`, `.oc-toast-message` et `.oc-toast-close`.
- Migration de la surface, des textes et du bouton de fermeture vers les tokens clair/sombre.
- Conservation des types success/info/warning/error, de la durée, des actions, du contexte React et des rôles ARIA.
- Les couleurs de statut restent distinctes ; elles ne sont pas remplacées par une couleur neutre.

### Contrôles
- Vérification statique des substitutions de classes ; API `useToast` et `ToastInput` inchangées.
- Build/lint et test navigateur non exécutés.

## 2026-11-05 — Sprint 3 : première primitive graphique partagée

### Audit et décision
- La page Santé possédait un `TrendChart` local SVG, non réutilisable par les autres modules.
- Le projet dispose déjà de SVG natif et n'a pas besoin d'une dépendance graphique supplémentaire pour cette primitive.
- La préparation des données (filtrage par période, calcul de moyenne, formatage métier) reste dans le module Santé.

### Livré
- Création de `frontend/src/design-system/charts/LineChart.tsx`.
- Contrat générique de présentation : titre, points identifiés, libellés, formatteur, valeur récente, moyenne, libellés de période, état vide et libellé accessible.
- Affichage SVG avec grille, repères min/max, série, points et labels de dates.
- Couleurs issues des tokens `--oc-chart-*`, surfaces Subtle et chiffres tabulaires.
- Refactorisation du TrendChart local de Santé en adaptateur vers la primitive commune.

### Garde-fous Santé
- Les appels `fetchRecoveryAssessment` et `fetchWellnessTrends`, leurs paramètres, la sélection de fenêtre 7/14/30 jours et les types API restent inchangés.
- Aucune métrique, valeur absente, unité, source, série ou calcul de récupération n'a été modifié.
- Aucun calcul physiologique ou score Readiness n'a été ajouté.

### Contrôles et limites
- Relecture statique des fichiers modifiés et vérification des imports/contrats à partir du code existant.
- Build TypeScript, lint et contrôle visuel non exécutés ; le rendu SVG reste à valider en navigateur.
- Le graphique conserve la logique de tracé actuelle des points disponibles ; la gestion explicite des intervalles calendaires manquants reste un point à traiter avant d'utiliser ce composant pour des séries où la continuité temporelle doit être représentée strictement.


### Correction — continuité temporelle des séries
- Le contrat de `LineChartPoint.value` accepte désormais `number | null`.
- Le graphique découpe la ligne aux dates sans mesure : aucun zéro artificiel et aucune liaison visuelle à travers un jour manquant.
- L'adaptateur Santé construit la fenêtre calendaire complète de 7/14/30 jours et injecte `null` pour les dates absentes.
- La valeur récente et la moyenne restent calculées uniquement à partir des mesures réellement présentes.
- Si aucune mesure n'existe sur la période, le composant affiche son état vide plutôt qu'un axe artificiel.


## 2026-11-05 — Sprint 4 : widgets de données réutilisables

### Audit anti-doublon
- La page Santé possédait déjà deux présentations locales : `StatusCard` et `MetricTile`.
- Le projet n'avait pas de `MetricCard` générique dans le design system.
- La navigation adaptive est déjà présente dans `AppNavigation.tsx` : sidebar desktop, barre inférieure mobile, tiroir de navigation, profil et choix de thème. Le travail à venir porte sur l'harmonisation visuelle et l'accessibilité, pas sur une réécriture du routage.

### Livré
- Création de `frontend/src/design-system/components/MetricCard.tsx`.
- Contrat réutilisable : libellé, valeur, détail, icône, métadonnées et densité compacte.
- La carte utilise les tokens sémantiques et la primitive Card existante ; aucune palette locale ni nouvelle dépendance.
- Refactorisation des présentations `StatusCard` et `MetricTile` de Santé en adaptateurs vers `MetricCard`.
- Exports ajoutés au point d'entrée du design system.

### Préservation fonctionnelle
- Les valeurs, unités, moyennes, nombres d'échantillons et jours couverts restent préparés par HealthPage.
- Aucun appel API, type Wellness/Recovery, calcul métier ou comportement de chargement n'a été modifié.
- La carte ne calcule aucune statistique et n'interprète aucun statut.

### Décision bibliothèque graphique
- Recharts 3.x est retenu comme candidat pour les graphiques multi-séries, barres, aires et tooltips interactifs : API React composable, SVG, responsive et accessibilité clavier activée par défaut depuis la v3.
- La primitive LineChart SVG existante reste préférable pour les séries simples et légères.
- Aucune dépendance Recharts ajoutée à ce stade : on l'introduira au premier cas d'usage qui justifie réellement sa valeur, après contrôle du lockfile et du poids bundle.
- Références : https://recharts.org/ et https://recharts.github.io/en-US/guide/sizes/.

### Contrôles
- Vérification statique des contrats et imports via les fichiers GitHub.
- La CI du commit précédent `47fefbe` est terminée avec succès ; les commits du présent sprint déclenchent une nouvelle exécution CI.
- Le rendu navigateur et le build des nouveaux commits restent à confirmer.
- Aucun merge, aucune PR de fusion et aucun déploiement VM.


### Harmonisation visuelle de Santé
- Les cinq surfaces principales de HealthPage (chargement, historique, tendances, séries physiologiques et ressenti) utilisent maintenant la classe partagée `.oc-surface`.
- Les appels de données, états de chargement/erreur, filtres de période et données affichées sont inchangés.
- Les cartes de métriques utilisent `MetricCard` et les courbes utilisent `LineChart` : la page Santé consomme désormais deux primitives communes du design system.
- Les tuiles de séries horodatées restent locales pour le moment : leur contenu est plus spécifique (courant, moyenne, minimum, maximum, couverture et plage temporelle). Elles seront factorisées après définition d'un contrat de widget adapté, sans créer une abstraction trop générique.


## 2026-11-05 — Sprint 5 : cohérence inter-pages et chargement optimisé

### Performance de compilation et chargement
- Conversion des pages métier en imports dynamiques via `React.lazy` : Dashboard, Coach, Planning, Ressenti, Activités, Courses, Météo, Santé, Profils et Réglages.
- Ajout d'un fallback `Suspense` avec l'écran de chargement OpenCoach existant.
- Les contextes Training/Race et le shell de navigation restent chargés au démarrage ; les pages ne sont téléchargées qu'à leur première ouverture.
- Aucune bibliothèque graphique ajoutée, aucun changement de dépendances runtime.
- Aucun découpage manuel Vite ajouté : les chunks seront mesurés avant toute optimisation supplémentaire.

### Cohérence visuelle
- Ajout de `PageHeader`, primitive commune pour surtitre, titre, description et actions.
- Migration de Santé, Ressenti, Activités, Courses et Réglages vers `PageHeader`.
- Ajout de primitives CSS partagées : `oc-app-shell`, `oc-page-content`, `oc-page-header`, `oc-page-eyebrow`, `oc-page-title`, `oc-page-description`, `oc-section`.
- Harmonisation du fond de page pour Activités, Courses, Réglages et Planning ; le shell global utilise désormais les tokens Pulse.
- Typographie globale reliée au token `--oc-font-sans`.

### Périmètre et précautions
- Aucun endpoint, modèle, calcul d'entraînement, donnée Santé, route ou flux de navigation modifié volontairement.
- Le chargement différé peut déplacer le moment du téléchargement d'une page ; le fallback couvre cette attente.
- Le mode système de thème et les pages non encore migrées restent à auditer dans les prochains sprints.
- Les pages Coach, Dashboard, Météo, Profil et Planning nécessitent encore une harmonisation détaillée de leurs sections et composants internes.
- La bibliothèque graphique reste différée jusqu'à validation de la refonte.

### Validation
- La CI du sprint précédent avait réussi sur les changements Santé.
- Les contrôles des nouveaux commits sont en cours ; ne pas considérer cette série comme validée tant que lint, build et tests complets ne sont pas verts.
- Pas de merge, pas de déploiement VM.


## 2026-11-05 — Sprint 6 : échelle typographique unifiée

### Décision de design
- Les pages doivent partager les mêmes tailles de texte par rôle, plutôt que définir chacune leur propre taille.
- Les exceptions sont limitées aux données de performance qui nécessitent une emphase fonctionnelle (valeur principale d'un indicateur, score ou KPI).

### Livré
- Ajout de tokens typographiques sémantiques : titre de page, titre de section, titre de carte, texte courant, texte secondaire, libellé et légende.
- Ajout de classes réutilisables `.oc-type-section-title`, `.oc-type-card-title`, `.oc-type-body`, `.oc-type-secondary`, `.oc-type-label` et `.oc-type-caption`.
- Harmonisation des titres de page Coach, Profil sportif, Profil personnel et Météo sur la même classe `.oc-page-title`.
- Alignement du titre et du sous-titre du Dashboard sur les mêmes tokens.
- Harmonisation des fonds de page Profil sportif, Profil personnel et Météo avec les surfaces Pulse.

### Contrôles et limites
- Les changements portent sur la présentation uniquement ; aucune donnée, formule, API, navigation ou logique métier n'a été modifiée.
- Les sous-sections internes de Coach, Dashboard, Planning et Météo restent à auditer pour appliquer les rôles typographiques aux libellés et descriptions sans écraser les tailles des KPI.
- Validation visuelle multi-écrans et clair/sombre encore requise.


## 2026-11-05 — Sprint 7 : cohérence navigation et planning

### Livré
- Navigation desktop et mobile : surfaces, bordures et fonds translucides raccordés aux tokens Pulse clair/sombre.
- Libellés de navigation : rapprochement de l'échelle typographique commune.
- Réglages : surfaces de navigation et panneau actif harmonisés ; groupe, titre et description du panneau utilisent les rôles typographiques partagés.
- Ressenti : hiérarchie du bloc d'introduction alignée sur les tokens communs, avec contraste renforcé pour la lisibilité.
- Planning : surfaces des cartes de navigation hebdomadaire et informations secondaires rapprochées du système Pulse.

### À contrôler
- Vérifier les menus de profil, le tiroir mobile et la barre de navigation sur iOS et desktop.
- Contrôler les contrastes clair/sombre et les états actif, survol, focus et désactivé.
- Les composants de navigation conservent leurs comportements et routes ; seules les classes de présentation ont été modifiées.

## 2026-11-05 — Sprint 8 : harmonisation Dashboard et Santé

### Livré
- Page Santé : titres de sections et de cartes alignés sur les rôles typographiques Pulse.
- Page Santé : surfaces secondaires, bordures, périodes sélectionnées et textes de métadonnées raccordés aux tokens sémantiques clair/sombre.
- Page Santé : maintien des valeurs, calculs, périodes, sources COROS/Intervals et comportements de chargement/erreur ; seules les classes de présentation ont été ajustées.
- Cartes de widgets du Dashboard : titres, descriptions, métadonnées, bordures et surfaces neutres alignés sur le système Pulse.
- Les accents fonctionnels (succès, vigilance, alerte et couleurs métier) sont conservés pour garder une lecture immédiate des statuts.

### Contrôles
- Vérifier les états actif, focus et survol ainsi que les contrastes sur iPhone et desktop, en thèmes clair et sombre.
- Aucun changement de logique métier, d'API, de stockage ou de navigation.

## 2026-11-05 — Sprint 9 : cohérence des widgets principaux et navigation

### Livré
- Carte « objectif principal » et résumé hebdomadaire : surfaces, bordures, ombres, états interactifs et informations secondaires alignés sur les tokens Pulse.
- États de chargement des deux widgets raccordés aux surfaces et bordures sémantiques.
- Navigation desktop, menu profil et tiroir mobile : neutralisation des dernières couleurs fixes gris/blanc au profit des tokens de surface, texte, bordure et survol.
- Cahier des charges complété avec les contrats réellement utilisés pour Card, Button, PageHeader, WidgetCard, MetricCard et les surfaces interactives.
- Les couleurs de statut et d'accent métier sont préservées ; aucune donnée ou règle de calcul n'a été modifiée.

### À contrôler
- Vérification visuelle réelle sur iPhone, tablette et desktop, avec thèmes clair/sombre/système.
- Contrôle des états focus clavier, menu ouvert/fermé, tiroir mobile et zones tactiles.


## 2026-11-05 — Sprint 10 : cartes Coach et entraînement du jour

### Livré
- Widget d'entraînement du Dashboard : surface principale, états chargement/erreur, métriques secondaires et séparateurs raccordés aux tokens sémantiques Pulse.
- Widget Coach du jour : surfaces, bordures, textes secondaires, métriques et fonds neutres migrés vers les tokens clair/sombre.
- Les cartes interactives utilisent le contrat partagé `.oc-interactive-surface` pour le survol, le focus clavier et le respect de la réduction des animations.
- Les accents de statut (succès, vigilance, erreur), les icônes, les données, les libellés et les interactions existantes sont conservés.

### Garde-fous
- Aucune modification des hooks de récupération des données, des types de séance, des calculs de durée/charge, des règles de statut ou des callbacks.
- Aucun changement API, backend, stockage, synchronisation COROS/Intervals ou dépendance.
- Le widget de planning « Aujourd’hui » reste un composant distinct ; il n'a pas été dupliqué ni remplacé.

### Contrôles
- Relecture statique des composants après migration ; les derniers fonds et textes neutres codés en dur ont été éliminés des deux widgets ciblés.
- CI à relancer sur les derniers commits avant de considérer le sprint techniquement validé.
- Contrôle visuel iPhone/tablette/desktop et thèmes clair/sombre toujours requis.

### Complément — carte de séance du planning
- La carte « Aujourd’hui » du planning utilise désormais les surfaces, bordures et textes neutres Pulse en clair/sombre.
- Les repères de type de séance (renforcement, sortie longue/trail, intensité, endurance) et les statuts réalisé/non réalisé/à faire restent distincts.
- Les callbacks d'ouverture/ajout, les informations de séance et la synchronisation Intervals restent inchangés.


## 2026-11-05 — Sprint 11 : briefing Coach et calendrier hebdomadaire

### Livré
- Page Coach : conteneur principal, séance recommandée, rail de disponibilité, séparateurs, indicateurs et surfaces secondaires migrés vers les tokens Pulse.
- États neutres de la page Coach (titres, métadonnées, textes secondaires, fonds et bordures) harmonisés en clair/sombre.
- Calendrier hebdomadaire : cartes de jours, sélecteurs, séparateurs et textes neutres alignés sur les surfaces et la typographie sémantiques.
- Les états de statut (charge, disponibilité, séance réalisée/à faire, intensité) conservent leurs accents fonctionnels.

### Garde-fous
- Les calculs de disponibilité, charge, projections hebdomadaires, décisions du coach, données de séances, callbacks et navigation restent inchangés.
- Aucun endpoint, modèle, synchronisation COROS/Intervals ou dépendance modifié.
- Les composants et fonctions de présentation existants sont réutilisés ; aucune duplication de composant n'a été introduite.

### Contrôles
- Relecture statique des composants après migration et audit ciblé des classes neutres résiduelles.
- CI en cours sur la branche ; le sprint ne sera considéré comme validé qu'après réussite des contrôles complets.
- Contrôle visuel clair/sombre et responsive à réaliser dans un navigateur réel.


## 2026-11-05 — Sprint 12 : formulaires et panneaux de séance

### Livré
- Formulaire d'ajout de séance : surfaces, bordures, textes neutres, onglets, états vides et contrôles de saisie raccordés aux tokens Pulse clair/sombre.
- Import Intervals.icu et saisie manuelle : présentation harmonisée sans modifier les champs, validations, messages métier, appels API ou payloads.
- Panneau de guidage de séance : cartes, séparateurs, fonds secondaires, libellés et textes neutres alignés sur les tokens sémantiques.
- Le composant SidePanel partagé déjà existant est réutilisé ; aucune nouvelle primitive de panneau n'a été créée.

### Garde-fous
- Conservation des statuts, accents d'intensité, couleurs d'erreur et d'avertissement, icônes, callbacks et comportements de soumission.
- Aucun changement de schéma, endpoint, synchronisation Intervals/COROS, calcul d'entraînement ou dépendance.
- Aucun changement de la VM, aucun merge et aucun déploiement.

### Contrôles
- Audit statique des deux composants après migration : les classes neutres Tailwind restantes ont été remplacées par les variables sémantiques ; les accents fonctionnels sont conservés.
- Les états de formulaire, import, chargement, erreur, vide et saisie restent à vérifier en navigateur en clair/sombre et sur mobile.
- Build, lint et tests CI des derniers commits à confirmer avant validation technique.


## 2026-11-05 — Sprint 13 : largeur des panneaux et cockpit de séance

### Livré
- SidePanel partagé : suppression du plafond desktop de 560 px ; à partir du breakpoint tablette, largeur minimale `max(36vw, 460px)`, sans maximum fixe. Le panneau dépasse donc le tiers de l'écran et gagne encore en largeur sur les grands écrans.
- Mobile conservé en pleine largeur pour ne pas comprimer le contenu.
- En-tête, bouton de fermeture et sections repliables alignés sur les tokens sémantiques Pulse.
- Cockpit de détail de séance V3 : surfaces, bordures, textes neutres et séparateurs migrés vers les tokens clair/sombre. Les accents de charge, d'intensité, de réussite et d'alerte restent fonctionnels.

### Garde-fous
- Aucun changement aux données de séance, à la validation, aux appels API, au guidage, au débrief ou aux interactions de repli.
- Aucun nouveau composant, aucune dépendance ajoutée, aucune modification VM, aucun merge ou déploiement.

### Contrôles
- Audit statique des règles de largeur et des principales couleurs neutres du cockpit.
- Tests visuels tablette/desktop à effectuer aux largeurs 768, 1024, 1440 et 1920 px, puis contrôle mobile et thèmes clair/sombre.
- CI à confirmer après les derniers commits.


## 2026-11-05 — Sprint 14 : lisibilité du cockpit de séance

### Livré
- Résumé de séance : valeurs métriques renforcées, libellés plus lisibles et espacements adaptés à la largeur disponible.
- Cartes d'activités : meilleure lecture des données de durée, distance, dénivelé et ressenti, avec une hiérarchie plus nette.
- Débrief OpenCoach : carte structurée, objectif plus visible et texte/listes plus confortables à lire.
- Ajustements dédiés au mobile pour conserver une densité adaptée aux petits écrans.

### Garde-fous
- La grille du résumé, les données affichées, les critères de correspondance, les statuts, les sélections et les interactions restent inchangés.
- Aucun calcul, appel API, modèle, endpoint, synchronisation ou dépendance modifié.
- Aucun merge, déploiement ou changement de VM.

### Contrôles
- Relecture ciblée des composants et sélecteurs CSS ajoutés ; les styles sont limités au cockpit de détail de séance.
- Build et tests CI à confirmer après les commits du sprint.
- Vérification visuelle claire/sombre sur mobile, tablette et desktop toujours nécessaire.


## 2026-11-05 — Sprint 15 : guidage et consignes du coach

### Livré
- Étapes échauffement, cœur de séance et retour au calme : titres plus visibles et hiérarchie renforcée.
- Cartes de consignes : titres, descriptions et durées plus faciles à distinguer.
- Blocs d'intervalles : valeurs d'effort et durées de répétition mises en avant, avec chiffres alignés pour une lecture rapide.
- Cibles d'intensité : FC, VMA, vitesse, allure et effort mieux hiérarchisés sans changer les valeurs affichées.
- Panneau « Conseils & contexte » : objectif, justification, terrain, préparation, conseils et avertissements plus confortables à lire.
- Ajustements mobiles conservés pour éviter une densité excessive.

### Garde-fous
- Aucun contenu, ordre des étapes, cible d'intensité, formatage, calcul ou règle métier modifié.
- Aucun changement API, backend, stockage, synchronisation ou dépendance.
- Aucun merge, déploiement ou changement de VM.

### Contrôles
- Classes de présentation ciblées ajoutées aux éléments existants ; aucune duplication de composant.
- Audit des tokens : accent et couleurs neutres s'appuient sur les variables Pulse.
- CI à confirmer ; contrôle visuel clair/sombre et responsive à réaliser dans le navigateur.


## 2026-11-05 — Sprint 16 : hiérarchie du planning hebdomadaire

### Livré
- Cartes de séances prévues, réalisées et non réalisées : distinction visuelle renforcée par des surfaces et badges sémantiques cohérents avec les thèmes clair et sombre.
- Métadonnées de séance : lisibilité des métriques et des libellés harmonisée, avec chiffres tabulaires pour les valeurs.
- Repos et journées sans séance : états visuellement distincts des séances planifiées, sans ajouter de faux statut.
- Repères de type de séance existants (endurance, intensité, sortie longue/trail, renforcement) conservés.

### Garde-fous
- Aucun statut, calcul de charge, ordre, date, donnée de séance ou règle de planification modifié.
- Les callbacks, la navigation, les propositions de tests physiologiques et le statut de synchronisation Intervals restent inchangés.
- Aucun changement API, backend, stockage, dépendance, VM, merge ou déploiement.

### Contrôles
- Classes visuelles ciblées ajoutées aux composants existants ; aucune duplication de logique ou de composant.
- Les couleurs d'état utilisent les tokens sémantiques Pulse (success, warning, danger) et les surfaces neutres utilisent les tokens de thème.
- CI à confirmer sur les derniers commits ; contrôle visuel clair/sombre et responsive à effectuer dans le navigateur réel.


## 2026-11-05 — Sprint 17 : carte « Aujourd'hui »

### Livré
- Carte de séance prioritaire : surfaces, bordures, titres et métadonnées harmonisés avec les tokens Pulse.
- États réalisée, à faire et non réalisée : badges sémantiques cohérents avec le planning hebdomadaire.
- État sans séance : surface secondaire et contraste alignés sur le thème actif.
- Mise en page mobile : métadonnées autorisées à revenir à la ligne pour éviter les débordements.

### Garde-fous
- Les séances affichées, leurs informations, leurs statuts et leurs repères de type restent inchangés.
- Les interactions d'ouverture/ajout, la flèche, la synchronisation Intervals et les formats de durée/distance/intensité sont conservés.
- Aucun changement API, backend, stockage, dépendance, VM, merge ou déploiement.

### Contrôles
- Le composant existant est conservé ; seules des classes de présentation et des règles CSS ciblées sont ajoutées.
- Les surfaces et statuts utilisent les tokens Pulse clair/sombre.
- CI à confirmer sur les derniers commits et contrôle visuel navigateur à effectuer.
