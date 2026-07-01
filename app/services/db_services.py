"""
Service de persistance des tickets validés (SQLite).

⚠️ DÉCISION DE SCOPE (V1 minimale, à valider/faire évoluer en phase
   ANALYTICS) : chaque ticket est stocké en 2 formes -- (a) une sérialisation
   JSON complète du Ticket (dataclasses.asdict), source de vérité fidèle à
   100% au modèle Python actuel, et (b) quelques colonnes indexées
   (client/enseigne/ville/code_site/numéro incident) pour permettre une
   recherche basique immédiate sans dépendre d'un schéma SQL détaillé.

   Ce n'est PAS le schéma normalisé (MTTR, statut, date_cloture, etc.) déjà
   esquissé pour la phase ANALYTICS (cf. skill iris-copilot-data-analytics)
   -- cette table `tickets` est un stockage V1 volontairement simple, pensé
   pour être migré/étendu plus tard sans perdre de données (le JSON complet
   permet de reconstruire n'importe quel nouveau schéma a posteriori).
"""

import dataclasses
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.models.ticket import Ticket

# app/services/db_service.py -> remonte à la racine du projet (2 parents).
DB_PATH = Path(__file__).resolve().parent.parent.parent / "tickets.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_creation TEXT NOT NULL,
    client TEXT,
    enseigne TEXT,
    ville TEXT,
    code_site TEXT,
    numero_incident_client TEXT,
    texte_mail_original TEXT,
    ticket_json TEXT NOT NULL
);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Connexion SQLite avec row_factory pour un accès par nom de colonne."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Crée la table `tickets` si elle n'existe pas encore. Idempotent."""
    conn = get_connection(db_path)
    try:
        conn.execute(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def save_ticket(ticket: Ticket, texte_mail_original: str = "", db_path: Path = DB_PATH) -> int:
    """
    Sauvegarde un Ticket validé. Retourne l'id de la ligne insérée.
    `texte_mail_original` est conservé pour traçabilité / debug futur
    (permet de rejouer un agent sur un cas réel si un bug est découvert
    plus tard, comme on l'a fait plusieurs fois pendant le développement).
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        payload = json.dumps(dataclasses.asdict(ticket), ensure_ascii=False)
        curseur = conn.execute(
            """
            INSERT INTO tickets
                (date_creation, client, enseigne, ville, code_site,
                 numero_incident_client, texte_mail_original, ticket_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                ticket.customer.client,
                ticket.customer.enseigne,
                ticket.customer.ville,
                ticket.customer.code_site,
                ticket.intervention.numero_incident_client,
                texte_mail_original,
                payload,
            ),
        )
        conn.commit()
        return curseur.lastrowid
    finally:
        conn.close()


def lister_derniers_tickets(limite: int = 10, db_path: Path = DB_PATH) -> list[sqlite3.Row]:
    """Liste les derniers tickets enregistrés (résumé, pas le JSON complet) -- pour affichage rapide."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        return conn.execute(
            """
            SELECT id, date_creation, client, enseigne, ville, numero_incident_client
            FROM tickets
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,),
        ).fetchall()
    finally:
        conn.close()