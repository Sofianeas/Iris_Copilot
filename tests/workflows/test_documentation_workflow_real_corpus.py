# tests/workflows/test_documentation_workflow_real_corpus.py
#
# WF-DOC-015 -- Démontre la chaîne complète avec le VRAI contenu
# documentaire du projet IRIS Copilot (ADOPT.docx + TOKI_ADOPT.txt réels,
# tels que fournis en début de projet), pas des fixtures synthétiques
# minimales. Jalon "usage réel" : le vectorstore est construit à partir
# de contenu documentaire authentique, puis interrogé via la chaîne
# assemblée complète.

from app.models.documentation_workflow import DocumentationWorkflowRequest
from app.providers.vectorstore_documentation_provider import VectorStoreDocumentationProvider
from app.repositories.in_memory_documentation_repository import InMemoryDocumentationRepository
from app.services.vectorstore_service import construire_chunks, construire_vectorstore, make_tfidf_embedder
from app.workflows.documentation_workflow import DocumentationWorkflow

# Contenu RÉEL de ADOPT.docx, tel que fourni au tout début du projet
# (pas un extrait synthétique) -- source de vérité du client ADOPT.
ADOPT_DOCX_REEL = """ADOPT

*Client : ADOPT

*SITE D'INTERVENTION 
     -Enseigne : Présent dans le mail au niveau de **Adresse**** d'intervention**
     -Adresse : Présent dans le mail au niveau de **Adresse d'intervention**
     -Complément d'adresse : Si plusieurs lignes dans **Adresse d'intervention**
     -Code postal : Présent dans le mail au niveau de **Adresse d'intervention**
     -Ville : Présent dans le mail au niveau de **Adresse d'intervention**
     -Pays : Présent dans le mail au niveau de **Pays**

*CONTACT
 Remplir les champs en fonction des informations dans le mail au niveau de **Contacts**

*Type d'intervention
Sélectionner en fonction de la demande (En général **Contrat**)

*CONTRAT
Sélectionner le Contrat en fonction de la demande : 
     -On Demand France : Pour la France
     - On Demand Espagne/Pologne : Pour l'Espagne ou la Pologne
     - On Demand Belgique : Pour la Belgique
     - On Demand Italie : Pour l'Italie
     - Installation Boîtier CATO (Projet) : Pour l'installation de boîtier CATO (Si demande de ce genre, voir avec Anne ou David via Teams dans conversation CDS Alger)

*Typologie 
Sélectionner le type : 
Seulement pour le France, on choisit Maintenances ou Installation : Information présente dans le mail au niveau de **Type de demande**
Pour les 4 autres Contrats, c'est toujours Installation (Seul choix possible)
"""

# Contenu RÉEL de TOKI_ADOPT.txt, tel que fourni au tout début du projet
# -- retranscrit ICI EXACTEMENT tel quel (un seul marqueur "Etape 1:",
# aucun "Etape 2:" -- la section matériel s'enchaîne directement dans le
# fichier réel, sans en-tête de section propre).
TOKI_ADOPT_REEL = """Etape 1: creation d'une demande

Réception d'un mail dans la boite sav comprenant un tableau.
Dans ce tableau tous les éléments y sont notés

intitulé = intitulé de la demande

type d'intervention : intervention SANS ou AVEC pièce suivant la demande. LE besoin de matériel est noté en bas du tableau

nombre de technicien: 1
Temps d'intervention: généralement noté dans le bas du tableau

niveau de service = date et heure souhaitée

descriptif = description de la demande + contacts téléphoniques + commentaire si besoin - à reporter dans le descriptif de l'incident



si besoin de matériel (en France):

- commander les cables RJ45 en consignation Irisi (ref au format CAB-RJ-CAT6-*M-*)

- commander les vis M4x25 si demandé, ref B0CNL85C92

si besoin de matériel autre pays que la France - le prestataire a le matériel  - voir avec le responsable de compte pour la Belgique
"""


def test_chaine_complete_avec_vrai_contenu_documentaire_adopt(tmp_path):
    """
    Construit le vectorstore à partir du VRAI contenu ADOPT.docx +
    TOKI_ADOPT.txt du projet, puis interroge la chaîne complète avec une
    vraie question métier (le cas CATO, mentionné dans les 2 sources).
    """
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(ADOPT_DOCX_REEL, encoding="utf-8")
    (dossier_sources / "TOKI_ADOPT.txt").write_text(TOKI_ADOPT_REEL, encoding="utf-8")

    dossier_persistance = tmp_path / "vectorstore"
    chunks = construire_chunks(dossier_sources)
    assert len(chunks) > 0  # confirme que le vrai contenu produit bien des chunks exploitables

    embedder = make_tfidf_embedder([c.texte for c in chunks])
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)

    repository = InMemoryDocumentationRepository()  # vide -- force le passage par le vrai contenu indexé
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Comment traiter une demande de boîtier CATO ?")
    )

    assert resultat.succes is True
    assert resultat.source == "provider"
    assert "CATO" in resultat.reponse
    assert "Anne" in resultat.reponse or "David" in resultat.reponse


def test_chaine_complete_question_materiel_reseau_source_toki(tmp_path):
    """Même corpus réel, question ciblant spécifiquement le contenu TOKI (pas le docx) -- vérifie que les 2 sources sont bien indexées."""
    dossier_sources = tmp_path / "sources"
    dossier_sources.mkdir()
    (dossier_sources / "ADOPT.docx").write_text(ADOPT_DOCX_REEL, encoding="utf-8")
    (dossier_sources / "TOKI_ADOPT.txt").write_text(TOKI_ADOPT_REEL, encoding="utf-8")

    dossier_persistance = tmp_path / "vectorstore"
    chunks = construire_chunks(dossier_sources)
    embedder = make_tfidf_embedder([c.texte for c in chunks])
    construire_vectorstore(dossier_sources, dossier_persistance, embed_fn=embedder)

    repository = InMemoryDocumentationRepository()
    provider = VectorStoreDocumentationProvider(dossier_persistance=dossier_persistance, embed_fn=embedder)
    workflow = DocumentationWorkflow(repository=repository, provider=provider)

    resultat = workflow.execute(
        DocumentationWorkflowRequest(client="ADOPT", question="Quelle référence pour les câbles RJ45 ?")
    )

    assert resultat.succes is True
    assert "CAB-RJ-CAT6" in resultat.reponse