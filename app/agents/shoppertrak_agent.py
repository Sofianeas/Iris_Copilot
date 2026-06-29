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
     des mails (cohérents entre eux) -- mais la liste Pivot pourrait
     comporter d'autres pays non visibles (scroll de la capture). À
     confirmer.
  2. L'Intitulé ("Enseigne Ville Code Site - <titre de la demande>") :
     le "<titre>" n'a pas de champ dédié dans le mail -- j'utilise "Maintenance
     caméra" par défaut quand le texte mentionne une caméra (cas des 3
     exemples fournis), sinon je laisse cette partie vide et je signale.
     Pas une règle générale validée pour tout type de demande ShopperTrak.
  3. Aucune règle pour Type/Sous-type/Matériel/Planification/Consignes et
     mission -- en attente des précisions de Sofiane.
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
# Référentiel SHOPPERTRAK
# --------------------------------------------------------------------------

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

# Ordre fixe des champs positionnels (cf. docstring) : (clé, libellés possibles à retirer si présents)
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
    """
    Retire un préfixe de label optionnel (ex: 'Pays : FRANCE' -> 'FRANCE').
    N'agit que si le label est suivi d'un vrai séparateur (':' ou espace) --
    sinon 'PAYS-BAS' serait amputé en '-BAS' (le label 'pays' matchant le
    début du nom du pays lui-même).
    """
    ligne = (ligne or "").strip()
    for motif in motifs_labels:
        pattern = re.compile(rf"^{motif}(?:\s*:\s*|\s+)", re.IGNORECASE)
        nouvelle = pattern.sub("", ligne)
        if nouvelle != ligne:
            return nouvelle.strip()
    return ligne


def extraire_champs_shoppertrak(texte: str) -> dict:
    """
    Extrait les 7 champs positionnels + la Problématique et demande
    (cf. docstring du module pour le format).
    """
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
    """
    "Enseigne Ville Code Site - <titre de la demande>" (cf. Sofiane).
    Retourne (intitule, titre_devine) -- titre_devine=False si on n'a pas
    pu déterminer le titre depuis la problématique (cf. hypothèse 2).
    """
    base = " ".join(p for p in (enseigne, ville, code_site) if p)
    if "camera" in _normaliser(problematique) or "caméra" in problematique.lower():
        return f"{base} - Maintenance caméra", True
    return base, False


# --------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------

def enrich_ticket(ticket: Ticket, texte_mail: str = "") -> Ticket:
    """
    Enrichit un Ticket avec les règles SHOPPERTRAK connues à ce jour
    (Site d'intervention, Contrat par pays, Intitulé). Volontairement
    incomplet -- cf. avertissement du docstring du module.
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

    return ticket