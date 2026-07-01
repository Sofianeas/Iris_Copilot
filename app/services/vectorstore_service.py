"""
Service RAG -- ingestion documentaire + retrieval filtré par client.

Phase V2 du roadmap (STRUCTURE -> ACTION -> EXPLOITATION -> AUTOMATISATION
-> ANALYTICS) : ce module construit le vectorstore documentaire qui servira
de fallback aux agents (`skill-automation`) pour les règles non encore
codées en dur, et alimentera la future page `documentation.py` (Q&A
naturelle sur les procédures).

Principe directeur (cf. skill iris-copilot-rag-and-agent-architecture) :
le code déterministe des agents reste la source de vérité pour les règles
de champs Ticket -- la retrieval ne fait jamais autorité sur une règle déjà
codée, elle comble les trous et sert la documentation.

--- Deux sources d'ingestion, par ordre de priorité ---

1. **SKILL.md** (source primaire) : les blocs `<details><summary>CLIENT</summary>
   ...</details>` sont DÉJÀ curatés et dédupliqués (c'est nous qui les avons
   écrits, en croisant docx + TOKI + cas réels) -- un chunk = un client
   entier. Qualité la plus haute, cf. skill : "Treat the existing SKILL.md
   ... as a high-quality ingestion source in its own right".
2. **Fichiers .docx/TOKI bruts** (source secondaire, complément) : chunkés
   plus finement --
   - `.docx` client : un chunk par ligne commençant par "*" (convention
     d'écriture constante de ces fichiers -- "*Client :", "*SITE
     D'INTERVENTION", "*CONTRAT", etc. -- frontière naturelle de bloc de
     règle, pas un découpage arbitraire par tokens).
   - `TOKI_*.txt` : un chunk par section "Etape N:" si au moins 2 sont
     trouvées (la majorité des TOKI), sinon repli sur des paragraphes
     séparés par ligne vide, fusionnés jusqu'à une taille cible minimale
     (cas de TOKI_ETAM.txt, qui utilise des titres en forme de question
     plutôt que des "Etape N:").

Isolation par client stricte : **une collection ChromaDB par client**
(jamais une recherche cross-client) -- cf. skill, "filter-then-search:
filtrer au client connu avant la recherche par similarité".

--- Embeddings ---

Par défaut : Gemini (`embed_texts_gemini`), cohérent avec le reste du
pipeline (déjà sur `google-genai`). ⚠️ Nom de modèle à reconfirmer dans la
doc Gemini au moment du premier vrai run (`GEMINI_EMBEDDING_MODEL` ci-
dessous) -- non testé ici faute de clé API dans cet environnement.

Pour les tests SANS clé API (développement local, CI), une fonction
`embed_texts_tfidf` (scikit-learn, aucun appel réseau) peut être injectée
à la place -- cf. `tests/test_vectorstore.py`. Elle ne doit JAMAIS servir
en production : c'est un stand-in pour vérifier la mécanique de chunking/
stockage/retrieval, pas une vraie recherche sémantique.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import chromadb

EmbedFn = Callable[[list[str]], list[list[float]]]

GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"  # ⚠️ à reconfirmer dans la doc Gemini


# --------------------------------------------------------------------------
# Mapping client interne (router_service.TOUS_LES_CLIENTS) <-> fichiers source
# --------------------------------------------------------------------------

CLIENT_SOURCE_FILES = {
    "ADOPT": {"docx": "ADOPT.docx", "toki": "TOKI_ADOPT.txt", "skill_md_summary": "ADOPT"},
    "AEMSOFT": {"docx": "AEMSOFT.docx", "toki": "TOKI_AEM_SOFT.txt", "skill_md_summary": "AEMSOFT"},
    "AMPLIFON": {"docx": "AMPLIFON.docx", "toki": "TOKI_AMPLIFON.txt", "skill_md_summary": "AMPLIFON"},
    "AXE_ESANTE": {"docx": "AXE_E-SANTE.docx", "toki": None, "skill_md_summary": "AXE E-SANTE"},
    "BARRON": {"docx": "BARRON_MAC_CANN.docx", "toki": None, "skill_md_summary": "BARRON MAC CANN"},
    "BUT": {"docx": "BUT.docx", "toki": "TOKI_BUT.txt", "skill_md_summary": "BUT"},
    "DYNAMIZ_PHARMA": {"docx": "DYNAMIZ_PHARMA.docx", "toki": None, "skill_md_summary": "DYNAMIZ PHARMA"},
    "ETAM": {"docx": "ETAM.docx", "toki": "TOKI_ETAM.txt", "skill_md_summary": "ETAM"},
    "INNOVORDER": {"docx": "INNOVORDER.docx", "toki": "TOKI_INNOVORDER.txt", "skill_md_summary": "INNOVORDER"},
    "POS_SERVICE": {"docx": None, "toki": "TOKI_POS_SERVICE.txt", "skill_md_summary": None},
    "PROMETHEAN": {"docx": None, "toki": "TOKI_PROMETHEAN.txt", "skill_md_summary": None},
    "SHOPPERTRAK": {"docx": None, "toki": None, "skill_md_summary": None},  # pas de doc officielle à ce jour
}


@dataclass
class Chunk:
    client: str
    texte: str
    source: str  # nom de fichier d'origine
    type_source: str  # "skill_md" | "docx" | "toki"


# --------------------------------------------------------------------------
# Chunking
# --------------------------------------------------------------------------

RE_DETAILS_BLOCK = re.compile(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", re.DOTALL)


def chunker_skill_md(chemin_skill_md: Path) -> list[Chunk]:
    """Un chunk = un bloc <details> par client (source déjà curatée, cf. docstring du module)."""
    if not chemin_skill_md.exists():
        return []
    texte = chemin_skill_md.read_text(encoding="utf-8")
    summary_vers_client = {v["skill_md_summary"]: k for k, v in CLIENT_SOURCE_FILES.items() if v["skill_md_summary"]}

    chunks = []
    for match in RE_DETAILS_BLOCK.finditer(texte):
        summary = match.group(1).strip()
        contenu = match.group(2).strip()
        client = summary_vers_client.get(summary)
        if client and contenu:
            chunks.append(Chunk(client=client, texte=contenu, source=chemin_skill_md.name, type_source="skill_md"))
    return chunks


def chunker_docx_client(chemin_docx: Path, client: str) -> list[Chunk]:
    """
    Un chunk par ligne commençant par '*' (convention constante des fichiers
    client -- cf. docstring du module). Les fichiers projet sont en réalité
    du texte brut UTF-8 malgré l'extension .docx (pas de vrai binaire Word
    dans cet environnement) -- lecture directe, pas d'extraction nécessaire.
    """
    if not chemin_docx.exists():
        return []
    texte = chemin_docx.read_text(encoding="utf-8")
    lignes = texte.splitlines()

    chunks_bruts: list[list[str]] = []
    for ligne in lignes:
        if ligne.strip().startswith("*"):
            chunks_bruts.append([ligne])
        elif chunks_bruts:
            chunks_bruts[-1].append(ligne)
        # lignes avant le 1er "*" (ex. titre du fichier) : ignorées, pas de
        # règle métier dedans.

    return [
        Chunk(client=client, texte="\n".join(bloc).strip(), source=chemin_docx.name, type_source="docx")
        for bloc in chunks_bruts
        if "\n".join(bloc).strip()
    ]


RE_ETAPE = re.compile(r"^Etape\s+\d+\s*:", re.MULTILINE)
TAILLE_MIN_PARAGRAPHE = 120  # caractères -- fusionne les paragraphes trop courts (repli TOKI sans "Etape N:")


def chunker_toki(chemin_toki: Path, client: str) -> list[Chunk]:
    """
    Un chunk par section 'Etape N:' si au moins 2 sont détectées ; sinon
    repli sur des paragraphes séparés par ligne vide, fusionnés jusqu'à
    TAILLE_MIN_PARAGRAPHE (cf. docstring du module -- cas TOKI_ETAM.txt).
    """
    if not chemin_toki.exists():
        return []
    texte = chemin_toki.read_text(encoding="utf-8")

    bornes = [m.start() for m in RE_ETAPE.finditer(texte)]
    if len(bornes) >= 2:
        bornes.append(len(texte))
        blocs = [texte[bornes[i]:bornes[i + 1]].strip() for i in range(len(bornes) - 1)]
        return [
            Chunk(client=client, texte=bloc, source=chemin_toki.name, type_source="toki")
            for bloc in blocs if bloc
        ]

    # Repli : paragraphes séparés par ligne(s) vide(s), fusionnés
    paragraphes = [p.strip() for p in re.split(r"\n\s*\n", texte) if p.strip()]
    blocs_fusionnes: list[str] = []
    courant = ""
    for p in paragraphes:
        courant = f"{courant}\n\n{p}".strip() if courant else p
        if len(courant) >= TAILLE_MIN_PARAGRAPHE:
            blocs_fusionnes.append(courant)
            courant = ""
    if courant:
        blocs_fusionnes.append(courant)

    return [
        Chunk(client=client, texte=bloc, source=chemin_toki.name, type_source="toki")
        for bloc in blocs_fusionnes
    ]


def construire_chunks(dossier_sources: Path) -> list[Chunk]:
    """Construit tous les chunks (SKILL.md + docx + TOKI) pour tous les clients connus."""
    chunks: list[Chunk] = []

    chunks += chunker_skill_md(dossier_sources / "SKILL.md")

    for client, fichiers in CLIENT_SOURCE_FILES.items():
        if fichiers["docx"]:
            chunks += chunker_docx_client(dossier_sources / fichiers["docx"], client)
        if fichiers["toki"]:
            chunks += chunker_toki(dossier_sources / fichiers["toki"], client)

    return chunks


# --------------------------------------------------------------------------
# Embeddings
# --------------------------------------------------------------------------

def embed_texts_gemini(textes: list[str]) -> list[list[float]]:
    """
    Embeddings de production via google-genai (cohérent avec le reste du
    pipeline, déjà sur ce SDK). Nécessite GEMINI_API_KEY dans .env.
    ⚠️ Non testé dans l'environnement de développement (pas de clé API
    disponible) -- nom de modèle à reconfirmer au premier run réel.
    """
    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    resultat = client.models.embed_content(model=GEMINI_EMBEDDING_MODEL, contents=textes)
    return [e.values for e in resultat.embeddings]


def embed_texts_tfidf(textes: list[str]) -> list[list[float]]:
    """
    ⚠️ STAND-IN DE TEST UNIQUEMENT -- jamais en production. TF-IDF
    (scikit-learn, aucun appel réseau/API) : permet de vérifier la
    mécanique de chunking/stockage/retrieval ChromaDB sans clé Gemini.
    Pas une vraie recherche sémantique (pas de synonymes, pas de sens) --
    cf. tests/test_vectorstore.py.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(max_features=512)
    matrice = vectorizer.fit_transform(textes)
    return matrice.toarray().tolist()


# --------------------------------------------------------------------------
# Construction et persistance du vectorstore
# --------------------------------------------------------------------------

def construire_vectorstore(
    dossier_sources: Path,
    dossier_persistance: Path,
    embed_fn: EmbedFn = embed_texts_gemini,
) -> chromadb.ClientAPI:
    """
    Construit (ou reconstruit) le vectorstore : une collection ChromaDB par
    client, chunks issus de SKILL.md + docx + TOKI. Idempotent -- les
    collections existantes sont supprimées et recréées (rebuild complet,
    pas d'append incrémental pour cette V1).
    """
    chunks = construire_chunks(dossier_sources)

    chunks_par_client: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        chunks_par_client.setdefault(chunk.client, []).append(chunk)

    store = chromadb.PersistentClient(path=str(dossier_persistance))

    for client, chunks_client in chunks_par_client.items():
        nom_collection = client.lower()
        try:
            store.delete_collection(nom_collection)
        except Exception:
            pass  # n'existait pas encore, rien à faire
        collection = store.create_collection(nom_collection)

        textes = [c.texte for c in chunks_client]
        embeddings = embed_fn(textes)
        collection.add(
            ids=[f"{client}-{i}" for i in range(len(chunks_client))],
            documents=textes,
            embeddings=embeddings,
            metadatas=[{"client": c.client, "source": c.source, "type_source": c.type_source} for c in chunks_client],
        )

    return store


# --------------------------------------------------------------------------
# Retrieval filtré (jamais cross-client, cf. docstring du module)
# --------------------------------------------------------------------------

@dataclass
class ReponseRetrievee:
    chunks: list[str]
    sources: list[dict]


def lookup_rule(
    client: str,
    question: str,
    dossier_persistance: Path,
    embed_fn: EmbedFn = embed_texts_gemini,
    n_results: int = 3,
) -> ReponseRetrievee:
    """
    Recherche filtrée sur la SEULE collection du client donné -- jamais de
    recherche cross-client (cf. docstring du module). Si la collection
    n'existe pas (client jamais ingéré, ex. SHOPPERTRAK sans doc), retourne
    une réponse vide plutôt que de lever une exception ou d'élargir la
    recherche à d'autres clients.
    """
    store = chromadb.PersistentClient(path=str(dossier_persistance))
    nom_collection = client.lower()
    try:
        collection = store.get_collection(nom_collection)
    except Exception:
        return ReponseRetrievee(chunks=[], sources=[])

    embedding_question = embed_fn([question])[0]
    resultats = collection.query(query_embeddings=[embedding_question], n_results=n_results)

    documents = resultats.get("documents", [[]])[0]
    metadatas = resultats.get("metadatas", [[]])[0]
    return ReponseRetrievee(chunks=documents, sources=metadatas)