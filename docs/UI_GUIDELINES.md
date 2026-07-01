# 🛠️ IRIS Copilot
# UI GUIDELINES
Version : 1.0

---

# Objectif

Ce document définit les règles de conception de l'interface utilisateur d'IRIS Copilot.

L'objectif est de garantir :

- une interface homogène ;
- une excellente lisibilité ;
- une expérience utilisateur fluide ;
- une identité visuelle professionnelle ;
- des composants réutilisables.

Toutes les nouvelles pages doivent respecter ces règles.

---

# Philosophie

L'interface d'IRIS Copilot doit transmettre les valeurs suivantes :

- simplicité ;
- efficacité ;
- professionnalisme ;
- modernité ;
- clarté.

Le but n'est pas de produire une interface spectaculaire mais une interface agréable à utiliser toute la journée par un consultant HelpDesk.

---

# Inspirations

Le design s'inspire principalement de :

- Microsoft Copilot
- Microsoft Fluent Design
- GitHub
- Notion
- Linear
- Atlassian

L'objectif est un rendu sobre, moderne et cohérent.

---

# Palette de couleurs

## Couleur principale

IRIS Blue

```
#0F62FE
```

---

## Accent

```
#00C2FF
```

---

## Success

```
#22C55E
```

---

## Warning

```
#F59E0B
```

---

## Error

```
#EF4444
```

---

## Background

```
#0E1117
```

---

## Card

```
#1C1F26
```

---

## Texte principal

```
#F3F4F6
```

---

## Texte secondaire

```
#9CA3AF
```

---

# Typographie

Police recommandée

```
Inter
```

ou

```
Segoe UI
```

Toujours privilégier une police simple et lisible.

---

# Espacement

Utiliser un espacement régulier.

Valeurs recommandées :

```
8 px

16 px

24 px

32 px
```

Éviter les espacements arbitraires.

---

# Icônes

Une icône précède toujours les titres principaux.

Exemples :

🏠 Dashboard

📨 Analyse Mail

🎫 Génération Ticket

📚 Documentation

📜 Historique

🧠 Mémoire

📊 Statistiques

⚙ Paramètres

---

# Structure d'une page

Toutes les pages doivent suivre le même ordre.

```
Hero

↓

Informations principales

↓

Actions

↓

Contenu principal

↓

Résultats

↓

Informations complémentaires
```

---

# Hero

Chaque page commence par un Hero.

Exemple

```
🛠 IRIS Copilot

Assistant IA HelpDesk

----------------------------------
```

Le Hero est identique sur toutes les pages.

---

# Sections

Chaque section possède :

- une icône
- un titre
- une séparation visuelle

Exemple

```
━━━━━━━━━━━━━━━━━━━━━━

📨 Analyse d'un mail

━━━━━━━━━━━━━━━━━━━━━━
```

---

# Cartes

Toutes les informations importantes sont affichées dans des cartes.

Une carte contient :

- titre
- valeur
- icône
- éventuellement une couleur d'état

Exemple

```
┌────────────────────────┐

📩

15

Mails analysés

└────────────────────────┘
```

---

# KPI

Les indicateurs principaux utilisent toujours le même composant.

Exemples :

Nombre de tickets

Nombre de mails

Temps gagné

Documents indexés

Mémoire

---

# Badges

Les badges servent uniquement à représenter un état.

Exemples

🟢 Connecté

🟡 En attente

🔴 Erreur

---

# Alertes

Trois types uniquement.

Information

Succès

Erreur

Toujours avec une couleur cohérente.

---

# Boutons

Limiter le nombre de boutons.

Toujours privilégier :

Une action principale

Une ou deux actions secondaires

Éviter les interfaces surchargées.

---

# Formulaires

Tous les formulaires doivent être regroupés dans des sections logiques.

Exemple :

Informations client

↓

Informations intervention

↓

Commentaires

↓

Validation

---

# Sidebar

La sidebar est présente sur toutes les pages.

Ordre officiel

```
🏠 Dashboard

📨 Analyse Mail

🎫 Génération Ticket

📚 Documentation

📜 Historique

🧠 Mémoire

📊 Statistiques

⚙ Paramètres
```

En bas :

État des services

Gemini

SQLite

VectorStore

Mémoire

---

# États système

Toujours visibles.

Exemple

```
🟢 Gemini

🟢 SQLite

🟢 ChromaDB

🟡 Mémoire
```

---

# Notifications

Toutes les opérations importantes doivent afficher un retour utilisateur.

Exemple

```
✓ Ticket enregistré
```

ou

```
⚠ Procédure introuvable
```

---

# Loading

Les traitements IA doivent toujours afficher un indicateur.

Exemple

```
Analyse du mail...
```

ou

```
Recherche documentaire...
```

L'utilisateur ne doit jamais se demander si l'application travaille.

---

# Responsive

L'application doit rester utilisable sur :

- écran portable
- écran Full HD
- double écran

Éviter les composants trop larges.

---

# Accessibilité

Respecter les principes suivants :

- contraste élevé
- texte lisible
- icônes explicites
- couleurs non utilisées seules pour transmettre une information

---

# Animations

Limiter les animations.

Uniquement :

- transitions douces
- hover sur les cartes
- boutons
- loaders

Éviter les animations inutiles.

---

# Composants officiels

Tous les composants sont centralisés dans :

```
app/ui/
```

Composants prévus :

Hero

Section

MetricCard

StatusBadge

InfoCard

Notification

Timeline

Loading

QuickAction

SearchBar

Footer

Dialog

Tous les développements futurs doivent utiliser ces composants.

---

# CSS

Un seul fichier officiel :

```
app/ui/styles.css
```

Aucun CSS ne doit être copié dans plusieurs pages.

---

# JavaScript

Le JavaScript est utilisé uniquement lorsque Streamlit ne permet pas de réaliser une interaction.

Exemples autorisés :

- copier dans le presse-papiers ;
- raccourcis clavier ;
- drag & drop ;
- interactions avancées.

Le JavaScript ne doit jamais remplacer la logique métier.

---

# UX

Avant d'ajouter une fonctionnalité, toujours se poser les questions suivantes :

- Cette information est-elle utile ?
- Peut-elle être simplifiée ?
- Peut-elle être automatisée ?
- Est-elle affichée au bon moment ?

Chaque écran doit guider naturellement le consultant.

---

# Évolution

Toute nouvelle page ou fonctionnalité doit respecter cette charte.

En cas de nouveau composant graphique, celui-ci doit être ajouté à la bibliothèque UI afin d'être réutilisable dans l'ensemble du projet.

L'objectif est de construire une interface cohérente, professionnelle et évolutive.