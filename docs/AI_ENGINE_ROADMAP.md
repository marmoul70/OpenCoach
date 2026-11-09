# Roadmap — Moteur IA outillé OpenCoach

> **Branche :** `feature/ai-engine-main-integration`  
> **Statut global :** socle IA réintégré sur la base main 0.8.5 ; extension des outils en cours  
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
- [x] `training_load(nb_days)` : charge récente et comparaison prévu/réalisé via `RecentTrainingLoadService`, avec couverture du planning et données absentes explicitées.
- [x] `planning_comparison(nb_days)` : comparaison prévu/réalisé couverte par `training_load`, avec écarts et couverture.
- [x] `recovery_status(target_date)` : score Readiness, signaux, baselines, fraîcheur et indisponibilité explicite.
- [x] `activity_detail(activity_date | activity_id)` : détail d'une activité, sélection par date locale ou identifiant, choix explicite en cas d'ambiguïté et contrôle d'appartenance à l'athlète.
- [x] `training_trends(nb_days, comparison_days)` : comparaison de deux périodes successives, avec calcul des écarts et contrôle de couverture.
- [x] `athlete_training_profile()` : repères physiologiques, zones FC, capacité hebdomadaire et cibles de ravitaillement réellement configurés.
- [x] `race_calendar(start_date, horizon_days)` : calendrier des courses et objectifs de préparation.
- [x] `planned_sessions(start_date, end_date)` : séances prévues, prescriptions résumées et agrégats avec contrôle de couverture.

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

Les missions sont réalisées progressivement sur `feature/ai-engine-main-integration`. Chaque lot doit inclure tests et validation CI. Aucun merge sur `main` sans validation explicite.

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
| Cadrage / roadmap | Réalisé |
| AI Tool Engine | Implémenté, CI Python/Bash/frontend verte |
| Historique d'entraînement | Implémenté, contrôles de couverture explicites |
| Outils complémentaires | 7 outils complémentaires implémentés ; profil, calendrier, séances planifiées et détail d'activité couverts |
| Orchestration IA | Boucle bornée et clarification testées ; validation Ollama réel restante |
| Benchmark modèles | À démarrer |
| Observabilité / intégration | À démarrer |

Dernière mise à jour : 9 novembre 2026.

### Mission 3 bis — bibliothèque de coaching

- `athlete_training_profile` expose les repères du profil sportif sans identité personnelle ; les zones cardiaques utilisent le calcul existant `get_heart_rate_zone`. Les champs absents restent `null` et sont listés.
- `race_calendar` lit les courses du seul athlète authentifié sur une fenêtre bornée de 1 à 365 jours.
- `planned_sessions` lit les séances sur une fenêtre obligatoire de 31 jours maximum ; les descriptions et prescriptions JSON brutes sont exclues. Les agrégats distance/D+ sont masqués si la couverture est incomplète.
- Les textes libres (titres, noms, lieux) sont bornés et explicitement considérés comme données non fiables.
- Aucun de ces outils ne modifie le profil, le calendrier ou les séances.
- Tests dédiés ajoutés pour les valeurs manquantes, la couverture partielle, les fenêtres et l'isolation par athlète. Validation CI en cours.

### Mission 3 — détail d'activité

- L'outil est enregistré dans le registre authentifié de l'athlète et réutilise `SqlActivityDetailRepository`.
- La sélection se fait par date locale ou identifiant OpenCoach ; si plusieurs séances correspondent, l'outil retourne une liste de choix et demande une clarification.
- Les données restituées sont filtrées : métriques générales, intervalles bornés à 40, textes libres tronqués et statistiques de streams (nombre d'échantillons, min/max/moyenne). Aucun JSON COROS brut ni série complète n'est transmis au modèle.
- Les activités d'un autre profil ne sont pas accessibles ; les détails absents sont explicitement signalés.
- Tests dédiés ajoutés ; validation CI à effectuer.

### Reprise sur main 0.8.5

- [x] Créer une branche propre depuis `main` 0.8.5, sans reprendre les 356 commits obsolètes de l'ancienne branche.
- [x] Réintégrer le moteur IA, `training_history`, les préférences du coach et les tests associés.
- [x] Ajouter les outils `training_load`, `recovery_status` et `training_trends` en lecture seule.
- [x] Couvrir la comparaison prévu/réalisé avec `training_load`.
- [x] Ajouter l'installation optionnelle d'Ollama via `install.sh --with-ai`, sans activer automatiquement le coach.
- [x] Enregistrer les paramètres Ollama locaux dans `.env.example` ; l'IA reste désactivée par défaut.
- [x] Valider CI Python 3.13, Bash/ShellCheck et frontend sur le commit `de1776e2` (run GitHub Actions `42617922430`).
- [ ] Valider la migration Alembic sur la VM Debian 13 et effectuer un test réel avec Ollama.
- [x] Ajouter `activity_detail` avec sélection par date ou identifiant, désambiguïsation et sortie de données filtrée.
- [ ] Benchmark des modèles et complétion de l'observabilité.

