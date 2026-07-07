"""
IRIS Copilot
UI Showroom

Page de démonstration de tous les composants graphiques.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from app.ui import (
    configure_page,
    primary_button,
    secondary_button,
    success_button,
    warning_button,
    danger_button,
    page_title,
    section_title,
    subtitle,
    body_text,
    caption,
    code_block,
    divider,
    metric,
    metric_row,
    data_table,
    timeline,
    sidebar,
    sidebar_title,
    sidebar_section,
    sidebar_text,
    sidebar_divider,
    breadcrumbs,
    nav_group,
    nav_link,
    tabs,
    text_input,
text_area,
number_input,
slider,
selectbox,
multiselect,
radio,
checkbox,
toggle,
date_input,
time_input,
file_uploader,
form_submit_button,
)

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
# Buttons
# ==========================================================

section(
    "Buttons",
    "🔘",
)

col1, col2 = st.columns(2)

with col1:

    if primary_button(
        "Créer un ticket",
        icon="➕",
        full_width=True,
        key="showcase_primary",
    ):
        st.success("Bouton principal cliqué.")

    if success_button(
        "Valider",
        icon="✅",
        full_width=True,
        key="showcase_success",
    ):
        st.success("Action validée.")

with col2:

    if secondary_button(
        "Annuler",
        icon="✖️",
        full_width=True,
        key="showcase_secondary",
    ):
        st.info("Action annulée.")

    if warning_button(
        "Attention",
        icon="⚠️",
        full_width=True,
        key="showcase_warning",
    ):
        st.warning("Attention.")

    if danger_button(
        "Supprimer",
        icon="🗑️",
        full_width=True,
        key="showcase_danger",
    ):
        st.error("Suppression.")


# ==========================================================
# Typography
# ==========================================================

section(
    "Typography",
    "📝",
)

page_title("Titre principal")

section_title("Titre de section")

subtitle("Sous-titre")

body_text(
    "Ce texte est affiché via le composant body_text() "
    "du Design System."
)

caption(
    "Exemple de légende."
)

code_block(
    """def hello():
    print("Hello IRIS Copilot")""",
    language="python",
)

divider()

section_title("Metrics")
caption("Composants réutilisables pour l'affichage des indicateurs.")

metric(
    label="Tickets ouverts",
    value=42,
)

metric(
    label="SLA",
    value="97 %",
    delta="+2 %",
)

metric(
    label="Temps moyen",
    value="18 min",
    help="Temps moyen de résolution des tickets.",
)

metric_row(
    [
        {
            "label": "Tickets",
            "value": 142,
        },
        {
            "label": "SLA",
            "value": "96 %",
            "delta": "+3 %",
        },
        {
            "label": "Temps moyen",
            "value": "14 min",
            "help": "Calculé sur les 30 derniers jours.",
        },
    ]
)

# ==========================================================
# Footer
# ==========================================================

footer()

divider()

section_title("Tables")
caption("Composants réutilisables pour l'affichage de tableaux.")

demo_df = pd.DataFrame(
    {
        "Ticket": ["INC-1001", "INC-1002", "INC-1003"],
        "Client": ["ADOPT", "AMPLIFON", "AEMSOFT"],
        "Statut": ["Ouvert", "En cours", "Résolu"],
        "Priorité": ["Haute", "Moyenne", "Basse"],
    }
)

data_table(demo_df)

divider()

section_title("Timeline")
caption("Composant réutilisable pour l'affichage d'une chronologie.")

timeline(
    [
        {
            "title": "Ticket créé",
            "timestamp": "06/07/2026 09:15",
            "description": "Le ticket a été créé depuis la boîte SAV.",
        },
        {
            "title": "Technicien affecté",
            "timestamp": "06/07/2026 09:32",
            "description": "Le ticket a été affecté à un technicien N1.",
        },
        {
            "title": "Intervention planifiée",
            "timestamp": "06/07/2026 10:10",
        },
        {
            "title": "Ticket clôturé",
            "timestamp": "06/07/2026 11:48",
            "description": "Résolution validée par le client.",
        },
    ]
)

divider()

section_title("Sidebar")
caption("Composants réutilisables pour la barre latérale.")

with sidebar():
    sidebar_title("IRIS Copilot")

    sidebar_section("Informations")

    sidebar_text("Version : 0.1.0")

    sidebar_text("Environnement : Développement")

    sidebar_divider()

    sidebar_section("Utilisateur")

    sidebar_text("Nom : Démonstration")

divider()

section_title("Navigation")
caption("Composants réutilisables pour la navigation.")

breadcrumbs(
    [
        "Accueil",
        "Support",
        "Ticket #1542",
    ]
)

nav_group("Menu principal")

nav_link("Accueil")
nav_link("Tickets")
nav_link("Inventaire")
nav_link("Paramètres")

overview_tab, history_tab, comments_tab = tabs(
    [
        "Vue générale",
        "Historique",
        "Commentaires",
    ]
)

with overview_tab:
    st.write("Contenu de la vue générale.")

with history_tab:
    st.write("Historique du ticket.")

with comments_tab:
    st.write("Commentaires.")


# ==========================================================
# Forms
# ==========================================================

divider()

section_title("Forms")
caption("Composants réutilisables pour les formulaires.")

subtitle("Text Inputs")

text_input(
    "Text input",
    placeholder="Enter some text...",
    help="Example of a text input.",
)

text_area(
    "Text area",
    placeholder="Write something...",
    help="Example of a multiline text area.",
)

divider()

subtitle("Numeric Inputs")

number_input(
    "Number input",
    value=10,
    min_value=0,
    max_value=100,
)

slider(
    "Slider",
    min_value=0,
    max_value=100,
    value=50,
)

divider()

subtitle("Selection Inputs")

selectbox(
    "Selectbox",
    [
        "Option 1",
        "Option 2",
        "Option 3",
    ],
)

multiselect(
    "Multiselect",
    [
        "Option 1",
        "Option 2",
        "Option 3",
    ],
    default=["Option 1"],
)

radio(
    "Radio",
    [
        "Option 1",
        "Option 2",
        "Option 3",
    ],
)

divider()

subtitle("Boolean Inputs")

checkbox(
    "Checkbox",
)

toggle(
    "Toggle",
    value=True,
)

divider()

subtitle("Date & Time Inputs")

date_input(
    "Date input",
)

time_input(
    "Time input",
)

divider()

subtitle("Upload & Submission")

with st.form("showcase_form"):

    file_uploader(
        "File uploader",
        type=["txt", "pdf"],
    )

    submitted = form_submit_button(
        "Submit",
    )

if submitted:
    st.success("Form submitted.")

