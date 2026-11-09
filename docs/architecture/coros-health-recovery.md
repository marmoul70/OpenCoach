# Architecture — Santé et récupération COROS vers OpenCoach

## Objectif

Faire d'OpenCoach le référentiel unique de données santé et récupération de l'athlète. COROS, Intervals.icu, Garmin, Apple Health et les autres intégrations sont des fournisseurs d'import interchangeables. Les données sont importées, normalisées et historisées dans la base OpenCoach. Readiness, les tendances, le tableau de bord et le coach lisent exclusivement ce stockage centralisé.

## État du code observé sur `main` (base 0.8.1)

### Connecteur Intervals.icu existant

- `integrations/intervals/client.py` expose `get_wellness(oldest, newest)` sur `/athlete/{athlete_id}/wellness`.
- `integrations/intervals/wellness_mapper.py` convertit les champs Intervals en `WellnessDay` : `ctl`, `atl`, `rampRate`, `restingHR`, `hrv`, `sleepSecs`, `sleepScore`, `sleepQuality`, `avgSleepingHR`, `spO2`, `steps`.
- `integrations/intervals/sync.py` persiste ces valeurs via `WellnessRepository`.
- Le modèle `WellnessDaily` et le modèle métier `WellnessDay` fournissent déjà une structure canonique partielle.
- Le service Readiness et les routes Wellness/Coach sont actuellement configurés avec `provider="intervals"`.

### Connecteur COROS existant

- Authentification OAuth/PKCE vers le serveur MCP COROS Europe ; jetons chiffrés côté serveur.
- Découverte des outils par `tools/list` et appels `tools/call`.
- Import incrémental/reprenable, checkpoints, verrou DB et timer systemd déjà en place.
- Les catégories santé actuellement déclarées comprennent `daily_health`, `sleep`, `hrv`, `heart_rate`, `resting_heart_rate`, `stress`, `stress_timeseries`, `health_check` et `training_load`.
- Les réponses sont conservées dans `coros_daily_data` sous forme de snapshots JSON par date et catégorie.

### Écart fonctionnel majeur

Le connecteur COROS stocke les réponses brutes dans `coros_daily_data`. Les réponses MCP observées sur le compte de test ne sont pas toutes des objets JSON : plusieurs outils renvoient des rapports texte contenant plusieurs dates. Le mapper doit donc extraire les journées internes au rapport, et non attribuer toutes les mesures à la date du snapshot. Les anciens chemins Readiness, Wellness et Coach sélectionnaient un fournisseur (COROS prioritaire, Intervals en repli). La branche de travail remplace cette logique par une agrégation des métriques de tous les imports stockés dans OpenCoach.

## Architecture cible

```text
COROS MCP
   |
   v
CorosMcpClient / CorosImportService
   |
   +--> coros_daily_data (archive brute, traçabilité et relecture)
   |
   v
COROS health mapper (payload fournisseur -> modèle métier)
   |
   v
WellnessDaily (mesures normalisées, provenance = coros)
   |
   +--> WellnessRepository / API Wellness
   |
   +--> Wellness aggregation OpenCoach (fusion par métrique et par date)
             |
             v
       ReadinessService (baseline individuelle + écarts)
             |
             v
       Coach quotidien / adaptation de séance
```

Les données brutes sont conservées pour permettre de corriger les mappings sans perdre les imports historiques. Les données normalisées sont la source de lecture du coach. Une donnée absente ou invalide reste `null` : aucune valeur n'est inventée et une synchronisation partielle ne doit jamais effacer une mesure déjà valide.

## Périmètre de données à couvrir

| Domaine | Catégories COROS déjà présentes dans le code | Utilisation cible |
|---|---|---|
| Sommeil | `sleep` | durée, score/qualité, horaires et phases si exposés |
| HRV | `hrv` | valeur nocturne, tendance et comparaison à la baseline |
| Fréquence cardiaque | `heart_rate`, `resting_heart_rate` | FC moyenne/nocturne et FC au repos |
| Stress | `stress`, `stress_timeseries` | niveau et évolution quotidienne |
| Santé quotidienne | `daily_health`, `health_check` | mesures réellement retournées par COROS (ex. SpO2 si disponible) |
| Charge | `training_load` | charge et indicateurs de forme si fournis |
| Activités | `activities`, `activity_details` | charge issue des séances et contexte d'effort |

Les champs exacts et les unités doivent être confirmés à partir des schémas MCP et de réponses réelles COROS. Ne pas supposer que COROS fournit une mesure simplement parce qu'Intervals.icu possède un champ homonyme.

### Contrat confirmé par l'export COROS de test (2026-11-04)

Les 36 snapshots exportés contiennent des rapports texte pour `daily_health`, `sleep`, `hrv`, `heart_rate`, `stress` et `training_load`. Les rapports `daily_health`, `sleep`, `hrv` et `training_load` peuvent contenir plusieurs dates dans un seul payload. Les dates du sommeil et de la HRV sont des dates de réveil.

Le parseur de la branche de travail normalise les champs suivants : durée du sommeil principal, score de sommeil, HRV nocturne moyenne et baseline HRV, FC au repos du jour le plus récent du rapport santé, FC moyenne/minimale/maximale du sommeil, durée des phases profond/léger/REM/éveil, stress moyen, pas, charge courte (ATL) et charge longue (CTL). Le ratio de charge COROS n'est pas enregistré dans `ramp_rate` car ces deux notions ne sont pas équivalentes. Les nouvelles mesures sont stockées dans des colonnes canoniques nullable de `wellness_daily`, avec migration Alembic dédiée. Les endpoints Wellness, Readiness et Coach consolident désormais les métriques de tous les fournisseurs importés dans OpenCoach. La valeur la plus récente est retenue par métrique et par date lorsque les horodatages de mise à jour le permettent. En cas de conflit de fraîcheur identique ou inconnue, la métrique reste inconnue et le conflit est signalé. Les snapshots bruts COROS restent une archive d'import et ne sont pas consultés par le coach IA.

Les rapports bruts ne doivent pas être ajoutés comme fixtures permanentes : ils peuvent contenir des données personnelles. Les tests utilisent des extraits synthétiques reprenant leur structure.

## Principes de conception

1. **OpenCoach est propriétaire de l'historique normalisé.** Une fois synchronisées, les données utiles restent consultables dans OpenCoach sans appel à Intervals.icu.
2. **Conserver la provenance.** Le fournisseur et, si nécessaire, le nom de l'outil/catégorie d'origine doivent rester identifiables.
3. **Séparer brut et canonique.** `coros_daily_data` conserve les réponses fournisseur ; `wellness_daily` expose les mesures normalisées au coach.
4. **Idempotence.** Une nouvelle synchronisation d'une même date met à jour les mêmes enregistrements sans doublon.
5. **Fusion non destructive.** Un payload partiel ne remplace pas une mesure existante par `null`.
6. **Qualité des données.** Valider dates, unités, types, valeurs finies et plages plausibles ; conserver les données brutes même si une mesure n'est pas normalisable.
7. **Pas de score opaque inventé.** Le score Readiness OpenCoach doit être calculé à partir des données disponibles et des baselines individuelles ; les scores COROS restent des mesures source.
8. **Sécurité et confidentialité.** Aucun jeton ou payload de santé sensible dans les logs. Accès strictement isolé par profil athlète.
9. **Lecture seule côté COROS.** OpenCoach ne modifie pas le calendrier ou les données COROS.

## Plan de réalisation

### Sprint 1 — Contrat et mapping COROS

- Capturer/valider les schémas réels de `tools/list` pour les outils santé activés.
- [x] Examiner un export réel anonymisé des snapshots COROS.
- [x] Définir un parseur indépendant du client MCP pour les rapports texte.
- [x] Extraire plusieurs journées datées d'un même rapport et les persister via `SqlWellnessRepository`.
- [x] Ajouter des tests synthétiques pour sommeil, HRV, santé quotidienne et charge.
- [x] Étendre le modèle canonique pour stress, baseline HRV, phases du sommeil et fréquences cardiaques nocturnes.
- [x] Exposer ces mesures dans les réponses Wellness et les tendances API.
- [x] Consolider les mesures de tous les fournisseurs importés dans OpenCoach, sans priorité fournisseur, métrique par métrique et date par date.
- [ ] Étendre le modèle canonique aux séries temporelles et autres mesures confirmées.
- [x] Valider les migrations et les tests d'intégration en CI.
- [ ] Valider un import complet sur la base locale de production et contrôler l'idempotence après synchronisation réelle.

### Sprint 2 — Readiness indépendant des fournisseurs

- [x] Faire lire Readiness depuis les lignes Wellness centralisées dans OpenCoach.
- [x] Consolider les métriques de tous les fournisseurs pour la journée courante et la baseline historique.
- [x] Utiliser la date de mise à jour fournisseur, puis la date d'import OpenCoach, pour résoudre la fraîcheur.
- [x] Écarter et signaler les métriques en conflit plutôt que choisir un fournisseur arbitrairement.
- [x] Retirer les repositories de données brutes COROS des chemins Readiness, Wellness et Coach IA.
- Vérifier les données nécessaires et dégrader proprement le calcul si une mesure manque.

### Sprint 3 — Coach quotidien

- Injecter dans le contexte du coach : sommeil, HRV, FC repos, FC nocturne/moyenne, stress, charge, fraîcheur et tendance multi-jours.
- Croiser ces signaux avec charge récente, séances réalisées, sensations et contraintes quotidiennes.
- Produire une recommandation explicable : maintenir, alléger, remplacer ou récupérer.
- Une donnée périmée ou absente doit déclencher un avertissement, pas une fausse précision.

### Sprint 4 — Synchronisation et observabilité

- Vérifier la couverture historique réelle de chaque outil COROS (fenêtre glissante ou plage datée).
- Synchroniser fréquemment les données récentes et rattraper les fenêtres manquées sans réimport complet.
- Afficher dernière synchronisation, catégories réussies/ignorées, fraîcheur et erreurs compréhensibles.
- Ajouter une vue Santé/Récupération dans le frontend après stabilisation du contrat API.

## Critères d'acceptation

- Une synchronisation COROS crée/met à jour des journées Wellness normalisées dans OpenCoach.
- Les données brutes COROS restent conservées.
- Le Readiness et le coach peuvent fonctionner sans compte Intervals.icu connecté.
- Les baselines sont calculées sur l'historique du même athlète et de la même source canonique.
- Les absences de données ne sont jamais remplacées par des zéros ou des valeurs estimées.
- Les tests couvrent les payloads réels COROS anonymisés et les imports répétés.
- Aucune modification n'est envoyée vers le calendrier COROS.


## Synthèse de récupération descriptive — ajout sur la branche de travail

Le module `opencoach.recovery_assessment` fournit une synthèse distincte du score Readiness. Il calcule des fenêtres glissantes de 7, 14 et 30 jours, sans fusionner les fournisseurs, et retourne pour chaque mesure la dernière valeur disponible, moyenne, médiane, nombre d'échantillons et couverture. Les domaines physiologiques (HRV, FC, sommeil, stress) et la charge (ATL/CTL) sont présentés séparément.

Le ressenti quotidien est repris uniquement depuis `DailyContext` pour la date demandée : fatigue, douleur, maladie, impact du traitement et motivation. Il n'est jamais déduit des capteurs. Si aucune mesure n'est disponible, les champs restent `null` et l'état de source est `unavailable`. Une source ancienne est signalée comme `stale`.

L'endpoint `GET /api/wellness/recovery` expose cette synthèse au coach et au futur écran Santé/Récupération. Il privilégie COROS et ne bascule sur Intervals que si aucune journée COROS n'est présente dans la fenêtre. Cette synthèse est descriptive : aucun seuil de stress ou de fatigue n'est introduit dans le score Readiness à ce stade.


## Reconstruction de l'historique Wellness COROS

Les snapshots déjà archivés dans \`coros_daily_data\` peuvent être retraités sans nouvel appel au serveur MCP COROS. Cette opération est utile lorsqu'un correctif de mapping doit être appliqué aux anciennes réponses ou lorsque des snapshots ont été importés avant la disponibilité du mapping quotidien.

### Fonctionnement

- \`rebuild_wellness_from_snapshots()\` relit les snapshots des catégories quotidiennes COROS du profil ciblé.
- La date métier extraite du rapport est utilisée ; \`CorosDailyData.metric_date\` n'est pas considérée comme la date unique des mesures, car un rapport peut contenir plusieurs journées.
- Les résultats sont agrégés par date avant toute écriture.
- Seuls les champs COROS absents sont complétés. Une valeur COROS déjà non nulle n'est pas remplacée.
- Les enregistrements Intervals ne sont ni lus pour la fusion, ni modifiés.
- Les snapshots sans mesure Wellness exploitable ne créent pas de journée vide.
- L'opération est idempotente : une seconde exécution sans nouveau snapshot ni changement de mapping ne doit produire aucune création ou mise à jour.

### Simulation puis application

Depuis la racine du dépôt, avec l'environnement virtuel OpenCoach activé :

\`\`\`bash
.venv/bin/python scripts/maintenance/rebuild-coros-wellness.py \\
  --start-date 2026-10-01 \\
  --end-date 2026-11-04
\`\`\`

La commande est en simulation par défaut : elle affiche le nombre de snapshots parcourus, les journées mappées et les créations/compléments qui seraient effectués. Elle ne modifie pas la base.

Après vérification du résultat, l'application réelle nécessite l'option explicite \`--apply\` :

\`\`\`bash
.venv/bin/python scripts/maintenance/rebuild-coros-wellness.py \\
  --start-date 2026-10-01 \\
  --end-date 2026-11-04 \\
  --apply
\`\`\`

Si plusieurs profils athlètes existent dans la base, fournir explicitement \`--profile-id UUID\`. La commande refuse de choisir arbitrairement un profil.

### Sécurité opérationnelle

- Effectuer une sauvegarde SQLite avant une application réelle.
- Ne pas lancer cette commande pendant une synchronisation COROS concurrente.
- La commande ne contacte pas COROS, ne modifie pas la configuration de synchronisation et n'écrit rien dans le calendrier COROS.
- Vérifier les compteurs de simulation avant d'utiliser \`--apply\`.
- La simulation n'est pas un remplacement de sauvegarde ; elle ne valide pas non plus la plausibilité physiologique des mesures.


## Frontend Santé & Récupération

Une page dédiée est disponible sur la branche de travail à l'adresse interne `/health`, avec une entrée **Santé** dans les navigations desktop et mobile. Elle complète la carte compacte « État de forme » du Dashboard sans la remplacer.

Le composant `frontend/src/modules/health/HealthPage.tsx` consomme l'endpoint existant `GET /api/wellness/recovery` au moyen du contrat TypeScript centralisé dans `frontend/src/core/wellness/api.ts`. Il ne duplique ni le calcul des fenêtres ni l'agrégation des séries côté navigateur.

La page présente :
- la source, la date de la dernière journée, l'état de fraîcheur et la couverture sur 30 jours ;
- un sélecteur 7/14/30 jours avec les mesures quotidiennes disponibles (HRV, baseline, fréquence cardiaque, sommeil détaillé, stress, SpO₂, pas et charge) ;
- des graphiques d'évolution quotidienne sur 7/14/30 jours pour HRV, FC au repos, sommeil, CTL, ATL et stress, calculés depuis l'endpoint de tendances déjà existant ;
- les séries COROS horodatées avec moyenne, minimum, maximum, nombre de mesures et jours couverts ;
- le ressenti subjectif séparément des mesures capteurs lorsqu'il est renseigné.

Les mesures absentes restent affichées comme indisponibles et ne sont jamais converties en zéro. Les graphiques et les mesures quotidiennes utilisent le même fournisseur (COROS ou Intervals selon la source retenue par l'évaluation de récupération), afin d'éviter de juxtaposer des séries issues de baselines différentes. Les séries sont descriptives et ne changent pas le calcul Readiness. Le bouton Actualiser relit l'API ; il ne déclenche pas de synchronisation COROS.

Validation attendue sur VM après mise à jour de la branche :
1. Ouvrir `/health` sur desktop et mobile.
2. Vérifier la navigation Santé et le lien direct.
3. Contrôler les fenêtres 7/14/30 jours et la cohérence des compteurs avec la base locale.
4. Vérifier le rendu des champs absents et des séries détaillées.
5. Vérifier qu'Actualiser ne déclenche aucun import ni appel de synchronisation COROS.


## Audit de fiabilité avant intégration sur main

L'audit du pipeline a confirmé les points suivants :

- Le timer `opencoach-coros-sync.timer` déclenche un contrôle toutes les 15 minutes ; la fréquence effective reste celle configurée sur chaque connexion COROS.
- Le service systemd est de type `oneshot` et exécute `opencoach.commands.sync_coros`.
- Les synchronisations API et planifiées utilisent le même worker `run_coros_sync_job`, avec verrou persistant par profil et checkpoints par catégorie/fenêtre.
- Les snapshots bruts sont uniques par profil/date/catégorie. Les activités d'une journée sont regroupées dans un snapshot et remplacées par identifiant COROS lors d'une nouvelle lecture.
- Les migrations COROS et leur point de fusion avec la branche équipement forment une chaîne Alembic à tête unique.

### Correctifs apportés pendant l'audit

1. **Synchronisation incrémentale sans nouvelle activité** : après un import initial réussi, une fenêtre incrémentale vide est un succès. `last_synced_at` doit avancer même si aucune nouvelle activité n'a été créée ; sinon le timer relance le même travail à chaque passage. Le premier import sans activité reste en erreur et réessayable.
2. **Référentiel unique OpenCoach** : les chemins Readiness, Wellness et Coach n'interrogent plus les tables brutes COROS ni les API fournisseurs. Ils lisent les lignes normalisées `wellness_daily` et fusionnent les imports par métrique. Les séries temporelles COROS restent une archive technique, hors du chemin de calcul du coach.
3. **Horodatage de Santé** : l'interface lit `last_synced_at` depuis `GET /api/integrations/coros/connection`, qui représente la dernière synchronisation réussie, et non le dernier déclenchement du timer systemd. Les timestamps SQL naïfs sont interprétés comme UTC côté navigateur.

### Tests de non-régression ajoutés

- Import initial vide : le timestamp n'avance pas et l'historique reste réessayable.
- Import incrémental vide après import initial : le timestamp avance.
- Import avec nouvelles activités : le timestamp avance.
- Catégorie activités désactivée : le timestamp avance après une synchronisation réussie.
- Agrégation multi-fournisseurs : métriques complémentaires fusionnées, fraîcheur résolue, conflits non départagés laissés inconnus.

### Limite de validation restante

La CI valide les mappings, repositories, API, idempotence et frontend sur des fixtures synthétiques. Elle ne remplace pas la validation finale sur la base locale réelle : vérifier les compteurs avant/après un import, relancer le même import, comparer les snapshots et confirmer l'absence de doublons. Cette validation doit être faite avec une sauvegarde préalable et sans lancer deux synchronisations simultanément.
