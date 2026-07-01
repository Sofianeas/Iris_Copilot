# 🛠️ IRIS Copilot
# DEVELOPMENT GUIDE
Version : 1.0

---

# Objectif

Ce document définit les règles de développement officielles d'IRIS Copilot.

Tous les développements (humains ou IA) doivent respecter ces conventions afin de garantir :

- une architecture cohérente ;
- une maintenance simplifiée ;
- une qualité de code constante ;
- une évolutivité du projet.

---

# Philosophie

IRIS Copilot est développé selon les principes suivants :

- Simplicité
- Lisibilité
- Modularité
- Réutilisabilité
- Testabilité
- Séparation des responsabilités

Nous privilégions toujours une architecture claire plutôt qu'une solution rapide mais difficile à maintenir.

---

# Architecture

Le projet est organisé en couches.

```

Interface (Streamlit)

↓

UI Components

↓

Services

↓

Agents

↓

Models

↓

Database

↓

External APIs

```

Chaque couche possède une responsabilité unique.

---

# Structure officielle

```

IRIS_COPILOT/

main.py

pages/

app/

agents/

services/

models/

utils/

ui/

database/

vectorstore/

tests/

docs/

```

Aucun nouveau dossier ne doit être créé sans justification.

---

# Convention des Pages Streamlit

Une page Streamlit ne contient que :

- l'affichage
- l'orchestration
- les appels aux services

Une page ne doit jamais :

- parser un mail
- appeler directement Gemini
- manipuler SQLite
- manipuler ChromaDB
- contenir des règles métier

Exemple :

```python
ticket = parser_service.parse(mail)

result = router_service.route(ticket)

ui.display(result)
```

Jamais :

```python
# ❌ À éviter

response = model.generate_content(...)

sqlite3.connect(...)

chromadb.Client(...)
```

---

# Convention des Services

Chaque service possède UNE responsabilité.

Exemple :

parser_service.py

→ analyse un mail

router_service.py

→ choisit l'agent

db_service.py

→ SQLite uniquement

vectorstore_service.py

→ ChromaDB uniquement

formatting_service.py

→ mise en forme

logging_service.py

→ journalisation

Les services ne doivent pas dépendre les uns des autres lorsque ce n'est pas nécessaire.

---

# Convention des Agents

Chaque client possède son propre agent.

```

agents/

aemsoft_agent.py

adopt_agent.py

amplifon_agent.py

...

```

Un agent :

- connaît son client
- connaît ses procédures
- ne connaît pas les autres agents

Aucune logique spécifique à un client ne doit être placée ailleurs.

---

# Convention UI

Tous les composants graphiques sont centralisés.

```

app/ui/

```

Les pages utilisent uniquement les composants disponibles.

Exemple :

```python
Hero()

MetricCard()

Section()

StatusBadge()

Notification()

```

Aucun composant ne doit être dupliqué.

---

# Convention CSS

Un seul CSS global.

```

app/ui/styles.css

```

Éviter le CSS inline.

Le CSS est partagé entre toutes les pages.

---

# Convention Python

Respect des règles suivantes :

- PEP8
- Typing lorsque pertinent
- Fonctions courtes
- Variables explicites
- Aucun code mort
- Aucun import inutile

---

# Fonctions

Une fonction doit idéalement :

- effectuer une seule tâche ;
- être facilement testable ;
- retourner une valeur claire ;
- documenter les cas particuliers.

Exemple :

```python
def detect_client(mail: str) -> str:
    """Retourne le client détecté à partir du contenu du mail."""
```

---

# Gestion des erreurs

Toutes les erreurs doivent être :

- capturées ;
- journalisées ;
- compréhensibles.

Éviter :

```python
except:
    pass
```

Préférer :

```python
except Exception as exc:
    logger.exception(exc)
```

---

# Logging

Toutes les opérations importantes doivent être journalisées.

Exemples :

- lancement d'un agent ;
- génération d'un ticket ;
- erreur Gemini ;
- indexation documentaire ;
- sauvegarde SQLite.

Le logging doit être centralisé dans :

```

app/services/logging_service.py

```

---

# Base de données

Les pages Streamlit ne doivent jamais manipuler SQLite directement.

Toujours utiliser :

```

db_service.py

```

---

# VectorStore

Même principe.

Toutes les opérations ChromaDB passent uniquement par :

```

vectorstore_service.py

```

---

# Configuration

Aucune valeur métier ne doit être codée en dur.

Utiliser :

- config.py
- .env
- constantes

---

# Tests

Les services doivent pouvoir être testés indépendamment de Streamlit.

Le dossier :

```

tests/

```

contient :

- tests unitaires
- tests fonctionnels
- données de test

---

# Documentation

Chaque nouveau module doit être accompagné :

- d'une docstring ;
- d'un commentaire lorsque la logique est complexe ;
- d'une mise à jour de la documentation si nécessaire.

---

# Performance

Toujours privilégier :

- le cache lorsque pertinent ;
- les traitements réutilisables ;
- les appels IA limités ;
- la mutualisation des ressources.

Éviter les calculs inutiles dans les pages Streamlit.

---

# Sécurité

Ne jamais :

- exposer une clé API ;
- enregistrer des informations sensibles dans les logs ;
- modifier automatiquement des règles métier.

Toutes les décisions importantes doivent rester validées par un utilisateur.

---

# Utilisation de Claude

Claude est principalement utilisé pour :

- développer rapidement des fonctionnalités ;
- créer des agents ;
- générer des services ;
- produire du code répétitif ;
- proposer des améliorations techniques.

Chaque contribution doit respecter cette architecture.

---

# Utilisation de ChatGPT

ChatGPT intervient principalement pour :

- définir l'architecture ;
- concevoir les composants UI ;
- effectuer les revues de code ;
- optimiser les performances ;
- proposer les évolutions du produit ;
- maintenir la cohérence globale du projet.

Les modifications structurelles importantes doivent être validées avant intégration.

---

# Workflow de développement

Toute nouvelle fonctionnalité suit le cycle suivant :

1. Définition du besoin
2. Conception
3. Développement
4. Revue
5. Tests
6. Validation
7. Documentation
8. Intégration

Aucune fonctionnalité ne doit être intégrée sans avoir suivi ce processus.

---

# Checklist avant un commit

Avant chaque commit Git, vérifier :

- [ ] Le code respecte l'architecture.
- [ ] Les imports sont propres.
- [ ] Aucun code dupliqué.
- [ ] Les services sont correctement séparés.
- [ ] Les pages Streamlit restent légères.
- [ ] Les erreurs sont gérées.
- [ ] Les logs sont cohérents.
- [ ] La documentation est à jour.
- [ ] Les tests passent.

---

# Principes d'évolution

IRIS Copilot doit rester :

- modulaire ;
- documenté ;
- maintenable ;
- évolutif.

Chaque nouvelle fonctionnalité doit pouvoir être ajoutée sans remettre en cause l'architecture existante.

Lorsque plusieurs solutions sont possibles, privilégier toujours celle qui :

- réduit le couplage ;
- favorise la réutilisation ;
- simplifie les tests ;
- facilite la maintenance à long terme.

---

# Devise du projet

> **Construire un copilote métier fiable, maintenable et évolutif, plutôt qu'une succession de scripts.**

# Conventions spécifiques à l'IA

IRIS Copilot utilise l'intelligence artificielle comme un assistant d'aide à la décision.

Les principes suivants sont obligatoires :

## Validation humaine

Toute proposition générée par l'IA doit pouvoir être relue, modifiée et validée par un utilisateur avant d'être enregistrée.

## Traçabilité

Chaque analyse doit conserver :

- l'agent utilisé ;
- la version du prompt ;
- les documents RAG consultés ;
- les valeurs proposées ;
- les valeurs validées.

## Amélioration continue

Les corrections utilisateur sont enregistrées afin d'identifier des tendances et d'améliorer les agents ou les procédures.

Les règles métier ne sont jamais modifiées automatiquement.

Toute évolution des agents ou des prompts résulte d'une décision humaine documentée.

## Transparence

L'application doit pouvoir expliquer, lorsque c'est possible, sur quelles procédures ou quels documents elle s'est appuyée pour produire une proposition.