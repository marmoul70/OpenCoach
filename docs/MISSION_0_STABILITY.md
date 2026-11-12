# Mission 0 — stabilisation et garde-fous

**Branche de travail :** `chore/mission-0-stability`  
**Branche de référence fonctionnelle :** `feature/ai-engine-main-integration`  
**Base de travail :** tête de la branche IA vérifiée le 12 novembre 2026  
**Version applicative :** 0.8.5

## Objectif

Stabiliser le dépôt avant la poursuite des missions IA et rendre les déploiements frontend réversibles. Cette mission ne fusionne pas la branche IA dans `main` et ne modifie aucune donnée de production.

## Corrections appliquées

- Alignement du fichier `VERSION`, de `pyproject.toml`, de `frontend/package.json` et du lockfile sur 0.8.5.
- Alignement du modèle de référence sur `qwen3:8b` dans la configuration, l'installation et le protocole de benchmark.
- Clarification de l'état de l'installation Ollama : l'installation du runtime ne déclenche pas l'activation du coach.
- Centralisation du déploiement frontend dans `scripts/deploy-frontend.sh`.
- Suppression du chemin local codé en dur dans l'ancien script snake_case ; celui-ci délègue désormais au point d'entrée canonique.
- Déploiement frontend par releases immuables et bascule atomique du lien `current`.
- Restauration automatique de la release précédente si la validation Nginx ou le rechargement échoue.
- Ajout d'une racine web configurable via `OPENCOACH_WEB_ROOT`, avec `/var/www/opencoach` comme valeur par défaut.
- Ajout d'un contrôle automatisé de cohérence des versions.
- Extension de ShellCheck et de la CI aux scripts de déploiement et aux contrôles de version.

## Procédure de déploiement frontend

Depuis la racine du dépôt, avec un dépôt Git propre :

```bash
./scripts/deploy-frontend.sh
```

Le script exécute `npm ci`, le lint et le build avant toute opération privilégiée. Il ne redémarre jamais le backend. La release active est conservée dans `/var/www/opencoach/current` et les cinq releases les plus récentes sont conservées.

Pour un environnement web de test distinct :

```bash
OPENCOACH_WEB_ROOT=/var/www/opencoach-test ./scripts/deploy-frontend.sh
```

Cette variable ne change pas automatiquement la configuration Nginx : le vhost de test doit pointer vers le dossier `current` correspondant.

## Contrôles locaux

```bash
./scripts/maintenance/check-version-consistency.sh
./scripts/maintenance/check-ai-model-config.sh
./scripts/maintenance/shellcheck.sh
bash ./tests/test-deploy-frontend.sh
```

La CI exécute ces contrôles ainsi que les tests Python, le lint et le build frontend.

## Limites de validation

La modification des scripts et la CI ne remplacent pas le test opérationnel sur Debian 13. La migration Alembic, le démarrage des services, le fonctionnement Ollama et les parcours UI réels restent à vérifier sur la VM avant toute fusion vers `main`.

## Règles de non-régression

- Ne jamais fusionner directement l'ancienne branche IA de 478 commits dans `main` sans audit dédié.
- Développer chaque mission sur une branche courte issue de la branche validée précédente.
- Ne pas modifier manuellement les fichiers déployés sous `/var/www/opencoach`.
- Utiliser les scripts du dépôt pour installer, mettre à niveau, tester et déployer.
- Avant une migration, sauvegarder la base avec le mécanisme prévu dans `scripts/bootstrap/upgrade.sh`.
- Incrémenter et vérifier les quatre déclarations de version ensemble lors d'une vraie livraison, pas à chaque commit de correction.
