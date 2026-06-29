"""
Agent Barron McCann.

Logique métier issue de la documentation interne IRIS :
- L'enseigne détermine le contrat (3 groupes connus à ce jour).
- Le pays détermine si le technicien doit être anglophone.
- Le nombre de techniciens dépend de la taille d'écran si mentionnée.
- PED est toujours un synonyme de TPE chez ce client.

Ce fichier est conçu pour être étendu : si un nouveau groupe
(enseigne/contrat) apparaît, ajouter une entrée dans BARRON_CONTRACTS
et une condition dans get_groupe(), sans toucher au reste.

--- Version durcie (relecture post-AEMSOFT/AMPLIFON/ADOPT/etc.) ---
Corrige, par rapport à la version initiale :
  1. Code postal / téléphone FR : aucune normalisation déterministe
     n'existait dans ce fichier (4->5 chiffres, 9->10 chiffres,
     cf. BARRON_MAC_CANN.docx) -> ajoutée en Python pur, plus fiable que
     de compter sur l'IA pour s'en souvenir à chaque extraction.
  2. Traduction Problématique/Travail attendu : une vraie traduction n'est
     pas une règle déterministe -> on détecte plutôt si le texte SEMBLE
     anglais (heuristique mots courants) et on flague pour traduction
     manuelle, on ne fabrique jamais de traduction.
  3. PED->TPE ne touchait pas `intitule`, alors que la règle est annoncée
     comme universelle dans le docx (pas limitée à certains champs) ->
     étendu. Volontairement PAS appliqué à `numero_serie`/
     `reference_materiel_client` (identifiants exacts, pas du texte
     descriptif -> remplacer un sous-texte "PED" y serait risqué).
  4. `remplacer_ped_par_tpe` ne gérait que 3 variantes de casse exactes
     -> remplacé par une regex insensible à la casse avec limites de mots
     (`\\bped\\b`), plus robuste.
  5. Ajout du système de `notes` consolidées dans `commentaire_interne`,
     pour rester cohérent avec les agents écrits depuis (aemsoft/amplifon/
     adopt/etc.) -- aucune déduction n'était signalée à l'utilisateur
     auparavant.
  6. `normaliser_sous_type` retombait sur le texte brut en silence si
     aucun libellé Pivot connu n'était reconnu -> désormais flagué.
"""

import re
import unicodedata

from app.models.ticket import Ticket


def _sans_accents(texte: str) -> str:
    """
    Retire les accents d'une chaîne pour permettre des comparaisons
    fiables quelle que soit la façon dont le mail/l'IA a écrit le mot
    (ex: "démontage" et "demontage" doivent être reconnus comme identiques).
    """
    if not texte:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )


def _normaliser(texte: str) -> str:
    """Normalise (minuscule + sans accent + trim) pour des comparaisons robustes."""
    return _sans_accents((texte or "").strip().lower())


def _ajouter_si_absent(texte_existant: str, bloc: str) -> str:
    """Ajoute `bloc` à `texte_existant` s'il n'y est pas déjà (idempotence)."""
    if not bloc:
        return texte_existant
    if texte_existant and bloc in texte_existant:
        return texte_existant
    if texte_existant:
        return f"{texte_existant.strip()}\n\n{bloc}"
    return bloc


# Pays/territoires francophones reconnus (codes ISO et noms usuels,
# en minuscules pour comparaison insensible à la casse).
# Pour ces pays -> technicien_anglophone = False.
# Tout pays absent de cette liste -> technicien_anglophone = True.
PAYS_FRANCOPHONES = {
    "fr", "france",
    "be", "belgique", "belgium",
    "ch", "suisse", "switzerland",
    "lu", "luxembourg",
    "mc", "monaco",
}


def est_pays_francophone(pays: str) -> bool:
    """
    Détermine si un pays est francophone à partir de PAYS_FRANCOPHONES.
    Un pays vide/non renseigné est considéré francophone par défaut
    (hypothèse raisonnable : la majorité des tickets Barron sont en France).
    """
    pays_normalise = _normaliser(pays)
    if not pays_normalise:
        return True
    return pays_normalise in PAYS_FRANCOPHONES


def est_france(pays: str) -> bool:
    """
    Spécifiquement la France (pas la francophonie au sens large) -- utilisé
    pour les règles BARRON_MAC_CANN.docx limitées à la France : normalisation
    CP/téléphone, et Problématique français-uniquement vs. français+anglais.
    """
    return _normaliser(pays) in ("fr", "france")


def normaliser_code_postal_fr(code_postal: str) -> str:
    """France : code postal sur 5 chiffres. Si 4 chiffres ('6800'), ajoute un 0 ('06800')."""
    cp = (code_postal or "").strip()
    if cp.isdigit() and len(cp) == 4:
        return f"0{cp}"
    return cp


def normaliser_telephone_fr(numero: str) -> str:
    """France : téléphone sur 10 chiffres. Si 9 chiffres ('612345678'), ajoute un 0 ('0612345678')."""
    chiffres = re.sub(r"\D", "", numero or "")
    if len(chiffres) == 9:
        return f"0{chiffres}"
    return (numero or "").strip()


# --------------------------------------------------------------------------
# Détection heuristique "texte en anglais" (pour flag de traduction,
# jamais pour fabriquer une traduction -- cf. point 2 du docstring)
# --------------------------------------------------------------------------

MOTS_ANGLAIS_COURANTS = (
    " the ", " and ", " please ", " replace ", " faulty ", " required ",
    " engineer ", " store ", " issue ", " request ", " unit ", " return ",
)


def semble_en_anglais(texte: str) -> bool:
    """Heuristique grossière : présence de mots anglais courants. Pas une certitude."""
    texte_normalise = f" {_normaliser(texte)} "
    return any(mot in texte_normalise for mot in MOTS_ANGLAIS_COURANTS)


# --------------------------------------------------------------------------
# Référentiel des contrats Barron (issu de Pivot, capture du 22/06/2026)
# --------------------------------------------------------------------------

BARRON_CONTRACTS = {
    "PRICING_FR": {
        "contrat": "OD.BARRONM16.001.1 - Pricing FR - NBD SLA (ON DEMAND)",
        "type": "MAINTENANCE",
        "sous_type": "TPE",
        "categorie": "",
    },
    "SMYTHS": {
        "contrat": "IM.BARRONM16.001.1 - IMAC Smyths Toys (IMAC)",
        "type": "ON DEMAND-IMAC",
        "sous_type": "",  # déduit du mail : "CAISSES ET PERIPHERIQUE" ou "INSTALLATION MAGASIN"
        "categorie": "",
    },
    "CLAIRES": {
        "contrat": "IM.BARRONM16.002.1 - CLAIRE'S FRANCE (IMAC)",
        "type": "ON DEMAND-CLAIRES",
        "sous_type": "",  # déduit du mail, voir SOUS_TYPES_CLAIRES ci-dessous
        "categorie": "",
    },
}

# Sous-types possibles pour Claire's (libellés exacts Pivot).
# Utilisé pour valider/normaliser ce que l'IA a déduit du mail.
SOUS_TYPES_CLAIRES = {
    "INSTALLATION MAGASIN": "ON DEMAND - Installation Magasin",
    "DEMONTAGE MAGASIN": "ON DEMAND - Demontage Magasin",
    "RELOCALISATION (REMODELING)": "ON DEMAND - Relocalisation (Remodeling)",
}

# Sous-types possibles pour Smyths Toys (libellés exacts Pivot).
SOUS_TYPES_SMYTHS = {
    "CAISSES ET PERIPHERIQUE": "CAISSES ET PERIPHERIQUE",
    "INSTALLATION MAGASIN": "INSTALLATION MAGASIN",
}

# Enseignes explicitement rattachées à Smyths Toys / Claire's.
# Toute enseigne absente de ces deux listes tombe dans PRICING_FR
# (comportement documenté, pas une supposition -- cf. docx).
ENSEIGNES_SMYTHS = {"smyths toys", "smyths"}
ENSEIGNES_CLAIRES = {"claire's", "claires", "claire's france"}


def get_groupe(enseigne: str) -> str:
    """
    Détermine le groupe contractuel Barron à partir de l'enseigne.
    Par défaut (toute enseigne non reconnue) -> PRICING_FR (comportement
    documenté dans le docx : "Pricing FR... pour tous les magasins SAUF
    Smyths Toys ou Claire's", pas une supposition non vérifiée).
    """
    enseigne_normalisee = (enseigne or "").strip().lower()

    if enseigne_normalisee in ENSEIGNES_SMYTHS:
        return "SMYTHS"

    if enseigne_normalisee in ENSEIGNES_CLAIRES:
        return "CLAIRES"

    return "PRICING_FR"


def normaliser_sous_type(groupe: str, sous_type_brut: str) -> tuple[str, bool]:
    """
    Convertit un sous-type déduit par l'IA (texte libre, ex: "installation")
    vers le libellé exact attendu par Pivot, si on le reconnaît.
    Retourne (valeur, reconnu) -- reconnu=False si on retombe sur le texte
    brut tel quel faute de correspondance (à signaler, cf. point 6).
    """
    if not sous_type_brut:
        return "", False

    cle = _sans_accents(sous_type_brut.strip().upper())

    table = SOUS_TYPES_CLAIRES if groupe == "CLAIRES" else SOUS_TYPES_SMYTHS if groupe == "SMYTHS" else {}
    for mot_cle, libelle_exact in table.items():
        mot_cle_normalise = _sans_accents(mot_cle)
        if mot_cle_normalise in cle or mot_cle_normalise.split()[0] in cle:
            return libelle_exact, True

    return sous_type_brut, False


def deduire_nombre_techniciens(ticket: Ticket) -> tuple[int, str]:
    """
    Règle : si le texte mentionne un écran à partir de 43 pouces,
    on passe à 2 techniciens. Sinon on garde la valeur déjà présente
    (issue du mail), avec 1 par défaut. Retourne (nombre, note_si_deduit).
    """
    texte_a_verifier = " ".join([
        ticket.procedure.travail_attendu or "",
        ticket.procedure.consignes_mission or "",
        ticket.intervention.problematique or "",
    ]).lower()

    match = re.search(r"(\d{2,3})\s*[\"\u2033]|\b(\d{2,3})\s*pouces?\b", texte_a_verifier)
    if match:
        taille = int(match.group(1) or match.group(2))
        if taille >= 43:
            return 2, f"Nombre de techniciens déduit à 2 (écran {taille}'' détecté >= 43'')."

    return ticket.procedure.nombre_techniciens or 1, ""


def remplacer_ped_par_tpe(texte: str) -> str:
    """
    Chez Barron, 'PED' désigne toujours un TPE en France.
    Regex insensible à la casse avec limites de mots (plus robuste que
    3 variantes de casse exactes -- cf. point 4 du docstring).
    """
    if not texte:
        return texte
    return re.sub(r"\bped\b", "TPE", texte, flags=re.IGNORECASE)


def fusionner_references_incident(ticket: Ticket) -> str:
    """
    Construit le numéro d'incident client au format exigé par Barron :
    "[Barron McCann Reference] – [Customer Ref]"
    Ex: "WOT0017951 – INC0529843"

    La référence Barron McCann est temporairement stockée dans
    ticket.intervention.code_projet par le prompt d'extraction
    (champ neutre, non utilisé ailleurs pour ce client).
    La Customer Ref est déjà dans ticket.intervention.numero_incident_client.
    """
    reference_barron = (ticket.intervention.code_projet or "").strip()
    reference_client = (ticket.intervention.numero_incident_client or "").strip()

    if reference_barron and reference_client:
        return f"{reference_barron} – {reference_client}"

    # Si une seule des deux références est présente, on la garde telle quelle
    return reference_barron or reference_client


def enrich_ticket(ticket: Ticket, texte_mail: str = "") -> Ticket:
    """
    Enrichit un Ticket déjà extrait du mail avec les règles métier
    spécifiques à Barron McCann.
    """
    notes: list[str] = []

    # --- Informations client fixes ---
    ticket.customer.client = "BARRON MAC CANN LTD"
    ticket.customer.numero_client = "BARRONM16"

    pays = ticket.customer.pays

    # --- Normalisation FR (code postal / téléphone) ---
    if est_france(pays):
        if ticket.customer.code_postal:
            ticket.customer.code_postal = normaliser_code_postal_fr(ticket.customer.code_postal)
        if ticket.customer.portable:
            ticket.customer.portable = normaliser_telephone_fr(ticket.customer.portable)
        if ticket.customer.fixe:
            ticket.customer.fixe = normaliser_telephone_fr(ticket.customer.fixe)

    # --- Détermination du groupe contractuel selon l'enseigne ---
    groupe = get_groupe(ticket.customer.enseigne)
    infos_contrat = BARRON_CONTRACTS[groupe]

    ticket.intervention.type_intervention = "Contrat"
    ticket.intervention.contrat = infos_contrat["contrat"]
    ticket.intervention.type = infos_contrat["type"]
    ticket.intervention.categorie = infos_contrat["categorie"]

    # Sous-type : fixe pour Pricing FR (toujours "TPE").
    # Pour Smyths/Claire's, on normalise ce que l'IA a déduit du mail
    # vers le libellé exact attendu par Pivot.
    if infos_contrat["sous_type"]:
        ticket.intervention.sous_type = infos_contrat["sous_type"]
    else:
        sous_type_normalise, reconnu = normaliser_sous_type(groupe, ticket.intervention.sous_type)
        ticket.intervention.sous_type = sous_type_normalise
        if sous_type_normalise and not reconnu:
            notes.append(
                f"Sous-type '{sous_type_normalise}' ({groupe}) non reconnu parmi les "
                f"libellés Pivot connus — conservé tel quel, à corriger manuellement."
            )
        elif not sous_type_normalise:
            notes.append(f"Sous-type introuvable dans le mail pour le groupe {groupe} — à compléter manuellement.")

    # --- Fusion des 2 références en un seul numéro d'incident client ---
    # IMPORTANT : fait avant de vider code_projet (qui servait de stockage temporaire).
    if not ticket.intervention.code_projet and not ticket.intervention.numero_incident_client:
        notes.append("Ni 'Barron McCann Reference' ni 'Customer Ref' trouvées — Numéro d'incident client à compléter manuellement.")
    ticket.intervention.numero_incident_client = fusionner_references_incident(ticket)
    ticket.intervention.code_projet = ""  # champ neutre, on le nettoie après usage

    # --- Règles transverses ---
    ticket.intervention.origine = "Email"
    ticket.procedure.intervention_sur_site = True
    ticket.procedure.prise_rdv = False
    ticket.procedure.procedure = True
    ticket.validation.type_validation = "Client"

    # Technicien anglophone : Non si pays francophone (France, Belgique,
    # Suisse, Luxembourg, Monaco), Oui sinon.
    if not pays:
        notes.append("Pays non renseigné — francophone supposé par défaut (technicien_anglophone=Non), à vérifier.")
    ticket.procedure.technicien_anglophone = not est_pays_francophone(pays)

    # Nombre de techniciens (règle écran 43'')
    nombre_techniciens, note_deduction = deduire_nombre_techniciens(ticket)
    ticket.procedure.nombre_techniciens = nombre_techniciens
    if note_deduction:
        notes.append(note_deduction)

    # --- Remplacement PED -> TPE (règle universelle, cf. point 3) ---
    # Volontairement PAS appliqué à numero_serie / reference_materiel_client :
    # ce sont des identifiants exacts, pas du texte descriptif.
    ticket.intervention.problematique = remplacer_ped_par_tpe(ticket.intervention.problematique)
    ticket.intervention.intitule = remplacer_ped_par_tpe(ticket.intervention.intitule)
    ticket.procedure.travail_attendu = remplacer_ped_par_tpe(ticket.procedure.travail_attendu)
    ticket.procedure.consignes_mission = remplacer_ped_par_tpe(ticket.procedure.consignes_mission)

    # --- Langue (Problématique français-only si France, sinon FR+EN ;
    # Travail attendu toujours traduit en français) -- jamais de traduction
    # fabriquée, uniquement un flag pour traduction manuelle (cf. point 2) ---
    if est_france(pays) and semble_en_anglais(ticket.intervention.problematique):
        notes.append(
            "Problématique semble être en anglais alors que l'intervention est en "
            "France (BARRON_MAC_CANN.docx : français UNIQUEMENT si France) — à "
            "traduire manuellement avant saisie."
        )
    elif not est_france(pays) and ticket.intervention.problematique:
        notes.append(
            "Intervention hors de France : vérifier que la Problématique est bien "
            "en français PUIS en anglais (BARRON_MAC_CANN.docx) — non vérifiable "
            "automatiquement."
        )

    if semble_en_anglais(ticket.procedure.travail_attendu):
        notes.append(
            "Travail attendu semble être en anglais — BARRON_MAC_CANN.docx demande "
            "de le traduire en français ('Required Actions' à traduire) — à "
            "traduire manuellement avant saisie."
        )

    if notes:
        bloc_notes = "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_notes
        )

    return ticket