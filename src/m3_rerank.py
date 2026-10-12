from __future__ import annotations

"""Module 3: Reranking — Cross-encoder top-20 → top-3 + latency benchmark."""

import os
import sys
import time
from dataclasses import dataclass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RERANK_TOP_K


@dataclass
class RerankResult:
    text: str
    original_score: float
    rerank_score: float
    metadata: dict
    rank: int


class CrossEncoderReranker:
    _cached_models: dict = {}

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            if self.model_name not in CrossEncoderReranker._cached_models:
                from sentence_transformers import CrossEncoder
                CrossEncoderReranker._cached_models[self.model_name] = CrossEncoder(self.model_name)
            self._model = CrossEncoderReranker._cached_models[self.model_name]
        return self._model

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
        """Rerank documents: top-20 → top-k."""
        if not documents:
            return []
        model = self._load_model()
        pairs = [(query, doc.get("text", "")) for doc in documents]
        scores = model.predict(pairs)
        if hasattr(scores, "tolist"):
            scores = scores.tolist()
        elif isinstance(scores, (int, float)):
            scores = [scores]

        scored = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
        return [
            RerankResult(
                text=doc.get("text", ""),
                original_score=float(doc.get("score", 0.0)),
                rerank_score=float(score),
                metadata=doc.get("metadata", {}),
                rank=i
            )
            for i, (score, doc) in enumerate(scored[:top_k])
        ]
