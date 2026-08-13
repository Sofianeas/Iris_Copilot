# tests/providers/test_static_documentation_provider.py
#
# Tests de la première implémentation concrète de DocumentationProvider
# (WF-DOC-009). Couvre les 8 exigences : instanciation, conformité au
# contrat, question connue/inconnue, isolation par client, absence de
# transformation, et le parcours COMPLET via un DocumentationWorkflow réel
# (pas seulement des fakes de test).

from app.models.documentation_workflow import DocumentationWorkflowRequest
from app.providers.base_provider import BaseProvider
from app.providers.documentation_provider import DocumentationProvider
from app.providers.static_documentation_provider import StaticDocumentationProvider, construire_donnees_demo
from app.repositories.documentation_repository import DocumentationRepository
from app.workflows.documentation_workflow import DocumentationWorkflow


# --------------------------------------------------------------------------
# 1-2 : instanciation et conformité au contrat
# --------------------------------------------------------------------------

def test_static_documentation_provider_instantiable():
    provider = StaticDocumentationProvider(donnees={})

    assert isinstance(provider, DocumentationProvider)
    assert isinstance(provider, BaseProvider)


# --------------------------------------------------------------------------
# 3-4 : question connue / inconnue
# --------------------------------------------------------------------------

def test_question_connue_retourne_la_bonne_reponse():
    provider = StaticDocumentationProvider(donnees=construire_donnees_demo())

    reponse = provider.fetch(("ADOPT", "Comment gérer une demande CATO ?"))

    assert reponse is not None
    assert "CATO" in reponse
    assert "Anne ou David" in reponse


def test_question_connue_avec_variation_de_casse_et_accents():
    """La normalisation (casse, accents) doit fonctionner -- pas une correspondance sensible à la casse stricte."""
    provider = StaticDocumentationProvider(donnees=construire_donnees_demo())

    reponse = provider.fetch(("ADOPT", "COMMENT GERER UNE DEMANDE cato ?"))

    assert reponse is not None
    assert "CATO" in reponse


def test_question_inconnue_retourne_none():
    provider = StaticDocumentationProvider(donnees=construire_donnees_demo())

    reponse = provider.fetch(("ADOPT", "Question totalement sans rapport"))

    assert reponse is None


def test_client_inconnu_retourne_none():
    provider = StaticDocumentationProvider(donnees=construire_donnees_demo())

    reponse = provider.fetch(("CLIENT_INEXISTANT", "Comment gérer une demande CATO ?"))

    assert reponse is None


# --------------------------------------------------------------------------
# 5 : isolation entre clients
# --------------------------------------------------------------------------

def test_isolation_entre_clients():
    """Une question qui existe pour ADOPT ne doit jamais répondre pour BARRON, même formulée à l'identique."""
    donnees = construire_donnees_demo()
    provider = StaticDocumentationProvider(donnees=donnees)

    reponse_adopt = provider.fetch(("ADOPT", "Comment gérer une demande CATO ?"))
    reponse_barron = provider.fetch(("BARRON", "Comment gérer une demande CATO ?"))

    assert reponse_adopt is not None
    assert reponse_barron is None  # BARRON n'a pas cette question dans ses donnees


# --------------------------------------------------------------------------
# 6 : absence de transformation inattendue de la réponse
# --------------------------------------------------------------------------

def test_reponse_retournee_verbatim_sans_transformation():
    texte_brut = "  Réponse AVEC espaces, Ponctuation!! et Accents éàç.  "
    provider = StaticDocumentationProvider(donnees={"CLIENT_X": {"question test": texte_brut}})

    reponse = provider.fetch(("CLIENT_X", "question test"))

    assert reponse == texte_brut  # identique bit a bit


# --------------------------------------------------------------------------
# 7-8 : le Workflow peut réellement utiliser ce Provider concret
# (parcours complet, pas seulement des fakes de test)
# --------------------------------------------------------------------------

class RepositoryToujoursVide(DocumentationRepository):
    """
    Implémentation concrète minimale, strictement limitée à cette
    démonstration -- retourne toujours None, pour forcer le fallback vers
    le Provider concret et prouver que la chaîne complète fonctionne.
    N'est PAS un mécanisme de persistance réel (aucune donnée stockée).
    """

    def save(self, entity):
        pass

    def get_by_id(self, entity_id):
        return None

    def find_by_question(self, client, question):
        return None


def test_parcours_complet_workflow_reel_avec_provider_concret():
    """
    Démontre que la chaîne architecturale complète fonctionne réellement :
    DocumentationWorkflowRequest -> DocumentationWorkflow ->
    DocumentationRepository (vide) -> fallback ->
    StaticDocumentationProvider (concret, réel) -> DocumentationWorkflowResult.
    """
    repository = RepositoryToujoursVide()
    provider = StaticDocumentationProvider(donnees=construire_donnees_demo())
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="BARRON", question="Que signifie PED chez ce client ?")
    )

    assert resultat.succes is True
    assert resultat.source == "provider"
    assert "TPE" in resultat.reponse
    assert "PED" in resultat.reponse


def test_parcours_complet_question_sans_reponse_echec_coherent():
    """Le parcours complet doit aussi retourner un DocumentationWorkflowResult cohérent quand rien n'est trouvé nulle part."""
    repository = RepositoryToujoursVide()
    provider = StaticDocumentationProvider(donnees=construire_donnees_demo())
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Question absente du dictionnaire statique")
    )

    assert resultat.succes is False
    assert resultat.reponse is None
    assert resultat.erreur is not None