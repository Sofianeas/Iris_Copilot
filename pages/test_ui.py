import streamlit as st

from app.ui import (
    configure_page,
    hero,
    section,
    divider,
    empty_state,
    footer,
    page_title,
)


configure_page("Test UI")


hero(
    title="IRIS Copilot",
    subtitle="Bibliothèque UI",
)


section(
    "Première section",
    "📨",
)

st.write("Bonjour 👋")


divider()


section(
    "Empty State",
    "📂",
)

empty_state(
    "Aucun ticket trouvé.",
    icon="📭",
)


section(
    "Titre simple",
    "📄",
)

page_title(
    "Historique",
    "📜",
)


footer()