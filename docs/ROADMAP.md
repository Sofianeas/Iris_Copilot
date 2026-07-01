# 🛠️ IRIS Copilot
# ROADMAP
Version : 1.0

---

# Vision

IRIS Copilot est un assistant intelligent destiné aux consultants HelpDesk Niveau 1 d'IRIS IT.

Son objectif est de réduire le temps de traitement des demandes, améliorer la qualité des tickets, centraliser la documentation métier et capitaliser l'expérience acquise au fil du temps grâce à une mémoire métier.

Ce document décrit l'état actuel du projet ainsi que les évolutions prévues.

---

# État actuel du projet

## Progression globale

| Domaine | État |
|----------|:----:|
| Architecture Python | ✅ |
| Agents spécialisés | ✅ |
| Parser IA | ✅ |
| Router | ✅ |
| SQLite | ✅ |
| Historique | ✅ |
| VectorStore | 🔄 |
| Interface Streamlit | 🔄 |
| Dashboard | ⏳ |
| Mémoire IA | ⏳ |
| Statistiques | ⏳ |

---

# Sprint 1 — Fondations techniques

## Objectif

Mettre en place toute l'infrastructure permettant de développer IRIS Copilot.

## Réalisé

- Architecture du projet
- Organisation des dossiers
- Configuration Python
- Configuration Gemini
- Agents spécialisés par client
- Router automatique
- Parser IA
- Services
- Base SQLite
- Historique
- Première version Streamlit

Statut :

✅ Terminé

---

# Sprint 2 — Interface Professionnelle

## Objectif

Transformer IRIS Copilot en une véritable application métier moderne.

## Travaux

### UI

- Bibliothèque de composants
- Cartes
- Badges
- Alertes
- Notifications
- Hero Header
- KPI

### Design

- Thème graphique IRIS
- CSS global
- Responsive
- Identité visuelle

### Dashboard

- Tableau de bord
- Actions rapides
- Dernières activités
- État des services
- Statistiques principales

### Sidebar

- Navigation
- Branding
- Icônes
- État système

Statut :

🔄 En cours

---

# Sprint 3 — Validation Fonctionnelle

## Objectif

Valider chaque fonctionnalité métier.

Modules concernés :

- Analyse Mail
- Génération Ticket
- Documentation
- Historique
- SQLite
- Parser
- Router
- Gemini
- VectorStore

Pour chaque module :

- validation fonctionnelle
- tests
- optimisation
- correction

Statut :

⏳ À venir

---

# Sprint 4 — IA Documentaire & Mémoire

## Objectif

Faire d'IRIS Copilot un assistant capable d'apprendre de l'expérience.

### Documentation

- Indexation automatique
- Recherche documentaire
- ChromaDB
- Citations

### Mémoire documentaire

- Procédures
- Guides
- TOKI

### Mémoire Tickets

- Tous les tickets validés
- Recherche de cas similaires

### Mémoire Corrections

Enregistrement :

- proposition IA
- correction utilisateur
- différence

Cette mémoire permettra :

- d'identifier les erreurs fréquentes
- d'améliorer les règles métier
- de proposer des recommandations

Les règles ne seront jamais modifiées automatiquement.

Validation humaine obligatoire.

Statut :

⏳ Planifié

---

# Sprint 5 — Productivité

## Objectif

Faire gagner un maximum de temps au technicien.

Fonctionnalités prévues

### Dashboard avancé

- KPI
- Graphiques
- Activité
- Performance

### Recherche globale

Recherche simultanée dans :

- documentation
- tickets
- historique
- mémoire

### Notifications

- succès
- erreur
- avertissement

### Export

- PDF
- Excel
- CSV
- Markdown
- JSON

### Journal

- Logs
- Activité
- Erreurs

Statut

⏳ Planifié

---

# Sprint 6 — Assistant IA

## Objectif

Construire un véritable copilote métier.

Fonctionnalités

- Analyse intelligente
- Cas similaires
- Suggestions
- Contrôles qualité
- Vérification automatique
- Recherche documentaire assistée
- Mémoire métier
- Recommandations

Statut

🚀 Vision long terme

---

# Backlog

## Haute priorité

- Dashboard
- UI Components
- CSS global
- VectorStore
- Documentation IA

---

## Priorité moyenne

- Statistiques
- Export PDF
- Notifications
- Recherche globale

---

## Long terme

- Outlook API
- Synchronisation PIVOT
- OCR
- Assistant vocal
- Mobile
- Authentification
- Multi-utilisateurs

---

# Dette technique

À surveiller

- Tests unitaires
- Documentation interne
- Optimisation Gemini
- Gestion des erreurs
- Cache
- Logging

---

# Critères de qualité

Chaque nouvelle fonctionnalité doit respecter les règles suivantes :

✅ Architecture modulaire

✅ Aucune duplication de logique

✅ Séparation UI / Métier

✅ Réutilisation maximale

✅ Documentation obligatoire

✅ Tests lorsque pertinent

---

# Objectif final

IRIS Copilot doit devenir une plateforme complète d'assistance HelpDesk permettant :

- d'analyser automatiquement les demandes,
- d'assister la création des tickets,
- de centraliser les connaissances,
- de réduire les erreurs,
- de capitaliser l'expérience métier,
- d'améliorer continuellement la qualité du support.

Le projet doit rester simple à maintenir, facilement extensible et suffisamment robuste pour être utilisé quotidiennement dans un contexte professionnel.