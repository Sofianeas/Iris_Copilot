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
  UPS, le matériel envoyé par le client, et le rappel ATTENTION (support AEM,
  bon de retour, photos, contact Amine) — source : TOKI_AEM_SOFT.txt.

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
     si ce n'est pas le cas, adapter `construire_intitule`.
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
SOUS_TYPES_CONNUS = (SOUS_TYPE_AEM, SOUS_TYPE_IRIS, SOUS_TYPE_SANS_PIECE)

CONTRAT_AEMSOFT = ""  # TODO : libellé Pivot non documenté, voir hypothèse 1 du docstring

# Durée moyenne TOKI, exception switch/serveur (cf. TOKI_AEM_SOFT.txt)
MOTS_CLES_DUREE_LONGUE = ("switch", "serveur", "server")

# Rappel opérationnel toujours ajouté au travail attendu (source : TOKI_AEM_SOFT.txt)
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
RE_MATERIEL_UPS = re.compile(r"mat[ée]riel envoy[ée] par ups\s*:?\s*(.+)", re.IGNORECASE)
RE_OUTILS_A_PREVOIR = re.compile(r"outils?\s+[aà]\s+pr[ée]voir\s*:?\s*(.+)", re.IGNORECASE)
RE_TYPE_LIGNE = re.compile(
    r"(?im)^\s*type\s*:?\s*(intervention\s+(?:j\s*\+\s*1|date\s+impos[ée]e))\s*$"
)
RE_INSTRUCTION_TECH = re.compile(
    r"instruction\s+tech\s*:?\s*(.+?)(?:\n\s*\n|lien de suivi|mat[ée]riel envoy|outils?\s+[aà]\s+pr[ée]voir|$)",
    re.IGNORECASE | re.DOTALL,
)


# --------------------------------------------------------------------------
# Helpers d'extraction (best-effort sur texte_mail brut)
# --------------------------------------------------------------------------

def nettoyer_numero_bdc(valeur: str) -> str:
    """Isole les chiffres d'un numéro de BDC, qu'il soit déjà préfixé 'BDC' ou non."""
    if not valeur:
        return ""
    match = RE_BDC.search(valeur) or re.search(r"(\d+)", valeur)
    return match.group(1) if match else ""


def extraire_numero_bdc(texte_mail: str) -> str:
    """Numéro de BDC présent dans l'objet du mail (filet de sécurité)."""
    return nettoyer_numero_bdc(texte_mail or "")


def extraire_tracking_ups(texte_mail: str) -> str:
    """Numéro/lien de suivi du colis UPS, champ 'Lien de suivi du colis UPS'."""
    if not texte_mail:
        return ""
    match = RE_TRACKING_UPS.search(texte_mail)
    return match.group(1).strip() if match else ""


def extraire_materiel_envoye_ups(texte_mail: str) -> str:
    """Matériel envoyé par le client, champ 'Matériel envoyé par UPS :'."""
    if not texte_mail:
        return ""
    match = RE_MATERIEL_UPS.search(texte_mail)
    return match.group(1).splitlines()[0].strip() if match else ""


def extraire_outils_a_prevoir(texte_mail: str) -> str:
    """Outillage spécifique demandé, champ 'OUTILS A PREVOIR' (hors matériel envoyé)."""
    if not texte_mail:
        return ""
    match = RE_OUTILS_A_PREVOIR.search(texte_mail)
    return match.group(1).splitlines()[0].strip() if match else ""


def extraire_type_aemsoft(texte_mail: str) -> str:
    """
    Filet de sécurité : relit la ligne 'Type :' du mail pour récupérer la
    valeur AEMSOFT exacte (Intervention J+1 / Intervention date imposée).
    Le champ générique `intervention.type` extrait par Gemini peut être pollué
    par une classification générique (Maintenance/Installation/...) héritée
    d'un prompt partagé entre plusieurs clients -> ce filet la corrige.
    """
    if not texte_mail:
        return ""
    match = RE_TYPE_LIGNE.search(texte_mail)
    if not match:
        return ""
    valeur = _normaliser(match.group(1))
    return TYPE_DATE_IMPOSEE if "date" in valeur else TYPE_J_PLUS_1


def extraire_instruction_tech(texte_mail: str) -> str:
    """
    Filet de sécurité : relit le bloc 'INSTRUCTION TECH :' du mail tel quel.
    AEMSOFT.docx exige de recopier TOUT ce bloc dans Problématique, mais
    l'extraction Gemini peut le scinder entre Problématique et Travail
    attendu -> ce filet restaure le texte intégral.
    """
    if not texte_mail:
        return ""
    match = RE_INSTRUCTION_TECH.search(texte_mail)
    return " ".join(match.group(1).split()) if match else ""


# --------------------------------------------------------------------------
# Helpers de déduction / construction
# --------------------------------------------------------------------------

def deduire_niveau_service(type_intervention: str) -> str:
    """
    NIVEAU DE SERVICE (AEMSOFT.docx) :
    "Date imposée" si Type = "Intervention date imposée", sinon "GTI 1J (5/7)"
    (couvre "Intervention J+1" et tout type non reconnu).
    """
    if _normaliser(type_intervention) == _normaliser(TYPE_DATE_IMPOSEE):
        return NIVEAU_SERVICE_DATE_IMPOSEE
    return NIVEAU_SERVICE_GTI_1J


def besoin_materiel_ok(sous_type: str) -> bool:
    """Besoin de matériel = Oui uniquement si pièces expédiées par IRIS."""
    return _normaliser(sous_type) == _normaliser(SOUS_TYPE_IRIS)


def deduire_duree_defaut(texte_mail: str, problematique: str) -> tuple[str, str]:
    """
    Durée moyenne TOKI : 1h, sauf intervention switch/serveur -> 3h.
    Retourne (valeur_a_appliquer, note_a_journaliser).
    """
    texte = _normaliser(f"{texte_mail or ''} {problematique or ''}")
    if any(mot in texte for mot in MOTS_CLES_DUREE_LONGUE):
        return "3h", "Durée non précisée dans le mail — 3h appliqué par défaut (switch/serveur, cf. TOKI)."
    return "1h", "Durée non précisée dans le mail — 1h appliqué par défaut (moyenne TOKI AEM SOFT)."


def construire_intitule(numero_bdc: str, objet: str) -> str:
    """
    Intitulé Pivot : "BDC <numero_bdc> – <objet>".
    Idempotent : si `objet` commence déjà par "BDC", on ne reconstruit pas.
    """
    objet = (objet or "").strip()
    if not numero_bdc or not objet:
        return objet
    if objet.lower().startswith("bdc"):
        return objet
    return f"BDC {numero_bdc} – {objet}"


def dedupliquer_lien_procedure(lien: str) -> str:
    """Ne garde qu'une occurrence de chaque token si le lien est dupliqué."""
    if not lien:
        return lien
    tokens = [t.strip() for t in re.split(r"[\s,;]+", lien) if t.strip()]
    vus: list[str] = []
    for t in tokens:
        if t not in vus:
            vus.append(t)
    return " ".join(vus)


def _ajouter_si_absent(texte_existant: str, bloc: str) -> str:
    """Ajoute `bloc` à `texte_existant` s'il n'y est pas déjà (idempotence)."""
    if not bloc:
        return texte_existant
    if texte_existant and bloc in texte_existant:
        return texte_existant
    if texte_existant:
        return f"{texte_existant.strip()}\n\n{bloc}"
    return bloc


def enrichir_travail_attendu(existant: str, instruction_tech: str, tracking_ups: str, materiel_ups: str) -> str:
    """Travail attendu = existant + INSTRUCTION TECH + tracking UPS + matériel UPS + rappel ATTENTION."""
    texte = existant
    if instruction_tech:
        texte = _ajouter_si_absent(texte, instruction_tech.strip())
    if tracking_ups:
        texte = _ajouter_si_absent(texte, f"Suivi colis UPS : {tracking_ups}")
    if materiel_ups:
        texte = _ajouter_si_absent(texte, f"Matériel envoyé par le client (UPS) : {materiel_ups}")
    return _ajouter_si_absent(texte, ATTENTION_AEM)


def enrichir_consignes_planification(existant: str, tracking_ups: str) -> str:
    """Consignes de planification = consigne standard AEM + existant + tracking UPS."""
    texte = _ajouter_si_absent(existant, CONSIGNE_PLANIFICATION_STANDARD)
    if tracking_ups:
        texte = _ajouter_si_absent(texte, f"Suivi colis UPS : {tracking_ups}")
    return texte


# --------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------

def enrich_ticket(ticket: Ticket, texte_mail: str = "") -> Ticket:
    """
    Enrichit un Ticket déjà extrait du mail avec les règles métier AEMSOFT.

    Le paramètre texte_mail (optionnel) sert de filet de sécurité pour
    récupérer, par regex best-effort, des informations que l'extraction
    Gemini n'a pas forcément de champ dédié pour capturer (numéro de BDC si
    non déjà nettoyé, tracking UPS, matériel envoyé par le client, outillage
    requis).
    """
    notes: list[str] = []

    # --- Identité client : France uniquement (TOKI) ---
    ticket.customer.client = "AEM SOFTS"
    ticket.customer.pays = "France"

    if ticket.customer.code_site and not re.fullmatch(r"\d{4}", ticket.customer.code_site.strip()):
        notes.append(
            f"Code site inhabituel ({ticket.customer.code_site!r}) — attendu sur "
            f"4 chiffres, à vérifier."
        )

    # --- Type d'intervention / Contrat ---
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

    # --- Typologie : Type / Sous-type / Niveau de service ---
    # Filet de sécurité : si `type` n'est pas une des 2 valeurs AEMSOFT connues
    # (cas observé en test : Gemini y met une classification générique comme
    # "Maintenance" au lieu de "Intervention J+1"/"Intervention date imposée"),
    # on relit la ligne 'Type :' du mail directement plutôt que de faire
    # confiance à l'extraction.
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

    if ticket.intervention.sous_type and _normaliser(ticket.intervention.sous_type) not in (
        _normaliser(s) for s in SOUS_TYPES_CONNUS
    ):
        notes.append(
            f"Sous-type inattendu : {ticket.intervention.sous_type!r} "
            f"(valeurs connues : AEM / IRIS / SANS pièces) — à vérifier."
        )
    elif not ticket.intervention.sous_type:
        notes.append("Sous-type non renseigné — Besoin de matériel mis à Non par défaut, à vérifier.")

    # --- Numéro de BDC -> Numéro d'incident client + Intitulé ---
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

    # --- Problématique : on fait confiance au bloc INSTRUCTION TECH relu tel
    # quel dans le mail plutôt qu'à l'extraction Gemini, qui peut le scinder
    # entre Problématique et Travail attendu (cas observé en test).
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

    # --- Matériel / Livraison ---
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

    if not ticket.procedure.autre_outillage:
        outillage_detecte = extraire_outils_a_prevoir(texte_mail)
        if outillage_detecte:
            ticket.procedure.autre_outillage = outillage_detecte
            notes.append(
                "Autre outillage spécifique détecté automatiquement depuis "
                "'OUTILS A PREVOIR' — vérifier qu'il ne s'agit pas du matériel "
                "déjà envoyé par IRIS."
            )

    # --- Durée ---
    if not ticket.procedure.duree:
        duree_defaut, note_duree = deduire_duree_defaut(texte_mail, ticket.intervention.problematique)
        ticket.procedure.duree = duree_defaut
        notes.append(note_duree)

    # --- Travail attendu / Consignes de planification (toujours enrichis) ---
    ticket.procedure.travail_attendu = enrichir_travail_attendu(
        ticket.procedure.travail_attendu,
        ticket.intervention.problematique,
        tracking_ups,
        materiel_ups,
    )
    ticket.procedure.consignes_planification = enrichir_consignes_planification(
        ticket.procedure.consignes_planification,
        tracking_ups,
    )

    # --- Règles fixes ---
    ticket.procedure.intervention_sur_site = True
    ticket.procedure.prise_rdv = False
    ticket.procedure.technicien_anglophone = False  # AEMSOFT = France uniquement
    ticket.procedure.procedure = True
    ticket.procedure.lien_procedure = dedupliquer_lien_procedure(ticket.procedure.lien_procedure)

    # --- Validation ---
    ticket.validation.type_validation = "Client"
    if not ticket.validation.telephone_validation:
        ticket.validation.telephone_validation = ticket.customer.portable or ticket.customer.fixe
        if not ticket.validation.telephone_validation:
            notes.append("Aucun numéro de validation trouvé (ni portable ni fixe) — à compléter manuellement.")

    # --- Consolidation des notes opérateur (toujours visibles dans Streamlit) ---
    if notes:
        bloc_notes = "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_notes
        )

    return ticket