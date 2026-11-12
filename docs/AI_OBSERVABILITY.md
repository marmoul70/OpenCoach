# Observabilité du moteur IA OpenCoach

**Périmètre de cette étape :** traces backend structurées, corrélées par requête et expurgées.  
**Stockage :** journaux du backend systemd ; aucune nouvelle table ni migration.  
**Modèle :** fournisseur local Ollama uniquement.

## Événements émis

OpenCoach émet une ligne JSON `opencoach_ai_observability` pour le routage déterministe du coach, chaque génération Ollama et chaque exécution d'outil métier.

### Routage Python

Le planificateur déterministe émet un événement `coach_router` avec le statut du plan, l'opération `execution_plan` et sa durée. Une demande qui nécessite une clarification est également tracée, sans journaliser le texte de la question.

### Génération Ollama

Les champs techniques disponibles sont :
- identifiant de trace aléatoire ;
- statut (`ok` ou `error`) ;
- fournisseur et nom du modèle ;
- durée murale côté client ;
- durées natives Ollama : totale, chargement, évaluation du prompt et génération ;
- nombre de tokens du prompt et de génération ;
- type d'exception, sans message d'erreur brut.

Les durées natives Ollama, initialement en nanosecondes, sont normalisées en millisecondes dans la trace.

### Exécution d'un outil Python

Chaque outil produit :
- le même identifiant de trace que la génération associée ;
- nom de l'outil ;
- statut normalisé ;
- durée d'exécution ;
- indicateur d'exécution effective du handler métier ;
- type d'exception éventuel.

## Confidentialité

La fonction `log_ai_event` applique une liste blanche stricte. Les traces structurées n'incluent jamais :
- le texte des questions ou des réponses ;
- l'historique conversationnel ;
- les arguments des outils ;
- les résultats sportifs ou données de récupération ;
- les identifiants d'utilisateur ou de profil athlète ;
- les URL Ollama, secrets ou variables d'environnement.

Les erreurs d'exécution des outils sont consignées par type d'exception, sans recopier le message d'exception susceptible de contenir une requête SQL ou une donnée métier.

## Corrélation

Les endpoints `/api/ai/chat` et `/api/ai/coach` créent un identifiant aléatoire par requête. Il est transmis en interne au client Ollama et au registre d'outils, mais n'est ni envoyé au modèle ni exposé dans la réponse HTTP.

## Diagnostic sur Debian

```bash
sudo journalctl -u opencoach-backend --since "1 hour ago" --no-pager | grep opencoach_ai_observability
```

Pour extraire uniquement les événements JSON :

```bash
sudo journalctl -u opencoach-backend --since "1 hour ago" --no-pager \
  | sed -n 's/^.*opencoach_ai_observability //p'
```

## Couverture des traces

Les événements sont émis au niveau des opérations réellement exécutées. Une clarification déterministe du planificateur qui retourne avant tout appel à Ollama ou à un outil ne produit donc pas d'événement de génération ou d'exécution ; elle ne déclenche aucun calcul ni accès au fournisseur.

## Agrégation et endpoint de supervision

L'endpoint authentifié `GET /api/ai/observability?window_hours=24` retourne les agrégats globaux des événements observés depuis le démarrage du processus :
- nombre d'événements, nombre d'erreurs et taux d'erreur ;
- latences p50, p95, minimum et maximum ;
- ventilation par type d'événement et modèle/outil/opération ;
- fenêtre de 1 à 168 heures.

Le stockage des échantillons est un tampon circulaire en mémoire de 5 000 événements maximum, partagé entre les requêtes du processus. Les échantillons les plus anciens sont évincés quand le tampon est plein. Aucun prompt, argument, identifiant de trace ou donnée sportive n'est retourné.

## Limites actuelles

- Les agrégats sont volatils : un redémarrage du backend vide les échantillons. Le nombre d'échantillons disponibles est indiqué dans la réponse.
- Le tampon est local au processus ; en cas de plusieurs workers, chaque worker aurait son propre agrégat. Le déploiement OpenCoach actuel utilise un seul processus backend.
- Aucune interface de supervision frontend n'est ajoutée dans cette étape.
- Les événements ne contiennent pas les prompts : l'évaluation qualitative des réponses reste un processus distinct basé sur le corpus synthétique.

## Suite prévue

1. Ajouter une agrégation bornée des événements pour produire p50/p95 et taux d'erreur.
2. Définir la rétention et les filtres d'accès si une persistance en base est nécessaire.
3. Ajouter une interface de supervision sans exposer les données personnelles.
4. Couvrir les scénarios d'indisponibilité Ollama et de repli structuré.
