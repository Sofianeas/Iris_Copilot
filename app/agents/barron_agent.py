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
  1. Code postal / téléphone FR : normalisation déterministe ajoutée.
  2. Traduction Problématique/Travail attendu : jamais fabriquée, uniquement
     un flag heuristique pour traduction manuelle.
  3. PED->TPE étendu à `intitule` (règle universelle du docx).
  4. `remplacer_ped_par_tpe` : regex insensible à la casse, limites de mots.
  5. Système de `notes` consolidées dans `commentaire_interne`.
  6. `normaliser_sous_type` : sous-type non reconnu désormais flagué.

--- Intégration Rule Engine (cette étape) ---
  7. Ajout de 2 paramètres optionnels à `enrich_ticket` :
     `rag_decision: RagDecision | None = None` et
     `activer_rule_engine: bool = False`. Désactivé par défaut :
     rétrocompatibilité totale. BARRON n'a qu'UN SEUL point de sortie
     (contrairement à ADOPT/BUT) : le bloc Rule Engine n'est ajouté
     qu'une fois, en fin de fonction.
"""

import re
import unicodedata

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services import rule_engine


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


def _formater_recommandations_rule_engine(recommandations) -> str:
    """
    Formate les RuleRecommendation (rule_engine.executer) en un bloc de
    texte destiné à commentaire_interne -- ne modifie JAMAIS un champ
    métier directement (même politique que sur les autres agents migrés).
    """
    if not recommandations:
        return ""
    lignes = ["🧩 Recommandations du Rule Engine (à vérifier, jamais appliquées automatiquement) :"]
    for reco in recommandations:
        lignes.append(
            f"- Champ '{reco.field}' -> '{reco.value}' "
            f"(confiance={reco.confidence:.2f}, source={reco.source}) : {reco.reason}"
        )
    return "\n".join(lignes)


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
    Un pays vide/non renseigné est considéré francophone par défaut.
    """
    pays_normalise = _normaliser(pays)
    if not pays_normalise:
        return True
    return pays_normalise in PAYS_FRANCOPHONES


def est_france(pays: str) -> bool:
    """Spécifiquement la France (pas la francophonie au sens large)."""
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


MOTS_ANGLAIS_COURANTS = (
    " the ", " and ", " please ", " replace ", " faulty ", " required ",
    " engineer ", " store ", " issue ", " request ", " unit ", " return ",
)


def semble_en_anglais(texte: str) -> bool:
    """Heuristique grossière : présence de mots anglais courants. Pas une certitude."""
    texte_normalise = f" {_normaliser(texte)} "
    return any(mot in texte_normalise for mot in MOTS_ANGLAIS_COURANTS)


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
        "sous_type": "",
        "categorie": "",
    },
    "CLAIRES": {
        "contrat": "IM.BARRONM16.002.1 - CLAIRE'S FRANCE (IMAC)",
        "type": "ON DEMAND-CLAIRES",
        "sous_type": "",
        "categorie": "",
    },
}

SOUS_TYPES_CLAIRES = {
    "INSTALLATION MAGASIN": "ON DEMAND - Installation Magasin",
    "DEMONTAGE MAGASIN": "ON DEMAND - Demontage Magasin",
    "RELOCALISATION (REMODELING)": "ON DEMAND - Relocalisation (Remodeling)",
}

SOUS_TYPES_SMYTHS = {
    "CAISSES ET PERIPHERIQUE": "CAISSES ET PERIPHERIQUE",
    "INSTALLATION MAGASIN": "INSTALLATION MAGASIN",
}

ENSEIGNES_SMYTHS = {"smyths toys", "smyths"}
ENSEIGNES_CLAIRES = {"claire's", "claires", "claire's france"}


def get_groupe(enseigne: str) -> str:
    """Détermine le groupe contractuel Barron à partir de l'enseigne. Défaut : PRICING_FR."""
    enseigne_normalisee = (enseigne or "").strip().lower()

    if enseigne_normalisee in ENSEIGNES_SMYTHS:
        return "SMYTHS"
    if enseigne_normalisee in ENSEIGNES_CLAIRES:
        return "CLAIRES"
    return "PRICING_FR"


def normaliser_sous_type(groupe: str, sous_type_brut: str) -> tuple[str, bool]:
    """Convertit un sous-type déduit par l'IA vers le libellé exact Pivot si reconnu."""
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
    """Règle : écran à partir de 43 pouces -> 2 techniciens."""
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
    """Chez Barron, 'PED' désigne toujours un TPE en France."""
    if not texte:
        return texte
    return re.sub(r"\bped\b", "TPE", texte, flags=re.IGNORECASE)


def fusionner_references_incident(ticket: Ticket) -> str:
    """Construit '[Barron McCann Reference] – [Customer Ref]'."""
    reference_barron = (ticket.intervention.code_projet or "").strip()
    reference_client = (ticket.intervention.numero_incident_client or "").strip()

    if reference_barron and reference_client:
        return f"{reference_barron} – {reference_client}"
    return reference_barron or reference_client


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """
    Enrichit un Ticket déjà extrait du mail avec les règles métier
    spécifiques à Barron McCann.

    `rag_decision` (optionnel) : une RagDecision déjà calculée en amont,
    transmise telle quelle au Rule Engine si celui-ci est activé.

    `activer_rule_engine` (par défaut False) : si True, exécute
    rule_engine.executer(ticket, rag_decision) et ajoute ses
    recommandations à commentaire_interne -- jamais à un champ métier.
    """
    notes: list[str] = []

    ticket.customer.client = "BARRON MAC CANN LTD"
    ticket.customer.numero_client = "BARRONM16"

    pays = ticket.customer.pays

    if est_france(pays):
        if ticket.customer.code_postal:
            ticket.customer.code_postal = normaliser_code_postal_fr(ticket.customer.code_postal)
        if ticket.customer.portable:
            ticket.customer.portable = normaliser_telephone_fr(ticket.customer.portable)
        if ticket.customer.fixe:
            ticket.customer.fixe = normaliser_telephone_fr(ticket.customer.fixe)

    groupe = get_groupe(ticket.customer.enseigne)
    infos_contrat = BARRON_CONTRACTS[groupe]

    ticket.intervention.type_intervention = "Contrat"
    ticket.intervention.contrat = infos_contrat["contrat"]
    ticket.intervention.type = infos_contrat["type"]
    ticket.intervention.categorie = infos_contrat["categorie"]

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

    if not ticket.intervention.code_projet and not ticket.intervention.numero_incident_client:
        notes.append("Ni 'Barron McCann Reference' ni 'Customer Ref' trouvées — Numéro d'incident client à compléter manuellement.")
    ticket.intervention.numero_incident_client = fusionner_references_incident(ticket)
    ticket.intervention.code_projet = ""

    ticket.intervention.origine = "Email"
    ticket.procedure.intervention_sur_site = True
    ticket.procedure.prise_rdv = False
    ticket.procedure.procedure = True
    ticket.validation.type_validation = "Client"

    if not pays:
        notes.append("Pays non renseigné — francophone supposé par défaut (technicien_anglophone=Non), à vérifier.")
    ticket.procedure.technicien_anglophone = not est_pays_francophone(pays)

    nombre_techniciens, note_deduction = deduire_nombre_techniciens(ticket)
    ticket.procedure.nombre_techniciens = nombre_techniciens
    if note_deduction:
        notes.append(note_deduction)

    ticket.intervention.problematique = remplacer_ped_par_tpe(ticket.intervention.problematique)
    ticket.intervention.intitule = remplacer_ped_par_tpe(ticket.intervention.intitule)
    ticket.procedure.travail_attendu = remplacer_ped_par_tpe(ticket.procedure.travail_attendu)
    ticket.procedure.consignes_mission = remplacer_ped_par_tpe(ticket.procedure.consignes_mission)

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

    if activer_rule_engine:
        recommandations = rule_engine.executer(ticket, rag_decision)
        bloc_recommandations = _formater_recommandations_rule_engine(recommandations)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_recommandations
        )

    return ticket