# tests/services/test_mail_documentation_pipeline.py
#
# WF-DOC-018 -- Teste le CABLAGE entre router_service.traiter_mail_complet
# (existant, non modifie) et enrichir_ticket_avec_documentation. Le
# comportement METIER de traiter_mail_complet (Gemini + 12 agents reels)
# n'est PAS testable dans ce sandbox (necessite GEMINI_API_KEY + les
# vrais fichiers agents) -- monkeypatche donc ici pour valider uniquement
# le bon ordre d'appel et la coherence du client transmis. Le
# comportement d'enrichir_ticket_avec_documentation lui-meme est deja
# valide avec de vrais composants dans test_documentation_enrichment_service.py.

import pytest

from app.models.ticket import Ticket
from app.repositories.in_memory_documentation_repository import InMemoryDocumentationRepository
from app.providers.static_documentation_provider import StaticDocumentationProvider
from app.services import mail_documentation_pipeline, router_service
from app.workflows.documentation_workflow import DocumentationWorkflow


def _workflow_reel_avec_reponse(client: str, question: str, reponse: str) -> DocumentationWorkflow:
    """Workflow reel (pas un fake), source StaticDocumentationProvider deja valide."""
    donnees = {client: {question.strip().lower(): reponse}}
    return DocumentationWorkflow(
        repository=InMemoryDocumentationRepository(),
        provider=StaticDocumentationProvider(donnees=donnees),
    )


def test_client_transmis_a_la_documentation_est_bien_celui_detecte(monkeypatch):
    """Vérifie que le CLIENT utilisé pour interroger la documentation est bien celui réellement détecté par router_service, pas une supposition séparée."""
    ticket_attendu = Ticket()

    monkeypatch.setattr(router_service, "detecter_client", lambda texte: "ADOPT")
    monkeypatch.setattr(router_service, "traiter_mail_complet", lambda texte, client_force=None: ticket_attendu)

    workflow = _workflow_reel_avec_reponse("ADOPT", "question test", "reponse ADOPT reelle")

    resultat = mail_documentation_pipeline.traiter_mail_avec_documentation(
        texte_mail="mail quelconque", documentation_workflow=workflow, question="question test",
    )

    assert "reponse ADOPT reelle" in resultat.intervention.commentaire_interne


def test_client_force_prioritaire_sur_la_detection(monkeypatch):
    """client_force doit être utilisé pour la documentation aussi, pas seulement pour traiter_mail_complet."""
    ticket_attendu = Ticket()

    appelle_avec = {}

    def fake_traiter_mail_complet(texte, client_force=None):
        appelle_avec["client_force"] = client_force
        return ticket_attendu

    monkeypatch.setattr(router_service, "detecter_client", lambda texte: "MAUVAIS_CLIENT")
    monkeypatch.setattr(router_service, "traiter_mail_complet", fake_traiter_mail_complet)

    workflow = _workflow_reel_avec_reponse("BARRON", "question test", "reponse BARRON reelle")

    resultat = mail_documentation_pipeline.traiter_mail_avec_documentation(
        texte_mail="mail quelconque", documentation_workflow=workflow, question="question test",
        client_force="BARRON",
    )

    assert appelle_avec["client_force"] == "BARRON"
    assert "reponse BARRON reelle" in resultat.intervention.commentaire_interne


def test_ticket_retourne_par_traiter_mail_complet_est_bien_celui_enrichi(monkeypatch):
    """Le Ticket enrichi par la documentation doit être le MÊME objet que celui produit par traiter_mail_complet, pas un nouveau Ticket vide."""
    ticket_reel = Ticket()
    ticket_reel.intervention.contrat = "Contrat deja rempli par l'agent"

    monkeypatch.setattr(router_service, "detecter_client", lambda texte: "ADOPT")
    monkeypatch.setattr(router_service, "traiter_mail_complet", lambda texte, client_force=None: ticket_reel)

    workflow = _workflow_reel_avec_reponse("ADOPT", "question test", "reponse doc")

    resultat = mail_documentation_pipeline.traiter_mail_avec_documentation(
        texte_mail="mail quelconque", documentation_workflow=workflow, question="question test",
    )

    assert resultat.intervention.contrat == "Contrat deja rempli par l'agent"
    assert "reponse doc" in resultat.intervention.commentaire_interne


def test_exception_traiter_mail_complet_remonte_sans_etre_avalee(monkeypatch):
    """Si traiter_mail_complet echoue (client non reconnu, cas reel de router_service.py), l'exception doit remonter -- pas etre masquee par le pipeline de composition."""
    def fake_qui_echoue(texte, client_force=None):
        raise ValueError("Client non reconnu dans ce mail.")

    monkeypatch.setattr(router_service, "traiter_mail_complet", fake_qui_echoue)

    workflow = _workflow_reel_avec_reponse("ADOPT", "question test", "reponse")

    with pytest.raises(ValueError, match="Client non reconnu"):
        mail_documentation_pipeline.traiter_mail_avec_documentation(
            texte_mail="mail non reconnaissable", documentation_workflow=workflow, question="question test",
        )

# Ajout à tests/services/test_mail_documentation_pipeline.py

def test_fichier_client_transmis_a_la_documentation_est_bien_celui_detecte(monkeypatch):
    """Équivalent fichier de test_client_transmis_a_la_documentation_est_bien_celui_detecte."""
    ticket_attendu = Ticket()

    monkeypatch.setattr(router_service, "detecter_client", lambda texte: "AXE_ESANTE")
    monkeypatch.setattr(
        router_service, "traiter_fichier_complet",
        lambda texte, fichier=None, client_force=None: ticket_attendu,
    )

    workflow = _workflow_reel_avec_reponse("AXE_ESANTE", "question test", "reponse AXE_ESANTE reelle")

    resultat = mail_documentation_pipeline.traiter_fichier_avec_documentation(
        texte_mail="mail quelconque", documentation_workflow=workflow, question="question test",
        fichier="fichier_bidon.xlsx",
    )

    assert "reponse AXE_ESANTE reelle" in resultat.intervention.commentaire_interne


def test_fichier_est_bien_transmis_a_traiter_fichier_complet(monkeypatch):
    """Vérifie que le paramètre fichier est bien propagé, pas perdu en chemin."""
    ticket_attendu = Ticket()
    appelle_avec = {}

    def fake_traiter_fichier_complet(texte, fichier=None, client_force=None):
        appelle_avec["fichier"] = fichier
        return ticket_attendu

    monkeypatch.setattr(router_service, "detecter_client", lambda texte: "ETAM")
    monkeypatch.setattr(router_service, "traiter_fichier_complet", fake_traiter_fichier_complet)

    workflow = _workflow_reel_avec_reponse("ETAM", "question test", "reponse ETAM")

    mail_documentation_pipeline.traiter_fichier_avec_documentation(
        texte_mail="mail quelconque", documentation_workflow=workflow, question="question test",
        fichier="mon_fichier.xlsx",
    )

    assert appelle_avec["fichier"] == "mon_fichier.xlsx"


def test_fichier_exception_traiter_fichier_complet_remonte(monkeypatch):
    """AXE_ESANTE/ETAM lèvent ValueError si le fichier requis est absent (cas réel de router_service.py) -- doit remonter, pas être avalé."""
    def fake_qui_echoue(texte, fichier=None, client_force=None):
        raise ValueError("AXE E-SANTE nécessite la pièce jointe Excel.")

    monkeypatch.setattr(router_service, "traiter_fichier_complet", fake_qui_echoue)

    workflow = _workflow_reel_avec_reponse("AXE_ESANTE", "question test", "reponse")

    with pytest.raises(ValueError, match="pièce jointe Excel"):
        mail_documentation_pipeline.traiter_fichier_avec_documentation(
            texte_mail="mail sans fichier", documentation_workflow=workflow, question="question test",
        )