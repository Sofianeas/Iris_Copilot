"""
app/models/workflow_contracts.py

Contrats communs de tout Workflow du Framework (WF-000). Aucune logique
métier, aucune dépendance UI/Repository/Provider/Service concret.

Contrairement à AgentRequest/AgentResult (forme fixe, tous les Agents
travaillent sur un Ticket), chaque Workflow a des besoins d'entrée/sortie
DIFFÉRENTS (ex. DocumentationWorkflowRequest : client+question ; un futur
HistoryWorkflowRequest aura probablement une forme totalement différente).
`WorkflowRequest`/`WorkflowResult` sont donc des classes MARQUEURS vides
-- chaque Workflow concret définit son propre contrat en héritant de
celles-ci, plutôt que d'utiliser directement des champs communs
(cf. philosophie déjà retenue pour BaseRepository[T]/BaseProvider[TInput,
TOutput] : générique, pas de forme imposée).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowRequest:
    """
    Classe marqueur de toute requête de Workflow. Ne porte aucun champ
    commun -- chaque Workflow concret définit les siens en héritant de
    cette classe (ex. `DocumentationWorkflowRequest(WorkflowRequest)`).

    Volontairement vide : ajouter un champ commun sans besoin concret
    démontré serait une abstraction anticipée, contraire à la
    gouvernance du Framework (cf. décision prise lors de P3-440.1).
    """

    pass


@dataclass(frozen=True)
class WorkflowResult:
    """
    Classe marqueur de tout résultat de Workflow. Ne porte aucun champ
    commun -- chaque Workflow concret définit les siens en héritant de
    cette classe (ex. `DocumentationWorkflowResult(WorkflowResult)`).
    """

    pass

