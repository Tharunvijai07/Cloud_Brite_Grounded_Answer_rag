import math
import re
from collections import Counter
from typing import List, Dict, Any, Optional

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

    # 2. DD Month YYYY or Month DD YYYY (e.g., '20 march 2025', 'march 20 2025')
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

    # 3. Month YYYY (e.g., 'february 2026', 'march 2025')
    MY_match = re.search(r'\b([a-z]+)\s+(202[4-9])\b', query_lower)
    if MY_match:
        month_str, year = MY_match.group(1), MY_match.group(2)
        if month_str in MONTH_MAP:
            return f"{year}-{MONTH_MAP[month_str]}-01"

    # 4. Explicit year match e.g. '2025' or '2024'
    year_match = re.search(r'\b(202[45])\b', query_lower)
    if year_match:
        return f"{year_match.group(1)}-12-31"

    return None


class ClauseRetriever:
    """
    In-memory vector retriever using term-frequency inverse-document-frequency (TF-IDF),
    word stemming, and heading weighting to retrieve top-k policy clauses.
    Supports date-filtered retrieval for temporal versioning.
    """

    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.doc_vectors = []
        self.idf = {}
        self.vocab = set()
        self._build_index()

    def _stem(self, word: str) -> str:
        """Simple English stemmer rule for plural/tense normalization."""
        w = word.lower()
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        if len(w) > 4 and w.endswith("ing"):
            w = w[:-3]
        if len(w) > 4 and w.endswith("ed"):
            w = w[:-2]
        return w

    def _tokenize(self, text: str) -> List[str]:
        """Tokenizes text into lowercase stemmed terms and section IDs."""
        raw_tokens = re.findall(r'\b\w+\b|\§?\d+\.\d+(?:\.\d+)?', text.lower())
        tokens = [self._stem(t) for t in raw_tokens]
        return tokens

    def _build_index(self):
        """Computes TF-IDF representations for all clause chunks."""
        N = len(self.chunks)
        doc_freqs = Counter()
        doc_tfs = []

        for chunk in self.chunks:
            full_content = (
                f"{chunk['clause_id']} {chunk['clause_id']} "
                f"{chunk['part']} {chunk['part']} "
                f"{chunk['heading']} {chunk['heading']} {chunk['heading']} "
                f"{chunk['text']}"
            )
            tokens = self._tokenize(full_content)
            tf = Counter(tokens)
            doc_tfs.append((chunk, tf, len(tokens)))
            for term in set(tokens):
                doc_freqs[term] += 1
                self.vocab.add(term)

        # Compute IDF
        for term, df in doc_freqs.items():
            self.idf[term] = math.log((N + 1.0) / (df + 1.0)) + 1.0

        # Compute normalized TF-IDF vector for each chunk
        for chunk, tf, total_tokens in doc_tfs:
            vec = {}
            norm_sq = 0.0
            for term, count in tf.items():
                tfidf = (count / total_tokens) * self.idf[term]
                vec[term] = tfidf
                norm_sq += tfidf ** 2
            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            
            norm_vec = {t: v / norm for t, v in vec.items()}
            self.doc_vectors.append((chunk, norm_vec))

    def retrieve(self, query: str, top_k: int = 5, claim_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves top-k clause chunks most relevant to the query."""
        target_date = claim_date if claim_date is not None else extract_claim_date(query)
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        q_tf = Counter(query_tokens)
        q_vec = {}
        norm_sq = 0.0

        for term, count in q_tf.items():
            if term in self.idf:
                tfidf = (count / len(query_tokens)) * self.idf[term]
                q_vec[term] = tfidf
                norm_sq += tfidf ** 2

        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        norm_q_vec = {t: v / norm for t, v in q_vec.items()}

        scored_chunks = []
        for chunk, doc_vec in self.doc_vectors:
            effective_date = chunk.get("effective_date", "2025-12-31")
            
            # If a specific pre-amendment claim date is provided, filter out amendment chunks
            if target_date and target_date < "2026-03-01" and effective_date == "2026-03-01":
                continue

            score = sum(val * doc_vec.get(term, 0.0) for term, val in norm_q_vec.items())
            
            # Boost score if explicit clause ID is referenced
            if chunk['clause_id'] in query or f"§{chunk['clause_id']}" in query:
                score += 0.5

            if score > 0.0:
                chunk_copy = dict(chunk)
                chunk_copy['score'] = round(score, 4)
                chunk_copy['active_claim_date'] = target_date or "UNSPECIFIED"
                scored_chunks.append(chunk_copy)

        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:top_k]
