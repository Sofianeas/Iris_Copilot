"""
Service de routage : détecte le client AVANT d'appeler l'IA,
pour que l'extraction utilise un prompt adapté à ce client.
"""

from app.models.ticket import Ticket
from app.services.parser_service import traiter_mail as extraire_ticket_brut
from app.agents import barron_agent, adopt_agent, aemsoft_agent, amplifon_agent, but_agent, innovorder_agent, pos_service_agent, shoppertrak_agent


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


def traiter_mail_complet(texte_mail: str) -> Ticket:
    """
    Pipeline complet :
    1. Détecter le client SUR LE TEXTE BRUT
    2. Extraire avec un prompt adapté à ce client
    3. Enrichir avec l'agent du client
    """
    client_detecte = detecter_client(texte_mail)

    if not client_detecte:
        raise ValueError(
            "Client non reconnu dans ce mail. "
            "Vérifie le contenu ou ajoute ses signatures dans detecter_client()."
        )

    # Extraction avec prompt adapté au client déjà connu
    ticket = extraire_ticket_brut(texte_mail, nom_client=client_detecte)

    # Enrichissement métier déterministe
    agent_enrich_fn = AGENTS_DISPONIBLES[client_detecte]
    ticket = agent_enrich_fn(ticket, texte_mail=texte_mail)

    return ticket