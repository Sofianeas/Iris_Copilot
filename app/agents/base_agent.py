"""
app/agents/base_agent.py

Classe de base abstraite du Framework des Agents (P3-424). Formalise
UNIQUEMENT le contrat public commun -- aucune logique métier, aucune
implémentation par défaut, aucune connaissance de Streamlit/Pages/
Repositories/Providers/Rule Engine.

Chaque agent concret (AdoptAgent, BarronAgent, ButAgent, ...) hérite de
cette classe et implémente `analyze()`. Les fonctions historiques
(`enrich_ticket`, `enrich_ticket_depuis_excel`, etc.) restent présentes en
parallèle, dans leurs modules respectifs, comme adaptateurs de
compatibilité vers `analyze()` -- cf. stratégie de migration P3-424.
"""

from abc import ABC, abstractmethod

from app.models.agent_contracts import AgentRequest, AgentResult


class BaseAgent(ABC):
    """
    Contrat commun à tous les agents clients. Une seule méthode publique :
    `analyze`. Un agent :
      - ne détecte jamais le client (fait par MailAnalysisService) ;
      - ne construit jamais le workflow ;
      - ne connaît jamais Streamlit, les Pages, les Repositories, les
        Providers ;
      - ne pilote jamais le Rule Engine (peut recevoir une RagDecision
        déjà calculée via `request.rag_decision`, ne la calcule jamais
        lui-même) ;
      - reçoit uniquement un AgentRequest, retourne uniquement un
        AgentResult (jamais un Ticket nu).
    """

    @abstractmethod
    def analyze(self, request: AgentRequest) -> AgentResult:
        """
        Enrichit `request.ticket` selon les règles métier du client
        concerné, et retourne le résultat sous forme d'AgentResult.
        Ne lève jamais d'exception métier non gérée vers l'appelant --
        toute erreur doit être reflétée dans `AgentResult.succes`/`erreur`.
        """
        raise NotImplementedError