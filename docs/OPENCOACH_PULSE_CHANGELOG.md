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
