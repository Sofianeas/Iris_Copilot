"""
Agent SHOPPERTRAK.

⚠️ VERSION 1 PARTIELLE -- pas de documentation officielle pour ce client
(ni .docx ni TOKI). Construit à partir de 3 exemples de mails réels fournis
par Sofiane + une capture d'écran du sélecteur de Contrat Pivot. Sofiane a
explicitement indiqué qu'il manque encore "2 ou 3 détails" pour d'autres
champs (Type/Sous-type, Matériel, Planification, Consignes et mission...)
qu'il communiquera ultérieurement -- cet agent ne couvre QUE ce qui a été
spécifié à ce jour : Site d'intervention, Contact, Contrat (par pays), et
Intitulé. Le reste n'est volontairement pas traité (pas de fabrication de
règle absente).

Format des mails ShopperTrak (Sensormatic / Diogo Lopes, "INTER RETAIL") :
  INTER
  RETAIL
  <Enseigne>
  <Code site>
  <Numéro incident client>
  <Pays>
  <Ville>
  <Adresse>
  <Code postal>
  <Problématique et demande (texte libre, jusqu'à la signature du mail)>

Chaque champ ci-dessus peut apparaître AVEC un libellé explicite (ex.
"Pays : FRANCE") OU EN VALEUR BRUTE SEULE (ex. juste "FRANCE") -- les 2
formats coexistent dans les exemples fournis. L'ORDRE est fixe dans les 3
exemples observés ; c'est sur cet ordre que repose l'extraction (pas sur
la présence de libellés, peu fiable).

Contrat : déterminé par le Pays (capture d'écran Pivot du 29/06/2026) --
correspond exactement au périmètre du signataire des mails ("Client
Support France & BeNeLux & Nordics") : France, Belgique, Pays-Bas,
Luxembourg (BeNeLux) + Danemark, Suède, Finlande, Norvège (Nordics).

⚠️ Hypothèses à vérifier :
  1. La liste de 8 pays est déduite de la capture d'écran ET du signataire
     des mails -- mais la liste Pivot pourrait comporter d'autres pays non
     visibles (scroll de la capture). À confirmer.
  2. L'Intitulé : le "<titre>" n'a pas de champ dédié dans le mail --
     j'utilise "Maintenance caméra" par défaut quand le texte mentionne
     une caméra, sinon je laisse cette partie vide et je signale.
  3. Aucune règle pour Type/Sous-type/Matériel/Planification/Consignes et
     mission -- en attente des précisions de Sofiane.

--- Intégration Rule Engine (cette étape) ---
  4. Ajout de 2 paramètres optionnels à `enrich_ticket` :
     `rag_decision: RagDecision | None = None` et
     `activer_rule_engine: bool = False`. Désactivé par défaut :
     rétrocompatibilité totale. SHOPPERTRAK n'a qu'UN SEUL point de
     sortie : le bloc Rule Engine n'est ajouté qu'une fois, en fin de
     fonction. Cette intégration est indépendante de l'incomplétude
     métier de l'agent (elle ne comble aucun des champs manquants
     mentionnés ci-dessus, elle ajoute uniquement des recommandations).
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


PAYS_VERS_CONTRAT = {
    "france": "OD.SHOPPE25.001.1 - ON DEMAND FRANCE (ON DEMAND)",
    "belgique": "OD.SHOPPE25.001.1 - ON DEMAND BELGIQUE (ON DEMAND)",
    "pays-bas": "OD.SHOPPE25.001.1 - ON DEMAND PAYS-BAS (ON DEMAND)",
    "luxembourg": "OD.SHOPPE25.001.1 - ON DEMAND LUXEMBOURG (ON DEMAND)",
    "danemark": "OD.SHOPPE25.001.1 - ON DEMAND DANEMARK (ON DEMAND)",
    "suede": "OD.SHOPPE25.001.1 - ON DEMAND SUEDE (ON DEMAND)",
    "finlande": "OD.SHOPPE25.001.1 - ON DEMAND FINLANDE (ON DEMAND)",
    "norvege": "OD.SHOPPE25.001.1 - ON DEMAND NORVEGE (ON DEMAND)",
}

CHAMPS_ORDRE = [
    ("enseigne", ("enseigne", "enseuigne")),
    ("code_site", ("code site",)),
    ("numero_incident_client", ("numero incident client", "numéro incident client")),
    ("pays", ("pays",)),
    ("ville", ("ville",)),
    ("adresse", ("adresse",)),
    ("code_postal", ("code postal",)),
]

RE_ANCRE_INTER_RETAIL = re.compile(r"^\s*I?NTER\s*\n\s*RETAIL\s*\n", re.IGNORECASE | re.MULTILINE)


def nettoyer_valeur_champ(ligne: str, motifs_labels: tuple) -> str:
    """Retire un préfixe de label optionnel (ex: 'Pays : FRANCE' -> 'FRANCE')."""
    ligne = (ligne or "").strip()
    for motif in motifs_labels:
        pattern = re.compile(rf"^{motif}(?:\s*:\s*|\s+)", re.IGNORECASE)
        nouvelle = pattern.sub("", ligne)
        if nouvelle != ligne:
            return nouvelle.strip()
    return ligne


def extraire_champs_shoppertrak(texte: str) -> dict:
    """Extrait les 7 champs positionnels + la Problématique et demande."""
    if not texte:
        return {}

    match_ancre = RE_ANCRE_INTER_RETAIL.search(texte)
    reste = texte[match_ancre.end():] if match_ancre else texte
    lignes = reste.splitlines()

    resultat: dict[str, str] = {}
    index_ligne = 0
    for cle, motifs_labels in CHAMPS_ORDRE:
        while index_ligne < len(lignes) and not lignes[index_ligne].strip():
            index_ligne += 1
        if index_ligne >= len(lignes):
            break
        resultat[cle] = nettoyer_valeur_champ(lignes[index_ligne], motifs_labels)
        index_ligne += 1

    texte_restant = "\n".join(lignes[index_ligne:]).strip()
    texte_restant = nettoyer_valeur_champ(texte_restant, ("problematique et demande", "problématique et demande"))
    texte_restant = re.split(r"\n\s*(merci|cordialement|regards)\b", texte_restant, flags=re.IGNORECASE)[0]
    resultat["problematique"] = texte_restant.strip()

    return resultat


def construire_intitule(enseigne: str, ville: str, code_site: str, problematique: str) -> tuple[str, bool]:
    """"Enseigne Ville Code Site - <titre de la demande>"."""
    base = " ".join(p for p in (enseigne, ville, code_site) if p)
    if "camera" in _normaliser(problematique) or "caméra" in problematique.lower():
        return f"{base} - Maintenance caméra", True
    return base, False


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """
    Enrichit un Ticket avec les règles SHOPPERTRAK connues à ce jour.
    Volontairement incomplet.

    `rag_decision` (optionnel) : une RagDecision déjà calculée en amont,
    transmise telle quelle au Rule Engine si celui-ci est activé.

    `activer_rule_engine` (par défaut False) : si True, exécute
    rule_engine.executer(ticket, rag_decision) et ajoute ses
    recommandations à commentaire_interne -- jamais à un champ métier.
    """
    notes: list[str] = []

    champs = extraire_champs_shoppertrak(texte_mail)

    ticket.customer.client = "SHOPPERTRAK"
    ticket.customer.enseigne = champs.get("enseigne", "")
    ticket.customer.code_site = champs.get("code_site", "")
    ticket.customer.adresse = champs.get("adresse", "")
    ticket.customer.code_postal = champs.get("code_postal", "")
    ticket.customer.ville = champs.get("ville", "")
    ticket.customer.pays = champs.get("pays", "")

    ticket.intervention.numero_incident_client = champs.get("numero_incident_client", "")
    ticket.intervention.problematique = champs.get("problematique", "")
    ticket.intervention.origine = "Email"
    ticket.intervention.type_intervention = "Contrat"

    pays_normalise = _normaliser(champs.get("pays", ""))
    contrat = PAYS_VERS_CONTRAT.get(pays_normalise, "")
    if contrat:
        ticket.intervention.contrat = contrat
    else:
        notes.append(
            f"Pays {champs.get('pays', '')!r} non reconnu parmi les 8 pays connus "
            f"(France/Belgique/Pays-Bas/Luxembourg/Danemark/Suède/Finlande/Norvège) "
            f"— Contrat à sélectionner manuellement, cf. hypothèse 1."
        )

    intitule, titre_devine = construire_intitule(
        ticket.customer.enseigne, ticket.customer.ville, ticket.customer.code_site, ticket.intervention.problematique
    )
    ticket.intervention.intitule = intitule
    if not titre_devine:
        notes.append(
            "Titre de la demande (ex. 'Maintenance caméra') non déterminé depuis la "
            "Problématique — à compléter manuellement dans l'Intitulé, cf. hypothèse 2."
        )

    notes.append(
        "⚠️ Agent SHOPPERTRAK volontairement incomplet : Type/Sous-type, Matériel, "
        "Planification et Consignes et mission ne sont pas encore couverts (règles "
        "en attente de précisions de Sofiane) — ne pas considérer ce ticket comme "
        "prêt à saisir sans compléter ces champs manuellement."
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
Agent SHOPPERTRAK.

⚠️ VERSION 1 PARTIELLE -- [... docstring métier inchangé ...]

--- Harmonisation Framework des Agents (P3-424) ---
Logique métier déplacée dans `_appliquer_regles_shoppertrak` (privée),
appelée par `ShoppertrakAgent.analyze()`. `analyze()` ne pilote jamais le
Rule Engine (Règle 9). `enrich_ticket()` reste un adaptateur de
compatibilité. Incomplétude métier volontaire de cet agent (cf.
avertissement du docstring) inchangée par cette harmonisation.
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


PAYS_VERS_CONTRAT = {
    "france": "OD.SHOPPE25.001.1 - ON DEMAND FRANCE (ON DEMAND)",
    "belgique": "OD.SHOPPE25.001.1 - ON DEMAND BELGIQUE (ON DEMAND)",
    "pays-bas": "OD.SHOPPE25.001.1 - ON DEMAND PAYS-BAS (ON DEMAND)",
    "luxembourg": "OD.SHOPPE25.001.1 - ON DEMAND LUXEMBOURG (ON DEMAND)",
    "danemark": "OD.SHOPPE25.001.1 - ON DEMAND DANEMARK (ON DEMAND)",
    "suede": "OD.SHOPPE25.001.1 - ON DEMAND SUEDE (ON DEMAND)",
    "finlande": "OD.SHOPPE25.001.1 - ON DEMAND FINLANDE (ON DEMAND)",
    "norvege": "OD.SHOPPE25.001.1 - ON DEMAND NORVEGE (ON DEMAND)",
}

CHAMPS_ORDRE = [
    ("enseigne", ("enseigne", "enseuigne")),
    ("code_site", ("code site",)),
    ("numero_incident_client", ("numero incident client", "numéro incident client")),
    ("pays", ("pays",)),
    ("ville", ("ville",)),
    ("adresse", ("adresse",)),
    ("code_postal", ("code postal",)),
]

RE_ANCRE_INTER_RETAIL = re.compile(r"^\s*I?NTER\s*\n\s*RETAIL\s*\n", re.IGNORECASE | re.MULTILINE)


def nettoyer_valeur_champ(ligne: str, motifs_labels: tuple) -> str:
    ligne = (ligne or "").strip()
    for motif in motifs_labels:
        pattern = re.compile(rf"^{motif}(?:\s*:\s*|\s+)", re.IGNORECASE)
        nouvelle = pattern.sub("", ligne)
        if nouvelle != ligne:
            return nouvelle.strip()
    return ligne


def extraire_champs_shoppertrak(texte: str) -> dict:
    if not texte:
        return {}

    match_ancre = RE_ANCRE_INTER_RETAIL.search(texte)
    reste = texte[match_ancre.end():] if match_ancre else texte
    lignes = reste.splitlines()

    resultat: dict[str, str] = {}
    index_ligne = 0
    for cle, motifs_labels in CHAMPS_ORDRE:
        while index_ligne < len(lignes) and not lignes[index_ligne].strip():
            index_ligne += 1
        if index_ligne >= len(lignes):
            break
        resultat[cle] = nettoyer_valeur_champ(lignes[index_ligne], motifs_labels)
        index_ligne += 1

    texte_restant = "\n".join(lignes[index_ligne:]).strip()
    texte_restant = nettoyer_valeur_champ(texte_restant, ("problematique et demande", "problématique et demande"))
    texte_restant = re.split(r"\n\s*(merci|cordialement|regards)\b", texte_restant, flags=re.IGNORECASE)[0]
    resultat["problematique"] = texte_restant.strip()

    return resultat


def construire_intitule(enseigne: str, ville: str, code_site: str, problematique: str) -> tuple[str, bool]:
    base = " ".join(p for p in (enseigne, ville, code_site) if p)
    if "camera" in _normaliser(problematique) or "caméra" in problematique.lower():
        return f"{base} - Maintenance caméra", True
    return base, False


def _appliquer_regles_shoppertrak(ticket: Ticket, texte_mail: str = "") -> Ticket:
    """Logique métier SHOPPERTRAK pure (extraite de l'ancien `enrich_ticket`, sans le bloc Rule Engine)."""
    notes: list[str] = []

    champs = extraire_champs_shoppertrak(texte_mail)

    ticket.customer.client = "SHOPPERTRAK"
    ticket.customer.enseigne = champs.get("enseigne", "")
    ticket.customer.code_site = champs.get("code_site", "")
    ticket.customer.adresse = champs.get("adresse", "")
    ticket.customer.code_postal = champs.get("code_postal", "")
    ticket.customer.ville = champs.get("ville", "")
    ticket.customer.pays = champs.get("pays", "")

    ticket.intervention.numero_incident_client = champs.get("numero_incident_client", "")
    ticket.intervention.problematique = champs.get("problematique", "")
    ticket.intervention.origine = "Email"
    ticket.intervention.type_intervention = "Contrat"

    pays_normalise = _normaliser(champs.get("pays", ""))
    contrat = PAYS_VERS_CONTRAT.get(pays_normalise, "")
    if contrat:
        ticket.intervention.contrat = contrat
    else:
        notes.append(
            f"Pays {champs.get('pays', '')!r} non reconnu parmi les 8 pays connus "
            f"(France/Belgique/Pays-Bas/Luxembourg/Danemark/Suède/Finlande/Norvège) "
            f"— Contrat à sélectionner manuellement, cf. hypothèse 1."
        )

    intitule, titre_devine = construire_intitule(
        ticket.customer.enseigne, ticket.customer.ville, ticket.customer.code_site, ticket.intervention.problematique
    )
    ticket.intervention.intitule = intitule
    if not titre_devine:
        notes.append(
            "Titre de la demande (ex. 'Maintenance caméra') non déterminé depuis la "
            "Problématique — à compléter manuellement dans l'Intitulé, cf. hypothèse 2."
        )

    notes.append(
        "⚠️ Agent SHOPPERTRAK volontairement incomplet : Type/Sous-type, Matériel, "
        "Planification et Consignes et mission ne sont pas encore couverts (règles "
        "en attente de précisions de Sofiane) — ne pas considérer ce ticket comme "
        "prêt à saisir sans compléter ces champs manuellement."
    )

    if notes:
        bloc_notes = "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_notes
        )

    return ticket


class ShoppertrakAgent(BaseAgent):
    """Agent SHOPPERTRAK conforme au contrat BaseAgent. Cf. `_appliquer_regles_shoppertrak` pour la logique métier."""

    def analyze(self, request: AgentRequest) -> AgentResult:
        try:
            ticket = _appliquer_regles_shoppertrak(request.ticket, texte_mail=request.texte_mail)
            return AgentResult(ticket=ticket, succes=True)
        except Exception as exc:
            return AgentResult(ticket=request.ticket, succes=False, erreur=str(exc))


_AGENT = ShoppertrakAgent()


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """⚠️ ADAPTATEUR DE COMPATIBILITÉ -- délègue à ShoppertrakAgent.analyze(), reproduit ici l'ancien comportement de activer_rule_engine."""
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