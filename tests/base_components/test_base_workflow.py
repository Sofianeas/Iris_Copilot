# tests/base_components/test_base_workflow.py
#
# Tests communs du contrat BaseWorkflow -- ne teste aucun Workflow métier
# concret (aucun n'existe encore). Vérifie uniquement le CONTRAT lui-même,
# y compris son caractère générique (chaque Workflow définit ses propres
# WorkflowRequest/WorkflowResult concrets par héritage).

from dataclasses import dataclass

import pytest

from app.models.workflow_contracts import WorkflowRequest, WorkflowResult
from app.workflows.base_workflow import BaseWorkflow


def test_workflow_request_est_un_frozen_dataclass_vide():
    import dataclasses

    assert dataclasses.is_dataclass(WorkflowRequest)
    assert WorkflowRequest.__dataclass_params__.frozen is True
    assert WorkflowRequest() is not None  # instantiable vide


def test_workflow_result_est_un_frozen_dataclass_vide():
    import dataclasses

    assert dataclasses.is_dataclass(WorkflowResult)
    assert WorkflowResult.__dataclass_params__.frozen is True
    assert WorkflowResult() is not None


def test_base_workflow_non_instantiable_directement():
    with pytest.raises(TypeError):
        BaseWorkflow()


def test_sous_classe_complete_avec_contrats_herites_fonctionne():
    @dataclass(frozen=True)
    class RequeteFactice(WorkflowRequest):
        valeur: str = ""

    @dataclass(frozen=True)
    class ResultatFactice(WorkflowResult):
        succes: bool = True

    class WorkflowFactice(BaseWorkflow[RequeteFactice, ResultatFactice]):
        def execute(self, request: RequeteFactice) -> ResultatFactice:
            return ResultatFactice(succes=True)

    workflow = WorkflowFactice()
    resultat = workflow.execute(RequeteFactice(valeur="test"))

    assert isinstance(resultat, ResultatFactice)
    assert isinstance(resultat, WorkflowResult)  # héritage du marqueur respecté
    assert resultat.succes is True


def test_sous_classe_incomplete_non_instantiable():
    class WorkflowIncomplet(BaseWorkflow):
        pass  # execute() non implémentée

    with pytest.raises(TypeError):
        WorkflowIncomplet()