# Qualité des analyses du coach IA

## Objectif

Améliorer la pertinence et la fiabilité rédactionnelle des analyses produites après exécution des outils Python OpenCoach, sans modifier le modèle local configuré ni les calculs métier.

## Contrat de synthèse

Le modèle doit :
- répondre directement avec une voix de coach, sans réciter les résultats bruts des outils ;
- relier volume, charge, sommeil, récupération, ressenti et phase du programme lorsque ces données sont disponibles ;
- expliquer la conséquence pratique des faits pour l'entraînement à venir ;
- rattacher chaque chiffre personnel aux résultats Python du tour ;
- respecter les périodes et la couverture retournées par les outils ;
- ne décrire une évolution que si deux valeurs comparables sont disponibles ;
- ne pas transformer une corrélation en causalité ;
- proposer des actions concrètes et proportionnées aux faits ;
- exposer les contradictions entre résultats sans arbitrage arbitraire.
- distinguer les mesures objectives (Wellness, Readiness, activités) du ressenti déclaré, avec leur date et leur provenance ;
- signaler les contradictions entre ces signaux sans fabriquer de score composite ;
- ne jamais interpréter une donnée absente, ancienne ou partielle comme une absence confirmée de fatigue, de douleur ou de contrainte ;
- limiter la précision d'une recommandation lorsque l'historique, la fraîcheur de la récupération, les contraintes ou le programme ne sont pas suffisamment documentés.

Le style par défaut est concis : 3 à 6 phrases courtes (environ 40 à 90 mots), 1 ou 2 paragraphes, un avis de coach et une action concrète. Les tableaux et inventaires de métriques sont proscrits par défaut. Une réponse plus longue n’est justifiée que si l’athlète demande une analyse détaillée ou si une limite de sécurité doit être expliquée. Les préférences enregistrées peuvent adapter le style, sans affaiblir les règles de sécurité ou de provenance.

## Corrections de la validation terrain

- Une demande de récupération récente expose au LLM uniquement la fenêtre de 7 jours ; les fenêtres 14 et 30 jours ne sont plus incluses dans ce résultat afin d'empêcher le modèle de choisir une période différente.
- Le résultat de récupération ne transmet au LLM que les métriques utiles à la synthèse, avec leur couverture et leur provenance filtrée.
- ATL et CTL restent des indicateurs distincts. Sans seuil individuel explicite, le coach ne les qualifie pas de faibles, normaux ou élevés.
- Les jours sans couverture du planning sont distingués des jours sans entraînement ou sans activité importée.

## Corrections après validation visuelle

- La récupération récente met la fenêtre de 7 jours au premier plan ; les fenêtres 14 et 30 jours restent un contexte facultatif.
- Les durées de sommeil sont transmises au modèle uniquement sous forme de chaînes déjà formatées en heures et minutes par Python ; les secondes brutes ne sont plus exposées.
- Le ratio ATL/CTL est explicitement descriptif ; il ne constitue pas une classification de charge ou un seuil de risque.
- La couverture du planning, le nombre de séances et la couverture des charges par séance sont trois notions distinctes. Les nombres de séances planifiées et réalisées ne permettent pas de déduire un taux d'adhérence sans association explicite entre elles.
- La rédaction privilégie une réponse conversationnelle et hiérarchisée, sans liste de métriques brutes. Le style par défaut est court (3 à 6 phrases, environ 40 à 90 mots) ; un style détaillé ne doit pas réintroduire un inventaire de données.
- Une analyse de charge avec période explicite expose également le cadre hebdomadaire, les données de récupération et la disponibilité personnelle afin de contextualiser le conseil.
- L'outil de charge expose le volume réellement effectué (durée, distance, dénivelé) avec couverture par métrique ; les totaux incomplets restent explicitement partiels.

## Architecture inchangée

- Le routeur Python sélectionne les outils et valide les paramètres. Pour une analyse de charge avec période valide, il ouvre aussi le contexte du plan hebdomadaire et de la récupération.
- Les outils métier OpenCoach restent les seules sources des faits sportifs.
- Le LLM intervient uniquement pour rédiger la synthèse des résultats structurés.
- Aucun accès direct aux fournisseurs externes ni écriture dans le planning n'est ajouté.
- Aucun changement de schéma, migration, configuration Ollama, modèle ou donnée athlète.

## Validation

Les tests de prompt vérifient la présence des règles de provenance, de comparaison, de causalité et de recommandation. La validation complète comprend les tests Python, Bash et frontend, puis un contrôle conversationnel sur la VM avec le modèle configuré.

## Limites

Ces instructions réduisent les dérives de rédaction mais ne constituent pas une preuve formelle que chaque phrase générée est factuellement correcte. Les tests de conversations réelles et l'évaluation humaine restent nécessaires avant généralisation.


## Scénarios de décision sportive

Le corpus d'évaluation comprend désormais des situations concrètes de recommandation :
- récupération défavorable avant une séance intense planifiée ;
- Readiness favorable en présence d'une douleur, avec priorité aux restrictions ;
- charge récente importante avant une sortie longue planifiée ;
- adaptation d'une séance à l'approche d'un objectif de trail.

Chaque scénario documente les outils attendus, l'action de coaching visée et les comportements interdits. Les tests Python vérifient le contexte collecté et le contrat de ces scénarios ; ils ne prétendent pas valider à eux seuls la décision finale générée par le modèle. Une évaluation comportementale avec le modèle local et une validation fonctionnelle sur VM restent nécessaires.

## Décisions de séance fondées sur la charge récente

- Toute recommandation de séance collecte désormais une fenêtre déterministe de 7 jours via `training_load`, en plus de l'historique, de la récupération, des contraintes, du planning et du profil.
- Cette fenêtre de 7 jours est un contexte interne standard de recommandation : elle ne déclenche pas une demande de période à l'utilisateur. Une durée est demandée uniquement si l'utilisateur sollicite explicitement une analyse de charge sans la préciser.
- Si une demande avec douleur inclut aussi une analyse de charge sur une durée explicite, cette durée est conservée ; si elle manque ou sort de la plage autorisée, le coach demande une précision au lieu de substituer silencieusement 7 jours.
- Cette fenêtre sert à confronter le travail réellement observé au cadre de charge OpenCoach ; elle ne remplace pas la fenêtre d'historique ni les fenêtres propres aux outils de récupération.
- Le modèle doit distinguer charge planifiée, charge réelle, couverture complète/partielle et absence de données. Il ne peut pas assimiler une charge indisponible à une charge nulle.
- La sortie attendue d'une recommandation est une décision opérationnelle explicite : maintenir, alléger, remplacer par une activité autorisée ou récupérer. Les règles ne reposent pas sur des seuils physiologiques inventés.
- Une Readiness favorable ne lève jamais une restriction ou une douleur ; une mesure périmée ne peut pas être présentée comme l'état actuel. En cas de contradiction, la recommandation reste prudente et peut demander le ressenti actuel.

## Décisions de coaching avec contraintes physiques

- Une demande de séance accompagnée d'une douleur, blessure, maladie ou indisponibilité consulte toujours les contraintes enregistrées en premier.
- Si l'athlète demande une recommandation malgré cette contrainte, le plan collecte ensuite l'historique récent, la récupération, le Readiness, la prochaine séance planifiée, le cadre hebdomadaire et le profil sportif.
- La contrainte enregistrée reste prioritaire : le modèle ne peut pas recommander une séance interdite par les règles OpenCoach. L'absence de contrainte enregistrée ne vaut pas autorisation médicale.
- Le conseil doit distinguer ce qui est faisable, ce qui est à éviter et ce qui nécessite un avis médical ; il ne pose aucun diagnostic et ne transforme pas une douleur en simple indicateur de fatigue.
