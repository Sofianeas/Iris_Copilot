# tests/test_rag_integration_layer.py
#
# pytest. Lancer avec : pytest tests/test_rag_integration_layer.py -v

import dataclasses

import chromadb
import pytest

from app.models.ticket import Ticket
from app.services.rag_integration_layer import enrichir_commentaire_si_pertinent
from app.services.vectorstore_service import make_tfidf_embedder

CORPUS_TEST = {
    "TESTCLIENT": [
        ("procedures.docx", "docx", "Le contrat applicable pour TESTCLIENT est OD.TEST.001 - On Demand France."),
    ],
}


@pytest.fixture
def vectorstore_prepare(tmp_path):
    """Même mini-vectorstore que test_rag_fallback_service.py, un seul client suffit ici."""
    tous_les_textes = [texte for chunks in CORPUS_TEST.values() for (_src, _type, texte) in chunks]
    embed_fn = make_tfidf_embedder(tous_les_textes)

    store = chromadb.PersistentClient(path=str(tmp_path))
    for client, chunks in CORPUS_TEST.items():
        collection = store.create_collection(client.lower())
        textes = [texte for (_src, _type, texte) in chunks]
        collection.add(
            ids=[f"{client}-{i}" for i in range(len(chunks))],
            documents=textes,
            embeddings=embed_fn(textes),
            metadatas=[{"client": client, "source": src, "type_source": t} for (src, t, _texte) in chunks],
        )
    return tmp_path, embed_fn


def _ticket_vierge() -> Ticket:
    return Ticket()


# --------------------------------------------------------------------------
# 1. Enrichissement de commentaire_interne
# --------------------------------------------------------------------------

def test_enrichissement_commentaire_interne_quand_pertinent(vectorstore_prepare):
    """Champ vide + résultat RAG pertinent -> commentaire_interne enrichi avec la suggestion sourcée."""
    dossier, embed_fn = vectorstore_prepare
    ticket = _ticket_vierge()

    enrichir_commentaire_si_pertinent(
        ticket=ticket,
        champ_manquant="Contrat",
        valeur_actuelle="",
        client="TESTCLIENT",
        question="quel est le contrat applicable",
        dossier_persistance=dossier,
        embed_fn=embed_fn,
    )

    assert "Contrat" in ticket.intervention.commentaire_interne
    assert "OD.TEST.001" in ticket.intervention.commentaire_interne
    assert "docx:procedures.docx" in ticket.intervention.commentaire_interne
    assert "NON APPLIQUÉE AU CHAMP" in ticket.intervention.commentaire_interne


def test_idempotence_pas_de_doublon_si_appele_deux_fois(vectorstore_prepare):
    """Appeler 2 fois la même suggestion ne duplique pas la note (cohérent avec le pattern _ajouter_si_absent des agents)."""
    dossier, embed_fn = vectorstore_prepare
    ticket = _ticket_vierge()

    for _ in range(2):
        enrichir_commentaire_si_pertinent(
            ticket=ticket, champ_manquant="Contrat", valeur_actuelle="",
            client="TESTCLIENT", question="quel est le contrat applicable",
            dossier_persistance=dossier, embed_fn=embed_fn,
        )

    assert ticket.intervention.commentaire_interne.count("OD.TEST.001") == 1


# --------------------------------------------------------------------------
# 2. Aucune modification des champs métier
# --------------------------------------------------------------------------

def test_aucune_modification_des_champs_metier(vectorstore_prepare):
    """
    Invariant central de l'architecture : seul `commentaire_interne` peut
    changer. Snapshot complet du ticket avant/après, comparaison champ par
    champ sur les 5 sous-modèles.
    """
    dossier, embed_fn = vectorstore_prepare
    ticket = _ticket_vierge()
    ticket.customer.client = "TESTCLIENT"
    ticket.customer.ville = "Lyon"
    ticket.intervention.problematique = "Panne écran"

    avant = dataclasses.asdict(ticket)

    enrichir_commentaire_si_pertinent(
        ticket=ticket, champ_manquant="Contrat", valeur_actuelle="",
        client="TESTCLIENT", question="quel est le contrat applicable",
        dossier_persistance=dossier, embed_fn=embed_fn,
    )

    apres = dataclasses.asdict(ticket)

    # On retire commentaire_interne des 2 côtés avant de comparer : c'est
    # le SEUL champ autorisé à changer.
    avant["intervention"].pop("commentaire_interne")
    apres["intervention"].pop("commentaire_interne")

    assert avant == apres, "Un champ métier autre que commentaire_interne a été modifié -- violation de l'architecture."
    # Et on vérifie explicitement que le champ retiré, lui, a bien bougé
    # (sinon le test ne prouverait rien -- s'assurer que le RAG a agi).
    assert ticket.intervention.commentaire_interne != ""


def test_champ_deja_resolu_aucune_tentative_rag(vectorstore_prepare):
    """
    Si `valeur_actuelle` est déjà renseignée, aucune tentative RAG n'est
    faite du tout (pas de note ajoutée, même si le vectorstore contiendrait
    une réponse différente) -- le déterministe prime toujours.
    """
    dossier, embed_fn = vectorstore_prepare
    ticket = _ticket_vierge()

    enrichir_commentaire_si_pertinent(
        ticket=ticket, champ_manquant="Contrat", valeur_actuelle="Contrat déjà décidé par l'agent",
        client="TESTCLIENT", question="quel est le contrat applicable",
        dossier_persistance=dossier, embed_fn=embed_fn,
    )

    assert ticket.intervention.commentaire_interne == ""


# --------------------------------------------------------------------------
# 3. Comportement si RAG vide / non disponible
# --------------------------------------------------------------------------

def test_rag_vide_client_sans_collection(vectorstore_prepare):
    """Client sans collection ingérée -> commentaire_interne reste vide, aucune exception."""
    dossier, embed_fn = vectorstore_prepare
    ticket = _ticket_vierge()

    enrichir_commentaire_si_pertinent(
        ticket=ticket, champ_manquant="Contrat", valeur_actuelle="",
        client="CLIENT_SANS_DOC", question="n'importe quoi",
        dossier_persistance=dossier, embed_fn=embed_fn,
    )

    assert ticket.intervention.commentaire_interne == ""


def test_vectorstore_non_fourni_aucun_crash(vectorstore_prepare):
    """dossier_persistance=None (agent appelé sans vectorstore, ex. router_service actuel non modifié) -> pas de crash, pas de note."""
    _dossier, embed_fn = vectorstore_prepare
    ticket = _ticket_vierge()

    enrichir_commentaire_si_pertinent(
        ticket=ticket, champ_manquant="Contrat", valeur_actuelle="",
        client="TESTCLIENT", question="quel est le contrat applicable",
        dossier_persistance=None, embed_fn=embed_fn,
    )

    assert ticket.intervention.commentaire_interne == ""


def test_score_min_strict_aucune_note_si_sous_seuil(vectorstore_prepare):
    """score_min trop exigeant -> aucune suggestion appliquée, même si un candidat existe techniquement."""
    dossier, embed_fn = vectorstore_prepare
    ticket = _ticket_vierge()

    enrichir_commentaire_si_pertinent(
        ticket=ticket, champ_manquant="Contrat", valeur_actuelle="",
        client="TESTCLIENT", question="quel est le contrat applicable",
        dossier_persistance=dossier, embed_fn=embed_fn, score_min=0.99,
    )

    assert ticket.intervention.commentaire_interne == ""