# Intégration COROS MCP

Conception initiale de l'intégration COROS dans OpenCoach.

- Serveur officiel COROS MCP, région Europe : `https://mcpeu.coros.com/mcp`.
- Connexion OAuth/PKCE avec parcours navigateur ; ne jamais collecter le mot de passe COROS.
- Historique initial limité aux six derniers mois.
- Import des activités, détails, tours, sommeil, HRV, fréquence cardiaque, stress, santé quotidienne et charge selon disponibilité des outils COROS.
- Synchronisation incrémentale configurable depuis l'interface web.
- Intégration indépendante d'Intervals.icu et strictement en lecture seule : aucune modification du planning COROS.
- Jetons chiffrés côté backend, aucun secret exposé au frontend.
- Import reprenable, idempotent et respectueux des quotas COROS, notamment 50 fichiers FIT par fenêtre de 24 heures.

Le détail du flux OAuth et les outils doivent être validés par tests d'intégration simulés avant de déclarer la connexion opérationnelle.
