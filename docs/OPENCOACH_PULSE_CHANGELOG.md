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
