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
5. enregistrer les tool calls, leurs arguments, leur validation Pydantic, la réponse textuelle disponible, les durées et compteurs natifs Ollama ;
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

Comparer l'impact du catalogue et du prompt sans changer la configuration de production :

```bash
python scripts/ai/benchmark_models.py --models qwen3:8b --tool-profile all --prompt-profile production --repetitions 3
python scripts/ai/benchmark_models.py --models qwen3:8b --tool-profile history --prompt-profile production --repetitions 3
python scripts/ai/benchmark_models.py --models qwen3:8b --tool-profile history --prompt-profile minimal --repetitions 3
```

Comparer plusieurs modèles uniquement s'ils sont déjà installés dans Ollama :

```bash
ollama list
python scripts/ai/benchmark_models.py --models qwen3:8b qwen3:4b qwen3:3b --repetitions 3
```

Le script :
- propose deux profils de prompt : `production` (prompt réel du coach) et `minimal` (règles de routage réduites, uniquement pour diagnostic) ;
- propose deux catalogues : `all` (13 outils) et `history` (training_history, training_load, recovery_analysis) ;
- réutilise les schémas Pydantic métier dans les deux catalogues ;
- injecte une date de référence synthétique fixe, mais ne charge pas le contexte athlète réel construit par `/coach` : le benchmark reste sans accès à la base et n’évalue donc pas l’effet des faits personnalisés ;
- n'expose pas le tool de proposition de données de profil, car ce runner est limité à la sélection des outils de lecture ;
- valide séparément les arguments générés contre les modèles Pydantic et marque les appels hors bornes (par exemple 500 jours) ;
- en production, le registre applique un contrôle Python de provenance pour les périodes d'historique, de charge et de tendances ; une période absente, hors bornes ou différente de celle formulée par l'utilisateur bloque l'exécution et retourne une question déterministe ;
- interroge uniquement l'API Ollama locale (localhost/loopback imposé) ;
- n'exécute aucun handler métier et ne modifie aucune donnée OpenCoach ;
- mesure la sélection d'outil, l'exactitude des arguments, les demandes de clarification de premier tour et la latence murale ;
- conserve les métriques Ollama `total_duration`, `load_duration`, `prompt_eval_count`, `prompt_eval_duration`, `eval_count` et `eval_duration` (durées en nanosecondes), ainsi que le débit de génération calculé ;
- écrit un rapport JSON détaillé et un CSV dans `data/ai-benchmarks/`.

Les clarifications qui ne peuvent être vérifiées qu'après un résultat métier (par exemple après le retour du calendrier des courses) sont marquées comme multi-tours et ne sont pas notées par ce premier runner. Les comportements interdits dans le texte libre nécessitent encore une revue qualitative ; le runner ne prétend pas les détecter automatiquement.

Après exécution, transmettre les deux fichiers de rapport et la sortie terminal pour interprétation.

## 8. Routage déterministe du catalogue en production

L'endpoint `/api/ai/coach` applique désormais un routeur Python conservateur avant l'appel Ollama :

- les intentions reconnues sélectionnent les familles d'outils correspondantes (historique, charge, récupération, tendances, activité, courses, planning, exécution, contraintes et profil) ;
- les demandes combinées cumulent les familles détectées ;
- les suivis courts peuvent s'appuyer sur les derniers messages utilisateur et sur la dernière question de clarification de l'assistant ;
- les outils à période obligatoire (`training_history`, `training_load`, `training_trends` et `race_preparation_analysis`) sont masqués tant que les durées requises ne sont pas explicitement présentes dans le tour courant ou dans une réponse courte contextualisée ;
- une période explicitement fournie dans une demande complète précédente n'est jamais réutilisée pour une nouvelle demande complète ;
- une demande vide, inconnue ou ambiguë conserve le catalogue complet ;
- `propose_profile_data` reste exposé comme capacité contrôlée de proposition, sans écriture directe dans le profil ;
- le registre applique la sélection à la fois aux définitions envoyées au modèle et à l'exécution : un appel à un outil masqué est refusé côté Python ;
- le contrôle de provenance reste actif avant validation Pydantic et bloque toute période absente, altérée ou hors limites, même si le modèle tente un appel d'outil non attendu.

Le routeur ne consulte aucune donnée sportive et ne calcule aucune métrique. Il ne choisit que les outils disponibles ; tous les calculs restent dans les services déterministes OpenCoach. Le routage est couvert par `tests/test_ai_tool_routing.py`, le contrôle de provenance par `tests/test_ai_tool_engine.py` et la simulation du catalogue par `tests/test_ai_benchmark_runner.py`.

**Limite connue :** les dates obligatoires de `planned_sessions` ne sont pas encore couvertes par le même contrôle de provenance temporelle. Le schéma Pydantic valide leur format et leur cohérence, mais une vérification de leur présence explicite dans les messages utilisateur reste à ajouter avant de considérer ce cas comme aussi robuste que les durées ci-dessus.

## 9. Étapes suivantes

- [x] Définir les dimensions d'évaluation et les critères de sécurité.
- [x] Créer un premier corpus versionné de scénarios de dialogue.
- [x] Générer les 13 schémas depuis les modèles Pydantic du registre métier et valider les arguments attendus du corpus contre ces schémas (`tests/test_ai_benchmark_runner.py`).
- [x] Ajouter un runner de sélection d'outils Ollama et un export JSON/CSV des résultats (`scripts/ai/benchmark_models.py`).
- [x] Ajouter des tests unitaires du scoring, des clarifications et des synthèses (`tests/test_ai_benchmark_runner.py`).
- [x] Aligner le prompt système et les descriptions des 13 outils de lecture sur le contrat de production, puis fixer la date de référence synthétique.
- [x] Valider les arguments réellement générés contre les schémas Pydantic et les exposer dans le rapport.
- [x] Ajouter un scénario multi-tours vérifiant qu'une période fournie après clarification est réutilisée sans être inventée.
- [x] Capturer les métriques natives Ollama pour séparer le coût de chargement, du prompt et de la génération.
- [x] Ajouter les profils comparatifs de catalogue (13 outils / 3 outils ciblés) et de prompt (production / minimal), sans modifier le prompt de production.
- [x] Ajouter un garde-fou Python de provenance des périodes : une valeur obligatoire doit correspondre à une durée explicitement fournie par l'utilisateur ; sinon l'outil métier n'est pas exécuté et une clarification déterministe est retournée.
- [x] Ajouter des tests de non-exécution en cas de période inventée, altérée ou hors limites.
- [x] Corriger le scénario de récupération pour tenir compte de la date facultative par défaut du contrat.
- [ ] Exécuter les trois configurations comparatives sur la VM.
- [ ] Comparer Qwen3 8B, 4B et 3B et documenter le choix.


### Benchmark du routeur de production

Le profil `production_router` applique `select_coach_tools` séparément à chaque scénario du corpus, puis ne transmet à Ollama que les définitions retenues. Le rapport enregistre `exposed_tool_count`, `exposed_tool_names` et `average_exposed_tool_count`. Ce profil permet de comparer la sélection et la latence au catalogue complet avec le même modèle, le même prompt et les mêmes cas. Les scénarios sans outil sont exécutés avec un catalogue vide ; les demandes ambiguës conservent le catalogue complet conformément au comportement de production.

Commande de référence :

```bash
python scripts/ai/benchmark_models.py \\
  --models qwen3:8b \\
  --tool-profile production_router \\
  --prompt-profile production \\
  --repetitions 1
```
