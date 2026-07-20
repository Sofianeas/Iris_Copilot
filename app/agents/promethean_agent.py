"""
Agent PROMETHEAN.

Logique métier issue de TOKI_PROMETHEAN.txt.

⚠️ CAS PARTICULIER -- architecture différente des 10 autres clients :
les autres agents enrichissent un Ticket déjà extrait du TEXTE DU MAIL.
Pour PROMETHEAN, le mail ne contient (dans 95% des cas, selon Sofiane)
qu'un LIEN UNIQUE vers une demande sur la plateforme Promethean -- les
données réelles ne sont disponibles qu'APRÈS connexion + navigation sur
cette plateforme (en anglais). C'est une tâche de navigation web (V3
Automatisation), pas une simple extraction de texte (V1 Structure).

Découpage retenu :
  1. `extraire_lien_promethean` : détecte un mail Promethean et isole le
     lien -- ça, c'est purement déterministe et testable sur texte_mail.
  2. `enrich_ticket` : logique métier des 2 scénarios documentés, mais
     prend en entrée `texte_page` (le texte de la page Promethean APRÈS
     connexion+navigation -- pas texte_mail).
  3. AUCUN exemple réel de page Promethean disponible à ce jour -- la
     détection de scénario et l'extraction de champs depuis `texte_page`
     sont basées sur des mots-clés anglais PLAUSIBLES, pas validées
     contre une vraie page.

⚠️ Hypothèses à vérifier (plus nombreuses qu'à l'habitude, faute
   d'exemple réel) :

  1. La détection de scénario (écran vs pièce) utilise des mots-clés
     anglais -- TOKI ne précise pas comment cette distinction apparaît
     réellement sur la page. À CONFIRMER avec une vraie page.
  2. Le tableau "Nombre de tech et temps d'intervention" (TOKI) référence
     une image absente du texte fourni -- non déduits automatiquement.
  3. "Rechercher le modèle du matériel dans Google" (TOKI) est une étape
     manuelle -- non automatisable ici.
  4. Les noms de champs anglais probables sur la page sont des
     suppositions.
  5. FootPrints (mentionné dans TOKI) est ignoré : confirmé par Sofiane
     comme l'ancien système, remplacé par Pivot.

--- Intégration Rule Engine (cette étape) ---
  6. Ajout de 2 paramètres optionnels à `enrich_ticket`, en FIN de
     signature (après `texte_mail`) : `rag_decision: RagDecision | None =
     None` et `activer_rule_engine: bool = False`. Désactivé par défaut :
     rétrocompatibilité totale. PROMETHEAN n'a qu'UN SEUL point de sortie.
     ⚠️ `contrat` n'est jamais assigné dans cet agent (reste toujours vide)
     -> `client_rule` SE DÉCLENCHE réellement ici si une RagDecision
     utilisable est fournie -- testé explicitement, même situation que
     AXE E-SANTE et DYNAMIZ PHARMA.
  7. Correction opportuniste : un caractère CJK parasite ("永続", artefact
     d'encodage) s'était glissé dans une note interne ("contacts
     génériques永続") -- remplacé par "permanents", texte français
     correct. Repéré en relisant le fichier intégralement pour cette
     livraison, sans rapport avec le Rule Engine.
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


EXPEDITEUR_PROMETHEAN = "donotreply@prometheanworld.com"
SUJET_PROMETHEAN = "promethean onsite job request"

RE_URL = re.compile(r"https?://\S+", re.IGNORECASE)


def est_mail_promethean(texte_mail: str) -> bool:
    """Signature très fiable : expéditeur + sujet caractéristiques (cf. TOKI)."""
    texte_n = _normaliser(texte_mail)
    return EXPEDITEUR_PROMETHEAN in texte_n or SUJET_PROMETHEAN in texte_n


def extraire_lien_promethean(texte_mail: str) -> str:
    """Isole le lien unique vers la demande Promethean."""
    match = RE_URL.search(texte_mail or "")
    return match.group(0).rstrip(".,;)") if match else ""


SCENARIO_REMPLACEMENT_ECRAN = "ecran"
SCENARIO_REMPLACEMENT_PIECE = "piece"

MOTS_CLES_ECRAN = ("screen replacement", "replace screen", "display replacement", "panel replacement")
MOTS_CLES_PIECE = ("part replacement", "component replacement", "replace part", "repair")

CONSIGNE_RDV_ECRAN = (
    "Lors de la prise de rendez-vous avec le contact sur site, merci de faire "
    "confirmer la livraison du matériel avant de planifier l'intervention. Si "
    "matériel non livré, ne pas prendre de rendez-vous avec le contact."
)
RAPPEL_EMBALLAGE_ECRAN = (
    "L'ancien écran doit être remis dans le carton du nouvel écran, le carton "
    "doit être fixé sur la palette avec l'aide des attaches et la palette doit "
    "être placée au niveau du rez de chaussée. Prendre une photo pour preuve."
)

SUPPORT_N3_PIECE = "Damien C. - +33 (0)6 33 35 09 69"
CONTACT_CLIENT_PIECE = "Maxime C. - +33 6 12 46 22 82"
SUPPORT_IRIS_PIECE = "09 88 66 03 32"


def detecter_scenario(texte_page: str) -> tuple[str, bool]:
    """Déduit le scénario (écran vs pièce) depuis le texte de la page Promethean."""
    texte = _normaliser(texte_page)
    if any(mot in texte for mot in MOTS_CLES_ECRAN):
        return SCENARIO_REMPLACEMENT_ECRAN, True
    if any(mot in texte for mot in MOTS_CLES_PIECE):
        return SCENARIO_REMPLACEMENT_PIECE, True
    return SCENARIO_REMPLACEMENT_ECRAN, False


def extraire_champ_page(texte_page: str, libelles: tuple) -> str:
    """Extraction best-effort 'Label: valeur' pour un ou plusieurs libellés possibles."""
    for libelle in libelles:
        pattern = re.compile(rf"{re.escape(libelle)}\s*:?\s*(.+)", re.IGNORECASE)
        match = pattern.search(texte_page or "")
        if match:
            return match.group(1).strip().splitlines()[0].strip()
    return ""


def enrich_ticket(
    ticket: Ticket,
    texte_page: str = "",
    texte_mail: str = "",
    rag_decision: RagDecision | None = None,
    activer_rule_engine: bool = False,
) -> Ticket:
    """
    Enrichit un Ticket à partir du texte de la page Promethean APRÈS
    connexion+navigation (PAS texte_mail). `texte_mail` est conservé
    uniquement pour récupérer le lien d'origine et le numéro de job
    request si présent dans le mail plutôt que sur la page.

    `rag_decision` (optionnel) : une RagDecision déjà calculée en amont,
    transmise telle quelle au Rule Engine si celui-ci est activé.

    `activer_rule_engine` (par défaut False) : si True, exécute
    rule_engine.executer(ticket, rag_decision) et ajoute ses
    recommandations à commentaire_interne -- jamais à un champ métier.
    """
    notes: list[str] = []

    ticket.customer.client = "PROMETHEAN"
    ticket.customer.commentaire = _ajouter_si_absent(
        ticket.customer.commentaire, "Sous-entité Pivot attendue : PROMETHEAN LIMITED HEADQUARTERS (à vérifier)."
    )

    lien = extraire_lien_promethean(texte_mail)

    scenario, confiant = detecter_scenario(texte_page)
    notes.append(
        f"⚠️ SCÉNARIO déduit automatiquement : « {'Remplacement écran' if scenario == SCENARIO_REMPLACEMENT_ECRAN else 'Remplacement pièce'} »"
        + ("" if confiant else " (PAR DÉFAUT, aucun mot-clé déterminant trouvé sur la page)")
        + " — AUCUN EXEMPLE RÉEL DE PAGE N'A ÉTÉ UTILISÉ POUR VALIDER CETTE DÉTECTION. À confirmer manuellement avant saisie."
    )

    ticket.customer.adresse = extraire_champ_page(texte_page, ("main contact address", "site address", "address"))
    numero_serie = extraire_champ_page(texte_page, ("serial number", "sn"))
    ticket.intervention.numero_serie = numero_serie

    job_request_number = extraire_champ_page(texte_page, ("job request number", "case number", "job number"))
    ticket.intervention.numero_incident_client = job_request_number
    if not job_request_number:
        notes.append("Numéro de job request/case introuvable dans le texte de la page — à compléter manuellement.")

    comments = extraire_champ_page(texte_page, ("comments", "comment"))

    ticket.intervention.origine = "Email"
    ticket.intervention.type_intervention = "Contrat"
    ticket.intervention.categorie = "Prestation / Remplacement"

    if scenario == SCENARIO_REMPLACEMENT_ECRAN:
        ticket.intervention.type = "Intervention SANS pièce"
        ticket.procedure.prise_rdv = True
        ticket.procedure.intervention_sur_site = True
        ticket.procedure.consignes_planification = _ajouter_si_absent(
            ticket.procedure.consignes_planification, CONSIGNE_RDV_ECRAN
        )

        description_parts = []
        if comments:
            description_parts.append(comments)
        else:
            notes.append("Paragraphe 'Comments' introuvable sur la page — Description à compléter manuellement.")
        description_parts.append(RAPPEL_EMBALLAGE_ECRAN)
        if lien:
            description_parts.append(f"Lien du formulaire Promethean : {lien}")
        ticket.intervention.problematique = "\n\n".join(description_parts)

        modele_materiel = extraire_champ_page(texte_page, ("model", "product model", "equipment model"))
        if modele_materiel:
            ticket.procedure.travail_attendu = f"Remplacer {modele_materiel} et faire test de fonctionnement."
        else:
            ticket.procedure.travail_attendu = "Remplacer *matériel* et faire test de fonctionnement."
            notes.append("Modèle du matériel introuvable sur la page — à compléter manuellement dans le Travail attendu (\"*matériel*\").")

        notes.append(
            "Rechercher le modèle du matériel sur Google pour déterminer s'il s'agit "
            "d'un Active Panel ou d'un ActiveBoard, et sa taille d'écran (cf. TOKI) "
            "— étape manuelle, non automatisée ici."
        )
        notes.append(
            "Nombre de techniciens et durée d'intervention dépendent d'un tableau "
            "(taille d'écran -> nb tech/durée) référencé dans TOKI_PROMETHEAN.txt mais "
            "dont l'image n'a pas été fournie — à compléter manuellement (cf. hypothèse 2)."
        )
        notes.append("Passer le dossier en '59-Intervention SANS pièce' sauf demande exceptionnelle de Promethean (cf. TOKI).")

    else:  # SCENARIO_REMPLACEMENT_PIECE
        ticket.intervention.type = "Intervention SANS pièce"
        ticket.procedure.prise_rdv = True
        ticket.procedure.intervention_sur_site = True

        modele_et_sn = " ".join(p for p in (extraire_champ_page(texte_page, ("model", "product model")), numero_serie) if p)
        ticket.intervention.problematique = (
            f"L'écran ({modele_et_sn or '[modèle + numéro de série à compléter]'}) "
            f"présente un dysfonctionnement sur site."
            + (f"\n\nDétails JOB MANAGER : {comments}" if comments else "")
        )
        ticket.procedure.travail_attendu = (
            "Procéder au remplacement de la pièce indiquée en respectant les "
            "procédures d'installation disponibles via le lien/token fourni.\n\n"
            "La pièce de remplacement aura déjà été livrée sur site avant "
            "l'intervention.\n\n"
            "Merci de laisser la ou les pièces remplacées sur site après l'intervention."
        )
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne,
            f"Support technique niveau 3 (difficulté technique) : {SUPPORT_N3_PIECE}\n"
            f"Contact client : {CONTACT_CLIENT_PIECE}\n"
            f"En cas de non-résolution, contacter le support IRIS au {SUPPORT_IRIS_PIECE} "
            f"avant de quitter le site.",
        )
        notes.append(
            "Coordonnées de contact (support N3, contact client) copiées telles "
            "quelles depuis TOKI_PROMETHEAN.txt -- ce sont probablement des contacts "
            "ponctuels liés à un cas précis, PAS des contacts génériques permanents. À "
            "reconfirmer auprès de Sofiane avant d'automatiser plus largement."
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