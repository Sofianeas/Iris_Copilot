"""
IRIS Copilot
UI Showroom

Page de démonstration de tous les composants graphiques.
"""

from __future__ import annotations

import streamlit as st

from app.ui import configure_page
from app.ui.components import *

# ==========================================================
# Configuration
# ==========================================================

configure_page("UI Showroom")

# ==========================================================
# Hero
# ==========================================================

hero(
    title="IRIS Copilot UI",
    subtitle="Bibliothèque officielle des composants",
)

# ==========================================================
# Layout
# ==========================================================

section(
    "Layout",
    "📐",
)

st.write(
    """
Cette page permet de tester l'ensemble des composants
de la bibliothèque UI officielle d'IRIS Copilot.
"""
)

divider()

# ==========================================================
# Empty State
# ==========================================================

section(
    "Empty State",
    "📂",
)

empty_state(
    "Aucun ticket trouvé.",
    icon="📭",
)

# ==========================================================
# Page Title
# ==========================================================

section(
    "Page Title",
    "📄",
)

page_title(
    "Historique",
    "📜",
)

# ==========================================================
# Cards
# ==========================================================

section(
    "Cards",
    "🧩",
)

col1, col2, col3 = st.columns(3)

with col1:

    metric_card(
        title="Tickets analysés",
        value=156,
        icon="📨",
        help_text="Aujourd'hui",
    )

with col2:

    metric_card(
        title="Documents",
        value=42,
        icon="📚",
        help_text="VectorStore",
    )

with col3:

    metric_card(
        title="Agents IA",
        value=8,
        icon="🤖",
        help_text="Disponibles",
    )

st.write("")

feature_card(
    title="Analyse Mail",
    description="Analyse intelligente des demandes entrantes.",
    icon="📨",
)

st.write("")

info_card(
    title="Version",
    content="IRIS Copilot v1.0",
)

st.write("")

stat_card(
    title="Taux de réussite",
    value="98 %",
    delta="+3 %",
)

st.write("")

action_card(
    label="🚀 Générer un ticket",
)

# ==========================================================
# Badges
# ==========================================================

section(
    "Badges",
    "🏷️",
)

st.write("### Statuts")

badge_group(
    [
        badge("Succès", "success"),
        badge("Erreur", "error"),
        badge("Analyse", "info"),
        badge("En attente", "warning"),
    ]
)

st.write("### Priorités")

badge_group(
    [
        badge("Urgent", "danger"),
        badge("Normale", "warning"),
        badge("Faible", "success"),
    ]
)

st.write("### Clients")

badge_group(
    [
        badge("ADOPT", "client"),
        badge("AMPLIFON", "client"),
        badge("ETAM", "client"),
        badge("PROMETHEAN", "client"),
        badge("AEMSOFT", "client"),
    ]
)

st.write("### Technologies")

badge_group(
    [
        badge("IA"),
        badge("Gemini"),
        badge("RAG"),
        badge("SQLite"),
        badge("Python"),
        badge("Streamlit"),
    ]
)

# ==========================================================
# Alerts
# ==========================================================
st.markdown(
    """
<div style="background:red;color:white;padding:20px;border-radius:10px">
    TEST HTML
</div>
""",
    unsafe_allow_html=True,
)


section(
    "Alerts",
    "🚨",
)

alert(
    title="Connexion réussie",
    description="Toutes les données ont été synchronisées.",
    variant="success",
)

alert(
    title="Attention",
    description="Le ticket approche de son SLA.",
    variant="warning",
)

alert(
    title="Erreur",
    description="Impossible de contacter Microsoft Graph.",
    variant="error",
)

alert(
    title="Information",
    description="Le cache documentaire a été mis à jour.",
    variant="info",
)

# ==========================================================
# Prochaines sections
# ==========================================================

section(
    "Composants à venir",
    "🚀",
)

st.info(
"""
Les prochains composants seront ajoutés ici :

• Buttons

• Forms

• Tables

• Sidebar

• Timeline

• Toast

• Modal

• KPI

• Charts
"""
)

# ==========================================================
# Footer
# ==========================================================

footer()

import app.ui.components as ui

if ui.primary_button(
    "Créer un ticket",
    icon="➕",
    full_width=True,
):
    st.success("Ticket créé")

if ui.primary_button("Créer un ticket", icon="➕", full_width=True):
    st.success("Ticket créé")
