"""
pages/analyse_mail.py -- Page de validation humaine du pipeline Iris Copilot.

Workflow : coller un mail (+ pièce jointe Excel si le client en dépend)
-> détecter/confirmer le client -> générer le ticket enrichi -> relire et
corriger dans un formulaire -> valider (sauvegarde tickets.db) -> copier le
résumé au format Ticket PIVOT (SKILL.md) pour saisie manuelle dans Pivot.

⚠️ Cette page suppose que main.py utilise la convention multipage Streamlit
classique (fichiers dans pages/ découverts automatiquement). Si main.py
utilise st.navigation()/st.Page() (API multipage explicite plus récente),
il faudra y ajouter une ligne référençant ce fichier -- je n'ai pas le
contenu de main.py pour le confirmer.

⚠️ Compatibilité non testée ici (pas d'environnement Streamlit) :
st.file_uploader() retourne un UploadedFile, qui se comporte comme un
objet binaire avec .read()/.seek() -- openpyxl.load_workbook() est censé
l'accepter directement (sans écrire de fichier temporaire), comme pour
n'importe quel objet fichier-like. À confirmer au premier test réel ; en
cas d'erreur, la solution de repli est d'écrire l'upload dans un fichier
temporaire avant de le passer aux agents.
"""

import dataclasses

import streamlit as st

from app.models.ticket import Ticket
from app.services.router_service import (
    detecter_client,
    traiter_mail_complet,
    traiter_fichier_complet,
    TOUS_LES_CLIENTS,
    CLIENTS_FICHIER,
    CLIENTS_NON_AUTOMATISES,
)
from app.services.db_service import save_ticket, lister_derniers_tickets
from app.services.formatting_service import formater_ticket_markdown


st.set_page_config(page_title="Analyse de mail — Iris Copilot", page_icon="📧")
st.title("📧 Analyse de mail")
st.caption("Colle un mail client, vérifie le ticket généré, corrige si besoin, puis valide.")


# --------------------------------------------------------------------------
# Configuration des champs éditables, groupés par sous-modèle du Ticket.
# Format : (attribut, label affiché, type de widget).
# Centralisé ici pour que l'ajout d'un futur champ au modèle Ticket ne
# nécessite qu'une ligne, pas une réécriture de la page.
# --------------------------------------------------------------------------

CHAMPS_CUSTOMER = [
    ("client", "Client", "text"),
    ("numero_client", "Numéro client", "text"),
    ("enseigne", "Enseigne", "text"),
    ("adresse", "Adresse", "text"),
    ("complement_adresse", "Complément d'adresse", "text"),
    ("code_postal", "Code postal", "text"),
    ("ville", "Ville", "text"),
    ("pays", "Pays", "text"),
    ("code_site", "Code Site", "text"),
    ("prenom", "Prénom (contact)", "text"),
    ("nom", "Nom (contact)", "text"),
    ("portable", "Portable", "text"),
    ("fixe", "Fixe", "text"),
    ("email", "Email", "text"),
    ("commentaire", "Commentaire (site)", "area"),
]

CHAMPS_INTERVENTION = [
    ("type_intervention", "Type d'intervention", "text"),
    ("contrat", "Contrat", "text"),
    ("type", "Type", "text"),
    ("sous_type", "Sous-type", "text"),
    ("categorie", "Catégorie", "text"),
    ("numero_serie", "Numéro de série", "text"),
    ("reference_materiel_client", "Référence matériel client", "text"),
    ("type_ticket", "Type de ticket", "text"),
    ("intitule", "Intitulé", "text"),
    ("numero_incident_client", "Numéro d'incident client", "text"),
    ("code_projet", "Code projet", "text"),
    ("problematique", "Problématique", "area"),
    ("origine", "Origine", "text"),
    ("niveau_priorite", "Niveau de service / priorité", "text"),
    ("commentaire_interne", "⚠️ Commentaire interne (notes de l'agent)", "area"),
]

CHAMPS_LOGISTICS = [
    ("besoin_materiel", "Besoin de matériel ?", "bool"),
    ("pieces", "Pièce(s)", "text"),
    ("envoi_piece_par", "Envoi de la pièce par", "text"),
    ("consigne_livraison", "Destination / consigne de livraison", "text"),
    ("date_expedition_souhaitee", "Date d'expédition souhaitée", "text"),
    ("tracking", "Tracking", "text"),
    ("integration_a_faire", "Intégration à faire", "bool"),
    ("retour_piece", "Retour de pièces", "text"),
    ("commentaire_logistique", "Commentaire logistique", "area"),
]

CHAMPS_PROCEDURE = [
    ("intervention_sur_site", "Intervention sur site", "bool"),
    ("prise_rdv", "Prise de RDV", "bool"),
    ("date_limite", "Date limite", "text"),
    ("contrainte", "Contrainte", "text"),
    ("nombre_techniciens", "Nombre de techniciens", "int"),
    ("duree", "Durée", "text"),
    ("consignes_mission", "Consignes de mission", "area"),
    ("consignes_planification", "Consignes de planification", "area"),
    ("travail_attendu", "Travail attendu", "area"),
    ("technicien_anglophone", "Technicien anglophone", "bool"),
    ("outillage_specifique", "Outillage spécifique", "text"),
    ("autre_outillage", "Autre outillage spécifique", "text"),
    ("procedure", "Procédure (Oui/Non)", "bool"),
    ("lien_procedure", "Lien de la procédure", "text"),
]

CHAMPS_VALIDATION = [
    ("type_validation", "Validation de l'intervention", "text"),
    ("telephone_validation", "Téléphone/Contact pour la validation", "text"),
    ("travail_realise", "Travail réalisé", "area"),
]

SECTIONS = [
    ("customer", "🏠 Site d'intervention / Contact", CHAMPS_CUSTOMER),
    ("intervention", "📋 Intervention", CHAMPS_INTERVENTION),
    ("logistics", "📦 Matériel / Logistique", CHAMPS_LOGISTICS),
    ("procedure", "🛠️ Planification / Consignes", CHAMPS_PROCEDURE),
    ("validation", "✅ Validation", CHAMPS_VALIDATION),
]


def widget_pour_champ(sous_modele_nom: str, attribut: str, label: str, type_widget: str, valeur_actuelle):
    """Affiche le bon widget Streamlit selon le type, retourne la valeur saisie."""
    cle = f"{sous_modele_nom}__{attribut}"
    if type_widget == "bool":
        return st.checkbox(label, value=bool(valeur_actuelle), key=cle)
    if type_widget == "int":
        return st.number_input(label, value=int(valeur_actuelle or 0), step=1, key=cle)
    if type_widget == "area":
        return st.text_area(label, value=valeur_actuelle or "", key=cle, height=100)
    return st.text_input(label, value=valeur_actuelle or "", key=cle)


def reconstruire_ticket_depuis_formulaire(ticket_original: Ticket) -> Ticket:
    """Reconstruit un Ticket à partir des valeurs actuelles des widgets (st.session_state)."""
    ticket = dataclasses.replace(ticket_original)
    for sous_modele_nom, _titre, champs in SECTIONS:
        sous_modele = getattr(ticket, sous_modele_nom)
        for attribut, _label, _type_widget in champs:
            cle = f"{sous_modele_nom}__{attribut}"
            if cle in st.session_state:
                setattr(sous_modele, attribut, st.session_state[cle])
    return ticket


# --------------------------------------------------------------------------
# Étape 1 -- Saisie du mail + pièce jointe éventuelle
# --------------------------------------------------------------------------

texte_mail = st.text_area("Coller le mail reçu", height=280, key="texte_mail_input")

fichier_upload = st.file_uploader(
    "Pièce jointe Excel (uniquement pour AXE E-SANTE / ETAM / DYNAMIZ PHARMA)",
    type=["xlsx"],
    help="Le PDF 'fiche d'intervention' (AXE E-SANTE) ou 'bon de commande' "
         "(AEMSOFT) ne se charge pas ici : il n'est jamais lu, juste attaché "
         "tel quel au ticket final.",
)

if "ticket" not in st.session_state:
    st.session_state.ticket = None
if "client_confirme" not in st.session_state:
    st.session_state.client_confirme = None


# --------------------------------------------------------------------------
# Étape 2 -- Détection du client (avec possibilité de correction manuelle)
# --------------------------------------------------------------------------

col_detect, col_select = st.columns([1, 2])
with col_detect:
    detecter_clique = st.button("🔍 Détecter le client", width="stretch")

if detecter_clique:
    if not texte_mail.strip():
        st.warning("Colle d'abord le texte du mail.")
    else:
        client_detecte = detecter_client(texte_mail)
        st.session_state.client_confirme = client_detecte or None
        if client_detecte:
            st.success(f"Client détecté : **{client_detecte}**")
        else:
            st.warning("Client non reconnu automatiquement — sélectionne-le manuellement ci-dessous.")

with col_select:
    options = ["— choisir —"] + list(TOUS_LES_CLIENTS)
    index_par_defaut = (
        options.index(st.session_state.client_confirme)
        if st.session_state.client_confirme in options
        else 0
    )
    client_choisi = st.selectbox("Client (corrige si la détection est fausse)", options, index=index_par_defaut)
    st.session_state.client_confirme = client_choisi if client_choisi != "— choisir —" else None


# --------------------------------------------------------------------------
# Étape 3 -- Génération du ticket
# --------------------------------------------------------------------------

if st.button("⚙️ Générer le ticket", type="primary"):
    client = st.session_state.client_confirme
    if not client:
        st.error("Choisis ou détecte d'abord un client.")
    elif client in CLIENTS_NON_AUTOMATISES:
        st.error(
            f"**{client}** n'est pas encore automatisable : ce client nécessite une "
            f"navigation web (connexion + lecture de page) non encore développée (V3). "
            f"Traiter manuellement via TOKI_PROMETHEAN.txt."
        )
    else:
        try:
            if client in CLIENTS_FICHIER:
                if client in ("AXE_ESANTE", "ETAM") and fichier_upload is None:
                    st.error(f"**{client}** nécessite la pièce jointe Excel — upload-la ci-dessus.")
                else:
                    ticket = traiter_fichier_complet(texte_mail, fichier=fichier_upload, client_force=client)
                    st.session_state.ticket = ticket
                    st.success("Ticket généré.")
            else:
                ticket = traiter_mail_complet(texte_mail, client_force=client)
                st.session_state.ticket = ticket
                st.success("Ticket généré.")
        except Exception as exc:  # affichage convivial plutôt qu'une traceback brute
            st.error(f"Erreur lors de la génération du ticket : {exc}")


# --------------------------------------------------------------------------
# Étape 4 -- Relecture / édition / validation
# --------------------------------------------------------------------------

if st.session_state.ticket is not None:
    ticket = st.session_state.ticket

    if ticket.intervention.commentaire_interne:
        st.warning(f"⚠️ Points signalés par l'agent :\n\n{ticket.intervention.commentaire_interne}")

    st.divider()
    st.subheader("Relecture et correction")

    with st.form("formulaire_ticket"):
        for sous_modele_nom, titre, champs in SECTIONS:
            with st.expander(titre, expanded=(sous_modele_nom in ("customer", "intervention"))):
                sous_modele = getattr(ticket, sous_modele_nom)
                for attribut, label, type_widget in champs:
                    widget_pour_champ(sous_modele_nom, attribut, label, type_widget, getattr(sous_modele, attribut))

        valider_clique = st.form_submit_button("✅ Valider et enregistrer", type="primary")

    if valider_clique:
        ticket_final = reconstruire_ticket_depuis_formulaire(ticket)
        st.session_state.ticket = ticket_final

        pieces_jointes = [fichier_upload.name] if fichier_upload is not None else []
        try:
            ticket_id = save_ticket(ticket_final, texte_mail_original=texte_mail)
            st.success(f"Ticket enregistré (id #{ticket_id}).")
        except Exception as exc:
            st.error(f"Échec de l'enregistrement en base : {exc}")
            ticket_id = None

        st.subheader("📋 Résumé copiable (format Ticket PIVOT)")
        resume = formater_ticket_markdown(ticket_final, pieces_jointes=pieces_jointes)
        st.code(resume, language="markdown")


# --------------------------------------------------------------------------
# Derniers tickets enregistrés (vérification rapide que la persistance marche)
# --------------------------------------------------------------------------

st.divider()
with st.expander("🗂️ Derniers tickets enregistrés"):
    try:
        derniers = lister_derniers_tickets(limite=10)
        if derniers:
            st.dataframe([dict(row) for row in derniers], width="stretch")
        else:
            st.caption("Aucun ticket enregistré pour l'instant.")
    except Exception as exc:
        st.caption(f"Impossible de lire tickets.db : {exc}")