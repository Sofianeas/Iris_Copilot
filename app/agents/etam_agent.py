"""
Agent ETAM.

Logique métier issue de ETAM.docx + TOKI_ETAM.txt.

⚠️ AVERTISSEMENT IMPORTANT : la structure de lecture (`lire_champs_etam`)
est déduite d'une CAPTURE D'ÉCRAN fournie par Sofiane, PAS d'un vrai fichier
.xlsx inspecté (contrairement à AXE E-SANTE où on a pu lire le vrai
fichier). La logique métier (branche Mobilité/Smartphone, règle A52,
LOG-SWAP-UPS...) est testée et fiable ; la lecture de cellules par
POSITION DE COLONNE (A=Label, B=Valeur, C=Valeur secondaire pour le seul
champ "Matériel à préparer") est une hypothèse à confirmer contre le vrai
fichier.

Couverture de cette version :
- Branche "Maintenance Mobilité" / sous-cas Smartphone Samsung (Swap
  Transporteur) : entièrement implémentée et testée contre l'exemple
  fourni (ETAM Lingerie 0351, Samsung A54 demandé -> A52 imposé).
- Branches TPE ETAM / IMAC / Slovaquie & RT : détection de branche
  implémentée, mais SEULES les règles communes sont appliquées (pas
  d'exemple réel disponible pour ces 3 branches à ce jour) -> toujours
  signalé, jamais fabriqué.

Règles clés de la branche Mobilité/Smartphone :
- Type = "Swap Transporteur" (TOKI : "Intégration + envoi avec swap
  transporteur" pour les smartphones Samsung) -> pas d'intervention sur site.
- ⚠️ RÈGLE CRITIQUE (TOKI_ETAM.txt, "Consigne client") : prioriser
  SYSTÉMATIQUEMENT l'A52 sur chaque ticket de maintenance, MÊME SI Akkodis
  demande explicitement un A54 ou un A56. Cet agent applique cette priorité
  et le signale -- ne JAMAIS relayer tel quel le modèle demandé dans le
  formulaire sans appliquer cette règle.
- "Panne" -> transporteur AFFRETEMENT SANS + référence LOG-SWAP-UPS.
  "Perte/Vol" -> transporteur CLIENT SANS, PAS de LOG-SWAP-UPS.
- Code client ETAM vs INVEST21 : INVEST21 si l'enseigne n'est PAS "Etam"
  elle-même (ex. Undiz, Maison 123 sous le même groupe) -- ne pas confondre
  ETAM et ERAM (clients différents).
- Technicien anglophone déduit du champ "Langue" du formulaire (donnée
  fournie directement, plus fiable qu'une déduction depuis le pays).
- "Noter le nom du matériel dans le champ TAG de FootPrints" (TOKI) :
  IGNORÉ -- FootPrints est l'ancien logiciel, non utilisé (confirmé par
  Sofiane), cette instruction ne s'applique plus.
"""

import re
import unicodedata

from openpyxl import load_workbook

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
# Lecture du fichier ETAM (structure déduite d'une capture d'écran, cf.
# avertissement du docstring)
# --------------------------------------------------------------------------

SECTIONS_CONNUES = {
    "information sur l'enseigne": "enseigne",
    "information technique du materiel en panne": "panne",
    "information technique du materiel a preparer": "preparer",
    "description de l'incident rencontre": "incident",
    "information n": "incident_akkodis",
}


def detecter_section(label_normalise: str) -> str:
    """Détecte une ligne de titre de section (cf. SECTIONS_CONNUES)."""
    for motif, cle in SECTIONS_CONNUES.items():
        if label_normalise.startswith(motif):
            return cle
    return ""


def construire_cle(section: str, label_normalise: str) -> str:
    """Mappe (section_courante, label) -> clé interne. 'materiel (modele)' est ambigu (2 occurrences) -> dépend de la section."""
    if label_normalise.startswith("code magasin"):
        return "code_magasin"
    if label_normalise.startswith("adresse de livraison"):
        return "adresse_livraison"
    if label_normalise.startswith("nom et n"):
        return "contact_nom"
    if label_normalise.startswith("adresse mail du site"):
        return "email_site"
    if label_normalise.startswith("materiel (modele)") or label_normalise.startswith("materiel(modele)"):
        if section == "panne":
            return "materiel_panne"
        if section == "preparer":
            return "materiel_preparer"
        return ""
    if label_normalise.startswith("numero de serie"):
        return "numero_serie"
    if label_normalise.startswith("pays"):
        return "pays"
    if label_normalise.startswith("langue"):
        return "langue"
    if label_normalise.startswith("typologie panne"):
        return "typologie_panne"
    if label_normalise.startswith("description panne"):
        return "description_panne"
    if label_normalise.startswith("tests effectues"):
        return "tests_effectues"
    if label_normalise.startswith("commentaires"):
        return "commentaires"
    if label_normalise.startswith("n") and "dossier akkodis" in label_normalise:
        return "numero_dossier_akkodis"
    return ""


def lire_champs_etam(fichier, feuille: str | None = None) -> dict:
    """
    Lit le fichier ETAM. Hypothèse de colonnes (NON VÉRIFIÉE contre un vrai
    fichier, cf. avertissement du docstring) : A=Label, B=Valeur, C=Valeur
    secondaire UNIQUEMENT pour "Matériel (Modèle) à préparer" (qui porte à
    la fois une description humaine en B et les références Pivot en C).
    """
    wb = load_workbook(fichier, data_only=True)
    ws = wb[feuille] if feuille else wb.active

    resultat: dict[str, str] = {}
    section_courante = ""
    for row in ws.iter_rows():
        cells = list(row)
        label_brut = str(cells[0].value).strip() if len(cells) > 0 and cells[0].value else ""
        valeur_b = str(cells[1].value).strip() if len(cells) > 1 and cells[1].value else ""
        valeur_c = str(cells[2].value).strip() if len(cells) > 2 and cells[2].value else ""

        if not label_brut:
            continue
        label_normalise = _normaliser(label_brut)

        section_detectee = detecter_section(label_normalise)
        if section_detectee and not valeur_b:
            section_courante = section_detectee
            continue

        cle = construire_cle(section_courante, label_normalise)
        if not cle:
            continue

        if cle == "materiel_preparer":
            resultat["materiel_preparer_description"] = valeur_b
            resultat["materiel_preparer"] = valeur_c or valeur_b
        else:
            resultat[cle] = valeur_b

    return resultat


# --------------------------------------------------------------------------
# Parsing du bloc adresse (multi-lignes, cf. exemple ETAM Lingerie)
# --------------------------------------------------------------------------

RE_ENSEIGNE_CODE = re.compile(r"^(.+?)\s*\(n°?\s*(\d+)\)", re.IGNORECASE)
RE_CP_VILLE = re.compile(r"^(\d{4,5})\s+(.+)$")
RE_TEL = re.compile(r"t[ée]l\s*:?\s*(.+)", re.IGNORECASE)
RE_PREFIXE_INTL_FR = re.compile(r"0033\s*\(0\)\s*")


def normaliser_telephone_fr_intl(numero: str) -> str:
    """Convertit '0033 (0) 4 67 64 04 46' -> '04 67 64 04 46' (format national FR)."""
    if not numero:
        return numero
    return RE_PREFIXE_INTL_FR.sub("0", numero).strip()


def parser_bloc_adresse_etam(bloc: str) -> dict:
    """
    Parse le bloc multi-lignes "Adresse de livraison et d'enlèvement" :
      "<Enseigne> (n° <code>)
       [<complément, ex. nom du centre commercial>]
       <rue>
       <CP> <Ville>
       <PAYS>
       Tél : <numéro>"
    """
    resultat = {
        "enseigne": "", "code_magasin": "", "complement_adresse": "",
        "adresse": "", "code_postal": "", "ville": "", "pays": "", "telephone_site": "",
    }
    if not bloc:
        return resultat

    lignes_restantes = []
    for ligne in (l.strip() for l in bloc.splitlines() if l.strip()):
        m_enseigne = RE_ENSEIGNE_CODE.match(ligne)
        if m_enseigne:
            resultat["enseigne"] = m_enseigne.group(1).strip()
            resultat["code_magasin"] = m_enseigne.group(2).strip()
            continue
        m_tel = RE_TEL.match(ligne)
        if m_tel:
            resultat["telephone_site"] = normaliser_telephone_fr_intl(m_tel.group(1).strip())
            continue
        m_cp_ville = RE_CP_VILLE.match(ligne)
        if m_cp_ville:
            resultat["code_postal"] = m_cp_ville.group(1).strip()
            resultat["ville"] = m_cp_ville.group(2).strip()
            continue
        lignes_restantes.append(ligne)

    if lignes_restantes:
        derniere = lignes_restantes[-1]
        if derniere.isupper() and len(derniere) < 30:
            resultat["pays"] = derniere
            lignes_restantes = lignes_restantes[:-1]
        if lignes_restantes:
            resultat["adresse"] = lignes_restantes[-1]
            if len(lignes_restantes) > 1:
                resultat["complement_adresse"] = " ".join(lignes_restantes[:-1])

    return resultat


# --------------------------------------------------------------------------
# Référentiel ETAM (issu de TOKI_ETAM.txt)
# --------------------------------------------------------------------------

BUNDLE_A52 = (
    "CETAMOB-SAMSUNG-A52-5G",
    "SMARTPHONE SAMSUNG A52-5G – ETAM – SPARE (inclut téléphone, verre trempé, coque, tour de cou)",
)
REF_LOG_SWAP_UPS = "LOG-SWAP-UPS"


def detecter_modele_samsung(texte: str) -> str:
    """A52 / A54 / A56, détecté dans le matériel demandé."""
    texte_n = _normaliser(texte)
    for modele in ("a52", "a54", "a56"):
        if modele in texte_n:
            return modele.upper()
    return ""


def determiner_transporteur_et_swap(typologie_panne: str) -> tuple[str, bool, str]:
    """Panne -> AFFRETEMENT SANS + LOG-SWAP-UPS. Perte/Vol -> CLIENT SANS, pas de swap."""
    texte = _normaliser(typologie_panne)
    if "perte" in texte or "vol" in texte:
        return "CLIENT SANS", False, (
            "Typologie 'Perte/Vol' détectée : transporteur 'CLIENT SANS' appliqué, "
            "PAS de LOG-SWAP-UPS demandé (cf. TOKI_ETAM.txt)."
        )
    return "AFFRETEMENT SANS", True, ""


def determiner_code_client(enseigne: str) -> tuple[str, bool]:
    """ETAM.docx : INVEST21 si l'enseigne n'est pas Etam elle-même (ex. Undiz, Maison 123)."""
    if "etam" in _normaliser(enseigne):
        return "ETAM", True
    return "INVEST21", False


def technicien_anglophone_depuis_langue(langue: str) -> tuple[bool, bool]:
    """Retourne (technicien_anglophone, langue_reconnue) -- depuis le champ Langue du formulaire."""
    langue_n = _normaliser(langue)
    if not langue_n:
        return False, False
    if "francais" in langue_n or "french" in langue_n:
        return False, True
    return True, True


def detecter_branche(materiel_panne: str, materiel_preparer: str) -> tuple[str, bool]:
    """
    Déduit la branche ETAM (TPE / MOBILITE / IMAC / SLOVAQUIE_RT).
    Retourne (branche, confiant) -- confiant=False si c'est un repli par
    défaut plutôt qu'une détection explicite par mot-clé.
    """
    texte = _normaliser(f"{materiel_panne} {materiel_preparer}")
    if any(mot in texte for mot in ("p400", "v400m", "adyen", "terminal de paiement", " tpe ", "tpe ")):
        return "TPE", True
    if any(mot in texte for mot in (
        "samsung", "smartphone", "ipad", "tablette", "douchette", "zebra",
        "pathfinder", "rfid", "sco", "kiosk", "tabletop",
    )):
        return "MOBILITE", True
    if any(mot in texte for mot in ("fermeture", "ouverture", "ajout materiel", "ramassage materiel", "transfert boutique")):
        return "IMAC", True
    return "MOBILITE", False  # branche la plus fréquemment observée à ce jour, à confirmer si erroné


# --------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------

def enrich_ticket_depuis_fichier(ticket: Ticket, fichier_etam, texte_mail: str = "") -> Ticket:
    """
    Enrichit un Ticket à partir du fichier ETAM (xlsx -- structure déduite
    d'une capture d'écran, cf. avertissement du docstring du module) et, en
    complément, du texte du mail s'il porte les mêmes informations (Sofiane :
    "ils envoient ça comme fichier mais parfois directement dans le mail").
    """
    notes: list[str] = []

    champs = lire_champs_etam(fichier_etam)

    # --- Bloc adresse ---
    bloc_adresse = parser_bloc_adresse_etam(champs.get("adresse_livraison", ""))

    code_magasin = champs.get("code_magasin") or bloc_adresse["code_magasin"]
    if champs.get("code_magasin") and bloc_adresse["code_magasin"] and champs["code_magasin"] != bloc_adresse["code_magasin"]:
        notes.append(
            f"Code magasin incohérent entre le champ dédié ({champs['code_magasin']!r}) "
            f"et le bloc adresse ({bloc_adresse['code_magasin']!r}) — à vérifier."
        )
    if code_magasin and not re.fullmatch(r"\d{4}", code_magasin.strip()):
        notes.append(f"Code magasin inhabituel ({code_magasin!r}) — attendu sur 4 chiffres, à vérifier.")
    ticket.customer.code_site = code_magasin

    enseigne = bloc_adresse["enseigne"]
    ticket.customer.enseigne = enseigne
    code_client, reconnu_etam = determiner_code_client(enseigne)
    ticket.customer.client = code_client
    if not reconnu_etam:
        notes.append(
            f"Enseigne '{enseigne}' différente de Etam -- code client 'INVEST21' "
            f"appliqué au lieu de 'ETAM' (cf. ETAM.docx). Vérifier qu'il ne s'agit "
            f"pas d'ERAM (client différent, à ne pas confondre)."
        )

    ticket.customer.adresse = bloc_adresse["adresse"]
    ticket.customer.complement_adresse = bloc_adresse["complement_adresse"]
    ticket.customer.code_postal = bloc_adresse["code_postal"]
    ticket.customer.ville = bloc_adresse["ville"]
    ticket.customer.pays = champs.get("pays") or bloc_adresse["pays"]
    ticket.customer.fixe = bloc_adresse["telephone_site"]

    nom_contact = champs.get("contact_nom", "")
    if nom_contact:
        ticket.customer.prenom = nom_contact
        notes.append(
            f"Contact '{nom_contact!r}' placé dans prenom (un seul nom donné dans "
            f"le formulaire, pas de nom de famille distinct) — à corriger si besoin."
        )
    else:
        notes.append("Nom du contact sur site introuvable — à compléter manuellement.")
    ticket.customer.email = champs.get("email_site", "")

    # --- Branche ETAM ---
    branche, branche_confiante = detecter_branche(champs.get("materiel_panne", ""), champs.get("materiel_preparer", ""))
    notes.append(
        f"⚠️ BRANCHE déduite : « {branche} »"
        + ("" if branche_confiante else " (PAR DÉFAUT, aucun mot-clé déterminant trouvé)")
        + " — À CONFIRMER avant saisie."
    )

    ticket.intervention.type_intervention = "Contrat"
    ticket.intervention.numero_serie = champs.get("numero_serie", "")
    ticket.intervention.problematique = champs.get("description_panne", "")
    ticket.intervention.origine = "Email"
    ticket.intervention.numero_incident_client = champs.get("numero_dossier_akkodis", "")
    if not ticket.intervention.numero_incident_client:
        notes.append("N° Dossier Akkodis introuvable — Numéro d'incident client à compléter manuellement.")

    langue_anglophone, langue_reconnue = technicien_anglophone_depuis_langue(champs.get("langue", ""))
    ticket.procedure.technicien_anglophone = langue_anglophone
    if not langue_reconnue:
        notes.append("Champ 'Langue' non renseigné/non reconnu — technicien_anglophone=Non appliqué par défaut, à vérifier.")

    travail_attendu_parties = []
    if champs.get("tests_effectues"):
        travail_attendu_parties.append(f"Tests déjà effectués sur site : {champs['tests_effectues']}")
    if champs.get("commentaires"):
        travail_attendu_parties.append(f"Commentaire du demandeur : {champs['commentaires']}")
    ticket.procedure.travail_attendu = "\n\n".join(travail_attendu_parties)

    if branche == "MOBILITE":
        modele_demande = detecter_modele_samsung(champs.get("materiel_preparer", "") + " " + champs.get("materiel_preparer_description", ""))

        ticket.intervention.contrat = "Maintenance Mobilité"
        ticket.intervention.type = "Swap Transporteur"
        ticket.procedure.intervention_sur_site = False  # "Swap Transporteur pas d'intervention sur Site" (docx)

        if modele_demande in ("A54", "A56"):
            ticket.intervention.sous_type = "Smartphone"
            ticket.logistics.pieces = f"{BUNDLE_A52[0]} ({BUNDLE_A52[1]})"
            notes.append(
                f"⚠️ RÈGLE CLIENT APPLIQUÉE : le formulaire demande un {modele_demande}, "
                f"mais TOKI_ETAM.txt exige de prioriser SYSTÉMATIQUEMENT l'A52 sur "
                f"chaque ticket de maintenance, même si Akkodis demande un A54/A56. "
                f"Référence A52 substituée — sauf rupture de stock A52 confirmée (à vérifier)."
            )
        elif modele_demande == "A52":
            ticket.intervention.sous_type = "Smartphone"
            ticket.logistics.pieces = f"{BUNDLE_A52[0]} ({BUNDLE_A52[1]})"
        else:
            notes.append(
                "Matériel mobilité non reconnu comme un smartphone Samsung "
                "(A52/A54/A56) — Type/Sous-type et pièce à compléter manuellement "
                "(douchette/iPad/imprimante non couverts par cette version de l'agent)."
            )

        ticket.logistics.besoin_materiel = True
        ticket.logistics.envoi_piece_par = "IRIS"
        transporteur, ajouter_swap, note_transporteur = determiner_transporteur_et_swap(champs.get("typologie_panne", ""))
        ticket.logistics.consigne_livraison = f"Transporteur : {transporteur}"
        if ajouter_swap and ticket.logistics.pieces:
            ticket.logistics.pieces = f"{ticket.logistics.pieces} + {REF_LOG_SWAP_UPS}"
        if note_transporteur:
            notes.append(note_transporteur)

        ville = ticket.customer.ville or ""
        ticket.intervention.intitule = " ".join(
            p for p in ("Maintenance Mobilité – Smartphone", enseigne, code_magasin, ville) if p
        )
        notes.append(
            "Intitulé construit sans règle stricte documentée pour la branche "
            "Mobilité (ETAM.docx ne donne pas de patron d'Intitulé pour cette "
            "branche, contrairement à TPE/IMAC) — format best-effort, à ajuster si besoin."
        )

    else:
        notes.append(
            f"Branche '{branche}' détectée mais NON ENCORE IMPLÉMENTÉE en détail "
            f"dans cet agent (seule la branche Mobilité/Smartphone a été testée "
            f"contre un exemple réel à ce jour) — seules les règles communes "
            f"(client, contrat='{branche}', origine) ont été appliquées, le reste "
            f"vient de l'extraction brute. Fournir un exemple réel de cette "
            f"branche pour la durcir."
        )
        ticket.intervention.contrat = branche

    if notes:
        bloc_notes = "⚠️ Points à vérifier (générés automatiquement) :\n" + "\n".join(f"- {n}" for n in notes)
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc_notes
        )

    return ticket