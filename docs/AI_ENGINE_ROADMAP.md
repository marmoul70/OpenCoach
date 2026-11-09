# Roadmap — Moteur IA outillé OpenCoach

> **Branche :** `feature/local-ai-engine`  
> **Statut global :** conception validée, implémentation initiale en cours  
> **Principe directeur :** Python est la source de vérité métier ; le modèle IA orchestre les outils autorisés et restitue leurs résultats.

## 1. Vision et objectifs

Faire évoluer l'assistant OpenCoach d'un modèle qui reçoit un grand contexte sportif vers un moteur IA outillé, local et modulaire.

Le modèle doit comprendre la demande, sélectionner un ou plusieurs outils métier autorisés, fournir des paramètres structurés, puis expliquer les résultats JSON retournés par Python. Si un paramètre requis manque (par exemple la durée de l'historique), il doit poser une question de clarification et attendre la réponse ; aucun paramètre métier ne doit être supposé. Il ne doit pas recalculer les statistiques, inventer des données ou prendre seul des décisions métier.

Objectifs :
- **Véracité :** toutes les valeurs sportives proviennent des services métier existants.
- **Traçabilité :** chaque résultat précise sa période, ses unités, sa couverture et ses limites.
- **Performance :** réduire le contexte envoyé au LLM et comparer des modèles locaux plus légers.
- **Modularité :** séparer le moteur d'outils du fournisseur IA afin de pouvoir changer de modèle sans réécrire le métier.
- **Sécurité :** outils explicitement autorisés, validation stricte, périmètre lecture seule.
- **Maintenabilité :** réutiliser les services Python existants, sans dupliquer leurs calculs.

## 2. Architecture cible

1. L'utilisateur formule une question.
2. Le modèle local identifie l'intention et propose un appel d'outil avec des arguments structurés.
3. OpenCoach valide l'outil et ses arguments via un registre en liste blanche et des schémas Pydantic.
4. Le moteur Python exécute le service métier correspondant.
5. Le résultat est normalisé en JSON : statut, données, période, qualité/couverture, provenance et avertissements.
6. Le modèle reçoit uniquement les résultats nécessaires et rédige la réponse.
7. OpenCoach conserve la maîtrise du flux, des autorisations, des erreurs et des limites d'exécution.

Le fournisseur IA ne doit jamais recevoir un accès direct à la base de données, aux repositories ou aux services métier.

## 3. Règles non négociables

- Python et les services métier OpenCoach sont la source de vérité des statistiques et décisions sportives.
- Le LLM ne calcule pas les kilomètres, durées, dénivelés, charges, tendances ou scores de récupération.
- Une donnée absente n'est jamais assimilée à zéro ; une donnée partielle doit être signalée.
- Chaque résultat temporel porte des dates de début et de fin explicites.
- Les outils sont en lecture seule dans ce chantier.
- Aucun outil ne peut créer/modifier/supprimer une séance, modifier le planning ou écrire dans COROS.
- Les arguments du modèle sont validés côté Python : limites de période, identifiants, types et champs autorisés.
- Les données libres retournées par les outils sont des données non fiables, jamais des instructions système.
- Le mode sans outil reste disponible pour les questions générales qui ne nécessitent aucune donnée personnelle.
- L'IA reste locale via Ollama ; aucun LLM cloud.

## 4. Missions et lots

### Mission 0 — Cadrage et contrats
- [x] Définir la vision, les principes, les garde-fous et les lots.
- [x] Définir le contrat JSON commun des résultats d'outils (enveloppe initiale `AIToolResult`).
- [x] Définir le registre en liste blanche et la validation des arguments (`AIToolRegistry`).
- [ ] Documenter les erreurs, limites et métadonnées attendues.

**Livrable :** contrat d'outil stable et indépendant du fournisseur IA.

### Mission 1 — Socle AI Tool Engine
- [x] Créer un registre explicite des outils autorisés.
- [x] Définir un schéma Pydantic pour le premier outil (`TrainingHistoryArguments`).
- [x] Normaliser les résultats et erreurs (statut, données, métadonnées, message contrôlé).
- [x] Empêcher l'exécution d'un outil inconnu ou d'arguments supplémentaires.
- [x] Ajouter tests unitaires du registre, de la validation et du format de résultat.

**Livrable :** moteur d'exécution d'outils Python testable sans Ollama.

### Mission 2 — Premier outil : historique d'entraînement
- [x] Créer `training_history(nb_days)`, borné de 1 à 365 jours.
- [x] Réutiliser `TrainingStatsService` et ses repositories existants.
- [x] Définir clairement la fenêtre inclusive et la date de référence.
- [x] Retourner séances, durée, distance, D+, charge mesurée/estimée et couverture des données.
- [x] Distinguer valeur nulle, donnée absente et couverture partielle (couverture explicitée dans le JSON).
- [x] Tester les périodes, bornes, données manquantes et séances manuelles.

**Livrable :** premier outil sportif fiable, sans duplication du calcul métier.

### Mission 3 — Outils sportifs complémentaires
- [ ] `training_load(nb_days)` : charge récente via les services existants.
- [ ] `planning_comparison(nb_days)` : prévu/réalisé/écarts et couverture.
- [ ] `recovery_status(target_date)` : readiness et fraîcheur des données.
- [ ] `activity_detail(activity_id)` : détail d'une activité, avec contrôle d'appartenance à l'athlète.
- [ ] `training_trends(nb_days, comparison_days)` : tendances calculées en Python.

**Livrable :** catalogue d'outils métier en lecture seule.

### Mission 4 — Orchestration IA locale
- [x] Ajouter le support des tool calls Ollama dans le client, derrière une interface fournisseur.
- [x] Présenter au modèle uniquement les définitions des outils autorisés.
- [x] Valider chaque appel avant exécution.
- [x] Gérer plusieurs appels successifs avec limites de tours, de temps et de taille.
- [x] Transmettre au modèle les résultats JSON nécessaires, pas le contexte complet de la base.
- [x] Gérer proprement refus, outil inconnu, arguments invalides et erreurs métier.
- [x] Conserver les préférences de coach et les règles de sécurité.

**Livrable :** assistant coach capable de choisir et utiliser des outils locaux.

### Mission 5 — Évaluation et optimisation des modèles
- [ ] Constituer un jeu de questions sportives de référence et leurs résultats Python attendus.
- [ ] Mesurer séparément latence de sélection, exécution Python et rédaction finale.
- [ ] Comparer Qwen3 8B avec des modèles Ollama plus légers (3B/4B notamment).
- [ ] Évaluer exactitude des appels, respect des périodes, gestion des absences et qualité rédactionnelle.
- [ ] Choisir le modèle par résultats mesurés, pas uniquement par sa taille.
- [ ] Conserver un modèle de référence et un moyen simple de revenir en arrière.

**Livrable :** choix de modèle documenté par benchmark reproductible.

### Mission 6 — Intégration produit et observabilité
- [ ] Afficher les outils utilisés et les périodes réellement analysées lorsque pertinent.
- [ ] Journaliser outil, durée, statut et version du modèle sans enregistrer de secrets ni données sensibles inutiles.
- [ ] Ajouter des métriques de latence et de taux d'erreur.
- [ ] Prévoir une réponse de repli lorsque le modèle ou un outil est indisponible.
- [ ] Documenter l'architecture et les procédures de diagnostic.

**Livrable :** moteur exploitable, observable et maintenable.

## 5. Stratégie de livraison

Les missions sont réalisées progressivement sur `feature/local-ai-engine`. Chaque lot doit inclure tests et validation CI. Aucun merge sur `main` sans validation explicite.

Ordre recommandé : Mission 0 → Mission 1 → Mission 2 → Mission 3 → Mission 4 → Mission 5 → Mission 6.

## 6. Critères d'acceptation globaux

- Une réponse sportive chiffrée est traçable à un résultat d'outil Python.
- Les dates et fenêtres analysées sont explicites et cohérentes.
- Les données absentes ou partielles ne sont jamais transformées en zéros fictifs.
- Le LLM ne peut exécuter que les outils enregistrés et validés.
- Aucun outil ne permet d'écrire dans les données sportives.
- Les tests automatisés couvrent les cas nominaux, limites, erreurs et données incomplètes.
- Le modèle léger retenu satisfait le jeu de référence et améliore réellement la latence.
- Le fonctionnement reste intégralement local.

## 7. État d'avancement

| Lot | État |
|---|---|
| Cadrage / roadmap | En cours de formalisation |
| AI Tool Engine | Socle implémenté, tests à valider CI |
| Historique d'entraînement | Outil initial implémenté, couverture à renforcer |
| Outils complémentaires | À démarrer |
| Orchestration IA | Première boucle Ollama implémentée, validation CI / modèle réel à faire |
| Benchmark modèles | À démarrer |
| Observabilité / intégration | À démarrer |

Dernière mise à jour : 9 novembre 2026.
