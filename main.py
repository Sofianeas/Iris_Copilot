import streamlit as st

from app.ui import load_theme

st.set_page_config(
    page_title="IRIS Copilot",
    page_icon="🛠️",
    layout="wide",
)

load_theme()


st.title("🛠️ IRIS Copilot")

st.markdown("""
Bienvenue dans IRIS Copilot

Projet d'assistant HelpDesk IRIS IT.
""")