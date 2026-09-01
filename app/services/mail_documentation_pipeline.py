"""
app/services/mail_documentation_pipeline.py

Compose router_service.traiter_mail_complet() (existant, NON MODIFIE)
avec enrichir_ticket_avec_documentation() (WF-DOC-017) -- point
d'integration explicite entre l'analyse de mail et le Workflow
Documentation. N'invente aucune logique de declenchement automatique :
l'appelant fournit explicitement la question a poser.
"""

from app.models.ticket import Ticket
from app.services import router_service
from app.services.documentation_enrichment_service import enrichir_ticket_avec_documentation
from app.workflows.documentation_workflow import DocumentationWorkflow


def traiter_mail_avec_documentation(
    texte_mail: str,
    documentation_workflow: DocumentationWorkflow,
    question: str,
    client_force: str | None = None,
) -> Ticket:
    """
    Pipeline : router_service.traiter_mail_complet() (detection +
    extraction + agent, INCHANGE) PUIS enrichir_ticket_avec_documentation()
    avec `question` fournie explicitement par l'appelant -- ce module ne
    decide jamais QUAND interroger la documentation, seulement COMMENT
    enchainer les 2 etapes deja existantes.

    Le client interroge pour la documentation est celui REELEMENT
    detecte/impose par traiter_mail_complet (jamais suppose separement),
    pour garantir la coherence entre le Ticket produit et la
    documentation consultee.
    """
    client_reel = client_force or router_service.detecter_client(texte_mail)
    ticket = router_service.traiter_mail_complet(texte_mail, client_force=client_force)
    return enrichir_ticket_avec_documentation(ticket, client_reel, question, documentation_workflow)