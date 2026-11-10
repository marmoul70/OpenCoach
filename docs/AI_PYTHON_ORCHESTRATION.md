# Orchestration IA pilotée par Python

## Décision

Depuis la branche `feature/ai-engine-main-integration`, OpenCoach n'utilise plus le tool calling du LLM pour déclencher les outils métier en production.

Le flux de production est :

1. Le routeur Python identifie une intention reconnue.
2. Le planificateur extrait les paramètres explicitement fournis ou retourne une clarification.
3. Le registre Python valide le nom de l'outil, les arguments Pydantic et les preuves temporelles.
4. Python exécute les services métier OpenCoach sur le profil authentifié.
5. Le LLM reçoit les résultats structurés et rédige une explication en français.
6. Si le LLM est indisponible après l'exécution métier, l'API retourne les résultats structurés plutôt que de perdre une consultation déjà calculée.

Le modèle n'a aucun accès à la base, aux repositories, aux services métier ou à un catalogue de fonctions. Il ne choisit ni outil ni argument.

## Modules

- `app/opencoach/ai/tool_routing.py` : sélection conservatrice des capacités.
- `app/opencoach/ai/execution_plan.py` : conversion d'une intention et de preuves utilisateur en appels Python ou en clarification.
- `app/opencoach/ai/argument_evidence.py` : validation de la provenance des périodes et plages de dates.
- `app/opencoach/ai/tool_engine.py` : liste blanche, validation Pydantic et exécution isolée.
- `app/opencoach/api/ai.py` : exécution Python avant rédaction par le modèle.

## Règles de sûreté

- Un paramètre obligatoire absent entraîne une clarification, jamais une valeur par défaut inventée.
- Les durées hors limites sont refusées avant tout calcul.
- Une douleur, blessure, maladie ou indisponibilité déclenche `active_constraints` en premier, puis `recovery_status` avant toute recommandation de séance.
- Une demande d'accès direct à COROS, Garmin, Suunto, Apple Health ou Intervals.icu est refusée ; OpenCoach reste le référentiel de lecture.
- Les demandes générales ne déclenchent aucun outil métier et ne construisent aucun contexte sportif.
- Une mise à jour de profil ne crée qu'une proposition en attente, fondée sur une citation exacte du message utilisateur. La confirmation reste une action explicite distincte.
- Les outils métier restent en lecture seule ; aucune séance ni aucun planning ne peut être modifié par le coach.
- Le registre limite aussi l'exécution : un outil non sélectionné ne peut pas être appelé.

## Couverture fonctionnelle du premier lot

- Historique et charge : durée explicitement fournie et bornée.
- Tendances : deux périodes explicitement fournies.
- Récupération : analyse descriptive ou état Readiness du jour.
- Contraintes : lecture prioritaire avant toute recommandation liée à une douleur ou blessure.
- Activité : sélection par identifiant ou date ; les résultats ambigus restent à départager par l'utilisateur.
- Planning : consultation uniquement sur une plage de dates explicite.
- Profil : lecture des repères et proposition de quelques mises à jour numériques explicitement formulées.
- Calendrier de courses : lecture sur un horizon explicite ou contractuel.
- Les scénarios multi-étapes non résolus automatiquement (sélection d'une course ou d'une séance) demandent une précision au lieu de fabriquer un identifiant.

## Stratégie de validation

Les tests unitaires du planificateur vérifient la sélection et les arguments des cas représentatifs. Les tests de l'API vérifient que les outils sont exécutés par Python et que le LLM ne reçoit aucune définition de fonction.

La validation finale doit être faite sur la VM Debian avec Ollama actif et une base OpenCoach contenant des activités synchronisées. Le succès de la CI ne constitue pas, à lui seul, une preuve de qualité des réponses rédigées par le modèle.

## Limites connues avant le test VM

- La compréhension des intentions reste basée sur des règles explicites et doit être étendue à partir de formulations réelles observées.
- L'extraction des dates d'activité couvre les dates ISO, les dates françaises usuelles et les références relatives simples.
- Les workflows qui nécessitent de sélectionner un identifiant retourné par un premier outil demandent encore une étape de clarification.
- Les temps de réponse Ollama et la qualité de la rédaction finale doivent être mesurés sur la VM ; aucune promesse de latence n'est faite avant cette mesure.
