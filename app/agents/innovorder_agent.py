"""
Agent INNOVORDER.

Logique métier issue de INNOVORDER.docx (source primaire, process Pivot
actuel) + TOKI_INNOVORDER.txt (appoint, cf. hypothèse 1 ci-dessous).

- 4 Contrats possibles : Maintenance France / IMAC France / IMAC DOM-TOM /
  Logistique France. Seul "Maintenance France" est documenté en détail
  dans INNOVORDER.docx ; les 3 autres se limitent à "on remplit le ticket
  en fonction des informations" -> cet agent applique uniquement les
  règles communes pour ces 3-là, sans fabriquer de logique absente.
- Maintenance France : Type = "Autre" (seul choix), Type de ticket =
  Incident, Niveau de service "GTR 2J (5/7)" + planification J+2
  (cf. TOKI_INNOVORDER.txt), technicien anglophone = Non (France only par
  définition de ce contrat).
- L'enseigne est isolée depuis "Intitulé de la demande" (avant le premier
  tiret), PAS depuis un champ Enseigne dédié.
- IMPORTANT (couche Playwright, pas Ticket) : INNOVORDER.docx demande de
  vider les champs Site d'intervention/Contact pré-remplis dans Pivot
  avant saisie -> n'a pas de sens côté `Ticket` Python (objet toujours
  neuf), c'est une instruction pour l'automatisation UI, pas pour cet agent.

⚠️ Hypothèses à vérifier :

  1. TOKI_INNOVORDER.txt mentionne explicitement "FootPrints" (pas Pivot)
     pour la création du ticket et le PV d'intervention -> comme pour
     PROMETHEAN, ce TOKI pourrait décrire un ANCIEN process. Je n'ai retenu
     de TOKI que des faits métier non liés au système (ex. SLA "GTR 2J
     (5/7)"), pas les étapes de saisie elles-mêmes. À confirmer avec toi.
  2. INNOVORDER.docx réutilise mot pour mot la phrase "Sous-type" /
     "Date imposée sinon GTI 1J (5/7)" d'AEMSOFT.docx, alors qu'INNOVORDER
     n'a pas de concept de Sous-type ni de Type "Date imposée" documenté
     par ailleurs -> probable copier-coller depuis AEMSOFT.docx au moment
     de la rédaction. Ignoré ici (non appliqué), au profit du SLA "GTR 2J
     (5/7)" de TOKI qui est, lui, spécifique à INNOVORDER.
  3. Numéro d'incident client = chiffres en tout début de l'objet du mail,
     filet de sécurité regex sur texte_mail (suppose que l'objet est en
     tête de texte_mail, même hypothèse que pour les agents précédents).
  4. "Besoin de matériel ? : Oui si Sous-type = AVEC pièces expédiées par
     IRIS" (INNOVORDER.docx) n'est pas applicable ici (pas de Sous-type
     documenté) -> non automatisé, laissé à l'extraction/validation humaine.
  5. Lien de procédure : choix via Token Drive selon le type de panne,
     aucune table panne -> token disponible -> non automatisé (comme BUT).

--- Intégration Rule Engine (cette étape) ---
  6. Ajout de 2 paramètres optionnels à `enrich_ticket` :
     `rag_decision: RagDecision | None = None` et
     `activer_rule_engine: bool = False`. Désactivé par défaut :
     rétrocompatibilité totale. INNOVORDER n'a qu'UN SEUL point de sortie :
     le bloc Rule Engine n'est ajouté qu'une fois, en fin de fonction.
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
# Référentiel INNOVORDER
# --------------------------------------------------------------------------

CONTRAT_MAINTENANCE_FRANCE = "Maintenance France"
CONTRAT_IMAC_FRANCE = "IMAC France"
CONTRAT_IMAC_DOMTOM = "IMAC DOM-TOM"
CONTRAT_LOGISTIQUE_FRANCE = "Logistique France"

NIVEAU_SERVICE_MAINTENANCE = "GTR 2J (5/7)"  # cf. TOKI_INNOVORDER.txt, hypothèse 1/2

MOTS_CLES_DOMTOM = (
    "dom-tom", "dom tom", "guadeloupe", "martinique", "reunion", "mayotte",
    "guyane", "polynesie", "nouvelle caledonie", "saint martin", "saint barthelemy",
)

RE_DIGITS_DEBUT = re.compile(r"^\s*(\d+)")


def detecter_contrat(texte_mail: str) -> tuple[str, bool]:
    """
    Déduit le Contrat (Maintenance France / IMAC France / IMAC DOM-TOM /
    Logistique France). Retourne (contrat, detecte_explicitement).
    """
    texte = _normaliser(texte_mail)
    if "logistique" in texte:
        return CONTRAT_LOGISTIQUE_FRANCE, True
    if "imac" in texte:
        if any(mot in texte for mot in MOTS_CLES_DOMTOM):
            return CONTRAT_IMAC_DOMTOM, True
        return CONTRAT_IMAC_FRANCE, True
    return CONTRAT_MAINTENANCE_FRANCE, False


def extraire_enseigne_depuis_intitule(intitule_brut: str) -> str:
    """Isole l'enseigne depuis "Intitulé de la demande", avant le 1er tiret."""
    if not intitule_brut:
        return ""
    segment = re.split(r"\s[-–]\s", intitule_brut)[0]
    return segment.strip().upper()


def extraire_numero_incident_depuis_objet(texte_mail: str) -> str:
    """Chiffres en tout début de l'objet du mail (filet de sécurité)."""
    if not texte_mail:
        return ""
    match = RE_DIGITS_DEBUT.match(texte_mail.strip())
    return match.group(1) if match else ""


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """
    Enrichit un Ticket déjà extrait du mail avec les règles métier INNOVORDER.

    `rag_decision` (optionnel) : une RagDecision déjà calculée en amont,
    transmise telle quelle au Rule Engine si celui-ci est activé.

    `activer_rule_engine` (par défaut False) : si True, exécute
    rule_engine.executer(ticket, rag_decision) et ajoute ses
    recommandations à commentaire_interne -- jamais à un champ métier.
    """
    notes: list[str] = []

    ticket.customer.client = "INNOVORDER"

    enseigne_isolee = extraire_enseigne_depuis_intitule(ticket.intervention.intitule)
    if enseigne_isolee:
        ticket.customer.enseigne = enseigne_isolee
    else:
        notes.append(
            "Enseigne non isolée depuis 'Intitulé de la demande' (champ vide ou "
            "sans séparateur ' - ') — à vérifier/compléter manuellement."
        )

    ticket.intervention.type_intervention = "Contrat"
    contrat, detecte_explicitement = detecter_contrat(texte_mail)
    ticket.intervention.contrat = contrat
    ticket.intervention.origine = "Email"
    if not detecte_explicitement:
        notes.append(
            f"Contrat '{contrat}' retenu PAR DÉFAUT, faute de mot-clé 'IMAC' ou "
            f"'Logistique' dans le mail — à vérifier avant saisie."
        )

    if contrat == CONTRAT_MAINTENANCE_FRANCE:
        ticket.intervention.type = "Autre"
        ticket.intervention.type_ticket = "Incident"
        ticket.intervention.niveau_priorite = NIVEAU_SERVICE_MAINTENANCE
        ticket.procedure.technicien_anglophone = False
        ticket.procedure.intervention_sur_site = True
        ticket.procedure.prise_rdv = False
        ticket.procedure.procedure = True

        numero_incident = ticket.intervention.numero_incident_client or extraire_numero_incident_depuis_objet(texte_mail)
        if numero_incident:
            ticket.intervention.numero_incident_client = numero_incident
        else:
            notes.append(
                "Numéro d'incident client introuvable (ni chiffres en début d'objet, "
                "ni champ 'Numéro d'incident Innovorder') — à compléter manuellement."
            )

        if ticket.customer.enseigne:
            ville = ticket.customer.ville or ""
            parts = ["Maintenance", ticket.customer.enseigne]
            if ville:
                parts.append(ville)
            ticket.intervention.intitule = " ".join(p for p in parts if p)
            notes.append(
                "Intitulé construit sans le segment [matériel] (ex. docx : "
                "'Maintenance Imprimante Ticket – LA FLAMME MARSEILLE') — aucune "
                "règle de détection du matériel n'est documentée pour INNOVORDER, "
                "à compléter manuellement si besoin."
            )

        notes.append(
            "Niveau de service 'GTR 2J (5/7)' et planification J+2 appliqués depuis "
            "TOKI_INNOVORDER.txt (le docx référence par erreur des concepts AEMSOFT "
            "non applicables ici, cf. hypothèse 2) — à confirmer."
        )

    elif contrat in (CONTRAT_IMAC_FRANCE, CONTRAT_IMAC_DOMTOM, CONTRAT_LOGISTIQUE_FRANCE):
        notes.append(
            f"Contrat '{contrat}' détecté : INNOVORDER.docx ne documente pas de règle "
            f"détaillée pour ce contrat ('on remplit le ticket en fonction des "
            f"informations') — seules les règles communes (client, contrat, origine) "
            f"ont été appliquées, le reste vient de l'extraction brute."
        )
        if contrat == CONTRAT_LOGISTIQUE_FRANCE and ticket.logistics.retour_piece:
            notes.append(
                "Retour de matériel mentionné (Logistique France) — vérifier "
                "attentivement l'adresse de renvoi (cf. INNOVORDER.docx)."
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

"""
Agent INNOVORDER.

[... docstring métier inchangé ...]

--- Harmonisation Framework des Agents (P3-424) ---
Logique métier déplacée dans `_appliquer_regles_innovorder` (privée),
appelée par `InnovorderAgent.analyze()`. `analyze()` ne pilote jamais le
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


CONTRAT_MAINTENANCE_FRANCE = "Maintenance France"
CONTRAT_IMAC_FRANCE = "IMAC France"
CONTRAT_IMAC_DOMTOM = "IMAC DOM-TOM"
CONTRAT_LOGISTIQUE_FRANCE = "Logistique France"

NIVEAU_SERVICE_MAINTENANCE = "GTR 2J (5/7)"

MOTS_CLES_DOMTOM = (
    "dom-tom", "dom tom", "guadeloupe", "martinique", "reunion", "mayotte",
    "guyane", "polynesie", "nouvelle caledonie", "saint martin", "saint barthelemy",
)

RE_DIGITS_DEBUT = re.compile(r"^\s*(\d+)")


def detecter_contrat(texte_mail: str) -> tuple[str, bool]:
    texte = _normaliser(texte_mail)
    if "logistique" in texte:
        return CONTRAT_LOGISTIQUE_FRANCE, True
    if "imac" in texte:
        if any(mot in texte for mot in MOTS_CLES_DOMTOM):
            return CONTRAT_IMAC_DOMTOM, True
        return CONTRAT_IMAC_FRANCE, True
    return CONTRAT_MAINTENANCE_FRANCE, False


def extraire_enseigne_depuis_intitule(intitule_brut: str) -> str:
    if not intitule_brut:
        return ""
    segment = re.split(r"\s[-–]\s", intitule_brut)[0]
    return segment.strip().upper()


def extraire_numero_incident_depuis_objet(texte_mail: str) -> str:
    if not texte_mail:
        return ""
    match = RE_DIGITS_DEBUT.match(texte_mail.strip())
    return match.group(1) if match else ""


def _appliquer_regles_innovorder(ticket: Ticket, texte_mail: str = "") -> Ticket:
    """Logique métier INNOVORDER pure (extraite de l'ancien `enrich_ticket`, sans le bloc Rule Engine)."""
    notes: list[str] = []

    ticket.customer.client = "INNOVORDER"

    enseigne_isolee = extraire_enseigne_depuis_intitule(ticket.intervention.intitule)
    if enseigne_isolee:
        ticket.customer.enseigne = enseigne_isolee
    else:
        notes.append(
            "Enseigne non isolée depuis 'Intitulé de la demande' (champ vide ou "
            "sans séparateur ' - ') — à vérifier/compléter manuellement."
        )

    ticket.intervention.type_intervention = "Contrat"
    contrat, detecte_explicitement = detecter_contrat(texte_mail)
    ticket.intervention.contrat = contrat
    ticket.intervention.origine = "Email"
    if not detecte_explicitement:
        notes.append(
            f"Contrat '{contrat}' retenu PAR DÉFAUT, faute de mot-clé 'IMAC' ou "
            f"'Logistique' dans le mail — à vérifier avant saisie."
        )

    if contrat == CONTRAT_MAINTENANCE_FRANCE:
        ticket.intervention.type = "Autre"
        ticket.intervention.type_ticket = "Incident"
        ticket.intervention.niveau_priorite = NIVEAU_SERVICE_MAINTENANCE
        ticket.procedure.technicien_anglophone = False
        ticket.procedure.intervention_sur_site = True
        ticket.procedure.prise_rdv = False
        ticket.procedure.procedure = True

        numero_incident = ticket.intervention.numero_incident_client or extraire_numero_incident_depuis_objet(texte_mail)
        if numero_incident:
            ticket.intervention.numero_incident_client = numero_incident
        else:
            notes.append(
                "Numéro d'incident client introuvable (ni chiffres en début d'objet, "
                "ni champ 'Numéro d'incident Innovorder') — à compléter manuellement."
            )

        if ticket.customer.enseigne:
            ville = ticket.customer.ville or ""
            parts = ["Maintenance", ticket.customer.enseigne]
            if ville:
                parts.append(ville)
            ticket.intervention.intitule = " ".join(p for p in parts if p)
            notes.append(
                "Intitulé construit sans le segment [matériel] (ex. docx : "
                "'Maintenance Imprimante Ticket – LA FLAMME MARSEILLE') — aucune "
                "règle de détection du matériel n'est documentée pour INNOVORDER, "
                "à compléter manuellement si besoin."
            )

        notes.append(
            "Niveau de service 'GTR 2J (5/7)' et planification J+2 appliqués depuis "
            "TOKI_INNOVORDER.txt (le docx référence par erreur des concepts AEMSOFT "
            "non applicables ici) — à confirmer."
        )

    elif contrat in (CONTRAT_IMAC_FRANCE, CONTRAT_IMAC_DOMTOM, CONTRAT_LOGISTIQUE_FRANCE):
        notes.append(
            f"Contrat '{contrat}' détecté : INNOVORDER.docx ne documente pas de règle "
            f"détaillée pour ce contrat ('on remplit le ticket en fonction des "
            f"informations') — seules les règles communes (client, contrat, origine) "
            f"ont été appliquées, le reste vient de l'extraction brute."
        )
        if contrat == CONTRAT_LOGISTIQUE_FRANCE and ticket.logistics.retour_piece:
            notes.append(
                "Retour de matériel mentionné (Logistique France) — vérifier "
                "attentivement l'adresse de renvoi (cf. INNOVORDER.docx)."
            )

    if notes:
        bloc_notes = "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_notes
        )

    return ticket


class InnovorderAgent(BaseAgent):
    """Agent INNOVORDER conforme au contrat BaseAgent. Cf. `_appliquer_regles_innovorder` pour la logique métier."""

    def analyze(self, request: AgentRequest) -> AgentResult:
        try:
            ticket = _appliquer_regles_innovorder(request.ticket, texte_mail=request.texte_mail)
            return AgentResult(ticket=ticket, succes=True)
        except Exception as exc:
            return AgentResult(ticket=request.ticket, succes=False, erreur=str(exc))


_AGENT = InnovorderAgent()


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """⚠️ ADAPTATEUR DE COMPATIBILITÉ -- délègue à InnovorderAgent.analyze(), reproduit ici l'ancien comportement de activer_rule_engine."""
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