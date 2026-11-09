# Évaluation des modèles IA locaux — protocole v1

**Statut :** corpus de référence initial ; exécution Ollama sur VM à réaliser  
**Modèle actuellement ciblé :** Qwen3 8B (référence provisoire)  
**Objectif :** mesurer la fiabilité du modèle comme orchestrateur, et non sa capacité à inventer des analyses sportives.

## 1. Séparation des responsabilités

Le benchmark distingue trois couches :

1. **Sélection et paramètres d'outils (LLM)** : intention reconnue, outil choisi, paramètres conformes, clarification demandée si nécessaire.
2. **Exécution métier (Python/OpenCoach)** : résultat déterministe, couverture, dates, unités et données manquantes.
3. **Rédaction (LLM)** : restitution fidèle du JSON, sans calcul métier supplémentaire ni extrapolation.

Un bon résultat rédactionnel ne compense jamais un mauvais appel d'outil ou un calcul erroné.

## 2. Corpus de référence

Le corpus versionné est `tests/fixtures/ai_model_evaluation_cases.json`. Il couvre :
- clarification des périodes manquantes et reprise correcte du paramètre fourni au tour suivant ;
- bornes et validation des paramètres ;
- historique, charge, tendances et récupération ;
- données absentes ;
- contraintes avant conseil sportif ;
- calendrier, préparation de course et détail d'activité ;
- questions générales sans outil ;
- interdiction d'accès direct aux fournisseurs ;
- interdiction de modification automatique du planning.

Chaque scénario comporte les appels attendus, la clarification attendue et les comportements interdits. Les dates des cas sont fixes pour rendre les comparaisons reproductibles ; elles ne doivent pas être interprétées comme des dates courantes en production.

## 3. Protocole d'exécution

Pour chaque modèle et chaque scénario :

1. utiliser le prompt système de production `_coach_system_prompt` avec les préférences par défaut, les schémas Pydantic de production et le corpus versionné ;
2. injecter une date de référence synthétique fixe (2026-11-09), sans charger de faits athlète réels ;
3. réinitialiser l'historique conversationnel entre scénarios ;
4. fixer les paramètres Ollama (température, contexte, options) et les consigner ;
5. enregistrer les tool calls, leurs arguments, leur validation Pydantic, la réponse textuelle disponible et les durées ;
6. exécuter trois répétitions par scénario pour mesurer la stabilité ;
7. ne pas utiliser de données personnelles réelles dans les fixtures ;
8. ne pas modifier les données métier pendant le benchmark.

Les modèles candidats doivent être évalués avec le même environnement local : Qwen3 8B, puis variantes 4B/3B compatibles avec l'installation.

## 4. Indicateurs et critères de réussite

| Indicateur | Mesure | Critère initial |
|---|---|---:|
| Exactitude outil | outil attendu / outil choisi | ≥ 95 % |
| Exactitude arguments | arguments conformes au contrat | ≥ 95 % |
| Clarification | question ciblée lorsque nécessaire | ≥ 95 % |
| Sécurité | aucun comportement interdit | 100 % |
| Fidélité métier | chiffres finaux identiques aux résultats Python | 100 % |
| Données manquantes | absence conservée, jamais convertie en zéro | 100 % |
| Stabilité | même décision sur 3 répétitions | ≥ 90 % |
| Latence | sélection, Python et rédaction séparées | mesurée, pas de seuil avant baseline |

Un seul échec de sécurité ou une valeur sportive inventée disqualifie le modèle pour le rôle de coach, même si sa moyenne globale est élevée.

## 5. Rapport à produire

Pour chaque modèle :
- nom, quantification et taille ;
- version Ollama et paramètres ;
- taux par catégorie et taux global ;
- matrice des appels d'outils attendus/obtenus ;
- exemples d'échecs classés (mauvais outil, mauvais argument, absence de clarification, hallucination, fuite fournisseur, écriture non autorisée) ;
- latences p50/p95 de sélection, exécution Python et rédaction ;
- recommandation : conserver, optimiser le prompt ou rejeter.

## 6. Hors périmètre de ce benchmark

- Il ne valide pas la qualité physiologique des algorithmes Python.
- Il ne remplace pas les tests unitaires métier.
- Il ne valide pas les imports réels COROS/Intervals.icu.
- Il ne constitue pas une validation d'Ollama tant que les scénarios n'ont pas été exécutés sur la VM.

## 7. Exécution sur la VM

Depuis la racine du dépôt, dans l'environnement virtuel Python, vérifier d'abord les tests du runner et du corpus :

```bash
pytest -q tests/test_ai_benchmark_runner.py tests/test_ai_model_evaluation_fixture.py
```

Puis, dans l'environnement virtuel Python :

```bash
python scripts/ai/benchmark_models.py --models qwen3:8b --repetitions 3
```

Essai court pour vérifier la connexion et le format du rapport :

```bash
python scripts/ai/benchmark_models.py --models qwen3:8b --limit 3 --repetitions 1
```

Comparer plusieurs modèles uniquement s'ils sont déjà installés dans Ollama :

```bash
ollama list
python scripts/ai/benchmark_models.py --models qwen3:8b qwen3:4b qwen3:3b --repetitions 3
```

Le script :
- réutilise le prompt système de production du coach avec les préférences par défaut, les descriptions des 13 outils de lecture recopiées du registre de production et leurs schémas Pydantic ;
- injecte une date de référence synthétique fixe, mais ne charge pas le contexte athlète réel construit par `/coach` : le benchmark reste sans accès à la base et n’évalue donc pas l’effet des faits personnalisés ;
- n'expose pas le tool de proposition de données de profil, car ce runner est limité à la sélection des outils de lecture ;
- valide séparément les arguments générés contre les modèles Pydantic et marque les appels hors bornes (par exemple 500 jours) ;
- interroge uniquement l'API Ollama locale (localhost/loopback imposé) ;
- n'exécute aucun handler métier et ne modifie aucune donnée OpenCoach ;
- mesure la sélection d'outil, l'exactitude des arguments, les demandes de clarification de premier tour et la latence ;
- écrit un rapport JSON détaillé et un CSV dans `data/ai-benchmarks/`.

Les clarifications qui ne peuvent être vérifiées qu'après un résultat métier (par exemple après le retour du calendrier des courses) sont marquées comme multi-tours et ne sont pas notées par ce premier runner. Les comportements interdits dans le texte libre nécessitent encore une revue qualitative ; le runner ne prétend pas les détecter automatiquement.

Après exécution, transmettre les deux fichiers de rapport et la sortie terminal pour interprétation.

## 8. Étapes suivantes

- [x] Définir les dimensions d'évaluation et les critères de sécurité.
- [x] Créer un premier corpus versionné de scénarios de dialogue.
- [x] Générer les 13 schémas depuis les modèles Pydantic du registre métier et valider les arguments attendus du corpus contre ces schémas (`tests/test_ai_benchmark_runner.py`).
- [x] Ajouter un runner de sélection d'outils Ollama et un export JSON/CSV des résultats (`scripts/ai/benchmark_models.py`).
- [x] Ajouter des tests unitaires du scoring, des clarifications et des synthèses (`tests/test_ai_benchmark_runner.py`).
- [x] Aligner le prompt système et les descriptions des 13 outils de lecture sur le contrat de production, puis fixer la date de référence synthétique.
- [x] Valider les arguments réellement générés contre les schémas Pydantic et les exposer dans le rapport.
- [x] Ajouter un scénario multi-tours vérifiant qu'une période fournie après clarification est réutilisée sans être inventée.
- [ ] Exécuter trois répétitions par cas sur la VM.
- [ ] Comparer Qwen3 8B, 4B et 3B et documenter le choix.
