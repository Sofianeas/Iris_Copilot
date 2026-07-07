#!/usr/bin/env python3
"""
scripts/check_environment.py

Outil de diagnostic autonome, indépendant de pytest et de tout état
préalable : vérifie que chaque fichier du pipeline RAG + Rule Engine
existe RÉELLEMENT sur le disque à l'emplacement attendu, ET que chaque
module correspondant est RÉELLEMENT importable.

À utiliser dès qu'un import échoue de façon inattendue (ex. "No module
named ...", "Import could not be resolved") pour trancher immédiatement
entre les deux causes les plus fréquentes :
  1. Le fichier n'existe tout simplement pas encore à cet endroit (cause
     la plus fréquente -- ex. fichier livré mais pas encore copié/placé).
  2. Le fichier existe mais un problème plus profond empêche son import
     (erreur de syntaxe, dépendance manquante, etc.) -- dans ce cas
     l'exception exacte est affichée, pas seulement "ça ne marche pas".

Usage : python -m scripts.check_environment
Sortie : 0 si tout est présent ET importable, 1 sinon.
"""

import importlib
import sys
from pathlib import Path

FICHIERS_ATTENDUS = [
    "app/config/rag_settings.py",
    "app/models/rag_decision.py",
    "app/models/rule_recommendation.py",
    "app/services/rag_fallback_service.py",
    "app/services/rag_decision_service.py",
    "app/services/rag_integration_layer.py",
    "app/services/rule_engine.py",
    "app/rules/__init__.py",
    "app/rules/priority_rule.py",
    "app/rules/client_rule.py",
    "tests/test_rag_fallback_service.py",
    "tests/test_rag_decision_service.py",
    "tests/test_rag_integration_layer.py",
    "tests/test_rule_engine.py",
    "tests/rules/__init__.py",
    "tests/rules/test_priority_rule.py",
    "tests/rules/test_client_rule.py",
    "scripts/__init__.py",
    "scripts/validate_rag_pipeline.py",
    "scripts/validate_rag_decision.py",
    "scripts/validate_rule_engine.py",
]

MODULES_A_IMPORTER = [
    "app.config.rag_settings",
    "app.models.rag_decision",
    "app.models.rule_recommendation",
    "app.services.rag_fallback_service",
    "app.services.rag_decision_service",
    "app.services.rag_integration_layer",
    "app.services.rule_engine",
    "app.rules.priority_rule",
    "app.rules.client_rule",
    "scripts.validate_rag_pipeline",
    "scripts.validate_rag_decision",
    "scripts.validate_rule_engine",
]


def main() -> int:
    racine = Path.cwd()
    print("=" * 60)
    print("CHECK ENVIRONMENT")
    print("=" * 60)
    print(f"\nRépertoire courant (Path.cwd()) : {racine}\n")

    echecs: list[str] = []

    print("--- Présence réelle des fichiers sur le disque ---")
    for chemin_relatif in FICHIERS_ATTENDUS:
        chemin = racine / chemin_relatif
        existe = chemin.is_file()
        print(f"{'✔' if existe else '✘'} {chemin_relatif}")
        if not existe:
            echecs.append(f"fichier absent : {chemin_relatif}")

    print("\n--- Import réel de chaque module (indépendant de pytest) ---")
    for nom_module in MODULES_A_IMPORTER:
        try:
            importlib.import_module(nom_module)
            print(f"✔ {nom_module}")
        except Exception as exc:
            print(f"✘ {nom_module} -- {exc!r}")
            echecs.append(f"import échoué : {nom_module} ({exc!r})")

    print()
    if echecs:
        print(f"❌ {len(echecs)} probleme(s) detecte(s) :\n")
        for e in echecs:
            print(f"  - {e}")
        print("\nFAILURE")
        return 1

    print("SUCCESS -- tous les fichiers sont présents et importables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())