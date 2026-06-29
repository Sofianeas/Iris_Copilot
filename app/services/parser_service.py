import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.intervention import Intervention
from app.models.logistics import Logistics
from app.models.procedure import Procedure
from app.models.validation import Validation

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

BASE_PROMPT_PATH = "prompts/base_prompt.txt"
CLIENT_RULES_DIR = "prompts/client_rules"


def load_base_prompt() -> str:
    with open(BASE_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_client_rules(nom_client: str) -> str:
    """
    Charge les règles de mapping spécifiques à un client, si elles existent.
    Retourne une chaîne vide si aucun fichier de règles n'existe pour ce client
    (extraction générique uniquement, pas d'erreur bloquante).
    """
    chemin = os.path.join(CLIENT_RULES_DIR, f"{nom_client.lower()}.txt")
    if not os.path.exists(chemin):
        return ""
    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()


def construire_prompt_complet(nom_client: str) -> str:
    """
    Assemble le prompt final : règles de base + règles spécifiques
    au client détecté (si disponibles).
    """
    base = load_base_prompt()
    regles_client = load_client_rules(nom_client)

    if regles_client:
        return (
            f"{base}\n\n"
            f"--- Règles de mapping spécifiques au client {nom_client} ---\n"
            f"{regles_client}"
        )

    return base


def analyser_mail(texte_mail: str, nom_client: str = "") -> str:
    """
    Envoie le mail à Gemini avec le prompt adapté au client détecté
    (ou le prompt générique seul si nom_client est vide/inconnu).
    """
    prompt = construire_prompt_complet(nom_client)
    full_prompt = f"{prompt}\n\nMail à analyser :\n{texte_mail}"

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    return response.text


def parser_reponse_en_ticket(reponse_texte: str) -> Ticket:
    """
    Transforme la réponse JSON de Gemini en objet Ticket.
    """
    try:
        data = json.loads(reponse_texte)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Réponse Gemini invalide, JSON non parsable : {e}\n"
            f"Réponse brute reçue :\n{reponse_texte}"
        )

    ticket = Ticket(
        customer=Customer(**data.get("customer", {})),
        intervention=Intervention(**data.get("intervention", {})),
        logistics=Logistics(**data.get("logistics", {})),
        procedure=Procedure(**data.get("procedure", {})),
        validation=Validation(**data.get("validation", {})),
    )

    return ticket


def traiter_mail(texte_mail: str, nom_client: str = "") -> Ticket:
    """
    Fonction principale : mail -> Ticket rempli.
    Le nom_client (déjà détecté en amont) permet de charger
    les règles de mapping adaptées.
    """
    reponse = analyser_mail(texte_mail, nom_client=nom_client)
    ticket = parser_reponse_en_ticket(reponse)
    return ticket