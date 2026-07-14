"""
Agent ADOPT.

Logique métier issue de ADOPT.docx + TOKI_ADOPT.txt :
- Le pays (texte libre dans le mail) détermine le contrat applicable.
- Seule la France a un choix Maintenance/Installation ; les autres pays
  sont toujours en Installation.
- Le matériel envoyé dépend du pays (règles différentes France/Belgique/autres).
- Le cas CATO (boîtier projet) est rare : on le signale, on ne l'automatise pas.

--- Version durcie (relecture post-AEMSOFT/AMPLIFON/etc.) ---
Corrige 3 points par rapport à la version initiale :
  1. `commentaire_logistique` n'est plus écrasé (cable/vis) -> idempotent
     via `_ajouter_si_absent`, comme les agents écrits depuis.
  2. Pays non reconnu (hors France/Espagne/Pologne/Belgique/Italie) :
     auparavant retombait sur le contrat France EN SILENCE -> maintenant
     signalé explicitement dans `commentaire_interne`, le contrat France
     reste appliqué par défaut mais comme un choix visible, pas une
     hypothèse cachée.
  3. Ajout du système de `notes` consolidées dans `commentaire_interne`,
     pour rester cohérent avec aemsoft_agent.py / amplifon_agent.py / etc.
     (la déduction "écran >=43'' -> 2 techniciens" est maintenant signalée).
  4. Cas CATO : `customer.client` est désormais renseigné même dans la
     branche d'arrêt anticipé (oubli dans la version initiale).

--- Intégration Rule Engine (cette étape) ---
  5. Ajout de 2 paramètres optionnels à `enrich_ticket` :
     `rag_decision: RagDecision | None = None` et
     `activer_rule_engine: bool = False`. Désactivé par défaut :
     rétrocompatibilité totale avec tous les appels existants.
     ⚠️ ADOPT a DEUX points de sortie (`return ticket` dans la branche
     CATO, et `return ticket` en fin de fonction) -- le bloc Rule Engine
     est dupliqué dans les deux, sinon `activer_rule_engine=True`
     n'aurait aucun effet pour les mails détectés comme CATO.
"""

import re
import unicodedata

from app.models.ticket import Ticket
from app.models.rag_decision import RagDecision
from app.services import rule_engine


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


def _formater_recommandations_rule_engine(recommandations) -> str:
    """
    Formate les RuleRecommendation (rule_engine.executer) en un bloc de
    texte destiné à commentaire_interne -- ne modifie JAMAIS un champ
    métier directement (même politique que sur aemsoft_agent.py).
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


CONTRAT_FRANCE = "On Demand France"
CONTRAT_ESPAGNE_POLOGNE = "On Demand Espagne/Pologne"
CONTRAT_BELGIQUE = "On Demand Belgique"
CONTRAT_ITALIE = "On Demand Italie"
CONTRAT_CATO = "Installation Boîtier CATO (Projet)"

PAYS_VERS_CONTRAT = {
    "france": CONTRAT_FRANCE,
    "fr": CONTRAT_FRANCE,
    "espagne": CONTRAT_ESPAGNE_POLOGNE,
    "spain": CONTRAT_ESPAGNE_POLOGNE,
    "pologne": CONTRAT_ESPAGNE_POLOGNE,
    "poland": CONTRAT_ESPAGNE_POLOGNE,
    "belgique": CONTRAT_BELGIQUE,
    "belgium": CONTRAT_BELGIQUE,
    "italie": CONTRAT_ITALIE,
    "italy": CONTRAT_ITALIE,
}

REFERENCE_CABLE_RESEAU = "CAB-RJ-CAT6"
COULEURS_CABLE_PAR_DEFAUT = ("Gris", "Noir", "Blanc")

REFERENCE_VIS = "B0CNL85C92"


def detecter_cato(texte_mail: str) -> bool:
    """Détecte une demande d'installation de boîtier CATO."""
    texte_normalise = _sans_accents(texte_mail or "").lower()
    return "cato" in texte_normalise


def normaliser_pays(pays_brut: str) -> str:
    return _normaliser(pays_brut)


def get_contrat(pays_brut: str) -> tuple[str, bool]:
    pays_normalise = normaliser_pays(pays_brut)
    if pays_normalise in PAYS_VERS_CONTRAT:
        return PAYS_VERS_CONTRAT[pays_normalise], True
    return CONTRAT_FRANCE, False


def est_france(pays_brut: str) -> bool:
    return normaliser_pays(pays_brut) in ("france", "fr")


def est_belgique(pays_brut: str) -> bool:
    return normaliser_pays(pays_brut) in ("belgique", "belgium")


def deduire_nombre_techniciens(ticket: Ticket) -> tuple[int, str]:
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


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    notes: list[str] = []

    ticket.customer.client = "ADOPT"

    if detecter_cato(texte_mail):
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne,
            "ATTENTION : demande détectée comme Installation Boîtier CATO (Projet). "
            "Ne pas traiter automatiquement — voir avec Anne ou David via Teams "
            "(conversation CDS Alger) avant de poursuivre.",
        )
        if activer_rule_engine:
            recommandations = rule_engine.executer(ticket, rag_decision)
            bloc_recommandations = _formater_recommandations_rule_engine(recommandations)
            ticket.intervention.commentaire_interne = _ajouter_si_absent(
                ticket.intervention.commentaire_interne, bloc_recommandations
            )
        return ticket

    pays = ticket.customer.pays

    ticket.intervention.type_intervention = "Contrat"
    contrat, pays_reconnu = get_contrat(pays)
    ticket.intervention.contrat = contrat
    if not pays_reconnu:
        notes.append(
            f"Pays {pays!r} non reconnu parmi les contrats ADOPT documentés "
            f"(France/Espagne/Pologne/Belgique/Italie) — contrat France appliqué "
            f"par défaut, À VÉRIFIER avant saisie."
        )

    if est_france(pays):
        if not ticket.intervention.type:
            ticket.intervention.type = "Installation"
    else:
        ticket.intervention.type = "Installation"

    ticket.intervention.origine = "Email"
    ticket.logistics.integration_a_faire = False
    ticket.logistics.retour_piece = "Non"
    ticket.procedure.intervention_sur_site = True
    ticket.procedure.prise_rdv = False
    ticket.procedure.procedure = True
    ticket.validation.type_validation = "Client"

    if est_france(pays):
        if ticket.logistics.besoin_materiel and ticket.logistics.pieces:
            pieces_lower = ticket.logistics.pieces.lower()
            if "cable" in _sans_accents(pieces_lower) or "câble" in pieces_lower:
                ticket.logistics.commentaire_logistique = _ajouter_si_absent(
                    ticket.logistics.commentaire_logistique,
                    f"Référence câble réseau : {REFERENCE_CABLE_RESEAU}-*M-*. "
                    f"Vérifier longueur dans le mail. "
                    f"Couleur par défaut si non précisée : {'/'.join(COULEURS_CABLE_PAR_DEFAUT)}.",
                )
            if "vis" in pieces_lower:
                ticket.logistics.commentaire_logistique = _ajouter_si_absent(
                    ticket.logistics.commentaire_logistique,
                    f"Référence vis M4x25 : {REFERENCE_VIS}.",
                )

    elif est_belgique(pays):
        ticket.logistics.commentaire_logistique = _ajouter_si_absent(
            ticket.logistics.commentaire_logistique,
            "Belgique : ne pas décider seul — demander au Responsable de Compte "
            "si le matériel doit être envoyé.",
        )

    else:
        ticket.logistics.besoin_materiel = False
        if not ticket.procedure.autre_outillage and ticket.logistics.pieces:
            ticket.procedure.autre_outillage = ticket.logistics.pieces
        ticket.logistics.pieces = ""

    nombre_techniciens, note_deduction = deduire_nombre_techniciens(ticket)
    ticket.procedure.nombre_techniciens = nombre_techniciens
    if note_deduction:
        notes.append(note_deduction)

    ticket.procedure.technicien_anglophone = not est_france(pays)

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