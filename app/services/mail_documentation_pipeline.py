"""
app/services/mail_documentation_pipeline.py

Compose router_service.traiter_mail_complet()/traiter_fichier_complet()
(existants, NON MODIFIES) avec enrichir_ticket_avec_documentation()
(WF-DOC-017) -- point d'integration explicite entre l'analyse de
mail/fichier et le Workflow Documentation. N'invente aucune logique de
declenchement automatique : l'appelant fournit explicitement la question
a poser.
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
    Pipeline pour les clients texte-seul (cf. router_service.AGENTS_DISPONIBLES) :
    traiter_mail_complet() (detection + extraction + agent, INCHANGE) PUIS
    enrichir_ticket_avec_documentation() avec `question` fournie explicitement
    par l'appelant. Le client interroge pour la documentation est celui
    REELLEMENT detecte/impose par traiter_mail_complet (jamais suppose
    separement), pour garantir la coherence entre le Ticket produit et la
    documentation consultee.
    """
    client_reel = client_force or router_service.detecter_client(texte_mail)
    ticket = router_service.traiter_mail_complet(texte_mail, client_force=client_force)
    return enrichir_ticket_avec_documentation(ticket, client_reel, question, documentation_workflow)


def traiter_fichier_avec_documentation(
    texte_mail: str,
    documentation_workflow: DocumentationWorkflow,
    question: str,
    fichier=None,
    client_force: str | None = None,
) -> Ticket:
    """
    Équivalent de traiter_mail_avec_documentation() pour les clients dont
    la source de vérité est un fichier (cf. router_service.CLIENTS_FICHIER :
    AXE_ESANTE, ETAM, DYNAMIZ_PHARMA). Compose
    router_service.traiter_fichier_complet() (INCHANGE) avec
    enrichir_ticket_avec_documentation(), même logique de cohérence client
    que traiter_mail_avec_documentation().
    """
    client_reel = client_force or router_service.detecter_client(texte_mail)
    ticket = router_service.traiter_fichier_complet(texte_mail, fichier=fichier, client_force=client_force)
    return enrichir_ticket_avec_documentation(ticket, client_reel, question, documentation_workflow)