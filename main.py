import streamlit as st

from app.shell import ApplicationShell
from app.ui import load_theme

# ------------------------------------------------------------------
# Configuration Streamlit
# ------------------------------------------------------------------

st.set_page_config(
    page_title="IRIS Copilot",
    page_icon="🛠️",
    layout="wide",
)

# ------------------------------------------------------------------
# Chargement du thème
# ------------------------------------------------------------------

load_theme()

# ------------------------------------------------------------------
# Lancement de l'application
# ------------------------------------------------------------------

shell = ApplicationShell()
shell.run()