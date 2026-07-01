"""
Formatage du Ticket en bloc résumé copiable, format "Ticket PIVOT" défini
dans SKILL.md (Étape 4 -- gabarit de sortie standard, mêmes noms de champs
et même ordre que la référence du projet).
"""

from app.models.ticket import Ticket


def _ligne(label: str, valeur) -> str:
    """'- Label : valeur' -- vide proprement si valeur falsy (None, "", 0 pour les compteurs non pertinents)."""
    if valeur is None:
        valeur = ""
    if isinstance(valeur, bool):
        valeur = "Oui" if valeur else "Non"
    return f"- {label} : {valeur}"


def formater_ticket_markdown(ticket: Ticket, pieces_jointes: list[str] | None = None) -> str:
    """
    Construit le bloc Markdown "Ticket PIVOT — [Client]" tel que défini
    dans SKILL.md (Étape 4), à partir d'un Ticket déjà enrichi (et
    éventuellement corrigé manuellement par l'utilisateur).

    `pieces_jointes` : noms de fichiers à lister dans la section finale
    (ex. le PDF AEMSOFT/AXE E-SANTE jamais parsé, mais à attacher).
    """
    c, i, l, p, v = ticket.customer, ticket.intervention, ticket.logistics, ticket.procedure, ticket.validation

    lignes = [f"## Ticket PIVOT — {c.client or '[Client non renseigné]'}", ""]

    lignes += [
        "**Site d'intervention**",
        _ligne("Enseigne", c.enseigne),
        _ligne("Adresse", c.adresse),
        _ligne("Complément d'adresse", c.complement_adresse),
        _ligne("Code postal", c.code_postal),
        _ligne("Ville", c.ville),
        _ligne("Pays", c.pays),
        _ligne("Code Site", c.code_site),
        "",
        "**Contact**",
        _ligne("Nom / Prénom", " ".join(p2 for p2 in (c.prenom, c.nom) if p2)),
        _ligne("Téléphone", c.portable or c.fixe),
        _ligne("Email", c.email),
        "",
        "**Type d'intervention / Contrat / Typologie**",
        _ligne("Type d'intervention", i.type_intervention),
        _ligne("Contrat", i.contrat),
        _ligne("Type", i.type),
        _ligne("Sous-type", i.sous_type),
        _ligne("Niveau de service", i.niveau_priorite),
        "",
        "**Détails**",
        _ligne("Type de ticket", i.type_ticket),
        _ligne("Intitulé", i.intitule),
        _ligne("Numéro d'incident client", i.numero_incident_client),
        _ligne("Problématique", i.problematique),
        _ligne("Origine", i.origine or "Email"),
        "",
        "**Matériel**",
        _ligne("Besoin de matériel ?", l.besoin_materiel),
        _ligne("Pièce(s)", l.pieces),
        _ligne("Livraison (envoi par / destination)", " / ".join(x for x in (l.envoi_piece_par, l.consigne_livraison) if x)),
        _ligne("Intégration à faire", l.integration_a_faire),
        _ligne("Retour de pièces", l.retour_piece),
        "",
        "**Planification**",
        _ligne("Intervention sur site", p.intervention_sur_site),
        _ligne("Prise de RDV", p.prise_rdv),
        _ligne("Date limite", p.date_limite),
        "",
        "**Consignes et mission**",
        _ligne("Nombre de techniciens", p.nombre_techniciens),
        _ligne("Durée", p.duree),
        _ligne("Travail attendu par le(s) technicien(s)", p.travail_attendu),
        _ligne("Technicien anglophone", p.technicien_anglophone),
        _ligne("Autre outillage spécifique", p.autre_outillage),
        _ligne("Procédure (Oui/Non)", p.procedure),
        _ligne("Lien de la procédure", p.lien_procedure),
        _ligne("Validation de l'intervention", v.type_validation),
        _ligne("Téléphone/Contact pour la validation", v.telephone_validation),
        "",
        "**Pièces jointes à attacher (Documents)**",
        _ligne("Fichiers", ", ".join(pieces_jointes) if pieces_jointes else "(aucune)"),
    ]

    if i.commentaire_interne:
        lignes += ["", "**⚠️ Points à vérifier avant saisie**", i.commentaire_interne]

    return "\n".join(lignes)