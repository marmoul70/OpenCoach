# OpenCoach — Gestion des paquets Debian

## 1. Objectif

OpenCoach utilise le gestionnaire de paquets APT de Debian pour gérer les dépendances système nécessaires au projet.

La logique de gestion des paquets est centralisée dans :

```text
scripts/lib/package-manager.sh
```

La liste des paquets nécessaires au projet est centralisée dans :

```text
scripts/lib/packages.sh
```

Cette séparation permet d'éviter de mélanger :

* la définition des dépendances ;
* leur détection ;
* leur installation ;
* le diagnostic global de l'environnement.

---

## 2. Architecture

La gestion des paquets suit cette architecture :

```text
                    OpenCoach
                        │
                        ↓
                check-environment.sh
                        │
             ┌──────────┴──────────┐
             ↓                     ↓
       package-manager.sh      packages.sh
             │                     │
             │                     ↓
             │          OPENCOACH_REQUIRED_PACKAGES
             │
      ┌──────┼────────┬─────────────┐
      ↓      ↓        ↓             ↓
   has_apt  apt_    is_package_  get_missing_
            usable   installed()   packages()
                                      │
                                      ↓
                               install_packages()
                                      │
                                  --dry-run
```

---

## 3. `package-manager.sh`

Fichier :

```text
scripts/lib/package-manager.sh
```

Ce fichier contient les fonctions techniques permettant d'interagir avec le système de paquets Debian.

---

## 4. Détection d'APT

La fonction :

```bash
has_apt
```

vérifie que `apt-get` est disponible.

Exemple :

```bash
if has_apt; then
    echo "APT disponible"
else
    echo "APT absent"
fi
```

La fonction retourne :

```text
0
```

si APT est disponible.

Sinon :

```text
1
```

---

## 5. Vérification du fonctionnement d'APT

La fonction :

```bash
apt_is_usable
```

effectue plusieurs vérifications :

1. APT est présent ;
2. `apt-get` répond correctement ;
3. les informations des cibles APT peuvent être interrogées.

Exemple :

```bash
if apt_is_usable; then
    echo "APT est opérationnel"
else
    echo "APT n'est pas opérationnel"
fi
```

Cette fonction ne lance pas d'installation.

---

## 6. Détection d'un paquet installé

La fonction :

```bash
is_package_installed
```

permet de vérifier si un paquet Debian est réellement installé.

Exemple :

```bash
if is_package_installed git; then
    echo "git est installé"
else
    echo "git n'est pas installé"
fi
```

La fonction utilise la base de données des paquets Debian via :

```text
dpkg-query
```

Cette approche permet de vérifier le paquet lui-même et non simplement la présence d'une commande.

---

## 7. Pourquoi ne pas utiliser `command -v` ?

Une commande et un paquet Debian ne représentent pas nécessairement la même chose.

Par exemple :

```text
paquet Debian
      ↓
peut fournir plusieurs fichiers
      ↓
dont plusieurs commandes
```

Utiliser :

```bash
command -v git
```

répond à la question :

> La commande `git` est-elle disponible ?

Alors que :

```bash
is_package_installed git
```

répond à :

> Le paquet Debian `git` est-il installé ?

Pour le gestionnaire de paquets, la seconde question est la plus pertinente.

---

## 8. Détection des paquets manquants

La fonction :

```bash
get_missing_packages
```

permet d'examiner plusieurs paquets.

Exemple :

```bash
get_missing_packages git curl wget
```

La fonction affiche uniquement les paquets qui ne sont pas installés.

Si `git` est installé mais que `curl` et `wget` ne le sont pas :

```text
curl
wget
```

seront retournés.

---

## 9. Utilisation avec la liste OpenCoach

La liste officielle des paquets nécessaires est définie dans :

```text
scripts/lib/packages.sh
```

Actuellement :

```bash
readonly OPENCOACH_REQUIRED_PACKAGES=(
    bash
    git
)
```

Elle peut être utilisée ainsi :

```bash
get_missing_packages "${OPENCOACH_REQUIRED_PACKAGES[@]}"
```

Cette commande permet d'obtenir les paquets manquants sans modifier le système.

---

## 10. Pourquoi utiliser `readonly` ?

La liste est déclarée :

```bash
readonly OPENCOACH_REQUIRED_PACKAGES=(
    bash
    git
)
```

`readonly` empêche une autre partie du script de modifier accidentellement cette configuration après son chargement.

Cela protège notamment contre une modification involontaire de la liste des dépendances pendant l'exécution d'un script de bootstrap.

Si une modification de la liste est nécessaire, elle doit être effectuée dans le fichier source :

```text
scripts/lib/packages.sh
```

puis validée dans Git.

---

## 11. Installation des paquets

La fonction :

```bash
install_packages
```

permet d'installer un ou plusieurs paquets.

Exemple :

```bash
install_packages curl
```

ou :

```bash
install_packages curl wget unzip
```

L'installation utilise :

```bash
sudo apt-get install -y
```

L'utilisation de `sudo` permet au script d'effectuer l'opération avec les privilèges nécessaires tout en conservant un fonctionnement normal pour l'utilisateur `opencoach`.

---

## 12. Protection de l'installation

Avant toute installation, `install_packages` vérifie que :

```bash
apt_is_usable
```

est valide.

Si APT n'est pas opérationnel, l'installation est refusée.

La fonction accepte également un appel sans paquet :

```bash
install_packages
```

Dans ce cas, elle ne réalise aucune opération.

---

## 13. Mode `dry-run`

Le gestionnaire dispose d'un mode simulation :

```bash
install_packages --dry-run curl wget unzip
```

Résultat attendu :

```text
[DRY-RUN] Installation : curl wget unzip
```

Aucun paquet n'est installé.

Le mode `dry-run` est destiné notamment :

* aux tests ;
* au diagnostic ;
* à la validation des scripts ;
* à l'affichage préalable des opérations qui seraient réalisées.

---

## 14. Différence entre simulation et installation réelle

### Simulation

```bash
install_packages --dry-run curl
```

Effet :

```text
affiche l'opération
        ↓
aucune modification
```

### Installation réelle

```bash
install_packages curl
```

Effet :

```text
APT
 ↓
installation du paquet
```

L'installation réelle doit donc être utilisée uniquement lorsque le script qui l'appelle a déjà validé les conditions nécessaires.

---

## 15. Vérification de la disponibilité d'un paquet

Il faut distinguer deux notions :

### Paquet installé

```bash
is_package_installed git
```

Cela vérifie l'installation locale.

### Paquet disponible dans les dépôts APT

```bash
apt-cache show git
```

Cela vérifie que le paquet est connu par la configuration APT actuelle.

Un paquet peut donc être :

```text
connu par APT
mais
non installé
```

C'est précisément le cas que le bootstrap devra traiter.

---

## 16. Flux prévu pour l'installation automatique

L'architecture cible est :

```text
Liste des paquets requis
          │
          ↓
Détection des paquets installés
          │
          ↓
Liste des paquets manquants
          │
          ↓
Vérification APT
          │
          ↓
Vérification de disponibilité
          │
          ↓
Simulation éventuelle
          │
          ↓
Installation
          │
          ↓
Vérification post-installation
```

Cette approche évite de réinstaller inutilement les paquets déjà présents.

---

## 17. Exemple de scénario

Supposons que la liste soit :

```text
bash
git
curl
wget
```

et que la machine possède déjà :

```text
bash
git
```

Le processus doit produire :

```text
Paquets requis :
    bash
    git
    curl
    wget

Paquets déjà installés :
    bash
    git

Paquets manquants :
    curl
    wget
```

L'installation pourra alors être limitée à :

```text
curl
wget
```

et non à l'ensemble des paquets.

---

## 18. Séparation des responsabilités

Les fichiers doivent conserver leurs responsabilités.

### `packages.sh`

Définit :

```text
Quels paquets sont nécessaires ?
```

### `package-manager.sh`

Définit :

```text
Comment interagir avec Debian et APT ?
```

### `dependencies.sh`

Définit :

```text
Quelles commandes sont nécessaires ?
```

### `check-environment.sh`

Définit :

```text
L'environnement est-il conforme ?
```

Cette séparation facilite la maintenance et les tests.

---

## 19. Tests

### Vérification syntaxique

```bash
bash -n scripts/lib/package-manager.sh
```

### Vérification d'un paquet installé

```bash
source scripts/lib/package-manager.sh

is_package_installed git
echo $?
```

Résultat attendu :

```text
0
```

### Vérification d'un paquet absent

```bash
is_package_installed opencoach-package-does-not-exist
echo $?
```

Résultat attendu :

```text
1
```

### Détection des paquets manquants

```bash
get_missing_packages git opencoach-package-does-not-exist
```

Résultat :

```text
opencoach-package-does-not-exist
```

### Simulation d'installation

```bash
install_packages --dry-run curl wget
```

Résultat :

```text
[DRY-RUN] Installation : curl wget
```

---

## 20. Test depuis un autre répertoire

Les bibliothèques doivent pouvoir être chargées avec un chemin absolu.

Exemple :

```bash
cd /tmp
```

Puis :

```bash
source /home/opencoach/Projects/OpenCoach/scripts/lib/package-manager.sh
```

Les fonctions doivent rester disponibles :

```bash
has_apt
apt_is_usable
is_package_installed
get_missing_packages
install_packages
```

---

## 21. Sécurité

L'installation automatique de paquets est une opération ayant un impact sur le système.

Les scripts OpenCoach doivent donc éviter :

* les installations implicites ;
* les commandes APT non contrôlées ;
* les listes de paquets construites à partir d'une entrée utilisateur non validée ;
* les suppressions automatiques ;
* les modifications non documentées des dépôts.

Le mode `dry-run` doit être utilisé lorsque cela apporte une valeur de validation.

---

## 22. Évolution future

La gestion des paquets sera progressivement améliorée pour prendre en charge :

* la détection des paquets manquants ;
* l'installation contrôlée ;
* la validation avant installation ;
* la vérification après installation ;
* la gestion détaillée des erreurs APT ;
* la journalisation ;
* éventuellement le mode interactif ;
* éventuellement le mode non interactif pour l'automatisation.

Ces fonctionnalités doivent être ajoutées progressivement et testées individuellement.

---

## 23. Référence des fichiers

Gestionnaire :

```text
scripts/lib/package-manager.sh
```

Liste des paquets :

```text
scripts/lib/packages.sh
```

Diagnostic :

```text
scripts/bootstrap/check-environment.sh
```

Documentation :

```text
docs/setup/package-manager.md
```

---

## 24. État actuel

Cette documentation correspond à l'état du projet après :

```text
T0.7.5 — Gestionnaire APT
T0.7.6 — Détection et préparation de l'installation
```

Le gestionnaire sait actuellement :

* détecter APT ;
* vérifier qu'APT est utilisable ;
* détecter un paquet installé ;
* identifier les paquets manquants ;
* préparer une installation ;
* simuler une installation avec `--dry-run`.

L'installation automatique complète des dépendances sera construite dans les missions suivantes.
