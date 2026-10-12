from __future__ import annotations

"""
Module 5: Enrichment Pipeline
==============================
Làm giàu chunks TRƯỚC khi embed: Summarize, HyQA, Contextual Prepend, Auto Metadata.
"""

import os
import re
import sys
from dataclasses import dataclass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY


@dataclass
class EnrichedChunk:
    """Chunk đã được làm giàu."""
    original_text: str
    enriched_text: str
    summary: str
    hypothesis_questions: list[str]
    auto_metadata: dict
    method: str


def summarize_chunk(text: str) -> str:
    """Tạo summary ngắn cho chunk."""
    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    if sentences:
        s_part = ". ".join(sentences[:2])
        return s_part if s_part.endswith(".") else s_part + "."
    return text


def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:
    """Generate câu hỏi mà chunk có thể trả lời."""
    sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if len(s.strip()) > 10]
    return [f"{s.rstrip('.')}?" for s in sentences[:n_questions]]


def contextual_prepend(text: str, document_title: str = "") -> str:
    """Prepend context giải thích chunk nằm ở đâu trong document."""
    prefix = f"[Nguồn tài liệu: {document_title}] " if document_title else ""
    return f"{prefix}{text}"


def extract_metadata(text: str, source: str = "") -> dict:
    """Extract metadata cho chunk."""
    category = "policy"
    src_lower = source.lower()
    if any(k in src_lower for k in ("luong", "tam_ung", "mua_sam", "cong_tac", "chi_phi", "thuong")):
        category = "finance"
    elif any(k in src_lower for k in ("vpn", "mat_khau", "bao_mat", "phan_loai")):
        category = "it"
    elif any(k in src_lower for k in ("nghi_", "thu_viec", "dao_tao", "mentor", "danh_gia", "bao_hiem", "phu_cap")):
        category = "hr"
    return {
        "topic": source.replace(".md", "").replace(".pdf", "") if source else "general",
        "entities": [],
        "category": category,
        "language": "vi",
    }


def enrich_chunks(
    chunks: list[dict],
    methods: list[str] | None = None,
) -> list[EnrichedChunk]:
    """Chạy enrichment pipeline trên danh sách chunks, bảo toàn số lượng và thứ tự."""
    if methods is None:
        methods = ["contextual", "metadata"]

    enriched: list[EnrichedChunk] = []
    for chunk in chunks:
        text = chunk["text"]
        source = chunk.get("metadata", {}).get("source", "")
        summary = summarize_chunk(text)
        questions = generate_hypothesis_questions(text)
        enriched_text = contextual_prepend(text, source)
        auto_meta = extract_metadata(text, source)

        enriched.append(EnrichedChunk(
            original_text=text,
            enriched_text=enriched_text,
            summary=summary,
            hypothesis_questions=questions,
            auto_metadata={**chunk.get("metadata", {}), **auto_meta},
            method="+".join(methods),
        ))

    return enriched
