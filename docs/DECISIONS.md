# 🛠️ IRIS Copilot
# DECISIONS

Historique des décisions d'architecture.

Chaque décision importante est documentée afin de conserver son contexte.

---

# ADR-001

## Sujet

Architecture modulaire.

## Date

2026-07-01

## Décision

Le projet adopte une architecture modulaire.

Séparation en couches :

- UI
- Services
- Agents
- Models
- Database

## Motivation

Réduire le couplage.

Faciliter la maintenance.

Permettre l'ajout de nouvelles fonctionnalités.

## Conséquences

Chaque couche possède une responsabilité unique.

---

# ADR-002

## Sujet

Un agent par client.

## Décision

Chaque client possède son propre agent.

Exemple :

- AEMSOFT
- ADOPT
- AMPLIFON
- PROMETHEAN

## Motivation

Chaque client possède des règles métier spécifiques.

Cette séparation évite les conditions complexes.

## Conséquences

Ajouter un client consiste simplement à créer un nouvel agent.

---

# ADR-003

## Sujet

Utilisation de SQLite.

## Décision

SQLite devient la base locale officielle.

## Motivation

- léger
- simple
- portable
- aucune installation serveur

## Conséquences

Toutes les opérations passent par db_service.py.

---

# ADR-004

## Sujet

Recherche documentaire.

## Décision

Utilisation de ChromaDB.

## Motivation

Permettre :

- RAG
- recherche sémantique
- recherche documentaire

## Conséquences

Toutes les recherches documentaires passent par vectorstore_service.py.

---

# ADR-005

## Sujet

Validation humaine obligatoire.

## Décision

Toute proposition IA doit être validée.

## Motivation

Garantir la qualité des tickets.

L'IA assiste mais ne décide jamais seule.

## Conséquences

Toutes les pages doivent permettre la modification avant validation.

---

# ADR-006

## Sujet

Mémoire métier.

## Décision

Le système mémorise les interactions.

Il ne modifie jamais automatiquement les règles métier.

## Motivation

Capitaliser l'expérience.

Préserver le contrôle humain.

## Conséquences

Création d'une mémoire documentaire.

Création d'une mémoire tickets.

Création d'une mémoire corrections.

---

# ADR-007

## Sujet

Bibliothèque UI.

## Décision

Tous les composants graphiques sont centralisés.

## Motivation

Éviter la duplication.

Uniformiser l'interface.

## Conséquences

Toutes les pages utilisent les mêmes composants.

---

# ADR-008

## Sujet

CSS global.

## Décision

Un seul fichier styles.css.

## Motivation

Facilité de maintenance.

Cohérence graphique.

## Conséquences

Le CSS inline devient exceptionnel.

---

# ADR-009

## Sujet

Séparation UI / Métier.

## Décision

Les pages Streamlit n'ont aucune logique métier.

## Motivation

Faciliter les tests.

Réduire les dépendances.

## Conséquences

Toute logique passe par les services.

---

# ADR-010

## Sujet

Utilisation combinée de Claude et ChatGPT.

## Décision

Le développement s'appuie sur deux assistants complémentaires.

### Claude

- génération de code
- agents
- automatisation
- intégration

### ChatGPT

- architecture
- UI/UX
- revue de code
- optimisation
- roadmap
- qualité logicielle

## Motivation

Combiner rapidité de développement et cohérence architecturale.

## Conséquences

Toute évolution importante est revue avant intégration.

---

# ADR-011

## Sujet

Documentation obligatoire.

## Décision

Toute évolution importante doit mettre à jour :

- CHANGELOG
- ROADMAP
- Documentation concernée

## Motivation

Garantir la maintenabilité du projet.

## Conséquences

La documentation fait partie intégrante du développement.

---

# ADR-012

## Sujet

Vision produit.

## Décision

IRIS Copilot est développé comme une plateforme métier et non comme un simple projet Streamlit.

## Motivation

Créer un outil robuste, réutilisable et évolutif.

## Conséquences

Toutes les évolutions futures devront respecter cette vision.