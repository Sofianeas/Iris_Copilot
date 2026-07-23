"""
app/models/agent_contracts.py

Contrats officiels et GELÉS du Framework des Agents (P3-424). Ne pas
modifier -- toute évolution de ces contrats nécessite une validation
architecturale préalable (cf. décisions prises pendant P3-420/P3-424).

Ces contrats décrivent UNIQUEMENT des données -- aucun traitement, aucune
dépendance UI/service/agent concret/Gemini/SQLite/ChromaDB. `AgentRequest`
est produit par `MailAnalysisService` (jamais par un agent), `AgentResult`
est produit par un agent (jamais construit ailleurs).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app.models.rag_decision import RagDecision
from app.models.ticket import Ticket


@dataclass(frozen=True)
class AgentRequest:
    """
    Requête d'entrée d'un agent, construite exclusivement par
    `MailAnalysisService` (les agents ne construisent jamais leur propre
    `AgentRequest`).

    Attributs :
        ticket : le Ticket à enrichir -- vide ou partiellement rempli
            selon le client (cf. Règle 2 du Framework : le Ticket est créé
            avant l'agent, toujours, même pour les clients fichier où
            l'essentiel des données provient de `fichier_attache`).
        texte_mail : texte brut du mail. Toujours fourni, même pour les
            clients fichier (peut porter des informations complémentaires).
        fichier_attache : pièce jointe éventuelle (chemin, Path, ou flux
            binaire) -- requise pour les clients Groupe B (AXE E-SANTE,
            ETAM, DYNAMIZ PHARMA), absente sinon.
        rag_decision : une RagDecision déjà calculée en amont par le
            Service, si applicable. Aucun agent ne pilote jamais le Rule
            Engine ni ne calcule sa propre RagDecision (cf. Décision
            architecturale n°2 du Framework).
    """

    ticket: Ticket
    texte_mail: str
    fichier_attache: str | Path | BinaryIO | None = None
    rag_decision: RagDecision | None = None


@dataclass(frozen=True)
class AgentResult:
    """
    Résultat retourné par un agent après enrichissement. Un agent ne
    retourne JAMAIS un `Ticket` nu -- toujours un `AgentResult`.

    Attributs :
        ticket : le Ticket enrichi par l'agent.
        succes : indique si l'enrichissement a abouti normalement. `True`
            par défaut -- un agent qui enrichit correctement son Ticket
            n'a pas besoin de le préciser explicitement.
        erreur : message d'erreur lisible si succes=False, sinon None.
    """

    ticket: Ticket
    succes: bool = True
    erreur: str | None = None