# Évaluation des modèles IA locaux — protocole v1

**Statut :** corpus de référence initial ; premier benchmark comparatif exécuté sur VM le 13/11/2026  
**Modèle actuellement ciblé :** `qwen2.5:3b` (modèle réellement installé/configuré sur la VM ; qualité à confirmer par benchmark)  
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

Les modèles candidats doivent être évalués avec le même environnement local : `qwen2.5:3b` comme modèle courant ; les comparaisons avec d'autres modèles ne seront faites que si elles sont explicitement souhaitées et déjà installées.

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

## 4 bis. Candidat expérimental : Qwen3.5-2B

Le modèle de production reste `qwen2.5:3b`. `qwen3.5:2b` est un candidat de test uniquement : ne pas modifier `.env`, `.env.example`, la configuration de production ni le modèle actif pour réaliser cette comparaison.

Le runner mesure la sélection des outils, les arguments, les clarifications et la latence sur des scénarios synthétiques. Il n'exécute aucun outil métier, ne lit aucune donnée athlète et ne valide pas à lui seul la qualité de la synthèse finale. Une validation de rédaction doit donc compléter ce benchmark par des scénarios fonctionnels contrôlés.

Un benchmark Ollama peut durer plusieurs minutes : `--limit 3` limite le nombre de scénarios, mais ne garantit pas un test rapide. Ne lancer le corpus complet que si le diagnostic le justifie. Le test comparatif a été réalisé ; ses résultats et limites sont consignés à la section 10.

Le modèle candidat doit être déjà présent dans Ollama. Ces commandes sont historiques : elles décrivent le protocole utilisé le 13/11/2026 et ne sont pas une recommandation de relancer le benchmark complet. Elles ne changent pas `OPENCOACH_AI_MODEL`.
- sélection exacte de l'outil et des arguments ;
- clarification des périodes manquantes et reprise du contexte multi-tour ;
- respect des scénarios de sécurité ;
- latences p50/p95 et erreurs fournisseur.

Ne pas choisir un modèle sur une moyenne générale seule : tout échec de sécurité, appel métier injustifié ou argument temporel erroné est bloquant. Si Qwen3.5-2B est meilleur sur le routage mais moins bon en rédaction, conserver les rôles séparés et tester la rédaction indépendamment avant toute décision.

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
python scripts/ai/benchmark_models.py --models qwen2.5:3b --repetitions 3
```

Diagnostic réduit (3 scénarios, mais chaque génération Ollama peut encore prendre plusieurs dizaines de secondes) :

```bash
python scripts/ai/benchmark_models.py --models qwen2.5:3b --limit 3 --repetitions 1
```

Comparer l'impact du catalogue et du prompt sans changer la configuration de production :

```bash
python scripts/ai/benchmark_models.py --models qwen2.5:3b --tool-profile all --prompt-profile production --repetitions 3
python scripts/ai/benchmark_models.py --models qwen2.5:3b --tool-profile history --prompt-profile production --repetitions 3
python scripts/ai/benchmark_models.py --models qwen2.5:3b --tool-profile history --prompt-profile minimal --repetitions 3
```

Comparer plusieurs modèles uniquement s'ils sont déjà installés dans Ollama :

```bash
ollama list
python scripts/ai/benchmark_models.py --models qwen2.5:3b --repetitions 3
```

Le script :
- propose deux profils de prompt : `production` (prompt réel du coach) et `minimal` (règles de routage réduites, uniquement pour diagnostic) ;
- propose deux catalogues : `all` (14 outils) et `history` (training_history, training_load, recovery_analysis) ;
- réutilise les schémas Pydantic métier dans les deux catalogues ;
- injecte une date de référence synthétique fixe, mais ne charge pas le contexte athlète réel construit par `/coach` : le benchmark reste sans accès à la base et n’évalue donc pas l’effet des faits personnalisés ;
- n'expose pas le tool de proposition de données de profil, car ce runner est limité à la sélection des outils de lecture ;
- valide séparément les arguments générés contre les modèles Pydantic et marque les appels hors bornes (par exemple 500 jours) ;
- compare les arguments effectifs après application des valeurs Pydantic par défaut : un argument facultatif explicitement égal à sa valeur par défaut est équivalent à son omission ; les dates implicites utilisent la date de référence synthétique du scénario ;
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
- les outils à paramètres temporels obligatoires (`training_history`, `training_load`, `training_trends`, `race_preparation_analysis` et `planned_sessions`) sont masqués tant que les durées ou la plage de dates requises ne sont pas explicitement présentes dans le tour courant ou dans une réponse courte contextualisée ;
- les fenêtres hors limites sont également masquées avant l'appel au modèle : historique 1–365 jours, charge 1–90 jours, tendances 1–180 jours par période et préparation de course 7–180 jours d'historique ;
- `recovery_analysis` calcule ses fenêtres fixes de 7, 14 et 30 jours ; son seul argument facultatif est `target_date`, jamais `nb_days` ;
- une période explicitement fournie dans une demande complète précédente n'est jamais réutilisée pour une nouvelle demande complète ;
- une demande vide, inconnue ou ambiguë conserve le catalogue général, à l'exception des outils temporels dont les paramètres requis manquent ;
- `propose_profile_data` n'est exposé que lorsqu'un message utilisateur fournit explicitement une donnée durable de profil ; il est absent du catalogue de repli ambigu et ne modifie jamais directement le profil ;
- le registre applique la sélection à la fois aux définitions envoyées au modèle et à l'exécution : un appel à un outil masqué est refusé côté Python ;
- le contrôle de provenance reste actif avant validation Pydantic et bloque toute période absente, altérée ou hors limites, même si le modèle tente un appel d'outil non attendu.

Le routeur ne consulte aucune donnée sportive et ne calcule aucune métrique. Il ne choisit que les outils disponibles ; tous les calculs restent dans les services déterministes OpenCoach. Le routage est couvert par `tests/test_ai_tool_routing.py`, le contrôle de provenance par `tests/test_ai_tool_engine.py` et la simulation du catalogue par `tests/test_ai_benchmark_runner.py`.

Les dates obligatoires de `planned_sessions` sont également contrôlées : le routeur masque l'outil sans plage explicite, et le garde-fou Python vérifie que les dates transmises correspondent exactement à la plage demandée. Les formats couverts sont les plages françaises avec année (par exemple « du 9 au 15 novembre 2026 ») et deux dates ISO.

## 9. Étapes suivantes

- [x] Définir les dimensions d'évaluation et les critères de sécurité.
- [x] Créer un premier corpus versionné de scénarios de dialogue.
- [x] Générer les 14 schémas depuis les modèles Pydantic du registre métier et valider les arguments attendus du corpus contre ces schémas (`tests/test_ai_benchmark_runner.py`).
- [x] Ajouter un runner de sélection d'outils Ollama et un export JSON/CSV des résultats (`scripts/ai/benchmark_models.py`).
- [x] Ajouter des tests unitaires du scoring, des clarifications et des synthèses (`tests/test_ai_benchmark_runner.py`).
- [x] Aligner le prompt système et les descriptions des 14 outils de lecture sur le contrat de production, puis fixer la date de référence synthétique.
- [x] Valider les arguments réellement générés contre les schémas Pydantic et les exposer dans le rapport.
- [x] Ajouter un scénario multi-tours vérifiant qu'une période fournie après clarification est réutilisée sans être inventée.
- [x] Capturer les métriques natives Ollama pour séparer le coût de chargement, du prompt et de la génération.
- [x] Ajouter les profils comparatifs de catalogue (14 outils / 3 outils ciblés) et de prompt (production / minimal), sans modifier le prompt de production.
- [x] Ajouter un garde-fou Python de provenance des périodes : une valeur obligatoire doit correspondre à une durée explicitement fournie par l'utilisateur ; sinon l'outil métier n'est pas exécuté et une clarification déterministe est retournée.
- [x] Ajouter des tests de non-exécution en cas de période inventée, altérée ou hors limites.
- [x] Corriger le scénario de récupération pour tenir compte de la date facultative par défaut du contrat.
- [ ] Exécuter les trois configurations comparatives sur la VM.
- [ ] Exécuter et analyser le corpus avec `qwen2.5:3b` sur la VM ; ne comparer d'autres modèles que sur demande explicite.


### Benchmark du routeur de production

Le profil `production_router` applique `select_coach_tools` séparément à chaque scénario du corpus, puis ne transmet à Ollama que les définitions retenues. Le rapport enregistre `exposed_tool_count`, `exposed_tool_names` et `average_exposed_tool_count`. **Attention : ce runner mesure la capacité d'Ollama à émettre des tool calls dans un catalogue réduit ; il ne mesure pas directement le routage réel de l'endpoint `/api/ai/coach`.** En production, `build_coach_execution_plan` construit les appels métier déterministes en Python avant la synthèse du modèle. Les scores `tool_selection_accuracy` et `argument_validation_accuracy` de ce runner ne doivent donc pas être interprétés comme la fiabilité du routeur Python en production.

Commande de référence :

```bash
python scripts/ai/benchmark_models.py \\
  --models qwen2.5:3b \\
  --tool-profile production_router \\
  --prompt-profile production \\
  --repetitions 1
```


## 10. Résultats du benchmark comparatif du 13/11/2026

Le test a comparé `qwen2.5:3b` et `qwen3.5:2b` avec le profil `production_router`, le prompt `production`, 18 scénarios et 3 répétitions (54 générations par modèle).

| Indicateur | qwen2.5:3b | qwen3.5:2b |
|---|---:|---:|
| Générations réussies côté fournisseur | 54/54 | 54/54 |
| Tool selection accuracy du runner | 75,93 % | 33,33 % |
| Validation des arguments | 90,62 % | Non mesurable |
| Clarification accuracy (scénarios évaluables) | 25 % | 25 % |
| Latence médiane | 7,96 s | 14,66 s |
| Latence P95 | 40,23 s | 36,71 s |

Décision : **ne pas adopter `qwen3.5:2b`**. Sur ce corpus et ce protocole, il est plus lent en médiane et produit nettement moins de tool calls conformes. Le modèle de production reste `qwen2.5:3b`. Aucun changement de configuration ou de modèle actif n'est autorisé par ce benchmark.

Limite méthodologique importante : ces scores proviennent du runner LLM et ne représentent pas les appels réellement préparés par `build_coach_execution_plan` dans l'endpoint de production. Ils servent à comparer le comportement tool-calling brut des modèles, pas à mesurer la fiabilité de l'orchestration Python. La prochaine évaluation doit isoler trois mesures : (1) tests déterministes du plan d'exécution Python, (2) qualité de la synthèse du modèle à partir de résultats métier simulés, (3) latence Ollama. Ne pas relancer le corpus complet pour valider un simple correctif de routage.


### Détection des générations interrompues par la limite de tokens

Le client Ollama conserve le champ `done_reason` dans le résultat normalisé.
Les endpoints de conversation et de rédaction du coach rejettent une génération
dont `done_reason` vaut `length`, même si Ollama indique `done=true`.
Une réponse vide ou dont la génération n'est pas terminée est également rejetée.
Ce contrôle évite de présenter une synthèse tronquée comme une réponse complète.
