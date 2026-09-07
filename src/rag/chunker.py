"""Stage 7.2 Deterministic Text Chunker for RAG Documents."""

import re
from typing import List, Dict, Any

from src.rag.contracts import DocumentChunk, DocumentRecord


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """Split text into chunks deterministically based on paragraph/heading boundaries and character limits.

    Args:
        text: Cleaned text content to chunk.
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between adjacent chunks.

    Returns:
        List of text string chunks.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    # Split into structural blocks (paragraphs, markdown headers, code blocks)
    blocks = re.split(r"(\n\n+|(?=^#{1,6}\s))", text, flags=re.MULTILINE)
    blocks = [b for b in blocks if b and not re.match(r"^\n+$", b)]

    chunks: List[str] = []
    current_chunk = ""

    for block in blocks:
        block_str = block.strip()
        if not block_str:
            continue

        # If adding block_str exceeds chunk_size and current_chunk is non-empty
        if len(current_chunk) + len(block_str) + 2 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())

            # Apply overlap from trailing portion of current_chunk
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                overlap_text = current_chunk[-chunk_overlap:]
                # Try to align overlap to start of sentence/word if possible
                space_idx = overlap_text.find(" ")
                if space_idx != -1:
                    overlap_text = overlap_text[space_idx + 1:]
                current_chunk = overlap_text + "\n" + block_str
            else:
                current_chunk = block_str
        else:
            if current_chunk:
                current_chunk += "\n\n" + block_str
            else:
                current_chunk = block_str

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Fallback: if any individual block was larger than chunk_size, hard-split it
    final_chunks: List[str] = []
    for c in chunks:
        if len(c) > chunk_size + chunk_overlap * 2:
            sub_start = 0
            step = chunk_size - chunk_overlap
            while sub_start < len(c):
                sub_end = min(sub_start + chunk_size, len(c))
                final_chunks.append(c[sub_start:sub_end].strip())
                sub_start += step
        else:
            final_chunks.append(c)

    return [fc for fc in final_chunks if fc]


def chunk_document(
    document: DocumentRecord,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[DocumentChunk]:
    """Chunk a DocumentRecord into deterministic DocumentChunk objects.

    Each chunk is assigned a deterministic chunk_id: f"{document.document_id}_chunk_{chunk_index}".
    """
    raw_chunks = chunk_text(document.content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    total_chunks = len(raw_chunks)

    document_chunks: List[DocumentChunk] = []
    for idx, text_segment in enumerate(raw_chunks):
        chunk_id = f"{document.document_id}_chunk_{idx}"

        chunk_meta: Dict[str, Any] = {
            "document_id": document.document_id,
            "chunk_id": chunk_id,
            "filename": document.filename,
            "source": document.source,
            "stage": document.stage,
            "document_type": document.document_type,
            "checksum": document.checksum,
            "chunk_index": idx,
            "total_chunks": total_chunks,
            "path": document.path,
        }

        # Merge doc-level metadata if present
        if document.metadata:
            for k, v in document.metadata.items():
                if k not in chunk_meta and v is not None:
                    chunk_meta[k] = v

        doc_chunk = DocumentChunk(
            chunk_id=chunk_id,
            document_id=document.document_id,
            text=text_segment,
            chunk_index=idx,
            metadata=chunk_meta,
        )
        document_chunks.append(doc_chunk)

    return document_chunks
