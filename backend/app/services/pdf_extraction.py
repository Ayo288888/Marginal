from pypdf import PdfReader
from app.config import settings

def extract_pages(file_path: str) -> list[dict]:
    """Returns [{'page': 1, 'text': '...'}, ...]"""
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append({"page": i, "text": text})
    return pages

def chunk_pages(pages: list[dict], size=None, overlap=None) -> list[dict]:
    """Returns [{'text': chunk, 'page': n, 'chunk_index': i}, ...]
    Chunks never cross a page boundary, so citations stay accurate."""
    size = size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap
    chunks = []
    idx = 0
    for p in pages:
        text = " ".join(p["text"].split())
        start = 0
        while start < len(text):
            end = start + size
            piece = text[start:end].strip()
            if piece:
                chunks.append({"text": piece, "page": p["page"], "chunk_index": idx})
                idx += 1
            # Prevent infinite loops if size - overlap is <= 0
            step = size - overlap
            if step <= 0:
                step = 1
            start += step
    return chunks
