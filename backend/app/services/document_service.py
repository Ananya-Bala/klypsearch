"""
services/document_service.py
-----------------------------
RAG (Retrieval-Augmented Generation) document knowledge base.

Architecture:
    - Documents stored as markdown/txt files in backend/data/documents/
    - Chunked with overlap and embedded using TF-IDF (384-dim dense vectors)
    - Stored in a local persistent ChromaDB collection
    - Queried at analysis time to inject relevant filing context into the Groq prompt

Embedding strategy:
    Primary:  sentence-transformers/all-MiniLM-L6-v2 (requires HuggingFace access)
    Fallback: TF-IDF vectorizer fitted on the corpus (works fully offline)
    
    The service tries sentence-transformers first and falls back transparently.
    Both produce 384-dimensional dense vectors for ChromaDB.

Startup behaviour:
    On FastAPI startup, if the ChromaDB collection is empty, all documents in
    the data/documents/ directory are ingested automatically. Subsequent
    startups skip ingestion (idempotent). Forced re-ingestion via
    ingest_documents(force=True).

Chunking:
    chunk_size  = 1000 characters
    chunk_overlap = 150 characters
    Chunks carry metadata: company, source, file, chunk_index
"""

import logging
import os
import pickle
from pathlib import Path
from typing import Any

import chromadb
import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

DOCUMENTS_DIR   = Path(__file__).parent.parent.parent / "data" / "documents"
CHROMA_DB_DIR   = Path(__file__).parent.parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "earnings_filings"
CHUNK_SIZE      = 1000
CHUNK_OVERLAP   = 150
EMBEDDING_DIM   = 384
TOP_K_DEFAULT   = 3

# ── Ticker → company mapping (extend as you add more documents) ───────────────

TICKER_ALIASES: dict[str, list[str]] = {
    "NVDA": ["nvidia", "nvda"],
    "AAPL": ["apple", "aapl"],
    "MSFT": ["microsoft", "msft"],
    "TSLA": ["tesla", "tsla"],
    "AMZN": ["amazon", "amzn"],
    "AMD":  ["amd", "advanced micro"],
    "GOOG": ["google", "alphabet", "goog", "googl"],
    "META": ["meta", "facebook"],
    "NFLX": ["netflix", "nflx"],
}

# ── Embedding engine ──────────────────────────────────────────────────────────

class _EmbeddingEngine:
    """
    Wraps sentence-transformers with a TF-IDF fallback.
    Fitted lazily on the first encode() call if ST is unavailable.
    """

    def __init__(self) -> None:
        self._st_model = None
        self._tfidf    = None
        self._fitted   = False
        self._tfidf_path = CHROMA_DB_DIR / "tfidf_vectorizer.pkl"

    def _try_load_st(self) -> bool:
        """Attempt to load sentence-transformers. Return True on success."""
        try:
            import os as _os
            _os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding engine: sentence-transformers/all-MiniLM-L6-v2")
            return True
        except Exception as exc:
            logger.info("sentence-transformers unavailable (%s) — using TF-IDF fallback", exc)
            return False

    def _load_tfidf(self, corpus: list[str] | None = None) -> None:
        """Load or fit the TF-IDF vectorizer."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        if self._tfidf_path.exists():
            with open(self._tfidf_path, "rb") as f:
                self._tfidf = pickle.load(f)
            logger.info("Loaded TF-IDF vectorizer from cache (%s terms)", len(self._tfidf.vocabulary_))
            self._fitted = True
        elif corpus:
            self._fit_tfidf(corpus)
        else:
            # Bootstrap with minimal vocab — will be refitted on first ingestion
            self._tfidf = TfidfVectorizer(
                max_features=EMBEDDING_DIM,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            logger.info("TF-IDF vectorizer created (unfitted — will fit on first ingestion)")

    def fit_tfidf(self, corpus: list[str]) -> None:
        """Fit (or refit) the TF-IDF vectorizer on a corpus of texts."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._tfidf = TfidfVectorizer(
            max_features=EMBEDDING_DIM,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self._tfidf.fit(corpus)
        self._fitted = True

        CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
        with open(self._tfidf_path, "wb") as f:
            pickle.dump(self._tfidf, f)

        logger.info("TF-IDF vectorizer fitted and saved (%d terms)", len(self._tfidf.vocabulary_))

    def _to_dense(self, sparse_matrix) -> np.ndarray:
        """Convert sparse TF-IDF matrix to dense 384-dim array."""
        arr = sparse_matrix.toarray().astype(np.float32)
        if arr.shape[1] < EMBEDDING_DIM:
            arr = np.pad(arr, ((0, 0), (0, EMBEDDING_DIM - arr.shape[1])))
        return arr[:, :EMBEDDING_DIM]

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode a list of texts into 384-dim embedding vectors.
        Returns a list of lists (one per text).
        """
        if self._st_model is not None:
            return self._st_model.encode(texts, show_progress_bar=False).tolist()

        if self._tfidf is None:
            self._try_load_st() or self._load_tfidf()

        if self._st_model is not None:
            return self._st_model.encode(texts, show_progress_bar=False).tolist()

        if not self._fitted:
            # Can't encode before fit — return zero vectors as a last resort
            logger.warning("TF-IDF not fitted yet; returning zero embeddings")
            return [[0.0] * EMBEDDING_DIM for _ in texts]

        sparse = self._tfidf.transform(texts)
        return self._to_dense(sparse).tolist()

    def initialise(self) -> None:
        """Called at startup to try ST first, then fall back to cached TF-IDF."""
        if not self._try_load_st():
            self._load_tfidf()


# Module-level singleton
_engine = _EmbeddingEngine()


# ── ChromaDB client singleton ─────────────────────────────────────────────────

def _get_client() -> chromadb.PersistentClient:
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DB_DIR))


def _get_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    """
    Return the earnings_filings collection.
    We never pass an embedding_function to ChromaDB — we supply raw embeddings
    explicitly. This avoids ChromaDB trying to download models at runtime.
    """
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping character-level chunks.

    Each chunk is at most chunk_size characters.
    Consecutive chunks share `overlap` characters for context continuity.
    The final chunk is kept even if shorter than chunk_size.
    """
    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start += chunk_size - overlap

    return chunks


# ── Metadata extraction ───────────────────────────────────────────────────────

def _extract_metadata(filepath: Path) -> dict[str, str]:
    """
    Extract company name, ticker, and source from the file content and name.
    Reads the first 400 characters of the file for header parsing.
    """
    filename  = filepath.stem.lower()
    content   = filepath.read_text(encoding="utf-8", errors="ignore")[:400]
    company   = "Unknown"
    ticker    = "UNKNOWN"
    source    = filepath.stem.replace("_", " ").title()

    # Detect ticker from filename (e.g. nvda_q1_fy2025 → NVDA)
    for t in TICKER_ALIASES:
        if filename.startswith(t.lower()) or f"_{t.lower()}" in filename:
            ticker = t
            break

    # Extract company name from markdown header
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("**Company:**"):
            company = line.replace("**Company:**", "").strip()
            break
        if line.startswith("# "):
            # Use first heading as fallback
            company = line.lstrip("# ").split("—")[0].split("-")[0].strip()

    # Extract source from header
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("**Source:**"):
            source = line.replace("**Source:**", "").strip()
            break
        if line.startswith("**Period:**"):
            source = line.replace("**Period:**", "").strip()
            break

    return {"company": company, "ticker": ticker, "source": source, "file": filepath.name}


# ── Ingestion ─────────────────────────────────────────────────────────────────

def ingest_documents(force: bool = False) -> dict[str, Any]:
    """
    Scan DOCUMENTS_DIR, chunk all .md/.txt files, embed, and store in ChromaDB.

    Args:
        force: If True, delete existing collection and re-ingest everything.

    Returns a summary dict with counts for logging and the /health endpoint.
    """
    client     = _get_client()
    collection = _get_collection(client)

    if collection.count() > 0 and not force:
        logger.info(
            "ChromaDB collection '%s' already has %d chunks — skipping ingestion. "
            "Pass force=True to re-ingest.",
            COLLECTION_NAME,
            collection.count(),
        )
        return {"status": "skipped", "existing_chunks": collection.count()}

    if force and collection.count() > 0:
        logger.info("Force re-ingestion: deleting existing collection")
        client.delete_collection(COLLECTION_NAME)
        collection = _get_collection(client)

    # ── Discover documents ────────────────────────────────────────────────────
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    doc_files = sorted(
        f for f in DOCUMENTS_DIR.iterdir()
        if f.suffix in {".md", ".txt", ".markdown"} and f.is_file()
    )

    if not doc_files:
        logger.warning("No documents found in %s", DOCUMENTS_DIR)
        return {"status": "empty", "files": 0, "chunks": 0}

    logger.info("Found %d document(s) in %s", len(doc_files), DOCUMENTS_DIR)

    # ── Chunk all documents ───────────────────────────────────────────────────
    all_chunks:    list[str]        = []
    all_metadatas: list[dict]       = []
    all_ids:       list[str]        = []
    file_stats:    dict[str, int]   = {}

    for filepath in doc_files:
        try:
            text     = filepath.read_text(encoding="utf-8", errors="ignore")
            metadata = _extract_metadata(filepath)
            chunks   = _chunk_text(text)

            logger.info(
                "  [%s] %s — %d chars → %d chunks (company: %s, source: %s)",
                metadata["ticker"],
                filepath.name,
                len(text),
                len(chunks),
                metadata["company"],
                metadata["source"],
            )

            for idx, chunk in enumerate(chunks):
                chunk_id = f"{filepath.stem}__chunk_{idx:04d}"
                chunk_meta = {**metadata, "chunk_index": str(idx)}

                all_chunks.append(chunk)
                all_metadatas.append(chunk_meta)
                all_ids.append(chunk_id)

            file_stats[filepath.name] = len(chunks)

        except Exception as exc:
            logger.error("Failed to process %s: %s", filepath.name, exc, exc_info=True)

    if not all_chunks:
        logger.error("No chunks produced from any document")
        return {"status": "error", "files": len(doc_files), "chunks": 0}

    # ── Fit TF-IDF on full corpus (if not using sentence-transformers) ────────
    _engine.initialise()
    if _engine._tfidf is not None and not _engine._fitted:
        logger.info("Fitting TF-IDF vectorizer on %d chunks...", len(all_chunks))
        _engine.fit_tfidf(all_chunks)

    # ── Compute embeddings ────────────────────────────────────────────────────
    logger.info("Embedding %d chunks...", len(all_chunks))
    try:
        embeddings = _engine.encode(all_chunks)
    except Exception as exc:
        logger.error("Embedding failed: %s", exc, exc_info=True)
        raise

    # ── Store in ChromaDB in batches ──────────────────────────────────────────
    batch_size = 50
    total_stored = 0
    for i in range(0, len(all_chunks), batch_size):
        batch_end = min(i + batch_size, len(all_chunks))
        collection.add(
            embeddings=embeddings[i:batch_end],
            documents=all_chunks[i:batch_end],
            metadatas=all_metadatas[i:batch_end],
            ids=all_ids[i:batch_end],
        )
        total_stored += batch_end - i

    logger.info(
        "Ingestion complete: %d files, %d total chunks stored in ChromaDB collection '%s'",
        len(doc_files),
        total_stored,
        COLLECTION_NAME,
    )
    return {
        "status": "complete",
        "files": len(doc_files),
        "chunks": total_stored,
        "per_file": file_stats,
    }


def ensure_ingested_on_startup() -> None:
    """
    Called from FastAPI lifespan.
    If the ChromaDB collection is empty, ingest bundled documents.
    Non-fatal by design — callers catch exceptions to keep API boot resilient.
    """
    client = _get_client()
    collection = _get_collection(client)
    if collection.count() == 0:
        logger.info("ChromaDB collection empty — ingesting documents on startup")
        ingest_documents(force=False)
    else:
        logger.info("ChromaDB collection ready (%d chunks)", collection.count())


# ── Search ────────────────────────────────────────────────────────────────────

def search_documents(
    query: str,
    ticker: str | None = None,
    n_results: int = TOP_K_DEFAULT,
) -> list[dict[str, Any]]:
    """
    Retrieve the top-n most relevant document chunks for a query.

    Args:
        query:     Natural language query (e.g. "What did NVIDIA say about AI demand?")
        ticker:    Optional ticker to restrict search to a single company.
        n_results: Number of chunks to return (default: 3).

    Returns:
        List of dicts with keys: company, ticker, source, text, score, chunk_index
        Sorted by relevance (highest score first).
        Returns [] on any error so the pipeline degrades gracefully.
    """
    try:
        client     = _get_client()
        collection = _get_collection(client)

        if collection.count() == 0:
            logger.warning("ChromaDB collection is empty — no document context available")
            return []

        # Ensure embedder is initialised
        if _engine._st_model is None and _engine._tfidf is None:
            _engine.initialise()

        # Embed the query
        query_embedding = _engine.encode([query])

        # Optional ticker filter
        where_filter: dict | None = None
        if ticker:
            ticker_upper = ticker.upper()
            where_filter = {"ticker": {"$eq": ticker_upper}}

        # Clamp n_results to collection size
        effective_n = min(n_results, collection.count())

        result = collection.query(
            query_embeddings=query_embedding,
            n_results=effective_n,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        docs      = result.get("documents", [[]])[0]
        metas     = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        output = []
        for doc, meta, dist in zip(docs, metas, distances):
            # Convert cosine distance [0, 2] → similarity score [0, 1]
            score = round(max(0.0, 1.0 - dist / 2.0), 4)
            output.append({
                "company":     meta.get("company", "Unknown"),
                "ticker":      meta.get("ticker", "UNKNOWN"),
                "source":      meta.get("source", "Unknown"),
                "text":        doc,
                "score":       score,
                "chunk_index": int(meta.get("chunk_index", 0)),
                "file":        meta.get("file", ""),
            })

        logger.info(
            "Document search: query=%r ticker=%s → %d results (top score: %.3f)",
            query[:60],
            ticker or "any",
            len(output),
            output[0]["score"] if output else 0.0,
        )
        return output

    except Exception as exc:
        logger.error("Document search failed: %s", exc, exc_info=True)
        return []


def format_document_context(chunks: list[dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a prompt-ready string block.
    Called by ai_research_service and chat_service to inject document context.
    """
    if not chunks:
        return "No relevant document context found."

    lines = ["=== DOCUMENT CONTEXT (Earnings Filings) ==="]
    for i, chunk in enumerate(chunks, 1):
        lines.append(
            f"\n[{i}] {chunk['company']} — {chunk['source']} "
            f"(relevance: {chunk['score']:.2f})\n{chunk['text']}"
        )
    return "\n".join(lines)


def format_context_block(chunks: list[dict[str, Any]]) -> str:
    """
    Backwards-compatible alias for older callers expecting `format_context_block`.
    Delegates to `format_document_context` without changing behaviour.
    """
    return format_document_context(chunks)


def retrieve_context_for_research(
    ticker: str,
    company_name: str | None = None,
    n_results: int = TOP_K_DEFAULT,
) -> list[dict[str, Any]]:
    """
    Helper used by the Phase 3A analysis pipeline.

    Strategy:
        1. Query by "<COMPANY> <TICKER> earnings filing" restricted to `ticker`
        2. If nothing found, fall back to a broader company-name search

    Returns a list of chunk dicts compatible with `format_document_context`.
    """
    base_query_parts: list[str] = []
    if company_name:
        base_query_parts.append(company_name)
    base_query_parts.append(f"{ticker} earnings filing")
    query = " ".join(base_query_parts)

    # Primary: ticker-scoped search
    chunks = search_documents(query=query, ticker=ticker, n_results=n_results)
    if chunks:
        return chunks

    # Fallback: broader company-only search
    if company_name:
        return search_documents(query=company_name, n_results=n_results)

    return []


def get_collection_stats() -> dict[str, Any]:
    """Return current collection statistics for health checks and logging."""
    try:
        client     = _get_client()
        collection = _get_collection(client)
        count      = collection.count()
        return {"collection": COLLECTION_NAME, "chunk_count": count, "status": "ok"}
    except Exception as exc:
        return {"collection": COLLECTION_NAME, "chunk_count": 0, "status": str(exc)}
