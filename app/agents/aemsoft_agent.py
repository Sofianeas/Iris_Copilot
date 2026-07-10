"""
Agent AEMSOFT (AEM SOFTS).

Logique métier issue de AEMSOFT.docx + TOKI_AEM_SOFT.txt :

- Client France uniquement (TOKI : "INTER UNIQUEMENT EN FRANCE") : Pays forcé à
  "France", Technicien anglophone toujours Non.
- Intitulé et Numéro d'incident client sont construits/nettoyés à partir du
  numéro de BDC présent dans l'objet du mail : "BDC <n> – <Objet de l'intervention>".
- Besoin de matériel = Oui uniquement si Sous-type = "Intervention AVEC pièces
  expédiées par IRIS" (les 2 autres sous-types n'impliquent pas d'envoi par IRIS).
- Niveau de service déduit du Type : "Date imposée" si Type = "Intervention date
  imposée", sinon "GTI 1J (5/7)" (valeur par défaut, couvre aussi "Intervention J+1").
- Durée par défaut : 1h (moyenne TOKI), sauf mention switch/serveur -> 3h.
- Travail attendu et Consignes de planification sont enrichis (jamais remplacés,
  idempotent) avec : le contenu INSTRUCTION TECH (= Problématique), le tracking
  UPS, le matériel envoyé par le client, la Hotline AEM (numéro dynamique du
  mail si présent, sinon rappel générique), et le rappel ATTENTION (support
  AEM, bon de retour, photos, contact Amine) — source : TOKI_AEM_SOFT.txt.

⚠️ PIÈCE JOINTE PDF : AEM SOFT envoie aussi un PDF "Bon de commande
   d'intervention" qui duplique le contenu du mail. Ce PDF n'est PAS parsé
   par cet agent (texte_mail reste l'unique source) : un exemple réel a
   montré que l'extraction texte d'un PDF de ce type insère des artefacts
   de mise en page au milieu du texte utile (en-têtes de tableau, numéros
   de page, ex. "DATE: ... DQ-027 Bon de commande fournisseur PAGE: 1 ...
   Ref. fourni. Désignation QTE COMMANDEE ...") qui rendraient toute regex
   fragile. Le PDF doit simplement être attaché tel quel au ticket
   (Documents), jamais lu — même logique que la "fiche d'intervention" PDF
   d'AXE E-SANTE.

--- Corrections apportées après analyse d'un vrai mail AEM SOFT ---
  1. RE_TYPE_LIGNE tolère désormais un tiret collé après le ':' (format
     réel observé : "Type :-Intervention J+1", sans espace avant le "-").
  2. `extraire_materiel_envoye_ups` capture maintenant TOUTES les lignes
     d'une liste à puces multi-lignes (bug corrigé : seule la 1ère ligne
     était récupérée, les suivantes silencieusement perdues).
  3. Le sous-type est désormais classifié par MOTS-CLÉS
     (`classifier_sous_type`) plutôt que par égalité stricte : un vrai mail
     contenait "Intervention Avec pièce Expédié par AEM" (singulier, accord
     masculin) alors que le libellé canonique du docx est au pluriel/accord
     féminin -- la comparaison stricte échouait sur ce cas réel pourtant
     valide.
  4. 3 champs supplémentaires, observés sur le terrain mais absents
     d'AEMSOFT.docx/TOKI, sont désormais extraits : N° TPV (->
     `reference_materiel_client`), "RETOUR COLIS PAR UPS : OUI/NON" (->
     `logistics.retour_piece`), et le numéro de Hotline AEM SOFTS
     spécifique à l'intervention (différent du contact générique "Amine"
     déjà codé en dur) -> ajouté dans `travail_attendu`.

--- Intégration Rule Engine (cette étape) ---
  5. Ajout de 2 paramètres optionnels à `enrich_ticket` :
     `rag_decision: RagDecision | None = None` et
     `activer_rule_engine: bool = False`. Désactivé par défaut : tous les
     appels existants (`enrich_ticket(ticket, texte_mail)`) conservent un
     comportement rigoureusement identique. Quand activé, le Rule Engine
     est exécuté en toute fin de fonction et ses recommandations sont
     ajoutées à `commentaire_interne` -- JAMAIS à un champ métier -- avec
     confiance/source/raison visibles, cohérent avec la politique déjà en
     place pour le RAG fallback ailleurs dans le projet.

⚠️ Hypothèses à vérifier (non documentées explicitement, ou en contradiction
   entre les deux sources) :

  1. Le contrat unique AEM SOFT n'a pas de libellé Pivot connu dans AEMSOFT.docx
     ("Sélectionner le seul contrat" sans préciser son nom) -> CONTRAT_AEMSOFT
     est laissé vide ; un commentaire est ajouté au ticket tant qu'il l'est.
     Renseigner CONTRAT_AEMSOFT une fois le libellé confirmé dans Pivot.
  2. "Niveau de service" est stocké dans `intervention.niveau_priorite`, faute de
     champ dédié dans le modèle Ticket actuel -> à corriger si un champ existe.
  3. AEMSOFT.docx utilise le libellé "GTI 1J (5/7)" ; TOKI_AEM_SOFT.txt utilise
     "GTR1J (5/7)" pour la même notion -> confirmer le libellé exact attendu
     par Pivot (NIVEAU_SERVICE_GTI_1J ci-dessous).
  4. `ticket.intervention.intitule` est supposé contenir, avant cet agent, le
     texte brut du champ mail "Objet de l'intervention" (extraction Gemini) ->
     si ce n'est pas le cas, adapter `construire_intitule`. NB : un vrai mail
     n'a montré aucune mention explicite de "BDC" dans le corps -- ce numéro
     est censé provenir de l'objet du mail (non visible dans cet exemple) ;
     si "BDC" s'avère absent même dans l'objet pour ce type de commande, le
     repli actuel (garder l'objet tel quel sans préfixe "BDC X –") reste correct.
  5. La position exacte de "N° TPV" dans le mail (juste après INSTRUCTION TECH,
     avant OUTILS A PREVOIR) fait qu'il reste aussi inclus tel quel dans la
     Problématique copiée verbatim (conforme à la règle "copier tout INSTRUCTION
     TECH") -- son extraction séparée vers reference_materiel_client est un
     AJOUT pour la traçabilité, pas un remplacement.
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


# --------------------------------------------------------------------------
# Référentiel AEMSOFT (issu de AEMSOFT.docx)
# --------------------------------------------------------------------------

TYPE_J_PLUS_1 = "Intervention J+1"
TYPE_DATE_IMPOSEE = "Intervention date imposée"

NIVEAU_SERVICE_DATE_IMPOSEE = "Date imposée"
NIVEAU_SERVICE_GTI_1J = "GTI 1J (5/7)"  # cf. hypothèse 3 du docstring (GTI vs GTR)

SOUS_TYPE_AEM = "Intervention AVEC pièces expédiées par AEM"
SOUS_TYPE_IRIS = "Intervention AVEC pièces expédiées par IRIS"
SOUS_TYPE_SANS_PIECE = "Intervention SANS pièces"

CONTRAT_AEMSOFT = ""  # TODO : libellé Pivot non documenté, voir hypothèse 1 du docstring

MOTS_CLES_DUREE_LONGUE = ("switch", "serveur", "server")

ATTENTION_AEM = (
    "ATTENTION !\n"
    "L'appel au support AEM doit être fait à l'arrivée et à la fin de l'intervention.\n"
    "Si un bon de retour est fourni avec le colis, l'ancienne pièce doit être "
    "retournée en utilisant ce bon.\n"
    "Il faut TOUJOURS prendre des photos de l'intervention et les mettre dans la "
    "clôture.\n"
    "Pour tout souci non technique, merci d'appeler Amine sur +33 6 44 18 52 74"
)

CONSIGNE_PLANIFICATION_STANDARD = (
    "Pas de RDV à prendre : appeler le contact pour prévenir de la date de passage. "
    "Créneaux : 9h-12h / 14h-17h. Planifier en J+1 à partir de la livraison du colis."
)

RE_BDC = re.compile(r"\bBDC\b\s*[:\-n°]*\s*(\d+)", re.IGNORECASE)
RE_TRACKING_UPS = re.compile(r"lien de suivi du colis ups\s*[:\-]?\s*(\S+)", re.IGNORECASE)
RE_MATERIEL_UPS = re.compile(
    r"mat[ée]riel envoy[ée] par ups\s*:?\s*\n?(.*?)(?:\n\s*-{3,}|\n\s*type\s*:|\n\s*sous-type\s*:|\n\s*\n\s*\n|$)",
    re.IGNORECASE | re.DOTALL,
)
RE_OUTILS_A_PREVOIR = re.compile(r"outils?\s+[aà]\s+pr[ée]voir\s*:?\s*(.+)", re.IGNORECASE)
RE_TYPE_LIGNE = re.compile(
    r"(?im)^\s*type\s*:?\s*-?\s*(intervention\s+(?:j\s*\+\s*1|date\s+impos[ée]e))\s*$"
)
RE_INSTRUCTION_TECH = re.compile(
    r"instruction\s+tech\s*:?\s*(.+?)(?:\n\s*\n|lien de suivi|mat[ée]riel envoy|outils?\s+[aà]\s+pr[ée]voir|$)",
    re.IGNORECASE | re.DOTALL,
)
RE_NUMERO_TPV = re.compile(r"n[°o]\s*tpv\s*:?\s*(\S+)", re.IGNORECASE)
RE_RETOUR_COLIS_UPS = re.compile(r"retour colis par ups\s*:?\s*(oui|non)", re.IGNORECASE)
RE_ETIQUETTE_RETOUR = re.compile(r"[ée]tiquette retour[^)\n]*", re.IGNORECASE)
RE_HOTLINE_ARRIVEE = re.compile(r"appeler le\s*:?\s*([\d.\s]{8,15}?)\s*\(hotline aem softs?\)", re.IGNORECASE)
RE_HORAIRE_HOTLINE = re.compile(r"horaire de la hotline aem softs?\s*:?\s*([^\n]+)", re.IGNORECASE)


def nettoyer_numero_bdc(valeur: str) -> str:
    if not valeur:
        return ""
    match = RE_BDC.search(valeur) or re.search(r"(\d+)", valeur)
    return match.group(1) if match else ""


def extraire_numero_bdc(texte_mail: str) -> str:
    return nettoyer_numero_bdc(texte_mail or "")


def extraire_tracking_ups(texte_mail: str) -> str:
    if not texte_mail:
        return ""
    match = RE_TRACKING_UPS.search(texte_mail)
    return match.group(1).strip() if match else ""


def extraire_materiel_envoye_ups(texte_mail: str) -> str:
    if not texte_mail:
        return ""
    match = RE_MATERIEL_UPS.search(texte_mail)
    if not match:
        return ""
    lignes = [l.strip() for l in match.group(1).splitlines() if l.strip()]
    return "\n".join(lignes)


def extraire_outils_a_prevoir(texte_mail: str) -> str:
    if not texte_mail:
        return ""
    match = RE_OUTILS_A_PREVOIR.search(texte_mail)
    return match.group(1).splitlines()[0].strip() if match else ""


def extraire_type_aemsoft(texte_mail: str) -> str:
    if not texte_mail:
        return ""
    match = RE_TYPE_LIGNE.search(texte_mail)
    if not match:
        return ""
    valeur = _normaliser(match.group(1))
    return TYPE_DATE_IMPOSEE if "date" in valeur else TYPE_J_PLUS_1


def extraire_instruction_tech(texte_mail: str) -> str:
    if not texte_mail:
        return ""
    match = RE_INSTRUCTION_TECH.search(texte_mail)
    return " ".join(match.group(1).split()) if match else ""


def extraire_numero_tpv(texte_mail: str) -> str:
    if not texte_mail:
        return ""
    match = RE_NUMERO_TPV.search(texte_mail)
    return match.group(1).strip() if match else ""


def extraire_retour_colis_ups(texte_mail: str) -> tuple[str, str]:
    if not texte_mail:
        return "", ""
    match = RE_RETOUR_COLIS_UPS.search(texte_mail)
    if not match:
        return "", ""
    valeur = "Oui" if match.group(1).lower() == "oui" else "Non"
    if valeur == "Oui":
        m_etiquette = RE_ETIQUETTE_RETOUR.search(texte_mail)
        detail = f" ({m_etiquette.group(0).strip()})" if m_etiquette else ""
        return valeur, f"Retour colis UPS confirmé dans le mail{detail}."
    return valeur, "Retour colis UPS : Non (confirmé dans le mail)."


def extraire_hotline_aem(texte_mail: str) -> tuple[str, str]:
    if not texte_mail:
        return "", ""
    match_numero = RE_HOTLINE_ARRIVEE.search(texte_mail)
    numero = match_numero.group(1).strip() if match_numero else ""
    match_horaire = RE_HORAIRE_HOTLINE.search(texte_mail)
    horaire = match_horaire.group(1).strip() if match_horaire else ""
    return numero, horaire


def deduire_niveau_service(type_intervention: str) -> str:
    if _normaliser(type_intervention) == _normaliser(TYPE_DATE_IMPOSEE):
        return NIVEAU_SERVICE_DATE_IMPOSEE
    return NIVEAU_SERVICE_GTI_1J


def besoin_materiel_ok(sous_type: str) -> bool:
    return classifier_sous_type(sous_type) == SOUS_TYPE_IRIS


def classifier_sous_type(sous_type: str) -> str:
    texte = _normaliser(sous_type)
    if not texte:
        return ""
    if "sans piece" in texte:
        return SOUS_TYPE_SANS_PIECE
    if "iris" in texte:
        return SOUS_TYPE_IRIS
    if "aem" in texte:
        return SOUS_TYPE_AEM
    return ""


def deduire_duree_defaut(texte_mail: str, problematique: str) -> tuple[str, str]:
    texte = _normaliser(f"{texte_mail or ''} {problematique or ''}")
    if any(mot in texte for mot in MOTS_CLES_DUREE_LONGUE):
        return "3h", "Durée non précisée dans le mail — 3h appliqué par défaut (switch/serveur, cf. TOKI)."
    return "1h", "Durée non précisée dans le mail — 1h appliqué par défaut (moyenne TOKI AEM SOFT)."


def construire_intitule(numero_bdc: str, objet: str) -> str:
    objet = (objet or "").strip()
    if not numero_bdc or not objet:
        return objet
    if objet.lower().startswith("bdc"):
        return objet
    return f"BDC {numero_bdc} – {objet}"


def dedupliquer_lien_procedure(lien: str) -> str:
    if not lien:
        return lien
    tokens = [t.strip() for t in re.split(r"[\s,;]+", lien) if t.strip()]
    vus: list[str] = []
    for t in tokens:
        if t not in vus:
            vus.append(t)
    return " ".join(vus)


def _ajouter_si_absent(texte_existant: str, bloc: str) -> str:
    if not bloc:
        return texte_existant
    if texte_existant and bloc in texte_existant:
        return texte_existant
    if texte_existant:
        return f"{texte_existant.strip()}\n\n{bloc}"
    return bloc


def enrichir_travail_attendu(existant: str, instruction_tech: str, tracking_ups: str, materiel_ups: str) -> str:
    texte = existant
    if instruction_tech:
        texte = _ajouter_si_absent(texte, instruction_tech.strip())
    if tracking_ups:
        texte = _ajouter_si_absent(texte, f"Suivi colis UPS : {tracking_ups}")
    if materiel_ups:
        texte = _ajouter_si_absent(texte, f"Matériel envoyé par le client (UPS) : {materiel_ups}")
    return _ajouter_si_absent(texte, ATTENTION_AEM)


def enrichir_consignes_planification(existant: str, tracking_ups: str) -> str:
    texte = _ajouter_si_absent(existant, CONSIGNE_PLANIFICATION_STANDARD)
    if tracking_ups:
        texte = _ajouter_si_absent(texte, f"Suivi colis UPS : {tracking_ups}")
    return texte


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


def enrich_ticket(
    ticket: Ticket,
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """
    Enrichit un Ticket déjà extrait du mail avec les règles métier AEMSOFT.

    `rag_decision` (optionnel) : une RagDecision déjà calculée en amont,
    transmise telle quelle au Rule Engine si celui-ci est activé.

    `activer_rule_engine` (par défaut False) : si True, exécute
    rule_engine.executer(ticket, rag_decision) en fin de fonction et
    ajoute ses recommandations à commentaire_interne -- jamais à un champ
    métier. Désactivé par défaut pour une rétrocompatibilité totale.
    """
    notes: list[str] = []

    ticket.customer.client = "AEM SOFTS"
    ticket.customer.pays = "France"

    if ticket.customer.code_site and not re.fullmatch(r"\d{4}", ticket.customer.code_site.strip()):
        notes.append(
            f"Code site inhabituel ({ticket.customer.code_site!r}) — attendu sur "
            f"4 chiffres, à vérifier."
        )

    ticket.intervention.type_intervention = "Contrat"
    if CONTRAT_AEMSOFT:
        ticket.intervention.contrat = CONTRAT_AEMSOFT
    elif not ticket.intervention.contrat:
        notes.append(
            "Contrat AEM SOFT non renseigné automatiquement : un seul contrat "
            "existe côté Pivot pour ce client, mais son libellé exact n'est pas "
            "documenté dans AEMSOFT.docx — sélectionner manuellement, ou "
            "compléter la constante CONTRAT_AEMSOFT dans cet agent."
        )
    else:
        notes.append(
            f"Contrat AEM SOFT extrait par l'IA ({ticket.intervention.contrat!r}) "
            f"mais NON VÉRIFIABLE : son libellé Pivot exact n'est documenté nulle "
            f"part — à confirmer avant saisie, ne pas faire confiance par défaut."
        )

    type_reconnu = _normaliser(ticket.intervention.type) in (
        _normaliser(TYPE_J_PLUS_1), _normaliser(TYPE_DATE_IMPOSEE)
    )
    if not type_reconnu:
        type_corrige = extraire_type_aemsoft(texte_mail)
        if type_corrige:
            if ticket.intervention.type:
                notes.append(
                    f"Type corrigé automatiquement : '{ticket.intervention.type}' "
                    f"(valeur générique extraite par l'IA) -> '{type_corrige}' (relu "
                    f"directement dans la ligne 'Type :' du mail). Pense à adapter le "
                    f"prompt AEMSOFT dans parser_service.py pour éviter cette confusion."
                )
            ticket.intervention.type = type_corrige
        else:
            ticket.intervention.type = TYPE_J_PLUS_1
            notes.append(f"Type non précisé/non reconnu dans le mail — défaut appliqué : {TYPE_J_PLUS_1}.")

    ticket.intervention.niveau_priorite = deduire_niveau_service(ticket.intervention.type)

    sous_type_classifie = classifier_sous_type(ticket.intervention.sous_type)
    if ticket.intervention.sous_type and not sous_type_classifie:
        notes.append(
            f"Sous-type non reconnu (mots-clés attendus : AEM / IRIS / SANS pièce) : "
            f"{ticket.intervention.sous_type!r} — à vérifier."
        )
    elif not ticket.intervention.sous_type:
        notes.append("Sous-type non renseigné — Besoin de matériel mis à Non par défaut, à vérifier.")

    numero_bdc = nettoyer_numero_bdc(ticket.intervention.numero_incident_client) or extraire_numero_bdc(texte_mail)
    if numero_bdc:
        ticket.intervention.numero_incident_client = numero_bdc
        ticket.intervention.intitule = construire_intitule(numero_bdc, ticket.intervention.intitule)
    else:
        notes.append(
            "Numéro de BDC introuvable dans l'objet du mail — Numéro d'incident "
            "client et Intitulé à compléter manuellement."
        )

    ticket.intervention.origine = "Email"

    numero_tpv = extraire_numero_tpv(texte_mail)
    if numero_tpv:
        if ticket.intervention.reference_materiel_client and ticket.intervention.reference_materiel_client != numero_tpv:
            notes.append(
                f"N° TPV extrait du mail ({numero_tpv!r}) différent de "
                f"reference_materiel_client déjà renseigné "
                f"({ticket.intervention.reference_materiel_client!r}) — à vérifier."
            )
        else:
            ticket.intervention.reference_materiel_client = numero_tpv

    instruction_tech = extraire_instruction_tech(texte_mail)
    if instruction_tech:
        if ticket.intervention.problematique and _normaliser(ticket.intervention.problematique) != _normaliser(instruction_tech):
            notes.append(
                "Problématique recalculée depuis le bloc 'INSTRUCTION TECH :' relu "
                "intégralement dans le mail (l'extraction Gemini avait scindé ce texte "
                "entre Problématique et Travail attendu)."
            )
        ticket.intervention.problematique = instruction_tech
    elif not ticket.intervention.problematique:
        notes.append("Bloc 'INSTRUCTION TECH :' introuvable dans le mail — Problématique à compléter manuellement.")

    ticket.logistics.besoin_materiel = besoin_materiel_ok(ticket.intervention.sous_type)
    if ticket.logistics.besoin_materiel:
        ticket.logistics.envoi_piece_par = "IRIS"
        ticket.logistics.consigne_livraison = "Pudo"
    else:
        if ticket.logistics.pieces:
            notes.append(
                "Sous-type ≠ 'pièces expédiées par IRIS' : pièce(s) détectée(s) "
                "dans le mail mais non retenue(s) pour un envoi IRIS."
            )
        ticket.logistics.pieces = ""

    tracking_ups = ticket.logistics.tracking or extraire_tracking_ups(texte_mail)
    if tracking_ups:
        ticket.logistics.tracking = tracking_ups
    materiel_ups = extraire_materiel_envoye_ups(texte_mail)

    if not ticket.logistics.retour_piece:
        retour_piece, note_retour = extraire_retour_colis_ups(texte_mail)
        if retour_piece:
            ticket.logistics.retour_piece = retour_piece
            notes.append(note_retour)

    if not ticket.procedure.autre_outillage:
        outillage_detecte = extraire_outils_a_prevoir(texte_mail)
        if outillage_detecte:
            ticket.procedure.autre_outillage = outillage_detecte
            notes.append(
                "Autre outillage spécifique détecté automatiquement depuis "
                "'OUTILS A PREVOIR' — vérifier qu'il ne s'agit pas du matériel "
                "déjà envoyé par IRIS."
            )

    if not ticket.procedure.duree:
        duree_defaut, note_duree = deduire_duree_defaut(texte_mail, ticket.intervention.problematique)
        ticket.procedure.duree = duree_defaut
        notes.append(note_duree)

    ticket.procedure.travail_attendu = enrichir_travail_attendu(
        ticket.procedure.travail_attendu,
        ticket.intervention.problematique,
        tracking_ups,
        materiel_ups,
    )
    hotline_numero, hotline_horaire = extraire_hotline_aem(texte_mail)
    if hotline_numero:
        ligne_hotline = (
            f"Hotline AEM SOFTS : appeler le {hotline_numero} à l'arrivée ET à la "
            f"fin de l'intervention"
            + (f" (horaires : {hotline_horaire})." if hotline_horaire else ".")
        )
        ticket.procedure.travail_attendu = _ajouter_si_absent(ticket.procedure.travail_attendu, ligne_hotline)
    ticket.procedure.consignes_planification = enrichir_consignes_planification(
        ticket.procedure.consignes_planification,
        tracking_ups,
    )

    ticket.procedure.intervention_sur_site = True
    ticket.procedure.prise_rdv = False
    ticket.procedure.technicien_anglophone = False
    ticket.procedure.procedure = True
    ticket.procedure.lien_procedure = dedupliquer_lien_procedure(ticket.procedure.lien_procedure)

    ticket.validation.type_validation = "Client"
    if not ticket.validation.telephone_validation:
        ticket.validation.telephone_validation = ticket.customer.portable or ticket.customer.fixe
        if not ticket.validation.telephone_validation:
            notes.append("Aucun numéro de validation trouvé (ni portable ni fixe) — à compléter manuellement.")

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