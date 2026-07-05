"""
app/config/rag_settings.py

Configuration centralisée de la couche RAG. Toute valeur ajustable de
comportement (seuils, sources autorisées, activation globale, verbosité
des logs, nombre de candidats) vit ICI -- jamais codée en dur dans
rag_fallback_service.py, rag_decision_service.py ou rag_integration_layer.py.

⚠️ Convention de lecture obligatoire pour tout code consommant ces valeurs
   (notamment rag_decision_service.py) : importer le MODULE
   (`import app.config.rag_settings as rag_settings`) et lire
   `rag_settings.MIN_SCORE` etc. DYNAMIQUEMENT au moment de l'appel --
   jamais `from app.config.rag_settings import MIN_SCORE` en tête de
   fichier, ce qui figerait une copie locale à l'import et rendrait tout
   monkeypatching en test (pytest `monkeypatch.setattr`) inopérant.
"""

# Score minimal (∈ (0, 1], cf. rag_fallback_service._distance_vers_score)
# pour qu'un résultat RAG soit considéré utilisable.
# ⚠️ Valeur provisoire, volontairement permissive (0.0 = aucun filtrage)
# faute de calibration empirique contre de vrais embeddings Gemini (le
# stand-in TF-IDF de test et Gemini ne vivent pas dans des espaces de score
# comparables) -- à recalibrer une fois des requêtes réelles disponibles.
MIN_SCORE: float = 0.0

# Types de source ("type_source" des chunks ingérés, cf.
# vectorstore_service.Chunk : "skill_md" | "docx" | "toki") considérés
# fiables pour qu'une suggestion RAG soit retenue comme utilisable.
AUTHORIZED_SOURCES: tuple[str, ...] = ("skill_md", "docx", "toki")

# Interrupteur global : si False, AUCUNE suggestion RAG n'est jamais
# retenue comme utilisable, quel que soit le résultat de la recherche
# sous-jacente (kill-switch, vérifié à la fois en amont dans
# rag_integration_layer.py -- pour éviter un appel réseau/retrieval inutile
# -- et en défense en profondeur dans rag_decision_service.py).
ENABLE_RAG: bool = True

# Niveau de verbosité des loggers "iris_copilot.rag_*". Fourni pour que
# l'APPLICATION (main.py, au démarrage) configure
# `logging.basicConfig(level=rag_settings.LOG_LEVEL)` -- les modules RAG
# eux-mêmes ne s'auto-configurent jamais (bonne pratique : une bibliothèque
# émet des records, elle n'impose pas sa propre configuration de logging
# à l'application qui l'utilise).
LOG_LEVEL: str = "INFO"

# Nombre de candidats examinés par requête avant de ne retenir que le
# meilleur score (cf. rag_fallback_service.tenter_fallback_rag, paramètre
# n_candidats).
MAX_RESULTS: int = 3