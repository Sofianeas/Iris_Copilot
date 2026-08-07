"""
app/providers/documentation_provider.py

Contrat spécifique au domaine Documentation, spécialisant BaseProvider
(WF-DOC-002). Reste ABSTRAIT -- aucune implémentation concrète (pas de
ChromaDB, pas d'appel réseau, pas de SDK). Sera implémenté plus tard par
un Provider concret (ex. ChromaDocumentationProvider), mission future non
anticipée ici.
"""

from abc import ABC

from app.providers.base_provider import BaseProvider

# (client, question) -- même forme que le besoin déjà démontré par
# DocumentationWorkflowRequest, mais volontairement un tuple simple plutôt
# qu'un nouveau dataclass : un Provider est une couche d'infrastructure,
# il ne doit jamais dépendre directement d'un contrat de Workflow
# spécifique (éviterait un couplage de couche). À reconsidérer si ce
# tuple s'avère peu lisible en pratique -- point ouvert, non tranché ici.
DocumentationQuery = tuple[str, str]


class DocumentationProvider(BaseProvider[DocumentationQuery, str], ABC):
    """
    Spécialisation de BaseProvider pour le domaine Documentation.

    `fetch((client, question)) -> str | None` -- reçoit une requête
    (client, question) et retourne le contenu brut trouvé par la source
    externe, avant toute interprétation par le Workflow ou le Repository.

    Aucune méthode supplémentaire n'est ajoutée : contrairement à
    DocumentationRepository (où `get_by_id` seul ne suffisait pas),
    `fetch()` hérité de BaseProvider couvre déjà exactement le besoin --
    une requête, un résultat.
    """

    pass