"""
app/rules/base_rule.py

Contrat officiel de toute Rule du Framework (P3-430). Formalise
UNIQUEMENT le contrat public commun -- aucune logique métier, aucune
implémentation par défaut.

Une Rule :
  - possède une responsabilité unique ;
  - ne connaît jamais les Services, les Agents, les Repositories, les
    Providers ;
  - ne modifie jamais un champ métier du Ticket (lecture seule) ;
  - ne persiste jamais rien, n'appelle jamais Gemini/ChromaDB/Streamlit ;
  - retourne uniquement une liste de RuleRecommendation (jamais un
    Ticket, jamais None -- une liste vide si rien à signaler).
"""

from abc import ABC, abstractmethod

from app.models.rag_decision import RagDecision
from app.models.rule_recommendation import RuleRecommendation
from app.models.ticket import Ticket


class BaseRule(ABC):
    """
    Contrat commun à toutes les Rules. Une seule méthode publique :
    `evaluate`. Comme pour BaseAgent, aucune autre méthode publique ne
    doit être ajoutée.
    """

    @abstractmethod
    def evaluate(self, ticket: Ticket, rag_decision: RagDecision | None) -> list[RuleRecommendation]:
        """
        Évalue `ticket` (lecture seule) et retourne une liste de
        RuleRecommendation (vide si rien à signaler). Ne lève jamais
        d'exception métier non gérée -- une Rule qui échoue doit être
        isolée par l'appelant (RuleEngine), pas par elle-même.
        """
        raise NotImplementedError