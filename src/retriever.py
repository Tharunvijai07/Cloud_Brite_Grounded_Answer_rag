import math
import re
from collections import Counter
from typing import List, Dict, Any
from src.loader import load_policy_manual
from src.chunker import parse_chunks


class ClauseRetriever:
    """
    In-memory vector retriever using term-frequency inverse-document-frequency (TF-IDF) 
    and sub-word/n-gram keyword matching to retrieve top-k policy clauses.
    """

    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.doc_vectors = []
        self.idf = {}
        self.vocab = set()
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenizes text into lowercase alphanumeric terms and section IDs."""
        tokens = re.findall(r'\b\w+\b|\§?\d+\.\d+(?:\.\d+)?', text.lower())
        return tokens

    def _build_index(self):
        """Computes TF-IDF representations for all clause chunks."""
        N = len(self.chunks)
        doc_freqs = Counter()
        doc_tfs = []

        for chunk in self.chunks:
            # Combine clause text, heading, part, and clause_id for richer indexing
            full_content = f"{chunk['clause_id']} {chunk['part']} {chunk['heading']} {chunk['text']}"
            tokens = self._tokenize(full_content)
            tf = Counter(tokens)
            doc_tfs.append((chunk, tf, len(tokens)))
            for term in set(tokens):
                doc_freqs[term] += 1
                self.vocab.add(term)

        # Compute IDF: log((N + 1) / (df + 1)) + 1
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
            
            # Normalize vector
            norm_vec = {t: v / norm for t, v in vec.items()}
            self.doc_vectors.append((chunk, norm_vec))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves top-k clause chunks most relevant to the user's query.

        Args:
            query: Plain-language user question.
            top_k: Number of candidate clauses to return (default 5).

        Returns:
            List of clause dictionaries enriched with a 'score' field.
        """
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
            # Cosine similarity dot product
            score = sum(val * doc_vec.get(term, 0.0) for term, val in norm_q_vec.items())
            
            # Boost score if explicit clause ID (e.g. 4.3.2) is referenced in query
            if chunk['clause_id'] in query or f"§{chunk['clause_id']}" in query:
                score += 0.5

            if score > 0.0:
                chunk_copy = dict(chunk)
                chunk_copy['score'] = round(score, 4)
                scored_chunks.append(chunk_copy)

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:top_k]


if __name__ == "__main__":
    manual_text = load_policy_manual()
    chunks = parse_chunks(manual_text)
    retriever = ClauseRetriever(chunks)
    
    test_query = "How many days do I have to report a change in income?"
    results = retriever.retrieve(test_query, top_k=3)
    
    print(f"Query: '{test_query}'")
    print(f"Top {len(results)} Results:")
    for r in results:
        print(f"  - [§{r['clause_id']}] {r['heading']} (Score: {r['score']})")
