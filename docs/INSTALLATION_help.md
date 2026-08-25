# Installation, réinstallation et mise à niveau d’OpenCoach

Ce document décrit la procédure de référence pour installer OpenCoach, mettre à niveau une installation existante et reconstruire complètement l’application sur une nouvelle machine virtuelle.

L’objectif est qu’une VM Debian 13 neuve, le dépôt Git, la configuration locale et une sauvegarde des données suffisent à remettre OpenCoach en service.

> **Principe important**
>
> Toute dépendance nécessaire au fonctionnement d’OpenCoach doit être intégrée aux scripts de bootstrap. Une installation ne doit pas dépendre d’une suite de commandes manuelles connue uniquement de la machine de développement.

---

## 1. Architecture de déploiement

OpenCoach comprend principalement :

- un backend Python / FastAPI ;
- une base SQLite gérée avec SQLAlchemy et Alembic ;
- un frontend React / TypeScript / Vite ;
- Nginx pour servir le frontend et faire reverse proxy vers l’API ;
- des unités systemd pour les services OpenCoach ;
- un timer de synchronisation Intervals.icu.

En exploitation, le backend FastAPI écoute uniquement sur l’interface locale :

```text
127.0.0.1:8000
```

Nginx constitue le point d’entrée HTTP :

```text
Navigateur
    |
    v
Nginx :80
    |
    +---- / --------> Frontend OpenCoach
    |
    +---- /api/ ----> FastAPI 127.0.0.1:8000
```

L’accès depuis le réseau local se fait donc simplement avec :

```text
http://ADRESSE_IP_DU_SERVEUR
```

Il n’est pas nécessaire d’ajouter `:8000` ou `:5173`.

---

## 2. Environnement de référence

L’installation OpenCoach actuelle cible :

- Debian 13 ;
- Python 3.13 ;
- environnement virtuel Python `.venv` ;
- Node.js ;
- npm ;
- Nginx ;
- systemd ;
- Git ;
- SQLite.

Les scripts de bootstrap vérifient l’environnement et installent les paquets système déclarés par le projet.

---

## 3. Scripts principaux

### Installation complète

```bash
sudo ./scripts/bootstrap/install.sh
```

### Installation complète en environnement de développement

```bash
sudo ./scripts/bootstrap/install.sh --dev
```

Le mode `--dev` installe également les dépendances de développement.

### Mise à niveau

```bash
sudo ./scripts/bootstrap/upgrade.sh
```

### Mise à niveau en développement

```bash
sudo ./scripts/bootstrap/upgrade.sh --dev
```

### Mise à niveau avec récupération Git

```bash
sudo ./scripts/bootstrap/upgrade.sh --pull
```

### Mise à niveau développement avec récupération Git

```bash
sudo ./scripts/bootstrap/upgrade.sh --dev --pull
```

L’option `--pull` est volontairement explicite. Le script ne doit pas modifier le dépôt Git sans demande. La récupération utilise un fast-forward uniquement afin d’éviter la création automatique d’un merge pendant un déploiement.

---

## 4. Installation complète sur une nouvelle VM

Cette procédure est celle à suivre lorsqu’on repart entièrement de zéro.

### 4.1 Créer la VM

Installer une nouvelle VM sous Debian 13.

Une fois connecté :

```bash
sudo apt update
sudo apt upgrade -y
```

Git est nécessaire pour récupérer OpenCoach :

```bash
sudo apt install -y git
```

Les autres dépendances applicatives doivent être prises en charge par le bootstrap OpenCoach.

### 4.2 Récupérer le dépôt

Créer le répertoire de travail :

```bash
mkdir -p ~/Projects
cd ~/Projects
```

Cloner OpenCoach :

```bash
git clone https://github.com/marmoul70/OpenCoach.git
```

Entrer dans le projet :

```bash
cd OpenCoach
```

Contrôler le dépôt :

```bash
git status
```

### 4.3 Créer la configuration locale

Le fichier `.env` contient la configuration propre à l’instance et ne doit pas être versionné.

Créer le fichier à partir de l’exemple :

```bash
cp .env.example .env
```

Puis l’éditer :

```bash
nano .env
```

Renseigner les paramètres nécessaires à l’installation, notamment les secrets et paramètres d’intégration propres à l’instance.

#### Règle de sécurité

Ne jamais ajouter `.env` au dépôt Git.

Les informations nécessaires pour reconstruire ce fichier doivent être conservées séparément et de manière sécurisée.

### 4.4 Lancer l’installation

Pour une VM de développement :

```bash
sudo ./scripts/bootstrap/install.sh --dev
```

Pour une installation sans dépendances de développement :

```bash
sudo ./scripts/bootstrap/install.sh
```

Pour la VM de développement principale d’OpenCoach, la commande de référence est :

```bash
sudo ./scripts/bootstrap/install.sh --dev
```

### 4.5 Ce que fait `install.sh`

Le bootstrap orchestre l’installation complète :

```text
Validation de Debian
        |
        v
Vérification / installation des paquets système
        |
        v
Installation applicative
        |
        +--> environnement virtuel Python
        +--> dépendances Python verrouillées
        +--> dépendances frontend
        +--> build Vite
        +--> migrations Alembic
        |
        v
Installation des services
        |
        +--> systemd
        +--> backend FastAPI
        +--> synchronisation Intervals
        +--> frontend compilé
        +--> Nginx
        |
        v
OpenCoach opérationnel
```

Le bootstrap doit être préféré à une installation manuelle composant par composant.

---

## 5. Installation applicative seule

Le script :

```bash
sudo ./scripts/bootstrap/install-application.sh
```

permet de préparer la partie applicative.

En développement :

```bash
sudo ./scripts/bootstrap/install-application.sh --dev
```

Il prend notamment en charge :

- la création ou la réutilisation de `.venv` ;
- la mise à jour de pip ;
- l’installation du package Python OpenCoach ;
- les contraintes Python verrouillées ;
- les dépendances de développement lorsque `--dev` est utilisé ;
- `npm ci` pour le frontend ;
- `npm run build` ;
- la vérification de `frontend/dist/index.html` ;
- `alembic upgrade head`.

Ce sous-script est normalement appelé par `install.sh` ou `upgrade.sh`.

---

## 6. Installation des services seule

Le script :

```bash
sudo ./scripts/bootstrap/install-services.sh
```

redéploie les éléments d’exploitation.

Il prend notamment en charge :

- les permissions nécessaires ;
- les unités systemd OpenCoach ;
- le backend ;
- le timer de synchronisation Intervals ;
- le déploiement du frontend compilé ;
- la configuration Nginx ;
- l’activation des services.

Ce sous-script est normalement appelé automatiquement.

---

## 7. Accès à l’application

À la fin du bootstrap, OpenCoach affiche l’adresse d’accès déterminée pour le serveur.

Exemple :

```text
http://192.168.1.52
```

Depuis une autre machine du réseau :

```text
http://ADRESSE_IP_DU_SERVEUR
```

Nginx écoute sur le port HTTP standard `80`, d’où l’absence de port explicite dans l’adresse.

---

## 8. Mise à niveau d’une installation existante

Pour une installation déjà fonctionnelle, utiliser `upgrade.sh` plutôt que refaire une installation manuelle.

En développement :

```bash
sudo ./scripts/bootstrap/upgrade.sh --dev
```

Si le script doit également récupérer les nouveaux commits :

```bash
sudo ./scripts/bootstrap/upgrade.sh --dev --pull
```

### 8.1 Dépôt Git propre obligatoire

`upgrade.sh` refuse volontairement de poursuivre si le dépôt contient des modifications locales non validées.

Contrôler avant l’upgrade :

```bash
git status
```

Le résultat attendu est équivalent à :

```text
Sur la branche main
Votre branche est à jour avec 'origin/main'.

rien à valider, la copie de travail est propre
```

Ce garde-fou empêche une mise à niveau de se mélanger avec du travail local non committé.

### 8.2 Séquence de mise à niveau

Le workflow de mise à niveau est conçu pour être conservateur :

```text
Contrôle Git
        |
        v
Éventuel git pull --ff-only
        |
        v
Lecture de la révision Alembic
        |
        v
Validation / mise à niveau de l’environnement
        |
        v
Sauvegarde SQLite
        |
        v
Vérification d’intégrité du backup
        |
        v
Réinstallation / mise à jour applicative
        |
        +--> Python
        +--> npm ci
        +--> build frontend
        +--> migrations Alembic
        |
        v
Redéploiement des services
        |
        v
Vérification Alembic
        |
        v
Vérification systemd
        |
        v
Vérification HTTP frontend + API
        |
        v
Affichage de l’adresse d’accès
```

---

## 9. Sauvegarde SQLite avant migration

Avant les migrations, `upgrade.sh` réalise une sauvegarde de la base SQLite.

Les sauvegardes sont placées dans :

```text
data/backups/
```

Le nom contient un horodatage, par exemple :

```text
data/backups/opencoach-20260825-205032.db
```

La sauvegarde utilise l’API de backup SQLite et non une simple copie brute du fichier.

C’est important car la base peut fonctionner avec le journal SQLite en mode WAL.

Le backup est ensuite contrôlé avec :

```sql
PRAGMA integrity_check;
```

L’upgrade ne doit pas continuer si la sauvegarde obtenue est invalide.

---

## 10. Base de données et Alembic

### Vérifier la révision

Depuis la racine du projet :

```bash
./.venv/bin/alembic current
```

La révision attendue doit correspondre à la tête des migrations :

```text
(head)
```

### Appliquer manuellement les migrations

En cas de diagnostic :

```bash
./.venv/bin/alembic upgrade head
```

En fonctionnement normal, il n’est pas nécessaire de lancer cette commande manuellement : les scripts d’installation et d’upgrade s’en chargent.

### 10.1 URL de base personnalisée

OpenCoach permet de surcharger l’URL de base avec la variable :

```text
OPENCOACH_DATABASE_URL
```

Exemple pour une base temporaire :

```bash
OPENCOACH_DATABASE_URL="sqlite:////tmp/opencoach-test.db" ./.venv/bin/alembic upgrade head
```

### 10.2 Paramètres SQLite

Pour une base SQLite fichier, OpenCoach configure notamment :

- les clés étrangères ;
- un délai d’attente en cas de verrouillage ;
- le mode WAL.

---

## 11. Vérification des services

### Backend

```bash
systemctl status   opencoach-backend.service   --no-pager   -l
```

### Synchronisation Intervals

```bash
systemctl status   opencoach-intervals-sync.timer   --no-pager   -l
```

### Nginx

```bash
systemctl status   nginx.service   --no-pager   -l
```

### 11.1 Vérifier les ports

```bash
sudo ss -lntp
```

En déploiement normal :

- Nginx écoute sur le port `80` ;
- FastAPI écoute sur `127.0.0.1:8000` ;
- le backend ne doit pas être exposé directement en `0.0.0.0:8000`.

---

## 12. Vérifications HTTP

### Frontend

```bash
curl -I http://127.0.0.1/
```

### API

```bash
curl -s http://127.0.0.1/api/profile
```

Pour un diagnostic HTTP plus détaillé :

```bash
curl -i http://127.0.0.1/api/profile
```

---

## 13. Diagnostic Nginx

Tester la syntaxe :

```bash
sudo nginx -t
```

Redémarrer si nécessaire :

```bash
sudo systemctl restart nginx
```

Afficher les dernières erreurs :

```bash
sudo tail -100 /var/log/nginx/error.log
```

Suivre le journal :

```bash
sudo tail -f /var/log/nginx/error.log
```

---

## 14. Logs du backend

Derniers messages :

```bash
journalctl   -u opencoach-backend.service   -n 100   --no-pager
```

Suivi en temps réel :

```bash
journalctl   -u opencoach-backend.service   -f
```

---

## 15. Tests de validation

Sur une machine de développement, activer éventuellement l’environnement :

```bash
source .venv/bin/activate
```

### Suite Python

```bash
pytest -q
```

### ShellCheck

```bash
./scripts/maintenance/shellcheck.sh
```

### Installation applicative

```bash
./tests/test-install-application.sh
```

### Nginx / déploiement

```bash
./tests/test-nginx-bootstrap.sh
```

### Upgrade

```bash
./tests/test-upgrade-bootstrap.sh
```

Avant un commit :

```bash
git diff --check
```

---

## 16. Repartir complètement de zéro

Cette section constitue la procédure courte de reprise après perte de la VM.

### Étape 1 — Nouvelle VM Debian 13

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git
```

### Étape 2 — Cloner le projet

```bash
mkdir -p ~/Projects
cd ~/Projects

git clone https://github.com/marmoul70/OpenCoach.git

cd OpenCoach
```

### Étape 3 — Restaurer la configuration

```bash
cp .env.example .env
nano .env
```

Remettre les paramètres et secrets de l’ancienne installation.

### Étape 4 — Restaurer les données si nécessaire

La base principale se trouve normalement sous :

```text
data/opencoach.db
```

Les sauvegardes automatiques d’upgrade sont conservées sous :

```text
data/backups/
```

Ne pas remplacer une base pendant que le backend est susceptible d’y écrire.

Arrêter les services concernés avant une restauration manuelle :

```bash
sudo systemctl stop opencoach-backend.service
sudo systemctl stop opencoach-intervals-sync.timer
```

### Étape 5 — Lancer le bootstrap

Développement :

```bash
sudo ./scripts/bootstrap/install.sh --dev
```

Installation standard :

```bash
sudo ./scripts/bootstrap/install.sh
```

### Étape 6 — Vérifier les services

```bash
systemctl status opencoach-backend.service --no-pager
systemctl status opencoach-intervals-sync.timer --no-pager
systemctl status nginx.service --no-pager
```

### Étape 7 — Vérifier HTTP

```bash
curl -I http://127.0.0.1/
curl -s http://127.0.0.1/api/profile
```

### Étape 8 — Accéder à OpenCoach

```text
http://ADRESSE_IP_DU_SERVEUR
```

---

## 17. Repartir de zéro sans ancienne base

Si aucune base ne doit être restaurée, ne pas créer manuellement les tables.

Après configuration de `.env`, lancer :

```bash
sudo ./scripts/bootstrap/install.sh --dev
```

ou :

```bash
sudo ./scripts/bootstrap/install.sh
```

Alembic reconstruit la structure de données à partir de l’historique des migrations du dépôt.

---

## 18. Que faut-il sauvegarder hors de la VM ?

Pour pouvoir reconstruire une instance complète après une perte de la VM, conserver au minimum :

1. le code source, normalement protégé par le dépôt Git distant ;
2. les informations permettant de reconstruire `.env` ;
3. une sauvegarde récente de `data/opencoach.db` ;
4. les éventuels secrets ou identifiants d’intégration non présents dans Git ;
5. toute autre donnée locale persistante ajoutée ultérieurement au projet.

Le dépôt Git ne doit pas contenir les secrets ni la base de production.

---

## 19. Différence entre installation et upgrade

Utiliser :

```bash
sudo ./scripts/bootstrap/install.sh --dev
```

lorsque :

- la VM est neuve ;
- OpenCoach n’est pas encore installé ;
- on reconstruit complètement l’environnement.

Utiliser :

```bash
sudo ./scripts/bootstrap/upgrade.sh --dev
```

lorsque :

- OpenCoach est déjà installé ;
- le code a évolué ;
- des migrations peuvent avoir été ajoutées ;
- les dépendances ont pu changer ;
- le frontend doit être reconstruit ;
- les services doivent être redéployés.

---

## 20. Commandes de référence

### Installation neuve — développement

```bash
sudo ./scripts/bootstrap/install.sh --dev
```

### Installation neuve — standard

```bash
sudo ./scripts/bootstrap/install.sh
```

### Upgrade — développement

```bash
sudo ./scripts/bootstrap/upgrade.sh --dev
```

### Upgrade — standard

```bash
sudo ./scripts/bootstrap/upgrade.sh
```

### Upgrade avec Git

```bash
sudo ./scripts/bootstrap/upgrade.sh --pull
```

### Upgrade développement avec Git

```bash
sudo ./scripts/bootstrap/upgrade.sh --dev --pull
```

### État Git

```bash
git status
```

### Révision DB

```bash
./.venv/bin/alembic current
```

### Backend

```bash
systemctl status opencoach-backend.service
```

### Nginx

```bash
sudo nginx -t
systemctl status nginx.service
```

### Tests

```bash
pytest -q
./scripts/maintenance/shellcheck.sh
./tests/test-install-application.sh
./tests/test-nginx-bootstrap.sh
./tests/test-upgrade-bootstrap.sh
```

---

## 21. Mise à jour des dépendances Python

OpenCoach utilise deux niveaux de déclaration pour les dépendances Python.

Le fichier :

```text
pyproject.toml
```

décrit les dépendances requises par le projet et les plages de versions acceptées.

Le fichier :

```text
requirements/constraints.txt
```

contient les versions exactes validées pour OpenCoach.

Il permet d’obtenir un environnement Python reproductible lors :

- d’une nouvelle installation ;
- d’une reconstruction complète de la VM ;
- d’une mise à niveau ;
- de l’exécution de la CI GitHub.

`requirements/constraints.txt` est généré automatiquement avec `pip-tools`.

Il ne doit pas être modifié manuellement.

### 21.1 Ajouter une dépendance Python

Une nouvelle dépendance permanente ne doit pas être ajoutée uniquement avec :

```bash
pip install nom-du-paquet
```

Cette commande peut servir temporairement pour tester une bibliothèque, mais la dépendance définitive doit être déclarée dans :

```text
pyproject.toml
```

Exemple pour une dépendance applicative :

```toml
dependencies = [
    "fastapi>=0.141,<1",
    "nouvelle-bibliotheque>=1,<2",
]
```

Pour une dépendance réservée au développement :

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "pip-tools>=7.6,<8",
]
```

### 21.2 Régénérer le verrouillage

Après toute modification d’une dépendance dans `pyproject.toml`, exécuter :

```bash
./scripts/maintenance/update-python-dependencies.sh
```

Le script :

1. vérifie l’environnement virtuel OpenCoach ;
2. vérifie que `pip-tools` est disponible ;
3. régénère `requirements/constraints.txt` ;
4. verrouille les dépendances directes et transitives ;
5. verrouille également les dépendances nécessaires au build Python ;
6. exécute `pip check` ;
7. signale les erreurs avant le commit.

### 21.3 Workflow lors de l’ajout d’un package

```text
Modification de pyproject.toml
        |
        v
./scripts/maintenance/update-python-dependencies.sh
        |
        v
requirements/constraints.txt régénéré
        |
        v
Tests OpenCoach
        |
        v
Contrôle du diff
        |
        v
Commit pyproject.toml + constraints.txt
```

Après la régénération, lancer au minimum :

```bash
pytest -q
./scripts/maintenance/shellcheck.sh
git diff --check
```

Si une dépendance frontend a également été modifiée :

```bash
cd frontend
npm run lint
npm run build
cd ..
```

### 21.4 Ne pas modifier le lock manuellement

Ne jamais éditer directement :

```text
requirements/constraints.txt
```

Toute modification doit provenir de :

```bash
./scripts/maintenance/update-python-dependencies.sh
```

Cela garantit que le fichier reste cohérent avec `pyproject.toml` et que les dépendances transitives sont prises en compte.

### 21.5 Installation reproductible

Les scripts d’installation utilisent automatiquement :

```text
requirements/constraints.txt
```

avec les contraintes pip runtime et build.

La CI GitHub utilise le même fichier.

Ainsi, pour un commit OpenCoach donné :

```text
VM OpenCoach
      |
      +---- requirements/constraints.txt
      |
GitHub Actions
      |
      +---- requirements/constraints.txt
```

les deux environnements utilisent les mêmes versions Python validées.

### 21.6 Quand faut-il régénérer le lock ?

Régénérer `requirements/constraints.txt` lorsque :

- une dépendance est ajoutée dans `pyproject.toml` ;
- une dépendance est supprimée ;
- une plage de version est modifiée ;
- on souhaite volontairement mettre à jour les versions verrouillées ;
- `pip-tools` lui-même est mis à jour.

Ne pas régénérer le lock automatiquement à chaque démarrage ou à chaque installation.

Le lock représente les versions validées du projet et doit évoluer volontairement avec un commit.

---

## 22. Règles de maintenance du bootstrap

Pour conserver une installation reproductible :

- toute nouvelle dépendance système doit être déclarée dans les scripts prévus à cet effet ;
- toute nouvelle dépendance Python doit être déclarée dans `pyproject.toml` ;
- après toute modification Python, `requirements/constraints.txt` doit être régénéré avec `./scripts/maintenance/update-python-dependencies.sh` ;
- toute nouvelle dépendance frontend doit être déclarée dans `package.json` et verrouillée dans `package-lock.json` ;
- toute modification de schéma de base doit passer par Alembic ;
- les services nécessaires doivent être gérés par les scripts bootstrap ;
- une étape manuelle indispensable à l’installation doit être considérée comme une dette à automatiser ;
- les scripts Bash doivent utiliser les fonctions de log OpenCoach ;
- les scripts doivent rester vérifiables par ShellCheck et par les tests bootstrap.

---

## 23. Objectif de reproductibilité

La cible du système d’installation OpenCoach est la suivante :

> **Une VM Debian 13 neuve + le dépôt Git + la configuration locale + une sauvegarde des données doivent suffire pour reconstruire OpenCoach.**

Cette règle doit être conservée lors des évolutions futures du projet.

Le wiki intégré à l’interface pourra ultérieurement fournir une documentation plus riche sur l’API, le fonctionnement du moteur de planification, les intégrations et la configuration. La procédure de reconstruction doit néanmoins rester disponible dans le dépôt, car elle doit pouvoir être consultée même lorsqu’OpenCoach lui-même n’est plus accessible.
