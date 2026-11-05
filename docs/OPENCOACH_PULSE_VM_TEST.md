# Test isolé OpenCoach Pulse sur la VM

## Objectif

Tester le rendu frontend de la branche `feature/opencoach-pulse-design-system` sans changer le checkout, le backend, les services systemd, la base de données ou les fichiers de l'installation OpenCoach actuellement utilisée.

Le test utilise un **Git worktree séparé** et un serveur Vite sur le port **5173**. Le proxy API Vite reste celui du projet et cible le backend déjà présent sur `127.0.0.1:8000`.

## Prérequis

- Être connecté à la VM Debian.
- Avoir un clone Git local du dépôt OpenCoach avec le remote `origin) et un accès GitHub fonctionnel.
- Node.js et npm installés.
- Le backend OpenCoach habituel doit être démarré sur le port 8000 si l'on veut tester les écrans qui chargent des données.
- Le port TCP 5173 doit être libre.

## Lancer le test sans changer de branche

Depuis le dossier du clone OpenCoach déjà présent sur la VM :

```bash
git fetch origin feature/opencoach-pulse-design-system
git show FETCH_HEAD:scripts/test-pulse-frontend.sh > /tmp/test-pulse-frontend.sh
bash /tmp/test-pulse-frontend.sh
```

Le script :
1. récupère la dernière version de la branche dédiée ;
2. crée un worktree indépendant dans `~/opencoach-pulse-test` ;
3. installe les dépendances avec `npm ci`, à partir du lockfile ;
4. lance le build TypeScript/Vite ;
5. démarre le serveur frontend sur `0.0.0.0:5173).

Si le dossier `~/opencoach-pulse-test` existe déjà, le script s'arrête sans l'écraser. Un autre chemin peut être passé en premier argument :

```bash
bash /tmp/test-pulse-frontend.sh "$HOME/opencoach-pulse-test-2"
```

## Accéder à l'interface

- Depuis la VM : `http://127.0.0.1:5173`
- Depuis un appareil du même réseau : utiliser l'adresse IP locale de la VM, par exemple `http://IP_DE_LA_VM:5173`.

Le terminal affiche l'adresse détectée. Le pare-feu de la VM ou du réseau doit autoriser temporairement le port TCP 5173 pour un test depuis l'iPhone.

Pour arrêter le serveur : `Ctrl+C`.

## Périmètre et précautions

- Le frontend de test est celui de la branche Pulse.
- Les appels `/api` sont proxifiés vers le backend déjà actif sur la VM (127.0.0.1:8000). **Le backend n'est ni remplacé ni redémarré.**
- Si la version du backend actif ne correspond pas aux contrats de la branche de référence santé, certains écrans dynamiques peuvent afficher des erreurs API. Cela ne signifie pas nécessairement que le rendu Pulse est défectueux ; relever les erreurs console/réseau et les transmettre avant toute correction.
- Ne pas utiliser les actions de création, suppression, restauration de sauvegarde ou toute action métier avec des données réelles pendant ce contrôle visuel.
- Ce test ne modifie pas le service frontend actuellement utilisé par OpenCoach, la configuration Nginx, les fichiers `.env`, la base SQLite ou les services systemd.
- Le script ne réalise aucun merge et aucun déploiement.

## Nettoyage après validation

Après avoir arrêté le serveur, supprimer uniquement le worktree de test :

```bash
git worktree remove "$HOME/opencoach-pulse-test"
```

Si tu as choisi un autre chemin, remplace-le. Cela supprime le dossier de test et ses dépendances Node, pas le clone OpenCoach d'origine.

Vérifier ensuite :

```bash
git worktree list
```

## Grille de contrôle visuel

Vérifier au minimum :

- Dashboard : hiérarchie, cartes, métriques, widgets.
- Santé : cartes, graphiques, valeurs absentes, états de chargement et erreurs.
- Activités, Entraînement et Courses : listes, détails, formulaires et panneaux latéraux.
- Réglages : COROS, Intervals.icu, notifications, sauvegardes, localisation et automatisations.
- Navigation : sidebar desktop, navigation mobile, menu profil et tiroir.
- Thèmes : clair, sombre et système.
- Largeurs : mobile 320–390 px, tablette et desktop.
- Panneaux latéraux : pleine largeur mobile, largeur adaptée tablette/desktop et scroll indépendant.
- Lisibilité, contraste, textes tronqués, débordements, clavier mobile et safe areas iOS.

Noter les anomalies avec : page, appareil/largeur, thème, capture d'écran et étapes pour reproduire.

## Suite après ton feu vert

1. Corriger les défauts visuels confirmés sur la branche Pulse.
2. Refaire build, lint et CI.
3. Comparer explicitement la branche Pulse avec `feature/coros-health-recovery`.
4. Préparer le merge uniquement après ton accord.
5. Après merge, valider l'ensemble santé + interface, puis préparer un déploiement VM séparé et contrôlé.
