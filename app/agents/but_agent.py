"""
Agent BUT.

Logique métier issue de BUT.docx + TOKI_BUT.txt :

- 3 familles de demandes, chacune avec son propre Contrat Pivot :
    * Matériel d'encaissement (Caisse / Afficheur Client / Imprimante Ticket)
      -> Contrat MCO, Niveau de service "GTR 1J (6/7)" (auto).
    * Onduleur -> Contrat "AU CALL ONDULEUR", Niveau de service "date imposée".
    * Switch   -> Contrat "AU CALL SWITCH",   Niveau de service "date imposée".
- Délai de création du ticket : 1h MAX après réception du mail (HORS DELAI
  INTERDIT, cf. TOKI) -> rappel informatif uniquement, non automatisable.
- Pas de contre-appel pour aucune des 3 familles.
- TPE hors périmètre pour ce client.
- Caisse = SEUL matériel qui passe systématiquement en intégration ; Onduleur
  et Switch passent aussi en intégration (OUI) d'après le tableau pièces ;
  Afficheur/Imprimante : pas de règle d'intégration documentée.
- Durées fixes par matériel (TOKI) : Afficheur 30min, Imprimante 30min,
  Caisse 90min, Onduleur 60min, Switch 60min. Nombre de techniciens = 1
  (toujours, auto).
- Référence imprimante ticket conditionnée par le numéro de série du
  matériel sur site : préfixe "JAC" -> modèle III-JAC MICR spécifiquement ;
  sinon le modèle explicitement demandé dans le mail.
- Onduleur : retour de l'ancien onduleur via LOG-RAMASSAGE, avec la
  consigne "ramassage à J+1 après intervention" (cf. tableau pièces TOKI).

⚠️ Hypothèses à vérifier :

  1. TOKI_BUT.txt référence des lettres (A/B/C/D) pointant vers une image/
     capture d'écran absente du texte fourni. Déduction par contexte :
     A = Numéro d'incident client, B = Code site, C = Modèle du matériel
     concerné, D = Numéro de série. À CONFIRMER — si l'un de ces mappings
     est faux, l'Intitulé et le N° incident client construits ici le seront
     aussi.
  2. Libellés de contrat Onduleur/Switch déduits par symétrie de nommage
     ("CT.BUTINT17.001.1 - CONTRAT AU CALL ONDULEUR" / "... SWITCH") — seul
     le libellé Switch est donné littéralement dans TOKI, celui d'Onduleur
     est une extrapolation à confirmer dans Pivot.
  3. Le numéro de caisse ("N° de la caisse", utilisé dans l'Intitulé
     encaissement) n'a pas de champ dédié dans le `Ticket` -> extrait par
     regex best-effort depuis texte_mail (ex. "caisse n°1"), peut échouer
     si la formulation diffère.
  4. Choix entre les 2 références Switch (Aruba 6000 vs Aruba 2530) : aucune
     règle de sélection documentée -> signalé, jamais choisi en silence.
  5. Token/procédure : "Mettre le Token approprié à la panne" reste un choix
     humain (pas de table panne -> token disponible) -> non automatisé,
     sauf le cas Switch/Baie/Serveur/Onduleur qui partage un Token unique
     documenté (dossier complet "switch-baie-serveur-onduleur").
"""

import re
import unicodedata

from app.models.ticket import Ticket


def _sans_accents(texte: str) -> str:
    """Retire les accents pour fiabiliser les comparaisons de texte."""
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


# --------------------------------------------------------------------------
# Référentiel BUT (issu de TOKI_BUT.txt)
# --------------------------------------------------------------------------

MATERIEL_CAISSE = "Caisse"
MATERIEL_AFFICHEUR = "Afficheur Client"
MATERIEL_IMPRIMANTE = "Imprimante Ticket"
MATERIEL_ONDULEUR = "Onduleur"
MATERIEL_SWITCH = "Switch"

FAMILLE_ENCAISSEMENT = (MATERIEL_CAISSE, MATERIEL_AFFICHEUR, MATERIEL_IMPRIMANTE)
FAMILLE_CALL = (MATERIEL_ONDULEUR, MATERIEL_SWITCH)

CONTRAT_MCO = "CT.BUTINT17.001.1 - CONTRAT MCO"
CONTRAT_CALL_ONDULEUR = "CT.BUTINT17.001.1 - CONTRAT AU CALL ONDULEUR"  # cf. hypothèse 2
CONTRAT_CALL_SWITCH = "CT.BUTINT17.001.1 - CONTRAT AU CALL SWITCH"

NIVEAU_SERVICE_ENCAISSEMENT = "GTR 1J (6/7)"
NIVEAU_SERVICE_CALL = "Date imposée"

DUREE_PAR_MATERIEL = {
    MATERIEL_AFFICHEUR: "30 min",
    MATERIEL_IMPRIMANTE: "30 min",
    MATERIEL_CAISSE: "90 min",
    MATERIEL_ONDULEUR: "60 min",
    MATERIEL_SWITCH: "60 min",
}

# Référence (code, désignation)
REF_AFFICHEUR_SAGA = ("IBUTECR-ECRAN-8", "ECRAN 8\" + logo SAGA BUT")
REF_AFFICHEUR_WINCOR = ("IBUTAFF-AFFICHE", "AFFICHEUR WINCOR")
REF_IMPRIMANTE_JAC = ("IBUTIMP-TMH6-3U", "Epson TMH6000III-JAC MICR")
REF_IMPRIMANTE_TMH6_4U = ("IBUTIMP-TMH6-4U", "tm-h6000 IV USB noir MICR")
REF_IMPRIMANTE_TMH6000V = ("IBUTIMP-TMH6000V", "TM-H6000 V USB NOIR")
REF_IMPRIMANTE_TM88V = ("IBUTIMP-TM88V", "Imprimante TM T88V")
REF_CHEQUE_TEST = ("CHI56314", "Chèque de test")
REF_CAISSE = ("IBUTCAI-HP-RP9", "CAISSE HP RP9")
REF_ONDULEUR = ("CBUTOND-BUNDLE", "BUNDLE ONDULEUR")
REF_SWITCH_ARUBA_6000 = ("CBUTSWI-ARUBA-BUNDLE", "SWITCH ARUBA 6000 24G+GBIC")
REF_SWITCH_ARUBA_2530 = ("IBUT-SWITCH-ARUBA-2530", "SWITCH ARUBA 2530 POE+SWITCH 24 PORTS")

MOTS_CLES_MATERIEL = {
    MATERIEL_CAISSE: ("caisse", "rp9", "hp rp9", "tpv"),
    MATERIEL_AFFICHEUR: ("afficheur", "ecran client", "saga", "wincor"),
    MATERIEL_IMPRIMANTE: ("imprimante", "epson", "tmh", "tm-h6000", "tm88v", "tm-t88v", "tm t88v"),
    MATERIEL_ONDULEUR: ("onduleur",),
    MATERIEL_SWITCH: ("switch", "aruba"),
}

RE_NUMERO_CAISSE = re.compile(r"caisse\s*n?[°o]?\s*(\d+)", re.IGNORECASE)


# --------------------------------------------------------------------------
# Helpers de détection
# --------------------------------------------------------------------------

def detecter_materiel(texte_mail: str) -> str:
    """Déduit le matériel concerné (Caisse/Afficheur/Imprimante/Onduleur/Switch)."""
    texte = _normaliser(texte_mail)
    for materiel, mots_cles in MOTS_CLES_MATERIEL.items():
        if any(mot in texte for mot in mots_cles):
            return materiel
    return ""


def extraire_numero_caisse(texte_mail: str) -> str:
    """Numéro de caisse (ex. 'Caisse N°1') -- filet de sécurité, cf. hypothèse 3."""
    match = RE_NUMERO_CAISSE.search(texte_mail or "")
    return f"Caisse N°{match.group(1)}" if match else ""


def choisir_reference_imprimante(texte_mail: str, numero_serie: str) -> tuple[str, str]:
    """
    JAC en préfixe du numéro de série -> modèle III-JAC MICR spécifiquement.
    Sinon, le modèle explicitement demandé dans le mail (IV, V, ou TM T88V).
    """
    if (numero_serie or "").strip().upper().startswith("JAC"):
        return REF_IMPRIMANTE_JAC
    texte = _normaliser(texte_mail)
    if "tm88v" in texte or "t88v" in texte:
        return REF_IMPRIMANTE_TM88V
    if "tmh6000v" in texte or "tm-h6000 v" in texte or "h6000v" in texte:
        return REF_IMPRIMANTE_TMH6000V
    if "tmh6-4u" in texte or "h6000 iv" in texte or "tm-h6000 iv" in texte:
        return REF_IMPRIMANTE_TMH6_4U
    return ("", "")  # aucun modèle déduit avec confiance -> à choisir manuellement


def choisir_reference_afficheur(texte_mail: str) -> tuple[str, str]:
    """SAGA par défaut, sauf mention explicite de Wincor (cf. BUT.docx/TOKI)."""
    if "wincor" in _normaliser(texte_mail):
        return REF_AFFICHEUR_WINCOR
    return REF_AFFICHEUR_SAGA


def choisir_reference_switch(texte_mail: str) -> tuple[str, str, str]:
    """
    Aucune règle de sélection documentée entre Aruba 6000 et Aruba 2530
    (cf. hypothèse 4) -> retourne (code, designation, note_a_signaler).
    """
    texte = _normaliser(texte_mail)
    if "2530" in texte:
        return (*REF_SWITCH_ARUBA_2530, "")
    if "6000" in texte or "aruba 6000" in texte:
        return (*REF_SWITCH_ARUBA_6000, "")
    return (
        *REF_SWITCH_ARUBA_6000,
        "Modèle de switch (Aruba 6000 ou 2530) non précisé dans le mail — "
        "Aruba 6000 retenu par défaut, à vérifier.",
    )


# --------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------

def enrich_ticket(ticket: Ticket, texte_mail: str = "") -> Ticket:
    """Enrichit un Ticket déjà extrait du mail avec les règles métier BUT."""
    notes: list[str] = []

    ticket.customer.client = "BUT"

    if ticket.customer.code_site and not re.fullmatch(r"\d{3}", ticket.customer.code_site.strip()):
        notes.append(
            f"Code site inhabituel ({ticket.customer.code_site!r}) — attendu sur "
            f"3 chiffres, à vérifier."
        )

    materiel = detecter_materiel(texte_mail)
    if not materiel:
        notes.append(
            "Matériel concerné non détecté automatiquement dans le mail (Caisse / "
            "Afficheur / Imprimante / Onduleur / Switch) — à sélectionner manuellement, "
            "le reste de l'enrichissement n'a pas pu être appliqué."
        )
        if notes:
            ticket.intervention.commentaire_interne = _ajouter_si_absent(
                ticket.intervention.commentaire_interne,
                "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes),
            )
        return ticket

    ticket.intervention.type_intervention = "Contrat"
    ticket.intervention.type = materiel
    ticket.intervention.origine = "Email"
    ticket.procedure.nombre_techniciens = 1
    ticket.procedure.duree = DUREE_PAR_MATERIEL[materiel]

    ville = ticket.customer.ville or ""
    code_site = ticket.customer.code_site or ""

    if materiel in FAMILLE_ENCAISSEMENT:
        ticket.intervention.contrat = CONTRAT_MCO
        ticket.intervention.niveau_priorite = NIVEAU_SERVICE_ENCAISSEMENT

        numero_caisse = extraire_numero_caisse(texte_mail)
        if not numero_caisse and materiel == MATERIEL_CAISSE:
            notes.append("Numéro de caisse introuvable dans le mail — à compléter manuellement dans l'Intitulé.")
        intitule_parts = ["Maintenance", materiel]
        if numero_caisse:
            intitule_parts.append(numero_caisse)
        intitule_parts += [p for p in (ville, code_site) if p]
        ticket.intervention.intitule = " ".join(intitule_parts)

        if materiel == MATERIEL_CAISSE:
            ticket.logistics.pieces = f"{REF_CAISSE[0]} / {REF_CAISSE[1]}"
            ticket.logistics.integration_a_faire = True
        elif materiel == MATERIEL_AFFICHEUR:
            code, designation = choisir_reference_afficheur(texte_mail)
            ticket.logistics.pieces = f"{code} / {designation}"
        elif materiel == MATERIEL_IMPRIMANTE:
            code, designation = choisir_reference_imprimante(texte_mail, ticket.intervention.numero_serie)
            if code:
                pieces = f"{code} / {designation}"
                if code != REF_IMPRIMANTE_TM88V[0]:
                    pieces += f" + {REF_CHEQUE_TEST[0]} / {REF_CHEQUE_TEST[1]}"
                ticket.logistics.pieces = pieces
            else:
                notes.append(
                    "Modèle d'imprimante ticket non déduit avec confiance (ni préfixe "
                    "JAC dans le numéro de série, ni modèle IV/V/TM88V explicite dans le "
                    "mail) — pièce à sélectionner manuellement."
                )

        ticket.logistics.envoi_piece_par = "IRIS"

    elif materiel in FAMILLE_CALL:
        ticket.intervention.niveau_priorite = NIVEAU_SERVICE_CALL
        intitule_parts = ["Remplacement", materiel] + [p for p in (ville, code_site) if p]
        ticket.intervention.intitule = " ".join(intitule_parts)
        ticket.logistics.envoi_piece_par = "IRIS"
        ticket.logistics.integration_a_faire = True

        if materiel == MATERIEL_ONDULEUR:
            ticket.intervention.contrat = CONTRAT_CALL_ONDULEUR
            ticket.logistics.pieces = f"{REF_ONDULEUR[0]} / {REF_ONDULEUR[1]}"
            ticket.logistics.retour_piece = "Oui"
            ticket.logistics.commentaire_logistique = _ajouter_si_absent(
                ticket.logistics.commentaire_logistique,
                "Onduleur défectueux : envoi CLIENT AVEC LOG-RAMASSAGE. "
                "Consigne : ramassage à J+1 après intervention.",
            )
        else:  # Switch
            ticket.intervention.contrat = CONTRAT_CALL_SWITCH
            code, designation, note_switch = choisir_reference_switch(texte_mail)
            ticket.logistics.pieces = f"{code} / {designation}"
            if note_switch:
                notes.append(note_switch)
            notes.append(
                "Switch/Baie/Serveur/Onduleur partagent un Token unique documenté "
                "(dossier complet 'switch-baie-serveur-onduleur') — à appliquer."
            )

    if not ticket.intervention.numero_incident_client:
        notes.append(
            "Numéro d'incident client (placeholder 'A' dans TOKI_BUT.txt, image absente "
            "du texte fourni) non extrait — à vérifier manuellement, cf. hypothèse 1."
        )
    else:
        notes.append(
            f"Numéro d'incident client extrait par l'IA ({ticket.intervention.numero_incident_client!r}) "
            f"-- NON VÉRIFIABLE : son mapping exact (placeholder 'A' de TOKI_BUT.txt, "
            f"image absente) reste une supposition, cf. hypothèse 1."
        )

    notes.append(
        "Rappel SLA BUT (TOKI) : ticket PIVOT à créer sous 1h max après réception du "
        "mail, hors délai interdit — pas de contre-appel pour ce client."
    )

    if notes:
        bloc_notes = "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_notes
        )

    return ticket