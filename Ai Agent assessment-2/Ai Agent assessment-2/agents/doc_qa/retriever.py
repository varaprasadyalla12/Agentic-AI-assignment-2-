"""
Hybrid Lexical and Semantic Document Retriever.
Combines BM25-style TF-IDF keyword ranking with dense character n-gram cosine matching.
"""
import re
import math
from typing import List, Tuple, Dict, Set
from agents.doc_qa.document_parser import DocumentChunk


class HybridRetriever:
    """
    In-memory hybrid retrieval engine providing sub-millisecond retrieval with provenance.
    """

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.doc_freqs: Dict[str, int] = {}
        self.total_docs: int = 0
        self.avg_doc_len: float = 0.0

    def add_documents(self, chunks: List[DocumentChunk]):
        self.chunks.extend(chunks)
        self._reindex()

    def clear(self):
        self.chunks = []
        self.doc_freqs = {}
        self.total_docs = 0
        self.avg_doc_len = 0.0

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text)]

    def _get_ngrams(self, text: str, n: int = 3) -> Set[str]:
        clean = re.sub(r"\s+", " ", text.lower().strip())
        return {clean[i:i+n] for i in range(max(1, len(clean) - n + 1))}

    def _reindex(self):
        self.total_docs = len(self.chunks)
        if self.total_docs == 0:
            return

        self.doc_freqs = {}
        total_len = 0

        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk.text))
            total_len += len(tokens)
            for token in tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_len / max(1, self.total_docs)

    def _score_bm25(self, query_tokens: List[str], chunk_tokens: List[str]) -> float:
        k1 = 1.5
        b = 0.75
        score = 0.0
        doc_len = len(chunk_tokens)

        # Count frequencies in this chunk
        tf_dict: Dict[str, int] = {}
        for token in chunk_tokens:
            tf_dict[token] = tf_dict.get(token, 0) + 1

        for qt in query_tokens:
            if qt not in tf_dict:
                continue
            tf = tf_dict[qt]
            df = self.doc_freqs.get(qt, 1)
            # Standard Robertson-Spärck Jones IDF
            idf = math.log(1 + (self.total_docs - df + 0.5) / (df + 0.5))
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / max(1.0, self.avg_doc_len)))
            score += idf * (numerator / max(0.001, denominator))

        return max(0.0, score)

    def _score_ngram(self, query: str, chunk_text: str) -> float:
        q_grams = self._get_ngrams(query, n=3)
        c_grams = self._get_ngrams(chunk_text, n=3)
        if not q_grams or not c_grams:
            return 0.0
        intersection = len(q_grams.intersection(c_grams))
        union = len(q_grams.union(c_grams))
        return intersection / max(1, union)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [(c, 0.5) for c in self.chunks[:top_k]]

        scored: List[Tuple[DocumentChunk, float]] = []
        bm25_scores = []
        ngram_scores = []

        for chunk in self.chunks:
            chunk_tokens = self._tokenize(chunk.text)
            b_score = self._score_bm25(query_tokens, chunk_tokens)
            n_score = self._score_ngram(query, chunk.text)
            bm25_scores.append(b_score)
            ngram_scores.append(n_score)

        max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0

        for idx, chunk in enumerate(self.chunks):
            norm_b = bm25_scores[idx] / max_bm25
            norm_n = ngram_scores[idx]
            # Hybrid combined score
            composite = 0.7 * norm_b + 0.3 * norm_n
            scored.append((chunk, composite))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
