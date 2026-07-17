"""
Agent AMPLIFON.

Logique métier issue de AMPLIFON.docx + TOKI_AMPLIFON.txt :

- Contrat fixe = "IMAC" (seul contrat, confirmé par TOKI_AMPLIFON.txt).
- 4 "modèles d'incidents" possibles, chacun avec ses propres règles
  d'Intitulé / Problématique / Matériel / Livraison :
    A) Expédition matériel sans intégration
    B) Expédition d'un PC Dell avec intégration
    C) Intervention sur site
    D) Intervention pour imprimante (avec/sans reprise, alerte >30kg)
- Imprimante Ricoh 305/306/307 (ou mention explicite >30kg) -> reprise par
  palette via transporteur, prévenir Nicolas Vaduret (NVA) et Philippe
  Guiral (PGU) (source : TOKI_AMPLIFON.txt).
- "Consigne CDS" est une instruction de lecture humaine ("on lit pour être
  sûr et on s'adapte") présente dans les 4 modèles -> non automatisable,
  volontairement non traité par cet agent.

⚠️ Hypothèses à vérifier :

  1. La détection automatique du modèle d'incident (A/B/C/D) est une
     RECOMMANDATION basée sur mots-clés, pas une certitude — AMPLIFON.docx
     précise que c'est normalement le technicien qui choisit ce modèle dans
     Pivot. Elle est toujours signalée dans `commentaire_interne`, jamais
     appliquée silencieusement. Une mauvaise détection fausse tous les
     champs construits ensuite : à confirmer avant saisie.
  2. AMPLIFON.docx mentionne un bouton ("petit logo") qui auto-remplit le
     ticket dans Pivot une fois le modèle + BDC sélectionnés -> une partie
     de la construction d'Intitulé faite ici (modèles A/B/C/D) pourrait être
     redondante avec cet auto-remplissage natif.
  3. `intervention.categorie` est réutilisé pour stocker le libellé du
     modèle détecté, faute de champ dédié "modèle d'incident" dans le
     `Ticket` actuel.
  4. Aucun champ dédié pour "Destination" ni "Envoi Express" dans
     `Logistics` -> combinés dans `consigne_livraison`.
  5. Modèle B : construction en no-op si l'intitulé commence déjà par
     "changement" — à enrichir une fois un exemple réel disponible.
  6. La détection du client AMPLIFON dans router_service.py est plus
     fragile que pour les autres clients — basée sur "amplifon"/"epson"/
     "ricoh" — à renforcer si des faux négatifs apparaissent.

--- Intégration Rule Engine (cette étape) ---
  7. Ajout de 2 paramètres optionnels à `enrich_ticket` :
     `rag_decision: RagDecision | None = None` et
     `activer_rule_engine: bool = False`. Désactivé par défaut :
     rétrocompatibilité totale. AMPLIFON n'a qu'UN SEUL point de sortie
     (les 4 modèles A/B/C/D convergent tous vers le même bloc final) : le
     bloc Rule Engine n'est ajouté qu'une fois, en fin de fonction.
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


CONTRAT_AMPLIFON = "IMAC"

MODELE_A = "A"
MODELE_B = "B"
MODELE_C = "C"
MODELE_D = "D"

LIBELLE_MODELE = {
    MODELE_A: "Expédition matériel sans intégration",
    MODELE_B: "Expédition d'un PC Dell avec intégration",
    MODELE_C: "Intervention sur site",
    MODELE_D: "Intervention pour imprimante",
}

MOTS_CLES_IMPRIMANTE = ("imprimante", "epson", "ricoh")
MOTS_CLES_PC_DELL_INTEGRATION = ("changement poste", "changement de poste")
MOTS_CLES_INTERVENTION_SITE = ("intervention sur site", "intervention site")

RICOH_LOURDS = ("ricoh 305", "ricoh 306", "ricoh 307")

RE_BDC = re.compile(r"\bBDC\b\s*[:\-n°]*\s*(\d+)", re.IGNORECASE)


def nettoyer_numero_bdc(valeur: str) -> str:
    """Isole les chiffres d'un numéro de BDC, qu'il soit déjà préfixé 'BDC' ou non."""
    if not valeur:
        return ""
    match = RE_BDC.search(valeur) or re.search(r"(\d+)", valeur)
    return match.group(1) if match else ""


def extraire_numero_bdc(texte_mail: str) -> str:
    """Numéro de BDC présent dans l'objet du mail (filet de sécurité)."""
    return nettoyer_numero_bdc(texte_mail or "")


def detecter_modele_incident(texte_mail: str) -> str:
    """Déduit le modèle d'incident AMPLIFON (A/B/C/D). Ordre : D > B > C, A en dernier recours."""
    texte = _normaliser(texte_mail)
    if any(mot in texte for mot in MOTS_CLES_IMPRIMANTE):
        return MODELE_D
    if any(mot in texte for mot in MOTS_CLES_PC_DELL_INTEGRATION):
        return MODELE_B
    if any(mot in texte for mot in MOTS_CLES_INTERVENTION_SITE):
        return MODELE_C
    return MODELE_A


def detecter_reprise(texte_mail: str) -> bool:
    """Présence du mot 'reprise' -> installation 'avec reprise' (modèle D)."""
    return "reprise" in _normaliser(texte_mail)


def detecter_imprimante_lourde(texte_mail: str) -> bool:
    """Ricoh 305/306/307 ou mention explicite '+30kg' = imprimante >30kg."""
    texte = _normaliser(texte_mail)
    if any(modele in texte for modele in RICOH_LOURDS):
        return True
    return bool(re.search(r"\+?\s*30\s*kg", texte))


def detecter_type_stock_imprimante(texte_mail: str) -> str:
    """CONSIGNATION si imprimante neuve, SPARE si reconditionnée (modèle D)."""
    texte = _normaliser(texte_mail)
    if "reconditionn" in texte:
        return "SPARE"
    if "neuve" in texte or "neuf" in texte:
        return "CONSIGNATION"
    return ""


RE_RICOH_MODELE = re.compile(r"ricoh\s*(305|306|307)", re.IGNORECASE)


def extraire_modele_ricoh(texte_mail: str) -> str:
    """Isole le modèle Ricoh mentionné (305/306/307), pour la Problématique modèle D."""
    match = RE_RICOH_MODELE.search(texte_mail or "")
    return f"Ricoh {match.group(1)}" if match else ""


def construire_problematique_d(texte_mail: str, avec_reprise: bool) -> str:
    """D) "Installation imprimante [avec/sans reprise]" + marque/modèle."""
    base = "Installation imprimante"
    if not avec_reprise:
        return f"{base} sans reprise."
    modele_ricoh = extraire_modele_ricoh(texte_mail)
    if modele_ricoh:
        poids = " de +30Kg" if detecter_imprimante_lourde(texte_mail) else ""
        return f"{base} avec reprise de l'imprimante{poids} / {modele_ricoh} à reprendre."
    return f"{base} avec reprise de l'ancienne imprimante à reprendre (marque/modèle à préciser)."


def normaliser_duree_intervention(duree: str) -> str:
    """Mappe une durée libre vers 'Xh' / 'Demi-journée' / 'Journée' (modèle C)."""
    texte = _normaliser(duree)
    if not texte:
        return ""
    if "demi" in texte:
        return "Demi-journée"
    if "journee" in texte or "jour" in texte:
        return "Journée"
    match_heures = re.search(r"(\d+)\s*h", texte)
    if match_heures:
        return f"{match_heures.group(1)}h"
    return ""


def construire_intitule_a(numero_bdc: str, pieces: str) -> str:
    """A) "BDC <n> – envoi <pieces>"."""
    pieces = (pieces or "").strip()
    if not numero_bdc or not pieces:
        return ""
    return f"BDC {numero_bdc} – envoi {pieces}"


def construire_intitule_b(intitule_existant: str) -> str:
    """B) "Changement poste" + info objet du mail."""
    return (intitule_existant or "").strip()


def construire_intitule_c(numero_bdc: str, duree: str) -> str:
    """C) "BDC <n> – intervention sur site <Xh|Demi-journée|Journée>"."""
    if not numero_bdc:
        return ""
    descriptif_duree = normaliser_duree_intervention(duree)
    if not descriptif_duree:
        return ""
    return f"BDC {numero_bdc} – intervention sur site {descriptif_duree}"


def construire_intitule_d(numero_bdc: str, avec_reprise: bool) -> str:
    """D) "BDC <n> – installation Epson avec/sans reprise"."""
    if not numero_bdc:
        return ""
    suffixe = "avec reprise" if avec_reprise else "sans reprise"
    return f"BDC {numero_bdc} – installation Epson {suffixe}"


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """
    Enrichit un Ticket déjà extrait du mail avec les règles métier AMPLIFON.

    `rag_decision` (optionnel) : une RagDecision déjà calculée en amont,
    transmise telle quelle au Rule Engine si celui-ci est activé.

    `activer_rule_engine` (par défaut False) : si True, exécute
    rule_engine.executer(ticket, rag_decision) et ajoute ses
    recommandations à commentaire_interne -- jamais à un champ métier.
    """
    notes: list[str] = []

    ticket.customer.client = "AMPLIFON"

    if ticket.customer.code_site and not re.fullmatch(r"\d{3}", ticket.customer.code_site.strip()):
        notes.append(
            f"Code site inhabituel ({ticket.customer.code_site!r}) — attendu sur "
            f"3 chiffres, à vérifier."
        )

    ticket.intervention.type_intervention = "Contrat"
    ticket.intervention.contrat = CONTRAT_AMPLIFON
    ticket.intervention.origine = "Email"

    numero_bdc = nettoyer_numero_bdc(ticket.intervention.numero_incident_client) or extraire_numero_bdc(texte_mail)
    if numero_bdc:
        ticket.intervention.numero_incident_client = numero_bdc
    else:
        notes.append("Numéro de BDC introuvable dans l'objet du mail — à compléter manuellement.")

    modele = detecter_modele_incident(texte_mail)
    ticket.intervention.categorie = LIBELLE_MODELE[modele]
    notes.append(
        f"⚠️ MODÈLE D'INCIDENT déduit automatiquement : « {LIBELLE_MODELE[modele]} » "
        f"({modele}). AMPLIFON.docx précise que c'est normalement le technicien qui "
        f"choisit ce modèle dans Pivot — À CONFIRMER avant saisie, une mauvaise "
        f"détection fausse tous les champs ci-dessous."
    )

    if modele == MODELE_A:
        nouvel_intitule = construire_intitule_a(numero_bdc, ticket.logistics.pieces)
        if nouvel_intitule:
            ticket.intervention.intitule = nouvel_intitule
        ticket.logistics.envoi_piece_par = "IRIS"
        ticket.logistics.consigne_livraison = "Client — Envoi Express"
        ticket.logistics.integration_a_faire = False
        ticket.procedure.intervention_sur_site = False

    elif modele == MODELE_B:
        ticket.intervention.intitule = construire_intitule_b(ticket.intervention.intitule)
        texte_complet = (texte_mail or "").strip()
        if texte_complet and _normaliser(ticket.intervention.problematique) != _normaliser(texte_complet):
            notes.append(
                "Problématique = copie intégrale du mail, conformément à la règle "
                "AMPLIFON modèle B (l'extraction IA avait pu en faire un résumé)."
            )
        if texte_complet:
            ticket.intervention.problematique = texte_complet
        if not ticket.logistics.pieces:
            notes.append("Pièce non détectée — pour un remplacement simple, quantité attendue = 1.")
        ticket.logistics.envoi_piece_par = "IRIS"
        ticket.logistics.consigne_livraison = "Client — Envoi Express"
        ticket.logistics.integration_a_faire = True
        ticket.procedure.intervention_sur_site = False

    elif modele == MODELE_C:
        nouvel_intitule = construire_intitule_c(numero_bdc, ticket.procedure.duree)
        if nouvel_intitule:
            ticket.intervention.intitule = nouvel_intitule
        texte_complet = (texte_mail or "").strip()
        if texte_complet and _normaliser(ticket.intervention.problematique) != _normaliser(texte_complet):
            notes.append(
                "Problématique = copie intégrale du mail, conformément à la règle "
                "AMPLIFON modèle C."
            )
        if texte_complet:
            ticket.intervention.problematique = texte_complet
        if texte_complet and _normaliser(ticket.procedure.travail_attendu) != _normaliser(texte_complet):
            notes.append(
                "Travail attendu = copie intégrale du mail, conformément à la règle "
                "AMPLIFON modèle C."
            )
        if texte_complet:
            ticket.procedure.travail_attendu = texte_complet
        ticket.procedure.intervention_sur_site = True
        notes.append(
            "Modèle C : aucun défaut documenté pour Nombre de techniciens/Durée si "
            "absents du mail — vérifier manuellement contre le mail."
        )

    elif modele == MODELE_D:
        avec_reprise = detecter_reprise(texte_mail)
        nouvel_intitule = construire_intitule_d(numero_bdc, avec_reprise)
        if nouvel_intitule:
            ticket.intervention.intitule = nouvel_intitule

        nouvelle_problematique = construire_problematique_d(texte_mail, avec_reprise)
        if ticket.intervention.problematique and _normaliser(ticket.intervention.problematique) != _normaliser(nouvelle_problematique):
            notes.append(
                "Problématique reconstruite selon la règle AMPLIFON modèle D "
                "('Installation imprimante avec/sans reprise' + marque/modèle)."
            )
        ticket.intervention.problematique = nouvelle_problematique

        ticket.logistics.envoi_piece_par = "IRIS"
        ticket.procedure.intervention_sur_site = True

        if detecter_imprimante_lourde(texte_mail):
            ticket.logistics.commentaire_logistique = _ajouter_si_absent(
                ticket.logistics.commentaire_logistique,
                "Reprise ancienne imprimante >30Kg : prévenir Nicolas Vaduret (NVA) "
                "et Philippe Guiral (PGU) — reprise par palette via transporteur.",
            )
            notes.append(
                "Imprimante détectée comme >30kg (Ricoh 305/306/307 ou mention "
                "explicite) — reprise par palette, prévenir NVA + PGU."
            )

        type_stock = detecter_type_stock_imprimante(texte_mail)
        if type_stock:
            nature = "neuve" if type_stock == "CONSIGNATION" else "reconditionnée"
            notes.append(f"Stock imprimante déduit : {type_stock} (imprimante {nature}).")
        else:
            notes.append(
                "Impossible de déduire si l'imprimante est neuve (Stock CONSIGNATION) "
                "ou reconditionnée (Stock SPARE) — à vérifier."
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