# Audit et conception — Centre de notifications persistant

Date : 2026-11-05  
Dépôt : `marmoul70/OpenCoach`  
Branche : `feature/persistent-notification-center`  
Base : `main` à `09fe8eaf726817c5b835130df5d7b54e33112876`

## Objectif

Conserver dans OpenCoach chaque notification métier destinée à l'utilisateur, indépendamment de la livraison Web Push sur ses appareils. L'utilisateur doit pouvoir retrouver une notification même après l'avoir effacée du centre de notifications iOS.

## Résultat de l'audit du code existant

### Composants déjà présents

- `app/opencoach/services/push_notification.py` : service d'envoi Web Push. Il construit le payload (titre, corps, URL, badge) puis envoie aux abonnements.
- `app/opencoach/database/models/push_subscription.py` : abonnements par appareil, préférences par appareil et compteur `badge_count`.
- `app/opencoach/database/repositories/sql_push_subscription.py` : lecture/écriture des abonnements, préférences et compteur de badge.
- `app/opencoach/api/push.py` : routes authentifiées pour gérer abonnements, appareils, préférences et remise à zéro du badge.
- `frontend/src/modules/pwa/pushApi.ts` : client API pour les abonnements, appareils, préférences et badge.
- `frontend/public/sw.js` : réception et affichage des notifications système.
- `frontend/src/modules/settings/NotificationsSection.tsx` : activation et préférences Push.
- `frontend/src/components/ui/ToastProvider.tsx` : notifications éphémères dans l'interface, pas un historique.
- `app/opencoach/services/system_notification_state.py` : déduplication des alertes système via `data/notifications/system-alerts.json`. Ce fichier stocke uniquement un état d'échec/rétablissement par événement, pas les notifications à lire.

### Producteurs d'envoi identifiés

| Producteur | Méthode | Catégorie fonctionnelle |
|---|---|---|
| `commands/sync_intervals.py` | `send_system_sync_error` | Erreur de synchronisation Intervals.icu |
| `commands/refresh_daily_health.py` | `send_system_sync_error` | Échec de collecte des données santé |
| `scripts/backup_database.py` | `send_system_backup_error` | Échec de sauvegarde |
| `coaching/weekly_debrief_notification.py` | `send_weekly_debrief_notification` | Programme hebdomadaire prêt |
| `commands/send_tomorrow_training_reminder.py` | `send_training_reminder` | Rappel de séance |

Le service possède également `send_to_all`, qui envoie à tous les abonnements. Il faut vérifier ses éventuels usages avant de le faire évoluer.

### Lacune fonctionnelle confirmée

Le service Push envoie le contenu aux appareils et incrémente le compteur de badge de chaque abonnement. Il ne crée pas d'enregistrement métier consultable dans la base OpenCoach. Le compteur de badge est un compteur technique par appareil, pas un historique et pas un compteur fiable de notifications non lues.

Les préférences de notification et les abonnements sont persistants, mais le contenu des notifications n'est pas persisté comme une boîte de réception. Les Toasts sont éphémères. Le fichier JSON des alertes système ne contient pas les titres/corps/URLs et ne peut pas servir d'historique.

## Architecture cible

### Persistance métier

Créer un modèle SQLAlchemy dédié `Notification`, distinct de `PushSubscription`, avec au minimum :

- identifiant UUID ;
- `user_id` avec clé étrangère et suppression en cascade ;
- titre et message ;
- catégorie/type stable (ex. `system`, `training`, `coaching`) ;
- niveau/priorité ;
- URL interne optionnelle ;
- date de création UTC ;
- date de lecture nullable.

La suppression d'une notification doit supprimer son enregistrement. Une suppression globale doit être strictement limitée à l'utilisateur authentifié. Ne jamais exposer les endpoints Push, clés VAPID ou secrets dans les réponses du centre.

### Cycle d'envoi

Faire évoluer le point central d'envoi pour enregistrer une notification métier une seule fois par utilisateur, puis tenter sa livraison Push aux appareils autorisés. Plusieurs appareils ne doivent pas créer plusieurs entrées dans l'historique. Une panne de Push ne doit pas faire perdre l'entrée persistée. Les préférences Push contrôlent la livraison sur appareil ; elles ne doivent pas effacer ni empêcher la conservation d'un événement métier.

Les producteurs doivent fournir explicitement l'identité du destinataire et une catégorie. Les envois génériques sans destinataire doivent être traités explicitement, sans inventer un propriétaire.

### API cible

Ajouter des routes protégées par `get_current_user_id` :

- lister les notifications de l'utilisateur, triées de la plus récente à la plus ancienne, avec pagination ;
- obtenir le nombre de notifications non lues ;
- marquer une notification comme lue ;
- marquer toutes les notifications comme lues ;
- supprimer une notification ;
- supprimer toutes les notifications.

Toutes les opérations doivent inclure le filtre `user_id` côté SQL, y compris les opérations par identifiant.

### Interface cible

- Icône cloche dans l'en-tête de navigation avec badge du nombre de notifications non lues.
- Menu déroulant accessible sur desktop et mobile, avec les notifications récentes.
- Accès à une vue complète « Notifications » pour l'historique.
- Filtres « Toutes » / « Non lues ».
- Actions rapides : marquer comme lue, tout marquer comme lu, supprimer une entrée, tout effacer avec confirmation.
- États de chargement, vide et erreur ; rafraîchissement du compteur après chaque action.
- Respect du design system OpenCoach/Pulse et des contraintes d'affichage iPhone.

## Plan de réalisation et contrôles

1. Terminer l'inventaire des points d'envoi et vérifier les usages de `send_to_all`.
2. Ajouter modèle, migration Alembic, repository et service de persistance.
3. Intégrer la persistance au service central sans dupliquer une entrée par appareil.
4. Ajouter API authentifiée et tests d'isolation multi-utilisateur.
5. Ajouter client API, menu cloche/badge et vue historique responsive.
6. Tester les cas Push réussi, Push indisponible, aucun appareil, plusieurs appareils, lecture, suppression et isolation entre utilisateurs.
7. Exécuter la suite pytest concernée, lint et build frontend. Ne pas déployer sur la VM et ne pas fusionner dans `main` sans validation explicite.

## Contraintes de sécurité et de compatibilité

- Ne pas modifier le fonctionnement actuel d'inscription/désinscription Web Push ni les préférences existantes.
- Ne pas utiliser `badge_count` par appareil comme source de vérité pour le badge UI.
- Une notification enregistrée doit rester consultable même si le navigateur/iOS supprime sa notification système.
- Toutes les dates persistées et renvoyées par l'API doivent être cohérentes en UTC.
- Conserver les conventions de migrations et les tests existants du dépôt.
