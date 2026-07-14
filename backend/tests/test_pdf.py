import sys
from pathlib import Path

# Add backend to path so we can import app
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.pdf_extraction import chunk_pages, extract_pages

def test_chunk_pages():
    print("Running chunk_pages test...")
    pages = [
        {"page": 1, "text": "This is page one text. It should be split into smaller chunks if it exceeds the size limit."},
        {"page": 2, "text": "This is page two. Notice how chunking does not cross boundaries."}
    ]
    
    # Test with small size to force multiple chunks
    chunks = chunk_pages(pages, size=20, overlap=5)
    
    for c in chunks:
        print(f"Chunk {c['chunk_index']} (Page {c['page']}): '{c['text']}'")
        
    assert len(chunks) > 0, "Should generate chunks"
    assert all("page" in c and "text" in c and "chunk_index" in c for c in chunks), "All keys must exist"
    
    # Test boundaries: page 1 chunks should only have page 1 text
    for c in chunks:
        if c["page"] == 1:
            assert "page two" not in c["text"].lower(), "Page 1 chunk contains page 2 text!"
        if c["page"] == 2:
            assert "page one" not in c["text"].lower(), "Page 2 chunk contains page 1 text!"
            
    print("chunk_pages test passed!")

if __name__ == "__main__":
    test_chunk_pages()
    
    # If a pdf path is provided as argument, test extraction
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Extracting pages from: {pdf_path}")
        pages = extract_pages(pdf_path)
        print(f"Extracted {len(pages)} pages.")
        for p in pages:
            print(f"Page {p['page']} text length: {len(p['text'])}")
            if p['text']:
                print(f"Snippet: {p['text'][:100]}...")
