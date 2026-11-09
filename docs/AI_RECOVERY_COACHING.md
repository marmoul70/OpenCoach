# Analyse de la forme, de la fatigue et de la récupération

## Objectif

Le coach IA doit pouvoir mener une discussion structurée sur l'état de forme de
l'athlète, sans remplacer les services déterministes OpenCoach ni poser de diagnostic.
Le raccourci « Bilan forme, fatigue et sommeil » déclenche une analyse des données
disponibles et invite le coach à demander les informations subjectives manquantes.

## Sources utilisées

### Mesures objectives

L'outil `recovery_analysis` lit exclusivement les mesures déjà persistées dans
`wellness_daily` par les connecteurs et imports OpenCoach. Il ne contacte jamais
COROS, Intervals.icu, Garmin ou une autre plateforme. Tous les fournisseurs sont
des origines d'import, pas des sources de lecture du coach.

OpenCoach consolide les métriques indépendamment, journée par journée :

- sommeil : durée totale, score, qualité et phases disponibles ;
- HRV et baseline HRV ;
- fréquence cardiaque au repos et mesures cardiaques nocturnes ;
- stress et saturation SpO₂ lorsque disponible ;
- charge aiguë ATL et forme CTL.

Pour chaque métrique et chaque date, la valeur issue de l'import le plus récent
est retenue lorsque sa date de mise à jour est disponible. Si des valeurs
concurrentes ont la même fraîcheur ou aucune date de mise à jour, la métrique
reste inconnue et le conflit est signalé : aucun fournisseur n'est arbitrairement
privilégié. Le moteur Python `recovery_assessment.py` calcule ensuite les fenêtres
distinctes de 7, 14 et 30 jours sur ces journées consolidées.

### Ressenti subjectif

Le même outil retourne séparément les informations déjà saisies pour la journée :

- contexte quotidien : fatigue subjective, douleur, maladie, impact du traitement,
  motivation ;
- check-in Coach : énergie, confort/douleur, maladie, indisponibilité et zones
  douloureuses.

Ces sources ne sont pas fusionnées en un score unique. L'absence de check-in reste
explicitement inconnue ; elle ne signifie pas que l'athlète est en forme.

## Règles de dialogue

1. Pour toute question sur la forme, la fatigue, le sommeil, le stress ou la
   récupération, appeler `recovery_analysis`.
2. Pour une question de disponibilité d'entraînement ou de restrictions, compléter
   avec `recovery_status` et les contraintes actives.
3. Comparer les tendances personnelles, sans appliquer un seuil médical universel.
4. Préciser que les mesures viennent du stockage OpenCoach, la date de la dernière mesure, la couverture et, si utile, la provenance d'import par métrique.
5. Distinguer fatigue générale, énergie déclarée, douleur, maladie et charge
   d'entraînement. Ne pas déduire une douleur ou une maladie d'une variation de HRV.
6. Si le ressenti du jour est absent, recueillir énergie (1 à 5), confort/douleur
   (1 à 5), maladie et disponibilité. Si une douleur est déclarée, demander sa zone
   et son côté avant de constituer le check-in.
7. Quand les quatre réponses sont explicites, le coach peut créer une proposition
   `daily_checkin` avec `propose_profile_data`. La preuve doit être une citation exacte
   des messages utilisateur et étayer chaque valeur. Seul le bouton de confirmation
   dans l'interface persiste le check-in.
8. Si un check-in existe déjà pour aujourd'hui, ne pas proposer de remplacement ;
   orienter l'utilisateur vers le formulaire de modification existant.
9. Un check-in incomplet, ambigu ou sans preuve suffisante n'est jamais sauvegardé.
10. Si les données de sommeil ne sont pas importées, demander le ressenti ou signaler
    l'absence ; ne jamais fabriquer une durée ou une qualité de sommeil.
11. Ne jamais diagnostiquer un surentraînement, une maladie ou une blessure. Une
    recommandation d'entraînement doit rester cohérente avec les services de
    disponibilité et les contraintes actives.
12. Ne pas modifier automatiquement le planning. Toute adaptation reste soumise aux
    mécanismes explicites de décision de l'athlète.

## Collecte conversationnelle et confirmation

Le mécanisme de proposition existant est réutilisé, sans ajouter de table ni de
migration. Le champ `daily_checkin` exige explicitement :

- énergie et confort/douleur, chacun noté de 1 à 5 ;
- maladie et disponibilité, sans valeur par défaut implicite ;
- zone et côté si la note de confort/douleur est inférieure à 5 ;
- note facultative.

La date est limitée à aujourd'hui. La création de proposition ne touche pas à
`daily_checkins`. La confirmation vérifie qu'aucun check-in n'a été enregistré
entre-temps, puis crée la ligne et clôt la proposition dans la même transaction.
Un check-in déjà existant n'est pas écrasé par ce flux.

## Contrat de l'outil

`recovery_analysis(target_date?)` :

- `target_date` est facultatif et vaut aujourd'hui ;
- lit toutes les lignes Wellness du profil dans OpenCoach, sans filtre ni priorité fournisseur ;
- consolide chaque métrique entre les imports et signale les conflits non résolus ;
- ne lit que les données du profil athlète authentifié ;
- retourne les fenêtres 7/14/30 jours, la provenance des valeurs et les check-ins du jour ;
- ne réalise aucune écriture et ne calcule aucun score composite.

## Validation

Les tests dédiés couvrent :
- fenêtres de récupération et métriques sommeil ;
- présence du ressenti subjectif ;
- collecte quotidienne avec preuve utilisateur, validation des valeurs, absence d’écriture avant confirmation et conflit si un check-in existe déjà ;
- fusion de métriques complémentaires issues de plusieurs imports et gestion des conflits ;
- données manquantes explicitement inconnues ;
- enregistrement du nouvel outil dans le registre IA et règles du prompt.

Les essais de dialogue avec Ollama et la validation de la cohérence des réponses
restent à effectuer sur la VM de l'utilisateur.
