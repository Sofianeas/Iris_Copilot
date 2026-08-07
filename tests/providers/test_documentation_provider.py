# tests/providers/test_documentation_provider.py
#
# Tests du contrat DocumentationProvider -- aucune implémentation
# concrète n'existe encore (pas de ChromaDB, cf. WF-DOC-002). Vérifie
# uniquement le CONTRAT abstrait, via une sous-classe factice.

import pytest

from app.providers.base_provider import BaseProvider
from app.providers.documentation_provider import DocumentationProvider


def test_documentation_provider_non_instantiable_directement():
    with pytest.raises(TypeError):
        DocumentationProvider()


def test_sous_classe_complete_instantiable_et_fonctionnelle():
    class DocumentationProviderFactice(DocumentationProvider):
        def fetch(self, request):
            client, question = request
            if client == "ADOPT" and "CATO" in question:
                return "Voir Anne ou David via Teams."
            return None

    provider = DocumentationProviderFactice()

    assert provider.fetch(("ADOPT", "Comment gerer un CATO ?")) == "Voir Anne ou David via Teams."
    assert provider.fetch(("ADOPT", "Question sans rapport")) is None
    assert provider.fetch(("AUTRE_CLIENT", "CATO")) is None  # isolation stricte par client


def test_sous_classe_incomplete_non_instantiable():
    class ProviderIncomplet(DocumentationProvider):
        pass  # fetch() non implémentée (héritée de BaseProvider)

    with pytest.raises(TypeError):
        ProviderIncomplet()


def test_documentation_provider_est_bien_une_base_provider():
    class DocumentationProviderFactice(DocumentationProvider):
        def fetch(self, request):
            return None

    provider = DocumentationProviderFactice()
    assert isinstance(provider, BaseProvider)