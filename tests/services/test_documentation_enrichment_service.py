# tests/services/test_documentation_enrichment_service.py
#
# WF-DOC-017 -- Teste la connexion reelle entre un Ticket (tel que produit
# par un Agent metier, ex. le cas CATO d'ADOPT) et DocumentationWorkflow,
# via enrichir_ticket_avec_documentation(). Composants reels (pas de
# fakes) : InMemoryDocumentationRepository + VectorStoreDocumentationProvider
# + corpus ADOPT reel (memes extraits verifies que WF-DOC-015).

from app.models.ticket import Ticket
from app.repositories.in_memory_documentation_repository import InMemoryDocumentationRepository
from app.providers.vectorstore_documentation_provider import VectorStoreDocumentationProvider
from app.services.documentation_enrichment_service import enrichir_ticket_avec_documentation
from app.services.vectorstore_service import construire_chunks, construire_vectorstore, make_tfidf_embedder
from app.workflows.documentation_workflow import DocumentationWorkflow

ADOPT_DOCX_REEL = """ADOPT

*Client : ADOPT

*CONTRAT
Sélectionner le Contrat en fonction de la demande : 
     -On Demand France : Pour la France
     - Installation Boîtier CATO (Projet) : Pour l'installation de boîtier CATO (Si demande de ce genre, voir avec Anne ou David via Teams dans conversation CDS Alger)
"""


def _construire_workflow_reel(tmp_path):
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(ADOPT_DOCX_REEL, encoding="utf-8")
    dossier_persistance = tmp_path / "vectorstore"
    chunks = construire_chunks(dossier_sources)
    embedder = make_tfidf_embedder([c.texte for c in chunks])
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)

    repository = InMemoryDocumentationRepository()
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    return DocumentationWorkflow(repository=repository, provider=provider)


def test_enrichissement_reel_ticket_cato_adopt(tmp_path):
    workflow = _construire_workflow_reel(tmp_path)

    ticket = Ticket()
    ticket.intervention.commentaire_interne = (
        "ATTENTION : demande détectée comme Installation Boîtier CATO (Projet). "
        "Ne pas traiter automatiquement — voir avec Anne ou David via Teams "
        "(conversation CDS Alger) avant de poursuivre."
    )

    ticket_enrichi = enrichir_ticket_avec_documentation(
        ticket, client="ADOPT", question="Comment traiter une demande de boîtier CATO ?",
        documentation_workflow=workflow,
    )

    assert "📚 Réponse documentaire" in ticket_enrichi.intervention.commentaire_interne
    assert "CATO" in ticket_enrichi.intervention.commentaire_interne
    assert "ATTENTION" in ticket_enrichi.intervention.commentaire_interne


def test_idempotence_pas_de_doublon_si_appele_deux_fois(tmp_path):
    workflow = _construire_workflow_reel(tmp_path)
    ticket = Ticket()

    enrichir_ticket_avec_documentation(ticket, "ADOPT", "Comment traiter une demande de boîtier CATO ?", workflow)
    commentaire_apres_1_appel = ticket.intervention.commentaire_interne

    enrichir_ticket_avec_documentation(ticket, "ADOPT", "Comment traiter une demande de boîtier CATO ?", workflow)
    commentaire_apres_2_appels = ticket.intervention.commentaire_interne

    assert commentaire_apres_1_appel == commentaire_apres_2_appels


def test_aucun_champ_metier_modifie(tmp_path):
    workflow = _construire_workflow_reel(tmp_path)
    ticket = Ticket()
    ticket.intervention.contrat = "valeur_initiale"

    enrichir_ticket_avec_documentation(ticket, "ADOPT", "Comment traiter une demande de boîtier CATO ?", workflow)

    assert ticket.intervention.contrat == "valeur_initiale"


def test_aucune_reponse_trouvee_ticket_inchange(tmp_path):
    workflow = _construire_workflow_reel(tmp_path)
    ticket = Ticket()
    ticket.intervention.commentaire_interne = "commentaire original"

    ticket_resultat = enrichir_ticket_avec_documentation(
        ticket, client="CLIENT_INEXISTANT", question="question quelconque", documentation_workflow=workflow,
    )

    assert ticket_resultat.intervention.commentaire_interne == "commentaire original"

def test_isolation_par_client_avec_deux_corpus_distincts(tmp_path):
    """Vérifie que la connexion fonctionne pour un 2e client (BARRON), sans rien de câblé en dur pour ADOPT spécifiquement."""
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(ADOPT_DOCX_REEL, encoding="utf-8")
    (dossier_sources / "BARRON_MAC_CANN.docx").write_text(
        "BARRON MAC CANN\n\n*Note importante : Remplacer PED par TPE\n"
        "Pour information, chez Barron Mac Cann quand il est dit un PED c'est un TPE en France.\n",
        encoding="utf-8",
    )
    dossier_persistance = tmp_path / "vectorstore"
    chunks = construire_chunks(dossier_sources)
    embedder = make_tfidf_embedder([c.texte for c in chunks])
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)

    repository = InMemoryDocumentationRepository()
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    ticket_barron = Ticket()
    ticket_enrichi = enrichir_ticket_avec_documentation(
        ticket_barron, client="BARRON", question="Que signifie PED chez ce client ?", documentation_workflow=workflow,
    )

    assert "TPE" in ticket_enrichi.intervention.commentaire_interne
    assert "CATO" not in ticket_enrichi.intervention.commentaire_interne  # jamais de fuite du corpus ADOPT