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
- clarification des périodes manquantes ;
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

1. utiliser la même version du prompt système, du registre d'outils et du corpus ;
2. réinitialiser l'historique conversationnel entre scénarios ;
3. fixer les paramètres Ollama (température, contexte, options) et les consigner ;
4. enregistrer la réponse brute du modèle, les tool calls, leurs arguments, les résultats Python, la réponse finale et les durées ;
5. exécuter trois répétitions par scénario pour mesurer la stabilité ;
6. ne pas utiliser de données personnelles réelles dans les fixtures ;
7. ne pas modifier les données métier pendant le benchmark.

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

## 7. Étapes suivantes

- [x] Définir les dimensions d'évaluation et les critères de sécurité.
- [x] Créer un premier corpus versionné de scénarios de dialogue.
- [ ] Vérifier chaque schéma d'outil du corpus contre le registre réel.
- [ ] Ajouter un runner automatisé et un export JSON/CSV des résultats.
- [ ] Exécuter trois répétitions par cas sur la VM.
- [ ] Comparer Qwen3 8B, 4B et 3B et documenter le choix.
