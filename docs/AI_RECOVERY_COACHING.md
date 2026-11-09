# Analyse de la forme, de la fatigue et de la récupération

## Objectif

Le coach IA doit pouvoir mener une discussion structurée sur l'état de forme de
l'athlète, sans remplacer les services déterministes OpenCoach ni poser de diagnostic.
Le raccourci « Bilan forme, fatigue et sommeil » déclenche une analyse des données
disponibles et invite le coach à demander les informations subjectives manquantes.

## Sources utilisées

### Mesures objectives

Le nouvel outil `recovery_analysis` réutilise les données Wellness déjà importées
par COROS ou Intervals :

- sommeil : durée totale, score et phases disponibles ;
- HRV et baseline HRV ;
- fréquence cardiaque au repos et mesures cardiaques nocturnes ;
- stress ;
- charge aiguë ATL et forme CTL ;
- séries temporelles COROS disponibles.

Le moteur Python `recovery_assessment.py` calcule les fenêtres distinctes de 7, 14
et 30 jours. Chaque métrique expose sa valeur courante, moyenne, médiane, nombre
d'échantillons et couverture. Les séries temporelles sont agrégées et dédupliquées
par le moteur existant.

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
4. Toujours préciser la source, la date de la dernière mesure et la couverture.
5. Distinguer fatigue générale, énergie déclarée, douleur, maladie et charge
   d'entraînement. Ne pas déduire une douleur ou une maladie d'une variation de HRV.
6. Si le ressenti du jour est absent, poser une ou deux questions ciblées et inviter
   l'athlète à renseigner le check-in « Ton état aujourd'hui » dans OpenCoach.
7. Si les données de sommeil ne sont pas importées, demander le ressenti ou signaler
   l'absence ; ne jamais fabriquer une durée ou une qualité de sommeil.
8. Ne jamais diagnostiquer un surentraînement, une maladie ou une blessure. Une
   recommandation d'entraînement doit rester cohérente avec les services de
   disponibilité et les contraintes actives.
9. Ne pas modifier automatiquement le planning. Toute adaptation reste soumise aux
   mécanismes explicites de décision de l'athlète.

## Contrat de l'outil

`recovery_analysis(target_date?)` :

- `target_date` est facultatif et vaut aujourd'hui ;
- utilise COROS en priorité et Intervals en repli, sans fusionner les fournisseurs ;
- ne lit que les données du profil athlète authentifié ;
- retourne les fenêtres 7/14/30 jours, les séries temporelles disponibles et les
  check-ins du jour ;
- ne réalise aucune écriture et ne calcule aucun score composite.

## Validation

Les tests dédiés couvrent :
- fenêtres de récupération et métriques sommeil ;
- présence du ressenti subjectif ;
- repli Intervals sans séries COROS ;
- données manquantes explicitement inconnues ;
- enregistrement du nouvel outil dans le registre IA et règles du prompt.

Les essais de dialogue avec Ollama et la validation de la cohérence des réponses
restent à effectuer sur la VM de l'utilisateur.
