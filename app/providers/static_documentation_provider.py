"""
app/providers/static_documentation_provider.py

Première implémentation concrète de DocumentationProvider (WF-DOC-009).
Source documentaire = dictionnaire Python statique en mémoire, injecté
au constructeur. Aucune base de données, aucun appel réseau, aucune API
externe, aucune dépendance ChromaDB/Gemini.

Ce Provider est volontairement MINIMAL : correspondance EXACTE (client,
question normalisée) -> réponse, aucune recherche sémantique, aucun
scoring, aucune tolérance aux fautes de frappe. Il reste responsable de
son propre mécanisme de récupération -- le Workflow Documentation n'a et
ne doit jamais avoir connaissance de ce mécanisme (aucune logique de
correspondance ne fuit vers documentation_workflow.py).

⚠️ Différence avec le futur Provider ChromaDB (mission suivante,
non commencée ici) : celui-ci retrouvera des réponses par similarité
sémantique sur un corpus indexé (embeddings), avec un score de
pertinence et une tolérance aux reformulations. Ce Provider statique ne
fait qu'une correspondance exacte sur un dictionnaire fixe -- c'est un
jalon de démonstration de bout en bout, pas une solution définitive.
"""

import unicodedata

from app.providers.documentation_provider import DocumentationProvider, DocumentationQuery


def _normaliser_question(question: str) -> str:
    """Normalise une question pour la correspondance (minuscule, sans accent, trim)."""
    if not question:
        return ""
    sans_accents = "".join(
        c for c in unicodedata.normalize("NFD", question)
        if unicodedata.category(c) != "Mn"
    )
    return sans_accents.strip().lower()


class StaticDocumentationProvider(DocumentationProvider):
    """
    Provider concret minimal, source = dictionnaire Python statique.

    Les données sont TOUJOURS injectées au constructeur (jamais codées en
    dur dans la classe elle-même) : `{client: {question_normalisee:
    reponse}}`. Permet de construire différents jeux de données
    (démonstration, tests, futur contenu réel) sans jamais modifier le
    code de ce Provider.
    """

    def __init__(self, donnees: dict[str, dict[str, str]]):
        self._donnees = donnees

    def fetch(self, request: DocumentationQuery) -> str | None:
        """Correspondance exacte (client, question normalisée) -> réponse, ou None si absente."""
        client, question = request
        questions_du_client = self._donnees.get(client, {})
        return questions_du_client.get(_normaliser_question(question))


def construire_donnees_demo() -> dict[str, dict[str, str]]:
    """
    Jeu de données de démonstration, basé sur des cas réels déjà
    documentés dans le projet (ADOPT/CATO, BARRON/PED->TPE) -- illustre
    un usage réel plutôt qu'un contenu arbitraire. Ne constitue PAS le
    contenu documentaire définitif du projet (celui-ci viendra du futur
    Provider ChromaDB indexant les vrais documents clients).
    """
    return {
        "ADOPT": {
            _normaliser_question("Comment gérer une demande CATO ?"): (
                "ATTENTION : demande détectée comme Installation Boîtier CATO (Projet). "
                "Ne pas traiter automatiquement — voir avec Anne ou David via Teams "
                "(conversation CDS Alger) avant de poursuivre."
            ),
        },
        "BARRON": {
            _normaliser_question("Que signifie PED chez ce client ?"): (
                "Chez Barron Mac Cann, PED désigne toujours un TPE en France."
            ),
        },
    }