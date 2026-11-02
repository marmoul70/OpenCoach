# Intégration COROS MCP

Conception initiale de l'intégration COROS dans OpenCoach.

- Serveur officiel COROS MCP, région Europe : `https://mcpeu.coros.com/mcp`.
- Connexion OAuth/PKCE avec parcours navigateur ; ne jamais collecter le mot de passe COROS.
- Historique initial limité aux six derniers mois.
- Import des activités, détails, tours, sommeil, HRV, fréquence cardiaque, stress, santé quotidienne et charge selon disponibilité des outils COROS.
- Synchronisation incrémentale configurable depuis l'interface web.
- Intégration indépendante d'Intervals.icu et strictement en lecture seule : aucune modification du planning COROS.
- Jetons chiffrés côté backend, aucun secret exposé au frontend.
- Import idempotent par jour et catégorie ; les données déjà présentes sont mises à jour au lieu d'être dupliquées. Les FIT restent désactivés par défaut et soumis au quota COROS de 50 fichiers par fenêtre de 24 heures.

Le détail du flux OAuth et les outils doivent être validés par tests d'intégration simulés avant de déclarer la connexion opérationnelle.

## Flux OAuth officiel

Le client dynamique COROS s'enregistre via `POST /connect/register`, puis crée une session navigateur via `POST /api/v1/cli/login-sessions`. L'interface ouvre `loginUrl`; le backend interroge `/api/v1/cli/login-sessions/{sessionId}/claim` avec `X-Poll-Token`. Après autorisation, le backend échange le `loginTicket` contre les jetons OAuth via `/oauth2/token` et PKCE. Scopes : `openid offline_access mcp.tools`. Les jetons sont chiffrés côté serveur, jamais exposés au navigateur ni journalisés. Aucun mot de passe COROS n'est collecté.

## Capacités MCP à valider

Découvrir le catalogue avec `tools/list`, puis utiliser selon disponibilité : `querySportRecords`, `getActivityDetail`, `queryActivityLapData`, `queryCustomActivityLapData`, `downloadActivityFitFiles`, `queryDailyHealthData`, `querySleepOverview`, `querySleepHrv`, `queryAvgHeartRate`, `queryRestingHeartRate`, `queryStressLevel`, `queryStressTimeSeries` et `queryHealthCheckTimeSeries`. Les noms et schémas de forme/charge doivent être confirmés depuis le catalogue réel avant implémentation.

## Import et synchronisation

La première fenêtre est six mois glissants. Le endpoint asynchrone `POST /api/integrations/coros/sync/start` lance l'import en arrière-plan ; `GET /api/integrations/coros/sync/status/{job_id}` expose son état pendant la vie du processus. Le endpoint historique `POST /api/integrations/coros/sync` reste synchrone pour compatibilité. Les activités et catégories quotidiennes activées sont enregistrées dans `coros_daily_data`, avec mise à jour idempotente. Les plages datées sont découpées en fenêtres de sept jours. Après chaque fenêtre, le backend valide les données et persiste le prochain jour à traiter dans `integration_connections.config.coros_sync_checkpoint`. Si le processus s'arrête, un nouvel import reprend au prochain jour sauvegardé ; les fenêtres déjà validées ne sont pas rejouées. Le checkpoint est supprimé à la fin d'un import réussi. L'identifiant, le statut, les dates, le résultat, l'erreur générique et la catégorie en cours sont également persistés dans `integration_connections.config.coros_sync_job`. L'endpoint de connexion expose cet état et l'interface reprend le suivi après rechargement de la page. Un verrou dédié `coros_sync_locks`, unique par profil, empêche deux imports de démarrer simultanément, y compris entre plusieurs processus API. Il est rafraîchi à chaque fenêtre importée et libéré à la fin du traitement. Un verrou sans heartbeat depuis plus de 30 minutes est considéré comme orphelin et peut être récupéré après un arrêt brutal. L'exécution reste assurée par `BackgroundTasks` du processus API ; le verrou évite les doublons, mais ne transforme pas encore ce mécanisme en file de tâches durable capable de relancer seul un travail interrompu. Les outils COROS limités à une fenêtre glissante (santé quotidienne, FC au repos, stress et charge) ne fournissent ici que leurs sept derniers jours ; sommeil, HRV et FC moyenne utilisent des plages datées. Les FIT ne sont pas encore téléchargés. Le planificateur automatique est exécuté par un timer systemd toutes les 15 minutes. La commande `opencoach.commands.sync_coros` sélectionne les profils actifs dont la connexion est activée, puis compare `last_synced_at` à `sync_interval_hours`. Une fréquence de 0 désactive la synchronisation automatique ; une connexion jamais synchronisée est immédiatement éligible. Les imports planifiés réutilisent le même worker, les checkpoints et le verrou DB que les imports manuels. L'installation systemd déploie et active le service et son timer COROS.

## Interface cible

Réglages > Connexions > COROS : connexion navigateur, état, catégories activables, fréquence, bouton de synchronisation manuelle, progression, compteurs, erreurs et reprise. La déconnexion supprime les jetons mais conserve les données importées. OpenCoach ne modifie jamais le calendrier COROS.
