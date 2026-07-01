# 🛠️ IRIS Copilot
# Architecture Officielle
Version : 1.0

---

# Vision

IRIS Copilot est un assistant intelligent destiné aux consultants HelpDesk N1 d'IRIS.

L'objectif n'est pas simplement d'automatiser certaines tâches, mais de construire un véritable copilote métier capable d'assister les techniciens dans :

- l'analyse des demandes clients,
- la génération de tickets,
- la recherche documentaire,
- la capitalisation des connaissances,
- l'amélioration continue grâce à une mémoire métier.

Le projet doit être :

- modulaire,
- maintenable,
- évolutif,
- facilement testable,
- agréable à utiliser.

---

# Philosophie

Le projet suit quelques principes simples.

## 1. Séparation des responsabilités

Chaque couche possède une responsabilité unique.

La logique métier ne doit jamais être mélangée avec l'interface graphique.

L'interface graphique ne doit jamais contenir de règles métier.

---

## 2. Réutilisabilité

Tout composant créé doit pouvoir être réutilisé.

Si un composant est copié plusieurs fois, il doit devenir un composant partagé.

---

## 3. Lisibilité

Chaque fichier doit rester compréhensible rapidement.

Objectif :

- moins de 300 lignes par page Streamlit
- fonctions courtes
- noms explicites

---

## 4. Évolutivité

Ajouter un nouveau client ne doit pas nécessiter de modifier plusieurs fichiers.

Ajouter une nouvelle page doit être simple.

Ajouter un nouvel agent IA doit être indépendant des autres.

---

# Architecture générale

```
                 Streamlit UI
                       │
───────────────────────┼───────────────────────
                       │
                Application Layer
                       │
───────────────────────┼───────────────────────
                       │
                 Services IA
                       │
───────────────────────┼───────────────────────
                       │
                 Base de données
                       │
───────────────────────┼───────────────────────
                       │
              Services externes
```

---

# Architecture du projet

```
IRIS_COPILOT/

main.py

pages/

app/

database/

vectorstore/

prompts/

tests/

docs/

requirements.txt

config.py
```

---

# Couche UI

Tous les éléments graphiques sont contenus dans :

```
app/ui/
```

Elle contient uniquement :

- composants
- thème
- CSS
- helpers
- layouts

Elle ne contient jamais de logique métier.

---

# Couche Services

```
app/services/
```

Contient :

- parser
- router
- vectorstore
- sqlite
- formatting
- logging

Chaque service possède une responsabilité unique.

---

# Couche Agents

```
app/agents/
```

Chaque client possède son propre agent.

Exemple :

AEMSOFT

AMPLIFON

ADOPT

PROMETHEAN

...

Un agent ne doit jamais connaître un autre agent.

---

# Couche Models

```
app/models/
```

Contient uniquement les modèles de données.

Exemple :

Ticket

Mail

Client

Document

Historique

---

# Base documentaire

La documentation est indexée dans ChromaDB.

Les documents peuvent être :

DOCX

PDF

TXT

Markdown

Chaque client possède sa collection documentaire.

---

# Mémoire

IRIS Copilot possède plusieurs mémoires.

## Mémoire documentaire

Procédures

TOKI

Guides

---

## Mémoire Tickets

Tous les tickets validés.

---

## Mémoire Corrections

Toutes les corrections manuelles effectuées.

Cette mémoire permettra :

- retrouver des cas similaires
- identifier les erreurs fréquentes
- améliorer les règles métier

Aucune règle n'est modifiée automatiquement.

Les décisions restent toujours humaines.

---

# Pipeline de traitement

Mail

↓

Parser

↓

Détection du client

↓

Agent spécialisé

↓

Validation utilisateur

↓

SQLite

↓

VectorStore

↓

Dashboard

---

# Convention UI

Toutes les pages utilisent les mêmes composants.

Exemple :

Hero

Section

MetricCard

StatusBadge

Notification

Timeline

Loading

Aucune page ne doit recréer ces composants.

---

# Convention CSS

Un seul fichier CSS global.

```
app/ui/styles.css
```

Aucun CSS inline sauf exception.

---

# Convention Python

Respect des principes suivants :

PEP8

Typing lorsque pertinent

Fonctions courtes

Docstrings

Séparation claire UI / métier

---

# Convention des Pages Streamlit

Une page Streamlit doit uniquement :

- afficher
- appeler des services
- afficher les résultats

Elle ne doit jamais :

- appeler directement Gemini
- manipuler SQLite
- manipuler ChromaDB

Tout passe par les services.

---

# Qualité

Le projet doit rester :

Modulaire

Lisible

Robuste

Réutilisable

Documenté

---

# Roadmap

Sprint 1

✔ Architecture métier

✔ Agents spécialisés

✔ Parser

✔ Router

✔ SQLite

✔ VectorStore

---

Sprint 2

Construction de la bibliothèque UI

Thème graphique

Dashboard

Composants réutilisables

---

Sprint 3

Validation fonctionnelle

Analyse Mail

Documentation

Historique

Tickets

---

Sprint 4

Mémoire métier

Recherche intelligente

Cas similaires

Journal des corrections

---

Sprint 5

Dashboard avancé

Statistiques

Recherche globale

Exports

Notifications

---

# Technologies

Frontend

- Streamlit

Backend

- Python

IA

- Gemini

Base de données

- SQLite

Recherche documentaire

- ChromaDB

Embeddings

- Sentence Transformers

Manipulation documentaire

- LangChain

Office

- OpenPyXL

---

# Vision long terme

IRIS Copilot doit devenir un véritable assistant IA métier.

L'objectif n'est pas seulement de gagner du temps, mais également :

- standardiser le traitement des demandes,
- capitaliser les connaissances,
- assister les techniciens,
- réduire les erreurs,
- améliorer continuellement la qualité des tickets.

Chaque évolution devra respecter cette architecture afin de garantir la stabilité et la maintenabilité du projet.