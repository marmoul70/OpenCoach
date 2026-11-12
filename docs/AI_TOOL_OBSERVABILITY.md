# Observabilité du moteur IA — lot 1

## Objectif

Rendre mesurable le coût d'exécution des outils Python sans exposer de données athlète, de secrets ou de détails d'exception au modèle.

## Métadonnée ajoutée

Chaque résultat produit par `AIToolRegistry.execute` contient désormais :

- `executed_at` : horodatage UTC de fin de traitement ;
- `duration_ms` : durée monotone écoulée entre l'entrée dans le registre et la production du résultat.

La durée est présente pour tous les statuts : `ok`, `failed`, `invalid_arguments`, `needs_clarification` et `not_found`. Elle inclut les contrôles de provenance, la validation Pydantic et, lorsque l'appel est autorisé, le handler métier.

La mesure utilise `time.perf_counter()` : elle est adaptée à la mesure de durée et indépendante des ajustements de l'horloge système. L'horodatage reste fourni séparément en UTC.

## Confidentialité et sécurité

- Aucun argument d'outil n'est ajouté aux journaux par ce changement.
- Les messages d'exception détaillés restent dans les journaux backend ; le résultat destiné au modèle conserve un message contrôlé.
- Aucune donnée métier, aucun calcul et aucune règle d'autorisation ne sont modifiés.
- La mesure n'est pas utilisée pour interrompre ou modifier l'exécution d'un outil.

## Tests

`tests/test_ai_tool_engine.py` vérifie la présence d'une durée non négative sur les chemins succès, outil inconnu, arguments invalides et exception du handler.

## Suite prévue

Ce lot ne mesure que l'exécution Python des outils. Les lots suivants devront mesurer séparément :

1. la planification déterministe (routeur et construction du plan) ;
2. l'exécution des outils Python ;
3. la rédaction Ollama (latence murale et métriques natives Ollama) ;
4. le temps total de réponse API.

Les journaux structurés, la corrélation par identifiant de requête et les agrégats p50/p95 restent à implémenter. Le modèle et sa version ne doivent être journalisés qu'au niveau de la requête, sans recopier les prompts ni les résultats sportifs.
