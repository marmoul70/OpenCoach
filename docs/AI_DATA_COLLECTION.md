# Collecte et persistance des données par le coach IA

## Objectif

Le coach OpenCoach doit être capable de repérer une information manquante, de la demander à l'athlète, puis de proposer son enregistrement durable dans OpenCoach. Une information communiquée dans une conversation ne doit jamais être confondue avec une donnée effectivement sauvegardée.

Le modèle local orchestre le dialogue. Python reste responsable de l'identification des champs autorisés, de la validation, de la persistance et de la confirmation du résultat.

## Principes non négociables

1. **Demander plutôt que supposer** : aucune valeur manquante ne peut être inventée, déduite d'une ancienne conversation ou extrapolée.
2. **Collecte ciblée** : demander uniquement les champs indispensables à la tâche en cours ; expliquer brièvement pourquoi ils sont nécessaires.
3. **Séparer conversation et profil** : une réponse de l'utilisateur peut être utilisée pour l'analyse en cours sans être présentée comme enregistrée.
4. **Confirmation explicite** : avant une création ou une modification persistante, présenter le champ, la valeur, l'unité et, en cas de remplacement, l'ancienne valeur.
5. **Validation déterministe** : Pydantic et les services métier valident type, unité, bornes, format et cohérence inter-champs.
6. **Pas d'écrasement silencieux** : les conflits et changements de valeur nécessitent une nouvelle confirmation.
7. **Traçabilité** : après écriture, retourner le champ enregistré, sa valeur normalisée et la confirmation de persistance.
8. **Isolation** : chaque opération est limitée au profil de l'athlète authentifié ; le modèle ne choisit jamais un identifiant d'athlète.
9. **Aucune écriture implicite** : ni un tool call du modèle ni un simple « j'ai compris » ne constituent une autorisation.
10. **Échec honnête** : si le champ ne peut pas être enregistré, le coach le dit et conserve au besoin la valeur uniquement dans le contexte de la conversation.

## Cycle cible

### A. Détection

Un outil de lecture retourne les champs absents avec leur nom canonique, leur unité attendue, leur caractère requis ou optionnel et la source métier concernée.

Le coach détermine si le champ est réellement nécessaire à la demande. Il ne doit pas demander l'ensemble du profil à chaque conversation.

### B. Demande et collecte

Le coach pose une question claire. Les réponses peuvent être partielles. Si la réponse est ambiguë (par exemple une valeur sans unité, une date ambiguë ou plusieurs interprétations possibles), il demande une précision.

La valeur proposée doit être normalisée côté Python. Les conversions d'unités ne sont autorisées que lorsque l'unité source et l'unité cible sont explicites.

### C. Proposition de sauvegarde

OpenCoach crée une proposition persistée avec :
- l'identifiant du profil authentifié ;
- une clé de champ appartenant à une liste blanche ;
- la valeur normalisée et son unité ;
- la valeur existante et sa version au moment de la proposition ;
- l'origine (coach conversation) et la date de création ;
- un état en attente, une expiration et un identifiant opaque.

Le modèle ne reçoit aucun accès SQL et ne peut pas choisir une cible hors liste blanche. L'outil IA exige aussi une citation exacte d'un message utilisateur et vérifie côté Python que la valeur numérique apparaît dans cette citation.

### D. Confirmation utilisateur

L'interface affiche une action explicite de confirmation. La confirmation doit être un appel API distinct, authentifié et lié à la proposition en attente. Un texte libre interprété par le LLM ne doit pas déclencher l'écriture.

Pour une modification, OpenCoach vérifie que la valeur existante n'a pas changé depuis la proposition. Si elle a changé, la proposition est invalidée et une nouvelle confirmation est nécessaire.

### E. Écriture et vérification

Un service métier dédié applique la modification avec validation et transaction. Il relit ensuite la valeur persistée et retourne un résultat vérifié. La proposition devient confirmée uniquement après commit réussi.

Les propositions expirées, refusées, déjà consommées ou appartenant à un autre profil ne peuvent pas être appliquées.

## Périmètre des données

### Premier périmètre recommandé : profil sportif

S'appuyer sur les champs déjà modélisés par OpenCoach et sur les schémas existants de app/opencoach/schemas/profile.py :
- physique : taille, poids ;
- physiologie : VMA, FC maximale, FC repos, seuils SV1/SV2, zones FC ;
- entraînement : volume hebdomadaire, jours disponibles, expérience et disciplines ;
- nutrition : cibles glucides, hydratation et sodium, uniquement si elles sont explicitement renseignées et avec unités documentées.

Les champs composites (zones cardiaques, jours disponibles, disciplines) doivent être validés comme un ensemble cohérent et ne doivent pas être écrits champ par champ de façon incohérente.

### Extensions ultérieures

Après stabilisation du profil, étendre le même mécanisme aux objets métier qui possèdent déjà leurs propres services et règles :
- contraintes temporaires et indisponibilités ;
- calendrier des courses et objectifs ;
- matériel et chaussures ;
- préférences de coaching.

Chaque domaine doit utiliser son propre service métier. Ne pas créer un mécanisme générique qui autorise arbitrairement l'écriture dans toutes les tables.

## Architecture technique cible

- **Read model** : les outils existants exposent les champs manquants et leur qualité.
- **Conversation state** : l'API conserve les propositions en attente, leur propriétaire, leur expiration et leur état.
- **Write service** : service métier explicite avec liste blanche de champs et validation.
- **Confirmation API** : endpoint authentifié séparé pour confirmer ou refuser une proposition.
- **Frontend** : conversation intégrée au tableau de bord Coach ; carte de confirmation affichant champ, valeur, unité, ancienne valeur éventuelle et actions Confirmer / Refuser. Les propositions en attente sont rechargées depuis l'API après actualisation.
- **Audit** : journal minimal des changements (profil, champ, ancienne/nouvelle valeur, date, source), sans stocker les conversations complètes.
- **LLM** : peut proposer et expliquer ; ne peut ni confirmer à la place de l'utilisateur, ni écrire directement.

## Contrats API envisagés

Les noms exacts seront ajustés à l'architecture existante lors de l'implémentation.

- POST /api/ai/coach : peut retourner une proposition de collecte structurée en plus de la réponse textuelle.
- GET /api/ai/data-proposals/{proposal_id} : consulter une proposition appartenant à l'utilisateur authentifié.
- POST /api/ai/data-proposals/{proposal_id}/confirm : confirmer explicitement et appliquer la valeur.
- POST /api/ai/data-proposals/{proposal_id}/reject : refuser la proposition.

Aucun endpoint de confirmation ne doit accepter un nom de table, un nom d'attribut SQL ou un identifiant d'athlète fourni librement par le client.

## Critères d'acceptation

- Le coach repère une donnée manquante dans un outil et pose une question ciblée.
- Il attend la réponse avant de relancer l'outil qui dépend de cette donnée.
- La réponse utilisateur est utilisable dans le dialogue sans être faussement présentée comme persistée.
- Une proposition de sauvegarde est structurée, validée et liée au profil authentifié.
- Aucun enregistrement ne survient sans action explicite de confirmation côté interface/API.
- Une modification affiche l'ancienne et la nouvelle valeur et détecte les conflits.
- Les tests couvrent validation, unités, données composites, refus, expiration, double confirmation, isolation entre athlètes et échec transactionnel.
- Après sauvegarde, les outils de lecture retrouvent la nouvelle valeur depuis la base.

## Découpage de réalisation

1. **Contrats et état de proposition** : modèle SQLAlchemy, migration, schémas API et tests.
2. **Validation et écriture du profil** : service dédié réutilisant les schémas existants, liste blanche et contrôles de cohérence.
3. **Cycle de confirmation API** : lecture, confirmation, refus, expiration et protection contre les conflits.
4. **Orchestration conversationnelle** : détecter les champs manquants, collecter les réponses, créer les propositions sans écrire.
5. **Interface frontend** : carte de confirmation et retour de sauvegarde vérifiée.
6. **Extension métier** : contraintes, courses, matériel et préférences, domaine par domaine.

## Extension du profil d'entraînement

Le mécanisme de proposition couvre également les champs structurés déjà présents dans
`AthleteTrainingSchema` :

- `available_days` : liste de jours, avec lundi = 0 et dimanche = 6. Les valeurs
  hors plage et les doublons sont rejetés ; la liste est normalisée dans l'ordre
  croissant.
- `experience` : une valeur parmi `beginner`, `intermediate`, `advanced`
  et `expert`.
- `sport_disciplines` : liste issue de l'énumération métier
  (`road_running`, `trail_running`), sans doublon.

La citation utilisateur doit étayer chaque élément proposé. Pour les jours et les
disciplines, le validateur de preuve reconnaît les libellés français usuels ; il ne
se contente pas de vérifier que le tableau JSON est valide. À la confirmation, le
service reconstruit et valide l'ensemble des champs d'entraînement avant d'écrire
la seule propriété proposée. La comparaison avec la valeur initiale protège aussi
ces listes contre les modifications concurrentes.

L'interface affiche les valeurs structurées sous forme lisible (jours en français,
niveaux traduits et disciplines explicites). Le stockage utilise le champ JSON déjà
présent dans `athlete_profiles` : aucune migration supplémentaire n'est requise.
