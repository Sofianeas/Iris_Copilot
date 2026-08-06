# tests/base_components/test_base_repository.py
#
# Tests communs du contrat BaseRepository -- aucune implémentation
# concrète n'existe encore dans le projet (cf. P3-440.0/P3-440.1) ; ces
# tests valident uniquement le CONTRAT abstrait lui-même via une
# sous-classe factice.

import pytest

from app.repositories.base_repository import BaseRepository


def test_base_repository_non_instantiable_directement():
    with pytest.raises(TypeError):
        BaseRepository()


def test_sous_classe_complete_instantiable_et_fonctionnelle():
    class RepositoryFactice(BaseRepository):
        def __init__(self):
            self._stockage = {}

        def save(self, entity):
            self._stockage[entity["id"]] = entity

        def get_by_id(self, entity_id):
            return self._stockage.get(entity_id)

    repo = RepositoryFactice()
    repo.save({"id": "abc", "valeur": "test"})

    assert repo.get_by_id("abc") == {"id": "abc", "valeur": "test"}
    assert repo.get_by_id("inconnu") is None


def test_sous_classe_incomplete_manque_get_by_id_non_instantiable():
    class RepositoryIncomplete(BaseRepository):
        def save(self, entity):
            pass
        # get_by_id() non implémentée

    with pytest.raises(TypeError):
        RepositoryIncomplete()


def test_sous_classe_incomplete_manque_save_non_instantiable():
    class RepositoryIncomplete(BaseRepository):
        def get_by_id(self, entity_id):
            return None
        # save() non implémentée

    with pytest.raises(TypeError):
        RepositoryIncomplete()