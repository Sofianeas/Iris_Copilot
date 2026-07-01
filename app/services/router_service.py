"""
Service de routage : détecte le client AVANT d'appeler l'IA,
pour que l'extraction utilise un prompt adapté à ce client.
"""

from app.models.ticket import Ticket
from app.services.parser_service import traiter_mail as extraire_ticket_brut
from app.agents import barron_agent, adopt_agent, aemsoft_agent, amplifon_agent, but_agent, innovorder_agent, pos_service_agent, shoppertrak_agent
# Agents à signature différente -- NE PAS ajouter à AGENTS_DISPONIBLES, voir
# traiter_fichier_complet() ci-dessous pour l'explication et le dispatch dédié.
from app.agents import axe_esante_agent, etam_agent, dynamiz_pharma_agent, promethean_agent


AGENTS_DISPONIBLES = {
    "BARRON": barron_agent.enrich_ticket,
    "ADOPT": adopt_agent.enrich_ticket,
    "AEMSOFT": aemsoft_agent.enrich_ticket,
    "AMPLIFON": amplifon_agent.enrich_ticket,
    "BUT": but_agent.enrich_ticket,
    "INNOVORDER": innovorder_agent.enrich_ticket,
    "POS_SERVICE": pos_service_agent.enrich_ticket,
    "SHOPPERTRAK": shoppertrak_agent.enrich_ticket,
}

# Clients dont la source de vérité est un fichier/texte-brut (cf.
# traiter_fichier_complet()) -- signature différente d'AGENTS_DISPONIBLES,
# volontairement tenus à part plutôt que forcés dans le même dict.
CLIENTS_FICHIER = ("AXE_ESANTE", "ETAM", "DYNAMIZ_PHARMA")

# Détecté mais pas encore automatisable (V3 -- navigation web requise).
CLIENTS_NON_AUTOMATISES = ("PROMETHEAN",)

TOUS_LES_CLIENTS = tuple(sorted(set(AGENTS_DISPONIBLES) | set(CLIENTS_FICHIER) | set(CLIENTS_NON_AUTOMATISES)))


def detecter_client(texte_mail: str) -> str:
    """
    Détermine le client à partir de mots-clés caractéristiques du mail.
    Cette détection se fait AVANT l'appel à l'IA, sur le texte brut,
    pour permettre de charger un prompt d'extraction adapté.
    """
    texte_lower = texte_mail.lower()

    signatures_barron = [
        "store name", "store address", "barron mccann",
        "barron mc cann", "store number",
    ]
    if any(signature in texte_lower for signature in signatures_barron):
        return "BARRON"

    signatures_adopt = [
        "adresse d'intervention", "adresse d intervention",
        "type de demande",
    ]
    if any(signature in texte_lower for signature in signatures_adopt):
        return "ADOPT"

    signatures_aemsoft = [
        "site concerné par l'intervention", "site concerne par l'intervention",
        "site concerné par l intervention", "site concerne par l intervention",
        "instruction tech",
        "lien de suivi du colis ups",
    ]
    if any(signature in texte_lower for signature in signatures_aemsoft):
        return "AEMSOFT"

    # NB : placé AVANT AMPLIFON volontairement -- AMPLIFON détecte "epson"/
    # "ricoh", qui peuvent aussi apparaître dans un mail BUT (imprimante
    # Epson TMH-6000) : BUT doit être vérifié en premier pour éviter ce
    # faux positif.
    signatures_but = [
        "magasin but", "support but", "dsi but",
        "hp rp9", "ecran client saga", "tm-h6000", "tmh6000", "tmh-6000",
    ]
    if any(signature in texte_lower for signature in signatures_but):
        return "BUT"

    signatures_innovorder = [
        "innovorder", "numero d'incident innovorder", "numéro d'incident innovorder",
        "problematique constate sur site", "problématique constaté sur site",
    ]
    if any(signature in texte_lower for signature in signatures_innovorder):
        return "INNOVORDER"

    signatures_pos_service = ["pos service", "maxizoo", "maxi zoo", "geox"]
    if any(signature in texte_lower for signature in signatures_pos_service):
        return "POS_SERVICE"

    signatures_shoppertrak = ["shoppertrak", "diogo lopes", "sensormatic"]
    if any(signature in texte_lower for signature in signatures_shoppertrak):
        return "SHOPPERTRAK"

    # --- Clients à signature différente (fichier/texte-brut), cf.
    # traiter_fichier_complet() -- la détection reste ici car utile à l'UI
    # (savoir quel type de pièce jointe demander), même si le dispatch
    # d'enrichissement est séparé.
    if "diffme21" in texte_lower:
        return "AXE_ESANTE"

    signatures_etam = ["akkodis", "dossier akkodis", "sav akkodis vers iris"]
    if any(signature in texte_lower for signature in signatures_etam):
        return "ETAM"

    if "dynamiz" in texte_lower:
        return "DYNAMIZ_PHARMA"

    if promethean_agent.est_mail_promethean(texte_mail):
        return "PROMETHEAN"

    # NB : pas de libellé de champ unique commun aux 4 modèles AMPLIFON
    # (contrairement aux autres clients) -> détection plus fragile, basée
    # sur le nom d'enseigne + les mots-clés du modèle imprimante (D).
    # À renforcer si des faux négatifs apparaissent (cf. hypothèse 6 de
    # amplifon_agent.py).
    signatures_amplifon = [
        "amplifon", "epson", "ricoh",
    ]
    if any(signature in texte_lower for signature in signatures_amplifon):
        return "AMPLIFON"

    return ""


def traiter_mail_complet(texte_mail: str, client_force: str | None = None) -> Ticket:
    """
    Pipeline complet :
    1. Détecter le client SUR LE TEXTE BRUT (sauf si `client_force` fourni)
    2. Extraire avec un prompt adapté à ce client
    3. Enrichir avec l'agent du client

    `client_force` : permet d'imposer le client plutôt que de le détecter
    automatiquement -- utilisé par l'UI (Streamlit) quand l'utilisateur
    corrige une détection erronée. None (par défaut) = comportement
    inchangé, détection automatique comme avant.
    """
    client_detecte = client_force or detecter_client(texte_mail)

    if not client_detecte:
        raise ValueError(
            "Client non reconnu dans ce mail. "
            "Vérifie le contenu ou ajoute ses signatures dans detecter_client()."
        )
    if client_detecte not in AGENTS_DISPONIBLES:
        raise ValueError(
            f"Client '{client_detecte}' n'est pas un client texte-seul -- "
            f"utiliser traiter_fichier_complet() à la place."
        )

    # Extraction avec prompt adapté au client déjà connu
    ticket = extraire_ticket_brut(texte_mail, nom_client=client_detecte)

    # Enrichissement métier déterministe
    agent_enrich_fn = AGENTS_DISPONIBLES[client_detecte]
    ticket = agent_enrich_fn(ticket, texte_mail=texte_mail)

    return ticket


def traiter_fichier_complet(texte_mail: str, fichier=None, client_force: str | None = None) -> Ticket:
    """
    Pipeline pour les clients dont la source de vérité est un FICHIER
    (Excel) ou un texte brut analysé par regex -- PAS le pipeline standard
    Gemini : AXE E-SANTE, ETAM (Excel obligatoire dans les 2 cas) et
    DYNAMIZ PHARMA (texte du mail et/ou Excel aplati en texte).

    Contrairement à traiter_mail_complet(), AUCUN appel à extraire_ticket_brut
    (Gemini) n'est fait ici : chaque agent lit lui-même, de façon
    déterministe, le fichier ou le texte -- c'est déjà l'extraction.

    Les 3 agents ayant des signatures différentes (cf. AGENTS_DISPONIBLES),
    le dispatch est explicite plutôt que via un dict générique.

    `client_force` : voir traiter_mail_complet() -- même logique d'override
    manuel pour l'UI.
    """
    client_detecte = client_force or detecter_client(texte_mail)
    ticket = Ticket()

    if client_detecte == "AXE_ESANTE":
        if fichier is None:
            raise ValueError(
                "AXE E-SANTE nécessite la pièce jointe Excel ('demande.xlsx') -- "
                "aucun fichier fourni. Le PDF 'fiche d'intervention' n'est PAS "
                "à passer ici (pas de lecture nécessaire, à attacher tel quel)."
            )
        return axe_esante_agent.enrich_ticket_depuis_excel(ticket, fichier, texte_mail=texte_mail)

    if client_detecte == "ETAM":
        if fichier is None:
            raise ValueError("ETAM nécessite la pièce jointe Excel -- aucun fichier fourni.")
        return etam_agent.enrich_ticket_depuis_fichier(ticket, fichier, texte_mail=texte_mail)

    if client_detecte == "DYNAMIZ_PHARMA":
        # fichier optionnel ici : DYNAMIZ PHARMA fonctionne sur texte_mail
        # seul, sur fichier_excel seul, ou sur les deux combinés.
        return dynamiz_pharma_agent.enrich_ticket(ticket, texte_source=texte_mail, fichier_excel=fichier)

    if client_detecte == "PROMETHEAN":
        raise NotImplementedError(
            "PROMETHEAN détecté, mais ce client nécessite une navigation web "
            "(connexion + lecture de la page Promethean) non encore automatisée "
            "(V3). Traiter manuellement via TOKI_PROMETHEAN.txt pour l'instant."
        )

    if client_detecte in AGENTS_DISPONIBLES:
        raise ValueError(
            f"Client '{client_detecte}' détecté, mais c'est un client texte-seul "
            f"-- utiliser traiter_mail_complet() plutôt que traiter_fichier_complet()."
        )

    raise ValueError(
        "Client non reconnu dans ce mail/fichier. "
        "Vérifie le contenu ou ajoute ses signatures dans detecter_client()."
    )