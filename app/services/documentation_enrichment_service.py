"""
app/services/documentation_enrichment_service.py

Connecte DocumentationWorkflow à un Ticket déjà construit (par un Agent
métier), pour enrichir commentaire_interne avec une réponse documentaire
pertinente (WF-DOC-017). Fonction pure, AUCUNE dépendance à
MailAnalysisService/router_service/parser_service -- réutilisable
indépendamment de la couche appelante.

Ne décide jamais QUAND interroger la documentation (pas de logique
métier ici) -- l'appelant fournit déjà `client` et `question`
explicitement. Ne modifie jamais un champ métier -- uniquement
`commentaire_interne`, même politique que le Rule Engine.
"""

from app.models.documentation_workflow import DocumentationWorkflowRequest
from app.models.ticket import Ticket
from app.workflows.documentation_workflow import DocumentationWorkflow


def _ajouter_si_absent(texte_existant: str, bloc: str) -> str:
    if not bloc:
        return texte_existant
    if texte_existant and bloc in texte_existant:
        return texte_existant
    if texte_existant:
        return f"{texte_existant.strip()}\n\n{bloc}"
    return bloc


def enrichir_ticket_avec_documentation(
    ticket: Ticket,
    client: str,
    question: str,
    documentation_workflow: DocumentationWorkflow,
) -> Ticket:
    """
    Interroge `documentation_workflow` (DocumentationWorkflow réel ou tout
    objet respectant son contrat) et, si une réponse est trouvée, l'ajoute
    à `ticket.intervention.commentaire_interne`. Ne modifie jamais un
    champ métier. Idempotent (n'ajoute pas de doublon si le bloc existe
    déjà -- même convention que tous les agents). Si le Workflow échoue
    ou ne trouve rien, le Ticket est retourné inchangé (pas d'erreur
    propagée, cohérent avec la politique "jamais bloquant" déjà en place
    pour le RAG/Rule Engine).
    """
    resultat = documentation_workflow.execute(
        DocumentationWorkflowRequest(client=client, question=question)
    )
    if resultat.succes and resultat.reponse:
        bloc = f"📚 Réponse documentaire ({resultat.source}) : {resultat.reponse}"
        ticket.intervention.commentaire_interne = _ajouter_si_absent(
            ticket.intervention.commentaire_interne, bloc
        )
    return ticket