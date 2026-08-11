# Environnement de développement OpenCoach

## 1. Présentation

Ce document décrit l'environnement de développement et les contrôles actuellement utilisés par OpenCoach.

OpenCoach est actuellement dans sa phase de fondation technique. Les composants métier seront documentés au fur et à mesure de leur implémentation.

---

## 2. Environnement supporté

| Composant | Version / environnement |
|---|---|
| Système | Debian 13 |
| Shell | Bash |
| Gestionnaire de paquets | APT |
| Gestionnaire de versions | Git |
| Analyse statique | ShellCheck |
| Intégration continue | GitHub Actions |

La CI utilise également Debian 13 pour les tests fonctionnels.

---

## 3. Prérequis

Les composants suivants doivent être disponibles :

- Bash
- Git
- APT
- ShellCheck

Vérification :

    bash --version
    git --version
    apt --version
    shellcheck --version

---

## 4. Installation de ShellCheck

Sur Debian 13 :

    sudo apt update
    sudo apt install -y shellcheck

Vérification :

    shellcheck --version

---

## 5. Structure du projet

La structure principale actuelle est :

    OpenCoach/
    ├── backend/
    ├── docs/
    │   ├── architecture/
    │   └── setup/
    ├── frontend/
    ├── infra/
    ├── scripts/
    │   ├── bootstrap/
    │   ├── dev/
    │   ├── lib/
    │   └── maintenance/
    ├── tests/
    ├── .github/
    │   └── workflows/
    ├── LICENSE
    ├── README.md
    └── .gitignore

### backend/

Contiendra les composants backend du projet.

### frontend/

Contiendra les interfaces utilisateur du projet.

### infra/

Contiendra les éléments liés à l'infrastructure et au déploiement.

### scripts/lib/

Contient les bibliothèques Bash communes utilisées par les scripts OpenCoach.

### scripts/bootstrap/

Contient les scripts permettant de vérifier et préparer l'environnement OpenCoach.

### scripts/maintenance/

Contient les outils de maintenance et de contrôle qualité.

### tests/

Contient les tests fonctionnels des bibliothèques Bash.

### .github/workflows/

Contient les workflows GitHub Actions.

---

## 6. Tests fonctionnels

Les tests fonctionnels actuels sont regroupés dans :

    tests/test-libraries.sh

Exécution :

    ./tests/test-libraries.sh

Les tests vérifient notamment :

- la détection de Debian ;
- la détection de Debian 13 ;
- la disponibilité de Bash ;
- la disponibilité de Git ;
- le refus d'une commande inexistante ;
- le fonctionnement d'APT ;
- la disponibilité des paquets bash et git.

Résultat attendu actuellement :

    Tests réussis : 8
    Tests échoués : 0

Puis :

    [ OK ] Tous les tests sont réussis.

---

## 7. Analyse ShellCheck

Le contrôle ShellCheck est disponible avec :

    scripts/maintenance/shellcheck.sh

Exécution :

    ./scripts/maintenance/shellcheck.sh

Le script analyse le point d'entrée principal :

    scripts/bootstrap/check-environment.sh

Le contrôle suit également les bibliothèques chargées par source.

Résultat attendu :

    [ OK ] ShellCheck terminé sans erreur.

---

## 8. Vérification de la syntaxe Bash

Les scripts principaux peuvent être vérifiés avec :

    bash -n scripts/bootstrap/check-environment.sh
    bash -n scripts/maintenance/shellcheck.sh
    bash -n tests/test-libraries.sh

Une commande silencieuse indique qu'aucune erreur de syntaxe n'a été détectée.

---

## 9. Validation avant commit

Avant chaque commit, effectuer les contrôles suivants.

### 9.1 Syntaxe Bash

    bash -n scripts/bootstrap/check-environment.sh
    bash -n scripts/maintenance/shellcheck.sh
    bash -n tests/test-libraries.sh

### 9.2 ShellCheck

    ./scripts/maintenance/shellcheck.sh

### 9.3 Tests fonctionnels

    ./tests/test-libraries.sh

### 9.4 Vérification Git

    git diff --check
    git status

Tous les contrôles doivent être réussis avant de pousser une modification.

---

## 10. Intégration continue

OpenCoach utilise GitHub Actions pour automatiser les contrôles de qualité.

Le workflow est :

    .github/workflows/ci.yml

Il est exécuté lors :

- d'un push sur main ;
- d'une Pull Request vers main.

La CI effectue actuellement :

1. récupération du dépôt ;
2. installation de ShellCheck ;
3. vérification de la syntaxe Bash ;
4. analyse ShellCheck ;
5. exécution des tests fonctionnels dans Debian 13.

Le workflow doit terminer avec succès avant de considérer une modification comme validée.

---

## 11. Gestion des privilèges administrateur

Les opérations nécessitant des privilèges administrateur utilisent la fonction commune :

    run_as_root

Cette fonction permet :

- une exécution directe lorsque le script est lancé avec les privilèges administrateur ;
- l'utilisation de sudo lorsque le script est lancé par un utilisateur standard.

Les scripts exécutables utilisent :

    set -Eeuo pipefail

Les bibliothèques ne doivent pas modifier implicitement les options du shell appelant.

---

## 12. Commandes Git courantes

### État du dépôt

    git status

### Voir les modifications

    git diff

### Vérifier les problèmes de whitespace

    git diff --check

### Ajouter un fichier

    git add <fichier>

### Ajouter les modifications après vérification

    git add .

### Vérifier les fichiers staged

    git status

### Créer un commit

    git commit -m "type(scope): description"

### Envoyer vers GitHub

    git push origin main

---

## 13. Procédure de validation recommandée

Pour une modification courante :

1. Modifier le code.
2. Vérifier la syntaxe Bash.
3. Exécuter ShellCheck.
4. Exécuter les tests.
5. Exécuter git diff --check.
6. Vérifier git status.
7. Ajouter les fichiers avec git add.
8. Vérifier les fichiers staged.
9. Créer le commit.
10. Pousser vers GitHub.
11. Vérifier GitHub Actions.

Une modification est considérée comme validée lorsque les contrôles locaux et la CI GitHub sont réussis.

---

## 14. Organisation de la documentation

La documentation est organisée dans docs/.

### Configuration et développement

    docs/setup/

### Architecture

    docs/architecture/

### Architecture Decision Records

    docs/architecture/adr/

Les décisions d'architecture importantes doivent être documentées sous forme d'ADR.

---

## 15. Mise à jour de cette documentation

Ce document doit être mis à jour lorsque :

- l'environnement supporté évolue ;
- de nouveaux outils de validation sont ajoutés ;
- la procédure de développement change ;
- la structure du projet évolue ;
- la procédure de contribution change.

Les composants métier et les décisions d'architecture doivent être documentés dans les sections correspondantes de docs/.
