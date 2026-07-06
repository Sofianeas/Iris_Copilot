#!/usr/bin/env python3
"""
validate_rag_pipeline.py

Script de validation autonome (pas pytest) du pipeline RAG complet
(rag_fallback_service.py -> rag_decision_service.py ->
rag_integration_layer.py), exécuté de bout en bout via
`enrichir_commentaire_si_pertinent`.

Vérifie automatiquement, sur une batterie de scénarios couvrant les cas
limites connus :
  1. Aucune modification des champs métier (seul commentaire_interne peut changer).
  2. Chaque suggestion appliquée possède une source.
  3. Aucune décision n'est prise sans raison journalisée.
  4. Tous les appels sont journalisés (capture des logs via un handler dédié).
  5. Aucun résultat sans source n'est jamais accepté (cohérence avec le
     contrat RagResult/RagDecision).

Usage : python validate_rag_pipeline.py
Sortie : 0 si tout passe, 1 sinon (code de sortie exploitable en CI).
"""

import dataclasses
import logging
import sys
import tempfile
from pathlib import Path

import chromadb

from app.models.ticket import Ticket
from app.services.rag_integration_layer import enrichir_commentaire_si_pertinent
from app.services.vectorstore_service import make_tfidf_embedder

# --------------------------------------------------------------------------
# Capture des logs (pour vérifier "tous les appels sont journalisés")
# --------------------------------------------------------------------------

class CapteurDeLogs(logging.Handler):
    """Handler minimal qui accumule les records émis par les loggers RAG."""

    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _construire_mini_vectorstore(dossier: Path) -> tuple[Path, "EmbedFn"]:
    """Corpus minimal, un seul client, un seul chunk sourcé -- suffisant pour valider le pipeline."""
    from app.services.vectorstore_service import EmbedFn  # import local, type hint seulement

    textes = ["Le contrat applicable est OD.VALID.001 - On Demand France."]
    embed_fn = make_tfidf_embedder(textes)
    store = chromadb.PersistentClient(path=str(dossier))
    collection = store.create_collection("validclient")
    collection.add(
        ids=["validclient-0"],
        documents=textes,
        embeddings=embed_fn(textes),
        metadatas=[{"client": "VALIDCLIENT", "source": "procedures.docx", "type_source": "docx"}],
    )
    return dossier, embed_fn


def _snapshot_champs_metier(ticket: Ticket) -> dict:
    """Capture tous les champs SAUF commentaire_interne (le seul autorisé à changer)."""
    brut = dataclasses.asdict(ticket)
    brut["intervention"].pop("commentaire_interne")
    return brut


def main() -> int:
    capteur = CapteurDeLogs()
    capteur.setLevel(logging.INFO)
    for nom_logger in ("iris_copilot.rag_fallback", "iris_copilot.rag_decision", "iris_copilot.rag_integration"):
        logging.getLogger(nom_logger).addHandler(capteur)
        logging.getLogger(nom_logger).setLevel(logging.INFO)

    echecs: list[str] = []

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        dossier, embed_fn = _construire_mini_vectorstore(Path(tmp))

        scenarios = [
            # (nom, client, question, valeur_actuelle, dossier_persistance)
            ("suggestion_trouvee", "VALIDCLIENT", "quel est le contrat applicable", "", dossier),
            ("champ_deja_resolu", "VALIDCLIENT", "quel est le contrat applicable", "déjà rempli", dossier),
            ("client_sans_doc", "CLIENT_INCONNU", "peu importe", "", dossier),
            ("vectorstore_absent", "VALIDCLIENT", "quel est le contrat applicable", "", None),
        ]

        for nom, client, question, valeur_actuelle, dossier_scenario in scenarios:
            capteur.records.clear()
            ticket = Ticket()
            snapshot_avant = _snapshot_champs_metier(ticket)

            try:
                enrichir_commentaire_si_pertinent(
                    ticket=ticket, champ_manquant="Contrat", valeur_actuelle=valeur_actuelle,
                    client=client, question=question, dossier_persistance=dossier_scenario,
                    embed_fn=embed_fn,
                )
            except Exception as exc:  # ne devrait JAMAIS arriver
                echecs.append(f"[{nom}] exception non gérée levée : {exc!r}")
                continue

            snapshot_apres = _snapshot_champs_metier(ticket)

            # 1. Aucune modification des champs métier
            if snapshot_avant != snapshot_apres:
                echecs.append(f"[{nom}] un champ métier autre que commentaire_interne a été modifié")

            # 2. Si une suggestion a été appliquée, elle doit posséder une source
            if ticket.intervention.commentaire_interne and "source :" not in ticket.intervention.commentaire_interne:
                echecs.append(f"[{nom}] suggestion appliquée sans source visible dans commentaire_interne")

            # 3 & 4. Toutes les décisions doivent être journalisées
            if not capteur.records:
                echecs.append(f"[{nom}] aucun log émis pour ce scénario -- décision non journalisée")

            # 4bis. Chaque record de décision doit porter une raison non vide (rag_decision) ou un motif (rag_integration)
            for record in capteur.records:
                message = record.getMessage()
                if "iris_copilot.rag_decision" in record.name and "reason=" not in message:
                    echecs.append(f"[{nom}] log de décision sans champ reason= : {message!r}")
                if "iris_copilot.rag_integration" in record.name and "raison=" not in message and "score=" not in message:
                    echecs.append(f"[{nom}] log d'intégration sans raison identifiable : {message!r}")

    for nom_logger in ("iris_copilot.rag_fallback", "iris_copilot.rag_decision", "iris_copilot.rag_integration"):
        logging.getLogger(nom_logger).removeHandler(capteur)

    print("=" * 60)
    print("VALIDATE RAG PIPELINE")
    print("=" * 60)
    if echecs:
        print(f"\n❌ {len(echecs)} échec(s) détecté(s) :\n")
        for e in echecs:
            print(f"  - {e}")
        print("\nFAILURE")
        return 1

    print("\n✔ aucune modification de champ métier")
    print("✔ chaque suggestion appliquée possède une source")
    print("✔ aucune décision sans raison journalisée")
    print("✔ tous les appels sont journalisés")
    print("\nSUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())