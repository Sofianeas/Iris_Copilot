# tests/repositories/test_documentation_repository.py
#
# Tests du contrat DocumentationRepository -- aucune implémentation
# concrète n'existe encore (pas de ChromaDB, cf. WF-DOC-002). Vérifie
# uniquement le CONTRAT abstrait, via une sous-classe factice.

import pytest

from app.repositories.documentation_repository import DocumentationRepository


def test_documentation_repository_non_instantiable_directement():
    with pytest.raises(TypeError):
        DocumentationRepository()


def test_sous_classe_complete_instantiable_et_fonctionnelle():
    class DocumentationRepositoryFactice(DocumentationRepository):
        def __init__(self):
            self._stockage = {}

        def save(self, entity):
            self._stockage[entity] = entity

        def get_by_id(self, entity_id):
            return self._stockage.get(entity_id)

        def find_by_question(self, client, question):
            if client == "ADOPT" and "CATO" in question:
                return "Voir Anne ou David via Teams (conversation CDS Alger)."
            return None

    repo = DocumentationRepositoryFactice()

    assert repo.find_by_question("ADOPT", "Comment gerer un CATO ?") == "Voir Anne ou David via Teams (conversation CDS Alger)."
    assert repo.find_by_question("ADOPT", "Question sans rapport") is None
    assert repo.find_by_question("AUTRE_CLIENT", "CATO") is None  # isolation stricte par client


def test_sous_classe_manquant_find_by_question_non_instantiable():
    class RepositoryIncomplet(DocumentationRepository):
        def save(self, entity):
            pass

        def get_by_id(self, entity_id):
            return None
        # find_by_question() non implémentée

    with pytest.raises(TypeError):
        RepositoryIncomplet()


def test_sous_classe_manquant_save_non_instantiable():
    class RepositoryIncomplet(DocumentationRepository):
        def get_by_id(self, entity_id):
            return None

        def find_by_question(self, client, question):
            return None
        # save() non implémentée (héritée de BaseRepository)

    with pytest.raises(TypeError):
        RepositoryIncomplet()


def test_documentation_repository_est_bien_une_base_repository():
    from app.repositories.base_repository import BaseRepository

    class DocumentationRepositoryFactice(DocumentationRepository):
        def save(self, entity):
            pass

        def get_by_id(self, entity_id):
            return None

        def find_by_question(self, client, question):
            return None

    repo = DocumentationRepositoryFactice()
    assert isinstance(repo, BaseRepository)