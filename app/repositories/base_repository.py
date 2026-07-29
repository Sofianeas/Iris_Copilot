"""
app/repositories/base_repository.py

Contrat commun de toute Repository du Framework Métier (P3-440.0).
Infrastructure PURE -- aucune implémentation concrète, aucun Repository
métier (TicketRepository, etc.) n'est créé dans cette mission.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Contrat commun de toute Repository. Une Repository encapsule la
    PERSISTANCE d'un objet métier (Ticket, historique, mémoire de
    corrections, cas similaires, etc.) -- elle :
      - ne connaît jamais le mécanisme de stockage concret au niveau du
        contrat (SQLite, fichier, ChromaDB...) -- chaque implémentation
        concrète choisit le sien ;
      - ne contient aucune logique métier ;
      - ne connaît jamais Streamlit, les Pages, les widgets ;
      - ne décide jamais de la suite du workflow (elle persiste ou
        retrouve, rien de plus).

    ⚠️ Proposition à valider (cf. mission P3-440.0) : les 2 méthodes
    ci-dessous couvrent le cas d'usage le plus évident (persister puis
    retrouver une entité par identifiant) mais ne préjugent pas des
    besoins futurs (recherche par critère, suppression, pagination,
    mise à jour partielle...) -- à étendre lors de la conception de la
    première Repository concrète, jamais dans cette classe de base sans
    validation architecturale préalable.
    """

    @abstractmethod
    def save(self, entity: T) -> None:
        """
        Persiste `entity`. Ne retourne rien -- une Repository ne décide
        jamais de la suite du workflow (ça reste la responsabilité du
        Service appelant).
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, entity_id: str) -> T | None:
        """Retourne l'entité correspondant à `entity_id`, ou None si absente."""
        raise NotImplementedError