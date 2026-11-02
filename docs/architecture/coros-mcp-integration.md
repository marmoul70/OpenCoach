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

La première fenêtre est six mois glissants. Le endpoint manuel `POST /api/integrations/coros/sync` importe les activités et les détails disponibles, ainsi que les catégories quotidiennes activées, dans `coros_daily_data`. Les plages datées sont découpées en fenêtres de sept jours et les écritures sont idempotentes. Les outils COROS limités à une fenêtre glissante (santé quotidienne, FC au repos, stress et charge) ne fournissent ici que leurs sept derniers jours ; sommeil, HRV et FC moyenne utilisent des plages datées. Une relance reprend sans doublons, mais aucun curseur de progression n'est encore persisté. Les FIT ne sont pas encore téléchargés. Le réglage de fréquence est enregistré dans l'interface mais le planificateur automatique reste à implémenter.

## Interface cible

Réglages > Connexions > COROS : connexion navigateur, état, catégories activables, fréquence, bouton de synchronisation manuelle, progression, compteurs, erreurs et reprise. La déconnexion supprime les jetons mais conserve les données importées. OpenCoach ne modifie jamais le calendrier COROS.
