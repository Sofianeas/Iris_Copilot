# tests/base_components/test_base_provider.py
#
# Tests communs du contrat BaseProvider -- aucune implémentation concrète
# n'existe encore dans le projet (cf. P3-440.0/P3-440.1) ; ces tests
# valident uniquement le CONTRAT abstrait lui-même via une sous-classe
# factice.

import pytest

from app.providers.base_provider import BaseProvider


def test_base_provider_non_instantiable_directement():
    with pytest.raises(TypeError):
        BaseProvider()


def test_sous_classe_complete_instantiable_et_fonctionnelle():
    class ProviderFactice(BaseProvider):
        def fetch(self, request):
            return f"resultat pour {request}"

    provider = ProviderFactice()

    assert provider.fetch("question") == "resultat pour question"


def test_sous_classe_incomplete_non_instantiable():
    class ProviderIncomplet(BaseProvider):
        pass  # fetch() non implémentée

    with pytest.raises(TypeError):
        ProviderIncomplet()