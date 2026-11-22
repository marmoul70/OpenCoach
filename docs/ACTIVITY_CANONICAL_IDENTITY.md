# Conception — identité canonique des activités multi-fournisseurs

**Statut :** conception à valider avant migration SQL  
**Date :** 9 novembre 2026  
**Périmètre :** activités sportives importées dans OpenCoach et consommées par les services métier.

## 1. Problème confirmé

La table `activities` porte actuellement un couple unique `provider + provider_activity_id`. Le repository SQL recherche une activité avec ce même couple avant insertion. Cette règle empêche de réimporter deux fois la même activité depuis un fournisseur, mais ne reconnaît pas une activité identique importée depuis deux fournisseurs différents.

Conséquence : COROS et Intervals.icu peuvent créer deux lignes pour une même séance. Les agrégats qui lisent les activités OpenCoach peuvent alors compter deux fois la distance, la durée, le dénivelé ou la charge.

Cette conception doit préserver le principe directeur : **les calculs ne lisent que les données stockées dans OpenCoach**. La provenance sert à tracer les imports ; elle ne devient jamais une source de calcul externe.

## 2. Invariants métier

1. Une séance physique ne doit contribuer qu'une fois aux agrégats d'entraînement.
2. Chaque identifiant fournisseur importé doit rester traçable et réimportable de façon idempotente.
3. Les données brutes et métriques de chaque fournisseur doivent rester récupérables ; aucune information source ne doit être écrasée silencieusement.
4. Une correspondance incertaine ne doit jamais entraîner une fusion automatique.
5. Deux séances réellement distinctes, même proches dans le temps, doivent rester distinctes.
6. L'isolation par athlète est absolue : aucune correspondance entre profils.
7. Les activités manuelles doivent rester distinctes des imports, sauf association explicite déjà établie.
8. Le calcul métier consomme une activité canonique OpenCoach et non une ligne par fournisseur.

## 3. Architecture cible proposée

Séparer l'identité de la séance de ses identifiants d'import :

- `activities` devient l'enregistrement canonique OpenCoach d'une séance physique.
- Une table enfant `activity_sources` conserve une ligne par import : fournisseur, identifiant externe, date d'import, horodatages source, nom/appareil et métriques reçues.
- Une contrainte unique sur `(provider, provider_activity_id)` reste appliquée aux identifiants source, avec contrôle de profil.
- Chaque source pointe vers une activité canonique ; plusieurs sources peuvent donc documenter la même séance.
- Les services statistiques lisent uniquement les activités canoniques.
- Une politique de consolidation par métrique choisit la valeur la plus fiable et la plus fraîche selon des règles explicites. Les valeurs source restent conservées dans `activity_sources`.

La migration doit convertir chaque activité existante en activité canonique avec une source associée, sans supprimer de ligne ni modifier les agrégats historiques lors du backfill.

## 4. Détection de correspondances

La détection doit produire des candidats, pas fusionner directement.

### Signaux comparés

- Même athlète (condition obligatoire).
- Type de sport normalisé et compatible.
- Heure de départ UTC, avec tolérance initiale de 120 secondes.
- Durée écoulée ou en mouvement, avec tolérance initiale de 120 secondes ou 5 % (la plus grande des deux).
- Distance, avec tolérance initiale de 100 m ou 2 % (la plus grande des deux).
- Dénivelé positif comme signal secondaire uniquement : les fournisseurs peuvent appliquer des corrections altimétriques différentes.
- Nom, appareil et provenance de fichier ne sont jamais des preuves suffisantes.

### Décision

- **Correspondance forte :** athlète + sport compatibles + heure proche + au moins deux métriques indépendantes concordantes (durée et distance, ou durée et autre signal fiable). La proposition de liaison peut être automatique uniquement si un seul candidat satisfait les règles.
- **Ambiguë :** plusieurs candidats plausibles, métriques contradictoires ou données insuffisantes. Ne pas fusionner ; conserver les deux activités et produire un état de rapprochement à examiner.
- **Aucune correspondance :** créer une nouvelle activité canonique.
- **Import idempotent :** si le couple fournisseur/identifiant existe déjà, mettre à jour la source correspondante sans créer de nouvelle activité.

Les tolérances sont des valeurs de départ à confronter aux exports réels. Elles doivent être configurables/testées et ne doivent pas être présentées comme une vérité universelle.

## 5. Consolidation des métriques

La consolidation est indépendante pour chaque métrique (durée, distance, D+, fréquence cardiaque, puissance, cadence, etc.). Une métrique absente ne vaut jamais zéro.

Ordre de décision proposé :
1. conserver la valeur de la source la plus fraîche lorsque sa qualité est comparable ;
2. privilégier une mesure native/échantillonnée plutôt qu'une estimation dérivée, si cette distinction est explicitement disponible ;
3. si deux valeurs incompatibles ont une qualité ou une fraîcheur équivalente, marquer la métrique comme conflictuelle/inconnue ;
4. ne jamais faire de moyenne arbitraire entre fournisseurs.

La règle de sélection et la provenance retenue doivent être explicables et testables.

## 6. Migration et déploiement sans perte

1. Ajouter la nouvelle table source sans modifier le chemin de lecture.
2. Backfiller chaque activité existante vers une source, avec transaction et contrôle des volumes.
3. Vérifier l'unicité des identifiants fournisseur et l'absence de source orpheline.
4. Ajouter le service de détection en mode observation (aucune fusion, aucun impact sur les scores).
5. Comparer les candidats sur des jeux de données synthétiques et des imports réels anonymisés.
6. Activer les liens forts uniquement après validation des faux positifs et faux négatifs.
7. Faire lire les agrégats depuis les activités canoniques.
8. Conserver une procédure de retour arrière et des tests de non-régression des agrégats.

Aucune migration destructive ou fusion de données ne doit être réalisée sans sauvegarde vérifiée et validation des volumes.

## 7. Tests d'acceptation obligatoires

- Même activité COROS + Intervals : une seule activité canonique et deux sources.
- Réimport du même identifiant source : aucune nouvelle source ni activité.
- Deux activités rapprochées mais distinctes : aucune fusion.
- Activités de deux athlètes : aucune correspondance possible.
- Sport incompatible : aucune fusion.
- Départ proche mais distance/durée incompatibles : ambiguïté ou séparation, jamais fusion forte.
- Données manquantes : aucune conversion en zéro et aucun rapprochement sur ce seul motif.
- Plusieurs candidats : état ambigu, aucune fusion.
- Métriques différentes entre fournisseurs : consolidation indépendante et conflit explicite.
- Agrégats avant/après migration : égalité attendue hors doublons explicitement rapprochés.
- Import d'une activité manuelle : aucune association automatique silencieuse.
- Isolation multi-tenant sur toutes les opérations de rapprochement.

## 8. Décision de livraison

Cette architecture est une proposition technique à valider. Le code actuel ne doit pas être modifié pour fusionner les activités tant que :
- le modèle canonique et le modèle de sources ne sont pas validés ;
- les règles de correspondance n'ont pas été éprouvées sur des cas représentatifs ;
- la stratégie de consolidation par métrique n'est pas couverte par tests ;
- une migration réversible et un audit des agrégats ne sont pas prêts.

En attendant, OpenCoach doit signaler le risque de doublons inter-fournisseurs et ne pas prétendre que les agrégats multi-fournisseurs sont dédupliqués.
