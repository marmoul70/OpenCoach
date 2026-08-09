# OpenCoach — Vérification de l'environnement

## 1. Objectif

Le script `check-environment.sh` permet de vérifier que l'environnement système nécessaire à OpenCoach est correctement configuré.

Il est conçu pour être utilisé :

* lors de l'installation initiale ;
* avant l'exécution des missions de bootstrap ;
* après une modification importante du système ;
* lors du diagnostic d'un problème d'environnement ;
* dans les scripts d'automatisation futurs.

Le script effectue uniquement des **vérifications**.

Il ne doit pas installer automatiquement de paquets ni modifier la configuration du système.

---

## 2. Emplacement

Le script se trouve dans :

```text
scripts/bootstrap/check-environment.sh
```

Il utilise les bibliothèques communes présentes dans :

```text
scripts/lib/
```

---

## 3. Architecture

Le diagnostic s'appuie actuellement sur les composants suivants :

```text
scripts/bootstrap/check-environment.sh
│
├── scripts/lib/log.sh
├── scripts/lib/system.sh
├── scripts/lib/dependencies.sh
├── scripts/lib/package-manager.sh
└── scripts/lib/packages.sh
```

Chaque bibliothèque possède une responsabilité spécifique.

### `log.sh`

Gère l'affichage des messages du bootstrap :

* informations ;
* succès ;
* erreurs ;
* résultats des vérifications.

### `system.sh`

Contient les fonctions relatives à l'environnement système.

Il permet notamment de vérifier les informations liées à la distribution Debian.

### `dependencies.sh`

Décrit les commandes nécessaires à OpenCoach et permet de vérifier leur présence.

### `package-manager.sh`

Fournit les fonctions relatives au gestionnaire de paquets Debian :

* détection d'APT ;
* vérification du fonctionnement d'APT ;
* détection des paquets installés ;
* identification des paquets manquants ;
* installation des paquets ;
* mode `dry-run`.

### `packages.sh`

Centralise la liste des paquets Debian nécessaires à OpenCoach.

---

## 4. Utilisation

Depuis la racine du projet :

```bash
cd /home/opencoach/Projects/OpenCoach
```

Lancer le diagnostic :

```bash
./scripts/bootstrap/check-environment.sh
```

Le script doit pouvoir être exécuté depuis n'importe quel répertoire.

Par exemple :

```bash
cd /tmp
/home/opencoach/Projects/OpenCoach/scripts/bootstrap/check-environment.sh
```

Cette propriété est importante : le script doit utiliser le chemin du projet et non le répertoire courant comme référence.

---

## 5. Vérifications effectuées

Le diagnostic vérifie progressivement l'environnement.

### 5.1 Vérification du système

Le système doit correspondre à l'environnement supporté par le projet.

La version cible actuelle du bootstrap est :

```text
Debian 13
```

---

### 5.2 Vérification des commandes nécessaires

Le bootstrap vérifie la présence des commandes nécessaires à OpenCoach.

Par exemple :

```text
bash
git
```

Une dépendance disponible est signalée comme valide.

Une dépendance absente provoque l'échec du diagnostic.

---

### 5.3 Vérification d'APT

Le script vérifie qu'APT est disponible et utilisable.

La bibliothèque :

```text
scripts/lib/package-manager.sh
```

fournit notamment :

```bash
has_apt
```

Cette fonction vérifie la présence de :

```text
apt-get
```

Le diagnostic vérifie ensuite :

```bash
apt_is_usable
```

Cette fonction vérifie que `apt-get` peut être interrogé correctement.

---

### 5.4 Vérification des paquets Debian

La liste des paquets nécessaires est centralisée dans :

```text
scripts/lib/packages.sh
```

Exemple actuel :

```bash
readonly OPENCOACH_REQUIRED_PACKAGES=(
    bash
    git
)
```

Le diagnostic vérifie que ces paquets sont connus des dépôts APT configurés.

Cette vérification utilise notamment :

```bash
apt-cache show <paquet>
```

Cette opération ne demande pas l'installation du paquet.

---

## 6. Codes de retour

Le script utilise les codes de retour Unix standards.

### Succès

```text
0
```

Un code retour `0` signifie que toutes les vérifications ont réussi.

### Échec

```text
1
```

Un code retour différent de zéro indique qu'au moins une vérification a échoué.

Il est donc possible d'utiliser le script dans un autre script :

```bash
if ./scripts/bootstrap/check-environment.sh; then
    echo "Environnement valide"
else
    echo "Environnement invalide"
    exit 1
fi
```

---

## 7. Exemple de résultat attendu

Un environnement correctement configuré doit produire un résultat similaire à :

```text
[INFO] Vérification de l'environnement OpenCoach
[ OK ] Debian détecté
[ OK ] Debian 13 détecté
[ OK ] bash disponible
[ OK ] git disponible
[INFO] Résumé des dépendances
[ OK ] 2 dépendance(s) disponible(s)
[ OK ] APT est opérationnel
[ OK ] Paquet bash disponible
[ OK ] Paquet git disponible
[ OK ] Environnement de base valide
```

Le texte exact peut évoluer avec les futures versions du bootstrap.

La documentation décrit le comportement attendu et non une sortie figée.

---

## 8. Ce que le diagnostic ne fait pas

Le script de diagnostic ne doit pas :

* installer automatiquement des paquets ;
* supprimer des paquets ;
* modifier les dépôts APT ;
* modifier la configuration Debian ;
* redémarrer le système ;
* modifier Docker ;
* modifier la configuration réseau ;
* modifier les fichiers du projet.

La séparation entre **diagnostic** et **installation** est volontaire.

---

## 9. Installation des dépendances

L'installation des paquets est gérée séparément par :

```text
scripts/lib/package-manager.sh
```

La fonction :

```bash
install_packages
```

permet d'effectuer une installation contrôlée.

Un mode simulation est également disponible :

```bash
install_packages --dry-run curl git
```

Résultat :

```text
[DRY-RUN] Installation : curl git
```

Le mode `dry-run` ne modifie pas le système.

Le diagnostic `check-environment.sh` n'appelle pas automatiquement cette fonction.

---

## 10. Tests

Avant toute modification du bootstrap, les scripts Bash doivent être vérifiés syntaxiquement.

Exemple :

```bash
bash -n scripts/bootstrap/check-environment.sh
```

Pour les bibliothèques :

```bash
bash -n scripts/lib/package-manager.sh
bash -n scripts/lib/packages.sh
```

Aucune sortie indique que la syntaxe Bash est valide.

---

## 11. Test depuis un autre répertoire

Le bootstrap doit fonctionner même lorsque le répertoire courant n'est pas la racine du projet.

Test :

```bash
cd /tmp
```

Puis :

```bash
/home/opencoach/Projects/OpenCoach/scripts/bootstrap/check-environment.sh
```

Cette vérification permet de détecter les scripts qui utilisent accidentellement des chemins relatifs au répertoire courant.

---

## 12. Philosophie de sécurité

Le bootstrap OpenCoach suit progressivement le principe :

```text
Détecter
   ↓
Vérifier
   ↓
Identifier les éléments manquants
   ↓
Simuler
   ↓
Installer
   ↓
Vérifier à nouveau
```

L'objectif est d'éviter qu'un script d'installation effectue des modifications importantes sans validation préalable.

---

## 13. Évolution prévue

Le diagnostic sera progressivement enrichi au fur et à mesure du bootstrap.

Les futures missions pourront ajouter des vérifications concernant :

* Python ;
* Docker ;
* Docker Compose ;
* les services OpenCoach ;
* les fichiers de configuration ;
* les permissions ;
* les répertoires de données ;
* le réseau ;
* les services système.

Ces éléments ne doivent être ajoutés que lorsque les composants correspondants deviennent réellement nécessaires au projet.

---

## 14. Maintenance

Lorsqu'une nouvelle dépendance devient nécessaire :

1. déterminer la commande nécessaire ;
2. l'ajouter à la liste des dépendances ;
3. identifier le paquet Debian correspondant ;
4. l'ajouter à `packages.sh` ;
5. mettre à jour les tests ;
6. mettre à jour cette documentation si nécessaire.

Les responsabilités doivent rester séparées :

```text
Commande nécessaire
        ↓
dependencies.sh

Paquet Debian nécessaire
        ↓
packages.sh

Gestion d'APT
        ↓
package-manager.sh

Diagnostic global
        ↓
check-environment.sh
```

---

## 15. Validation

Une modification du diagnostic est considérée comme valide lorsque :

* le script passe `bash -n` ;
* les bibliothèques chargées passent `bash -n` ;
* le diagnostic fonctionne depuis la racine du projet ;
* le diagnostic fonctionne depuis `/tmp` ;
* un environnement valide retourne `0` ;
* une erreur détectée retourne un code non nul ;
* `git diff --check` ne signale aucune erreur.

---

## 16. Référence

Composant principal :

```text
scripts/bootstrap/check-environment.sh
```

Bibliothèques associées :

```text
scripts/lib/log.sh
scripts/lib/system.sh
scripts/lib/dependencies.sh
scripts/lib/package-manager.sh
scripts/lib/packages.sh
```

Cette documentation correspond à l'état du bootstrap après les missions T0.7.3 à T0.7.6.
