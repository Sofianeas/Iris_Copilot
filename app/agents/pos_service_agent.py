"""
Agent POS SERVICE.

Logique métier issue de TOKI_POS_SERVICE.txt (aucun .docx pour ce client).

POS SERVICE regroupe plusieurs enseignes (Geox, I Am, Six, Maxi Zoo,
Superdry, Gemo...), identifiables par un code à 3 lettres dans
l'intitulé/objet du mail : fre=Maxi Zoo, bee=I Am ou Six, geo=Geox
(d'autres codes existent -- ape/xpl/sup -- mais leur enseigne n'est pas
donnée dans TOKI -> non mappés, signalés).

4 sous-scénarios distincts, chacun avec son propre Contrat/règles :
  1. Maintenance Maxi Zoo : IRIS ne gère plus le stock matériel pour ce
     client -> Besoin de matériel = Non forcé, intervention à partir de
     10h00, consigne de vérifier le tracking colis avant planification.
  2. Maintenance autre enseigne : Contrat MAINTENANCE, pas de règle
     matériel forcée.
  3. Installation Maxi Zoo (nouveau magasin) : Contrat IMAC, pas de
     matériel, 2 techniciens, 7h.
  4. Démontage Geox : Contrat IMAC, pas de cartons à envoyer (tout sera
     sur place), 1 technicien, 2h, technicien anglophone, PAS de procédure.
  5. Réinstallation Geox : Contrat IMAC, 1 technicien, 4h, technicien
     anglophone, procédure (token), valider le numéro client à appeler.

⚠️ Hypothèses à vérifier :

  1. "Choix du contrat : MAINTENANCE" n'apparaît littéralement dans TOKI
     qu'après le cas "3.2 autre enseigne" -- j'ai supposé qu'il s'applique
     aussi au cas Maxi Zoo maintenance (3.1), faute de contrat alternatif
     documenté pour ce cas. À confirmer.
  2. Codes enseigne "ape"/"xpl"/"sup" sont mentionnés dans TOKI comme
     existants mais sans enseigne associée -> non mappés sur
     `customer.enseigne`, uniquement signalés.
  3. "Statut Pivot" (ex. "En cours - SANS pièce") n'a pas de champ dédié
     dans le `Ticket` actuel -> signalé en commentaire pour la couche
     Playwright/UI, pas appliqué à un champ.
  4. Détection du sous-scénario par mots-clés (installation/démontage/
     réinstallation + enseigne) -> toujours signalée comme une
     recommandation à confirmer, jamais appliquée en silence.

--- Intégration Rule Engine (cette étape) ---
  5. Ajout de 2 paramètres optionnels à `enrich_ticket` :
     `rag_decision: RagDecision | None = None` et
     `activer_rule_engine: bool = False`. Désactivé par défaut :
     rétrocompatibilité totale. POS_SERVICE n'a qu'UN SEUL point de
     sortie : le bloc Rule Engine n'est ajouté qu'une fois, en fin de
     fonction.
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


# --------------------------------------------------------------------------
# Référentiel POS SERVICE (issu de TOKI_POS_SERVICE.txt)
# --------------------------------------------------------------------------

CODE_VERS_ENSEIGNE = {
    "fre": "Maxi Zoo",
    "bee": "I Am ou Six",
    "geo": "Geox",
}
CODES_NON_MAPPES = ("ape", "xpl", "sup")

CONTRAT_MAINTENANCE = "MAINTENANCE"
CONTRAT_IMAC = "IMAC"

SCENARIO_MAXIZOO_INSTALLATION = "maxizoo_installation"
SCENARIO_GEOX_DEMONTAGE = "geox_demontage"
SCENARIO_GEOX_REINSTALLATION = "geox_reinstallation"
SCENARIO_MAXIZOO_MAINTENANCE = "maxizoo_maintenance"
SCENARIO_AUTRE_MAINTENANCE = "autre_maintenance"

LIBELLE_SCENARIO = {
    SCENARIO_MAXIZOO_INSTALLATION: "Installation Maxi Zoo (nouveau magasin)",
    SCENARIO_GEOX_DEMONTAGE: "Démontage Geox",
    SCENARIO_GEOX_REINSTALLATION: "Réinstallation Geox",
    SCENARIO_MAXIZOO_MAINTENANCE: "Maintenance Maxi Zoo",
    SCENARIO_AUTRE_MAINTENANCE: "Maintenance (autre enseigne)",
}

RE_CODE_ENSEIGNE = re.compile(r"\b(fre|bee|geo|ape|xpl|sup)\s*0*(\d+)\b", re.IGNORECASE)


def detecter_code_et_magasin(texte_mail: str) -> tuple[str, str]:
    """Code enseigne (3 lettres) + numéro de magasin (sans les lettres), cf. TOKI."""
    match = RE_CODE_ENSEIGNE.search(texte_mail or "")
    if not match:
        return "", ""
    return match.group(1).lower(), match.group(2)


def detecter_scenario(texte_mail: str, code_enseigne: str) -> str:
    """Déduit le sous-scénario POS SERVICE. RECOMMANDATION uniquement."""
    texte = _normaliser(texte_mail)
    est_maxizoo = code_enseigne == "fre" or "maxi zoo" in texte or "maxizoo" in texte
    est_geox = code_enseigne == "geo" or "geox" in texte

    if est_maxizoo and "installation" in texte and ("nouveau magasin" in texte or "ouverture" in texte):
        return SCENARIO_MAXIZOO_INSTALLATION
    if est_geox and ("demontage" in texte or "démontage" in texte):
        return SCENARIO_GEOX_DEMONTAGE
    if est_geox and ("reinstallation" in texte or "réinstallation" in texte or "installation" in texte):
        return SCENARIO_GEOX_REINSTALLATION
    if est_maxizoo:
        return SCENARIO_MAXIZOO_MAINTENANCE
    return SCENARIO_AUTRE_MAINTENANCE


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """
    Enrichit un Ticket déjà extrait du mail avec les règles métier POS SERVICE.

    `rag_decision` (optionnel) : une RagDecision déjà calculée en amont,
    transmise telle quelle au Rule Engine si celui-ci est activé.

    `activer_rule_engine` (par défaut False) : si True, exécute
    rule_engine.executer(ticket, rag_decision) et ajoute ses
    recommandations à commentaire_interne -- jamais à un champ métier.
    """
    notes: list[str] = []

    ticket.customer.client = "POS SERVICE"
    ticket.intervention.origine = "Email"
    ticket.intervention.type_intervention = "Contrat"

    code_enseigne, numero_magasin = detecter_code_et_magasin(texte_mail)
    if code_enseigne:
        if numero_magasin:
            ticket.customer.code_site = numero_magasin
        if code_enseigne in CODE_VERS_ENSEIGNE:
            ticket.customer.enseigne = CODE_VERS_ENSEIGNE[code_enseigne]
            if code_enseigne == "bee":
                notes.append("Code 'bee' = I Am OU Six (ambigu dans TOKI) — à confirmer manuellement.")
        elif code_enseigne in CODES_NON_MAPPES:
            notes.append(
                f"Code enseigne '{code_enseigne}' détecté mais non mappé (TOKI ne "
                f"donne pas l'enseigne associée) — à compléter manuellement."
            )
    else:
        notes.append("Code enseigne à 3 lettres introuvable dans le mail — enseigne/code site à vérifier manuellement.")

    scenario = detecter_scenario(texte_mail, code_enseigne)
    notes.append(
        f"⚠️ SCÉNARIO déduit automatiquement : « {LIBELLE_SCENARIO[scenario]} » — "
        f"À CONFIRMER avant saisie, une mauvaise détection fausse les champs ci-dessous."
    )

    if scenario == SCENARIO_MAXIZOO_MAINTENANCE:
        ticket.intervention.contrat = CONTRAT_MAINTENANCE
        ticket.logistics.besoin_materiel = False
        ticket.procedure.contrainte = "Intervention à partir de 10h00 (Maxi Zoo)"
        ticket.procedure.consignes_planification = _ajouter_si_absent(
            ticket.procedure.consignes_planification,
            "Vérifier le tracking du colis envoyé par le client avant de planifier "
            "l'intervention, pour confirmer la livraison du matériel (cf. 'PARTNER "
            "COMMENTS' du tableau reçu).",
        )
        if "onduleur" in _normaliser(texte_mail):
            ticket.procedure.prise_rdv = True
            notes.append(
                "Remplacement onduleur Maxi Zoo : prise de RDV avant ouverture du "
                "magasin, dossier à mettre en attente jusqu'à confirmation."
            )
        notes.append("Statut Pivot attendu : 'En cours - SANS pièce' (pas de champ dédié dans le Ticket, à saisir manuellement).")

    elif scenario == SCENARIO_AUTRE_MAINTENANCE:
        ticket.intervention.contrat = CONTRAT_MAINTENANCE
        notes.append("Statut Pivot attendu : 'En cours - sans pièce' (pas de champ dédié dans le Ticket, à saisir manuellement).")

    elif scenario == SCENARIO_MAXIZOO_INSTALLATION:
        ticket.intervention.contrat = CONTRAT_IMAC
        ticket.logistics.besoin_materiel = False
        ticket.procedure.nombre_techniciens = 2
        ticket.procedure.duree = "7h"
        ticket.procedure.intervention_sur_site = True

    elif scenario == SCENARIO_GEOX_DEMONTAGE:
        ticket.intervention.contrat = CONTRAT_IMAC
        ticket.procedure.nombre_techniciens = 1
        ticket.procedure.duree = "2h"
        ticket.procedure.technicien_anglophone = True
        ticket.procedure.procedure = False
        ticket.procedure.intervention_sur_site = True
        ticket.logistics.commentaire_logistique = _ajouter_si_absent(
            ticket.logistics.commentaire_logistique,
            "Pas de cartons à envoyer pour ce démontage : tout le matériel d'emballage sera déjà sur place.",
        )

    elif scenario == SCENARIO_GEOX_REINSTALLATION:
        ticket.intervention.contrat = CONTRAT_IMAC
        ticket.procedure.nombre_techniciens = 1
        ticket.procedure.duree = "4h"
        ticket.procedure.technicien_anglophone = True
        ticket.procedure.procedure = True
        ticket.procedure.intervention_sur_site = True
        if not ticket.validation.telephone_validation:
            notes.append("Numéro client à appeler pour validation d'intervention non trouvé — à compléter manuellement (cf. TOKI).")

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

"""
Agent POS SERVICE.

[... docstring métier inchangé ...]

--- Harmonisation Framework des Agents (P3-424) ---
Logique métier déplacée dans `_appliquer_regles_pos_service` (privée),
appelée par `PosServiceAgent.analyze()`. `analyze()` ne pilote jamais le
Rule Engine (Règle 9). `enrich_ticket()` reste un adaptateur de
compatibilité.
"""

import re
import unicodedata

from app.agents.base_agent import BaseAgent
from app.models.agent_contracts import AgentRequest, AgentResult
from app.models.rag_decision import RagDecision
from app.models.ticket import Ticket
from app.services import rule_engine


def _sans_accents(texte: str) -> str:
    if not texte:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )


def _normaliser(texte: str) -> str:
    return _sans_accents((texte or "").strip().lower())


def _ajouter_si_absent(texte_existant: str, bloc: str) -> str:
    if not bloc:
        return texte_existant
    if texte_existant and bloc in texte_existant:
        return texte_existant
    if texte_existant:
        return f"{texte_existant.strip()}\n\n{bloc}"
    return bloc


def _formater_recommandations_rule_engine(recommandations) -> str:
    if not recommandations:
        return ""
    lignes = ["🧩 Recommandations du Rule Engine (à vérifier, jamais appliquées automatiquement) :"]
    for reco in recommandations:
        lignes.append(
            f"- Champ '{reco.field}' -> '{reco.value}' "
            f"(confiance={reco.confidence:.2f}, source={reco.source}) : {reco.reason}"
        )
    return "\n".join(lignes)


CODE_VERS_ENSEIGNE = {"fre": "Maxi Zoo", "bee": "I Am ou Six", "geo": "Geox"}
CODES_NON_MAPPES = ("ape", "xpl", "sup")

CONTRAT_MAINTENANCE = "MAINTENANCE"
CONTRAT_IMAC = "IMAC"

SCENARIO_MAXIZOO_INSTALLATION = "maxizoo_installation"
SCENARIO_GEOX_DEMONTAGE = "geox_demontage"
SCENARIO_GEOX_REINSTALLATION = "geox_reinstallation"
SCENARIO_MAXIZOO_MAINTENANCE = "maxizoo_maintenance"
SCENARIO_AUTRE_MAINTENANCE = "autre_maintenance"

LIBELLE_SCENARIO = {
    SCENARIO_MAXIZOO_INSTALLATION: "Installation Maxi Zoo (nouveau magasin)",
    SCENARIO_GEOX_DEMONTAGE: "Démontage Geox",
    SCENARIO_GEOX_REINSTALLATION: "Réinstallation Geox",
    SCENARIO_MAXIZOO_MAINTENANCE: "Maintenance Maxi Zoo",
    SCENARIO_AUTRE_MAINTENANCE: "Maintenance (autre enseigne)",
}

RE_CODE_ENSEIGNE = re.compile(r"\b(fre|bee|geo|ape|xpl|sup)\s*0*(\d+)\b", re.IGNORECASE)


def detecter_code_et_magasin(texte_mail: str) -> tuple[str, str]:
    match = RE_CODE_ENSEIGNE.search(texte_mail or "")
    if not match:
        return "", ""
    return match.group(1).lower(), match.group(2)


def detecter_scenario(texte_mail: str, code_enseigne: str) -> str:
    texte = _normaliser(texte_mail)
    est_maxizoo = code_enseigne == "fre" or "maxi zoo" in texte or "maxizoo" in texte
    est_geox = code_enseigne == "geo" or "geox" in texte

    if est_maxizoo and "installation" in texte and ("nouveau magasin" in texte or "ouverture" in texte):
        return SCENARIO_MAXIZOO_INSTALLATION
    if est_geox and ("demontage" in texte or "démontage" in texte):
        return SCENARIO_GEOX_DEMONTAGE
    if est_geox and ("reinstallation" in texte or "réinstallation" in texte or "installation" in texte):
        return SCENARIO_GEOX_REINSTALLATION
    if est_maxizoo:
        return SCENARIO_MAXIZOO_MAINTENANCE
    return SCENARIO_AUTRE_MAINTENANCE


def _appliquer_regles_pos_service(ticket: Ticket, texte_mail: str = "") -> Ticket:
    """Logique métier POS SERVICE pure (extraite de l'ancien `enrich_ticket`, sans le bloc Rule Engine)."""
    notes: list[str] = []

    ticket.customer.client = "POS SERVICE"
    ticket.intervention.origine = "Email"
    ticket.intervention.type_intervention = "Contrat"

    code_enseigne, numero_magasin = detecter_code_et_magasin(texte_mail)
    if code_enseigne:
        if numero_magasin:
            ticket.customer.code_site = numero_magasin
        if code_enseigne in CODE_VERS_ENSEIGNE:
            ticket.customer.enseigne = CODE_VERS_ENSEIGNE[code_enseigne]
            if code_enseigne == "bee":
                notes.append("Code 'bee' = I Am OU Six (ambigu dans TOKI) — à confirmer manuellement.")
        elif code_enseigne in CODES_NON_MAPPES:
            notes.append(
                f"Code enseigne '{code_enseigne}' détecté mais non mappé (TOKI ne "
                f"donne pas l'enseigne associée) — à compléter manuellement."
            )
    else:
        notes.append("Code enseigne à 3 lettres introuvable dans le mail — enseigne/code site à vérifier manuellement.")

    scenario = detecter_scenario(texte_mail, code_enseigne)
    notes.append(
        f"⚠️ SCÉNARIO déduit automatiquement : « {LIBELLE_SCENARIO[scenario]} » — "
        f"À CONFIRMER avant saisie, une mauvaise détection fausse les champs ci-dessous."
    )

    if scenario == SCENARIO_MAXIZOO_MAINTENANCE:
        ticket.intervention.contrat = CONTRAT_MAINTENANCE
        ticket.logistics.besoin_materiel = False
        ticket.procedure.contrainte = "Intervention à partir de 10h00 (Maxi Zoo)"
        ticket.procedure.consignes_planification = _ajouter_si_absent(
            ticket.procedure.consignes_planification,
            "Vérifier le tracking du colis envoyé par le client avant de planifier "
            "l'intervention, pour confirmer la livraison du matériel (cf. 'PARTNER "
            "COMMENTS' du tableau reçu).",
        )
        if "onduleur" in _normaliser(texte_mail):
            ticket.procedure.prise_rdv = True
            notes.append(
                "Remplacement onduleur Maxi Zoo : prise de RDV avant ouverture du "
                "magasin, dossier à mettre en attente jusqu'à confirmation."
            )
        notes.append("Statut Pivot attendu : 'En cours - SANS pièce' (pas de champ dédié dans le Ticket, à saisir manuellement).")

    elif scenario == SCENARIO_AUTRE_MAINTENANCE:
        ticket.intervention.contrat = CONTRAT_MAINTENANCE
        notes.append("Statut Pivot attendu : 'En cours - sans pièce' (pas de champ dédié dans le Ticket, à saisir manuellement).")

    elif scenario == SCENARIO_MAXIZOO_INSTALLATION:
        ticket.intervention.contrat = CONTRAT_IMAC
        ticket.logistics.besoin_materiel = False
        ticket.procedure.nombre_techniciens = 2
        ticket.procedure.duree = "7h"
        ticket.procedure.intervention_sur_site = True

    elif scenario == SCENARIO_GEOX_DEMONTAGE:
        ticket.intervention.contrat = CONTRAT_IMAC
        ticket.procedure.nombre_techniciens = 1
        ticket.procedure.duree = "2h"
        ticket.procedure.technicien_anglophone = True
        ticket.procedure.procedure = False
        ticket.procedure.intervention_sur_site = True
        ticket.logistics.commentaire_logistique = _ajouter_si_absent(
            ticket.logistics.commentaire_logistique,
            "Pas de cartons à envoyer pour ce démontage : tout le matériel d'emballage sera déjà sur place.",
        )

    elif scenario == SCENARIO_GEOX_REINSTALLATION:
        ticket.intervention.contrat = CONTRAT_IMAC
        ticket.procedure.nombre_techniciens = 1
        ticket.procedure.duree = "4h"
        ticket.procedure.technicien_anglophone = True
        ticket.procedure.procedure = True
        ticket.procedure.intervention_sur_site = True
        if not ticket.validation.telephone_validation:
            notes.append("Numéro client à appeler pour validation d'intervention non trouvé — à compléter manuellement (cf. TOKI).")

    if notes:
        bloc_notes = "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_notes
        )

    return ticket


class PosServiceAgent(BaseAgent):
    """Agent POS SERVICE conforme au contrat BaseAgent. Cf. `_appliquer_regles_pos_service` pour la logique métier."""

    def analyze(self, request: AgentRequest) -> AgentResult:
        try:
            ticket = _appliquer_regles_pos_service(request.ticket, texte_mail=request.texte_mail)
            return AgentResult(ticket=ticket, succes=True)
        except Exception as exc:
            return AgentResult(ticket=request.ticket, succes=False, erreur=str(exc))


_AGENT = PosServiceAgent()


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """⚠️ ADAPTATEUR DE COMPATIBILITÉ -- délègue à PosServiceAgent.analyze(), reproduit ici l'ancien comportement de activer_rule_engine."""
    request = AgentRequest(ticket=ticket, texte_mail=texte_mail, rag_decision=rag_decision)
    result = _AGENT.analyze(request)
    ticket_resultat = result.ticket

    if activer_rule_engine:
        recommandations = rule_engine.executer(ticket_resultat, rag_decision)
        bloc_recommandations = _formater_recommandations_rule_engine(recommandations)
        ticket_resultat.intervention.commentaire_interne = _ajouter_si_absent(
            ticket_resultat.intervention.commentaire_interne, bloc_recommandations
        )
    return ticket_resultat