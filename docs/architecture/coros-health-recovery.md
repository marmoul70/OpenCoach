# Architecture — Santé et récupération COROS vers OpenCoach

## Objectif

Faire d'OpenCoach le référentiel de données santé et récupération de l'athlète. COROS est la source primaire via le serveur MCP officiel. Les données sont importées, normalisées, historisées dans la base OpenCoach, puis consommées par le moteur de disponibilité (Readiness) et le coach quotidien.

Intervals.icu sert de référence d'architecture et de fournisseur secondaire éventuel ; il ne doit pas être requis pour que le coach fonctionne.

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

Le connecteur COROS stocke les réponses brutes dans `coros_daily_data`. Les réponses MCP observées sur le compte de test ne sont pas toutes des objets JSON : plusieurs outils renvoient des rapports texte contenant plusieurs dates. Le mapper doit donc extraire les journées internes au rapport, et non attribuer toutes les mesures à la date du snapshot. Le moteur Readiness et le coach lisent encore explicitement le fournisseur Intervals.

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
WellnessDaily (mesures normalisées, source = coros)
   |
   +--> WellnessRepository / API Wellness
   |
   +--> ReadinessService (baseline individuelle + écarts)
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

Le parseur de la branche de travail normalise actuellement les champs déjà représentables dans `WellnessDay` : durée du sommeil principal, score de sommeil, HRV nocturne moyenne, FC au repos du jour le plus récent du rapport santé, FC moyenne du sommeil, pas, charge courte (ATL) et charge longue (CTL). Le ratio de charge COROS n'est pas enregistré dans `ramp_rate` car ces deux notions ne sont pas équivalentes. Le stress, les phases détaillées du sommeil, la baseline HRV et les séries temporelles restent conservés dans les snapshots bruts jusqu'à l'évolution du modèle canonique.

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
- [ ] Étendre le modèle canonique pour stress, baseline HRV, phases du sommeil et séries temporelles.
- [ ] Valider l'import complet en base et l'idempotence avec les réponses MCP réelles.

### Sprint 2 — Readiness indépendant d'Intervals

- Faire lire le Readiness à partir des données COROS normalisées.
- Garder la compatibilité historique Intervals pendant la transition, avec sélection explicite de source et indication de fraîcheur.
- Éviter tout mélange de baselines de fournisseurs différents.
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
