from __future__ import annotations

"""
Module 1: Advanced Chunking Strategies
=======================================
Implement semantic, hierarchical, và structure-aware chunking.
So sánh với basic chunking (baseline) để thấy improvement.
"""

import os
import sys
import glob
import re
from dataclasses import dataclass, field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (DATA_DIR, HIERARCHICAL_PARENT_SIZE, HIERARCHICAL_CHILD_SIZE,
                    SEMANTIC_THRESHOLD)


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


def _extract_pdf_text(path: str) -> str:
    """Extract text layer từ PDF. Trả về "" nếu PDF là scan ảnh (không có text)."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """Load tất cả markdown và PDF (có text layer) từ data/."""
    docs = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            docs.append({"text": f.read(), "metadata": {"source": os.path.basename(fp)}})

    for fp in sorted(glob.glob(os.path.join(data_dir, "*.pdf"))):
        text = _extract_pdf_text(fp)
        if text:
            docs.append({"text": text, "metadata": {"source": os.path.basename(fp)}})
        else:
            print(f"  ⚠️  Bỏ qua {os.path.basename(fp)}: PDF scan ảnh, không có text layer (cần OCR).")

    return docs


def chunk_basic(text: str, chunk_size: int = 500, metadata: dict | None = None) -> list[Chunk]:
    """Basic chunking: split theo paragraph (\\n\\n)."""
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
            current = ""
        current += para + "\n\n"
    if current.strip():
        chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
    return chunks


_semantic_model = None


def _get_semantic_model():
    global _semantic_model
    if _semantic_model is None:
        from sentence_transformers import SentenceTransformer
        _semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _semantic_model


def chunk_semantic(text: str, threshold: float = SEMANTIC_THRESHOLD,
                   metadata: dict | None = None) -> list[Chunk]:
    """Split text by sentence similarity — nhóm câu cùng chủ đề."""
    metadata = metadata or {}
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n\n', text) if s.strip()]
    if not sentences:
        return []
    if len(sentences) == 1:
        return [Chunk(text=sentences[0], metadata={**metadata, "strategy": "semantic"})]

    from numpy import dot
    from numpy.linalg import norm

    model = _get_semantic_model()
    embeddings = model.encode(sentences)

    def cosine_sim(a, b):
        return float(dot(a, b) / (norm(a) * norm(b) + 1e-9))

    chunks = []
    current_sentences = [sentences[0]]

    for i in range(1, len(sentences)):
        sim = cosine_sim(embeddings[i - 1], embeddings[i])
        if sim < threshold:
            chunks.append(Chunk(
                text=" ".join(current_sentences),
                metadata={**metadata, "strategy": "semantic"}
            ))
            current_sentences = [sentences[i]]
        else:
            current_sentences.append(sentences[i])

    if current_sentences:
        chunks.append(Chunk(
            text=" ".join(current_sentences),
            metadata={**metadata, "strategy": "semantic"}
        ))

    return chunks


def chunk_hierarchical(text: str, parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE,
                       metadata: dict | None = None) -> tuple[list[Chunk], list[Chunk]]:
    """Parent-child hierarchy: retrieve child (precision) → return parent (context)."""
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return ([], [])

    parents: list[Chunk] = []
    children: list[Chunk] = []

    parent_texts: list[str] = []
    current_parent = ""
    for para in paragraphs:
        if current_parent and (len(current_parent) + len(para) + 2 > parent_size):
            parent_texts.append(current_parent.strip())
            current_parent = ""
        while len(para) > parent_size:
            parent_texts.append(para[:parent_size].strip())
            para = para[parent_size:].strip()
        if para:
            current_parent = f"{current_parent}\n\n{para}".strip() if current_parent else para

    if current_parent.strip():
        parent_texts.append(current_parent.strip())

    src_prefix = metadata.get("source", "doc")
    for p_idx, p_text in enumerate(parent_texts):
        pid = f"{src_prefix}_parent_{p_idx}"
        parents.append(Chunk(
            text=p_text,
            metadata={**metadata, "chunk_type": "parent", "parent_id": pid},
            parent_id=pid
        ))

        sub_parts = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', p_text) if s.strip()]
        current_child = ""
        for part in sub_parts:
            if current_child and (len(current_child) + len(part) + 1 > child_size):
                children.append(Chunk(
                    text=current_child.strip(),
                    metadata={**metadata, "chunk_type": "child", "parent_id": pid},
                    parent_id=pid
                ))
                current_child = ""
            while len(part) > child_size:
                children.append(Chunk(
                    text=part[:child_size].strip(),
                    metadata={**metadata, "chunk_type": "child", "parent_id": pid},
                    parent_id=pid
                ))
                part = part[child_size:].strip()
            if part:
                current_child = f"{current_child} {part}".strip() if current_child else part

        if current_child.strip():
            children.append(Chunk(
                text=current_child.strip(),
                metadata={**metadata, "chunk_type": "child", "parent_id": pid},
                parent_id=pid
            ))

    return (parents, children)


def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    """Parse markdown headers → chunk theo logical structure."""
    metadata = metadata or {}
    if not text.strip():
        return []

    sections = re.split(r'(^#{1,3}\s+.+$)', text, flags=re.MULTILINE)
    chunks: list[Chunk] = []
    current_header = ""
    current_content = ""

    for sec in sections:
        if not sec:
            continue
        if re.match(r'^#{1,3}\s+', sec):
            chunk_text = f"{current_header}\n\n{current_content}".strip() if current_header else current_content.strip()
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    metadata={
                        **metadata,
                        "section": current_header.strip() if current_header else "intro",
                        "strategy": "structure"
                    }
                ))
            current_header = sec.strip()
            current_content = ""
        else:
            current_content += sec

    chunk_text = f"{current_header}\n\n{current_content}".strip() if current_header else current_content.strip()
    if chunk_text:
        chunks.append(Chunk(
            text=chunk_text,
            metadata={
                **metadata,
                "section": current_header.strip() if current_header else "intro",
                "strategy": "structure"
            }
        ))

    return chunks
