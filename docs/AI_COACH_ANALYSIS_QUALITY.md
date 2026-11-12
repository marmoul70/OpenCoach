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

Le style et la longueur restent modulés par les préférences du coach, dans une rédaction conversationnelle de coach sportif. Ces préférences ne peuvent jamais affaiblir les règles de sécurité ou de provenance.

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
- La rédaction privilégie une réponse conversationnelle de 80 à 180 mots, sans liste de métriques brutes.
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
