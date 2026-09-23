import math
import re
from collections import Counter
from typing import List, Dict, Any, Optional
import numpy as np

MONTH_MAP = {
    'january': '01', 'jan': '01',
    'february': '02', 'feb': '02',
    'march': '03', 'mar': '03',
    'april': '04', 'apr': '04',
    'may': '05',
    'june': '06', 'jun': '06',
    'july': '07', 'jul': '07',
    'august': '08', 'aug': '08',
    'september': '09', 'sep': '09', 'sept': '09',
    'october': '10', 'oct': '10',
    'november': '11', 'nov': '11',
    'december': '12', 'dec': '12'
}


def extract_claim_date(query: str) -> Optional[str]:
    """
    Extracts the claim/event date from the query string if explicitly mentioned.
    Returns ISO format date string 'YYYY-MM-DD' or None if no date is specified.
    """
    query_lower = query.lower().strip()

    # 1. ISO format: YYYY-MM-DD or YYYY-Month-DD
    iso_match = re.search(r'\b(202[4-9])-(0[1-9]|1[0-2]|[a-z]+)-(0[1-9]|[12]\d|3[01])\b', query_lower)
    if iso_match:
        year, month_str, day = iso_match.group(1), iso_match.group(2), iso_match.group(3)
        month = MONTH_MAP.get(month_str, month_str.zfill(2))
        return f"{year}-{month}-{day.zfill(2)}"

    # 2. DD Month YYYY or Month DD YYYY
    dmY_match = re.search(r'\b(0?[1-9]|[12]\d|3[01])\s+([a-z]+)\s+(202[4-9])\b', query_lower)
    if dmY_match:
        day, month_str, year = dmY_match.group(1), dmY_match.group(2), dmY_match.group(3)
        if month_str in MONTH_MAP:
            return f"{year}-{MONTH_MAP[month_str]}-{day.zfill(2)}"

    MdY_match = re.search(r'\b([a-z]+)\s+(0?[1-9]|[12]\d|3[01]),?\s+(202[4-9])\b', query_lower)
    if MdY_match:
        month_str, day, year = MdY_match.group(1), MdY_match.group(2), MdY_match.group(3)
        if month_str in MONTH_MAP:
            return f"{year}-{MONTH_MAP[month_str]}-{day.zfill(2)}"

    # 3. Month YYYY
    MY_match = re.search(r'\b([a-z]+)\s+(202[4-9])\b', query_lower)
    if MY_match:
        month_str, year = MY_match.group(1), MY_match.group(2)
        if month_str in MONTH_MAP:
            return f"{year}-{MONTH_MAP[month_str]}-01"

    # 4. Explicit year match (e.g. 2025, 2024)
    year_match = re.search(r'\b(202[45])\b', query_lower)
    if year_match:
        return f"{year_match.group(1)}-12-31"

    return None


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words and clause codes."""
    return re.findall(r'[§\w\.\-]+', text.lower())


class BM25Index:
    """
    Pure-Python in-memory BM25 implementation for zero-dependency keyword search.

    Improvement (2.2): term-frequency maps are pre-computed once at index time
    as Counter objects, so `get_scores()` is O(|query_tokens| × N) instead of
    re-scanning each document list for every query term.
    """

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_len = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_len) / len(corpus) if corpus else 1.0
        self.N = len(corpus)

        # Pre-compute per-document term frequency maps (2.2)
        self.tf: List[Counter] = [Counter(doc) for doc in corpus]

        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self._build_index()

    def _build_index(self):
        # Count how many documents contain each term
        for tf_map in self.tf:
            for term in tf_map:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        # Compute IDF scores
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log(1 + (self.N - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query_tokens: List[str]) -> np.ndarray:
        scores = np.zeros(self.N, dtype=np.float32)
        for q in query_tokens:
            if q not in self.idf:
                continue
            idf = self.idf[q]
            for idx in range(self.N):
                # O(1) lookup via pre-computed Counter (2.2)
                term_count = self.tf[idx].get(q, 0)
                if term_count > 0:
                    num = term_count * (self.k1 + 1)
                    denom = term_count + self.k1 * (
                        1 - self.b + self.b * (self.doc_len[idx] / self.avgdl)
                    )
                    scores[idx] += idf * (num / denom)
        return scores


class ClauseRetriever:
    """
    Hybrid Retriever (In-Memory NumPy Store):
    - Dense vector embeddings via BAAI/bge-small-en-v1.5 (with local TF-IDF fallback)
    - Lexical search via BM25
    - Hybrid scoring: combined = alpha × cosine + (1-alpha) × bm25_norm
    - Temporal date-aware clause filtering

    Improvement (2.1): `alpha` is now a tunable constructor parameter (default 0.7).
    """

    def __init__(
        self,
        chunks: List[Dict[str, Any]],
        embedding_model_name: str = "BAAI/bge-small-en-v1.5",
        alpha: float = 0.7,          # 2.1 — tunable hybrid weight
    ):
        self.chunks = chunks
        self.embedding_model_name = embedding_model_name
        self.alpha = alpha            # 2.1
        self.dense_model = None
        self.use_dense_model = False

        # Attempt to load sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.dense_model = SentenceTransformer(embedding_model_name)
            self.use_dense_model = True
        except Exception:
            self.use_dense_model = False

        self._build_indexes()

    def _build_indexes(self):
        # 1. Build BM25 Index (uses pre-computed Counters internally)
        corpus_tokenized = [
            tokenize(f"{c.get('display_id', '')} {c.get('heading', '')} {c.get('text', '')}")
            for c in self.chunks
        ]
        self.bm25 = BM25Index(corpus_tokenized)

        # 2. Build In-Memory Dense Vector Store (NumPy Array)
        if self.use_dense_model and self.dense_model is not None:
            texts = [
                f"{c.get('display_id', '')}: {c.get('heading', '')}\n{c.get('text', '')}"
                for c in self.chunks
            ]
            embeddings = self.dense_model.encode(texts, normalize_embeddings=True)
            self.dense_embeddings = np.array(embeddings, dtype=np.float32)
        else:
            self._build_tfidf_fallback()

    def _build_tfidf_fallback(self):
        self.vocab: Dict[str, int] = {}
        for c in self.chunks:
            tokens = set(
                tokenize(f"{c.get('display_id', '')} {c.get('heading', '')} {c.get('text', '')}")
            )
            for t in tokens:
                self.vocab[t] = self.vocab.get(t, 0) + 1

        self.term_list = sorted(list(self.vocab.keys()))
        self.term_to_id = {t: i for i, t in enumerate(self.term_list)}
        self.num_docs = len(self.chunks)

        matrix = np.zeros((self.num_docs, len(self.term_list)), dtype=np.float32)
        for idx, c in enumerate(self.chunks):
            tokens = tokenize(
                f"{c.get('display_id', '')} {c.get('heading', '')} {c.get('text', '')}"
            )
            counts = Counter(tokens)
            for t, count in counts.items():
                if t in self.term_to_id:
                    tid = self.term_to_id[t]
                    idf = math.log((self.num_docs + 1) / (self.vocab[t] + 1)) + 1.0
                    matrix[idx, tid] = (1 + math.log(count)) * idf

        # Normalise rows to unit length for fast dot product
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.dense_embeddings = matrix / norms

    def _get_query_dense_embedding(self, query: str) -> np.ndarray:
        if self.use_dense_model and self.dense_model is not None:
            emb = self.dense_model.encode([query], normalize_embeddings=True)[0]
            return np.array(emb, dtype=np.float32)
        else:
            vec = np.zeros(len(self.term_list), dtype=np.float32)
            tokens = tokenize(query)
            counts = Counter(tokens)
            for t, count in counts.items():
                if t in self.term_to_id:
                    tid = self.term_to_id[t]
                    idf = math.log((self.num_docs + 1) / (self.vocab.get(t, 0) + 1)) + 1.0
                    vec[tid] = (1 + math.log(count)) * idf
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        claim_date: Optional[str] = None,
        use_hybrid: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant clauses using Cosine Similarity over in-memory
        NumPy vectors, with optional BM25 keyword boosting for exact statutory terms.

        Hybrid weight: combined = alpha × cosine + (1-alpha) × bm25_norm  (2.1)
        """
        target_date = claim_date if claim_date is not None else extract_claim_date(query)

        # 1. Cosine Similarity via dot product on normalised vectors
        q_dense = self._get_query_dense_embedding(query)
        cosine_similarities = np.dot(self.dense_embeddings, q_dense)

        # 2. BM25 Lexical Scores
        q_tokens = tokenize(query)
        bm25_scores = self.bm25.get_scores(q_tokens)
        max_bm25 = float(np.max(bm25_scores)) if np.max(bm25_scores) > 0 else 1.0
        bm25_norm = bm25_scores / max_bm25

        # 3. Final Ranking Score (2.1 — uses self.alpha)
        if use_hybrid:
            combined_scores = self.alpha * cosine_similarities + (1.0 - self.alpha) * bm25_norm
        else:
            combined_scores = cosine_similarities

        # 4. Filter by temporal validity and collect scored candidates
        scored_candidates = []
        for idx, chunk in enumerate(self.chunks):
            effective_date = chunk.get("effective_date", "2025-12-31")

            # Temporal filtering:
            # - target_date < 2026-03-01: exclude post-amendment chunks
            # - target_date >= 2026-03-01 or None: include all chunks
            if (
                target_date is not None
                and target_date < "2026-03-01"
                and effective_date >= "2026-03-01"
            ):
                continue

            c_copy = dict(chunk)
            c_copy["score"] = float(combined_scores[idx])
            c_copy["cosine_similarity"] = float(cosine_similarities[idx])
            c_copy["bm25_score"] = float(bm25_scores[idx])
            scored_candidates.append(c_copy)

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]
