import sys
import shutil
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import settings

# Override config to use a separate test database path to avoid polluting main db
test_chroma_dir = settings.data_dir / "test_chroma_db"
settings.chroma_dir = test_chroma_dir
test_chroma_dir.mkdir(parents=True, exist_ok=True)

from app.services.vector_store import add_chunks, query_chunks, delete_paper

def test_vector_store():
    print("Running vector store test...")
    paper_id = "test_paper_123"
    chunks = [
        {"text": "Sentence Transformers is a framework for state-of-the-art sentence embeddings.", "page": 1, "chunk_index": 0},
        {"text": "Chroma is an AI-native open-source vector database designed to build AI applications.", "page": 1, "chunk_index": 1},
        {"text": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python.", "page": 2, "chunk_index": 2}
    ]
    
    # 1. Add chunks
    print("Adding chunks...")
    add_chunks(paper_id, chunks)
    print("Chunks added.")
    
    # 2. Query chunks
    print("Querying for 'what is fastapi'...")
    results = query_chunks(paper_id, "what is fastapi", top_k=2)
    print(f"Query results: {results}")
    
    assert len(results) > 0, "Query should return results"
    # The first result should be the one about FastAPI
    assert "fastapi" in results[0]["text"].lower(), "FastAPI chunk should be retrieved"
    assert results[0]["page"] == 2, "FastAPI chunk should be on page 2"
    
    # 3. Query for another paper (should be empty)
    print("Querying for non-existent paper...")
    empty_results = query_chunks("other_paper", "what is fastapi")
    assert len(empty_results) == 0, "Should not return results for other paper"
    
    # 4. Delete paper
    print("Deleting paper...")
    delete_paper(paper_id)
    print("Paper deleted.")
    
    # 5. Query again (should be empty)
    deleted_results = query_chunks(paper_id, "what is fastapi")
    assert len(deleted_results) == 0, "Should return empty list after deletion"
    
    print("Vector store test passed!")

if __name__ == "__main__":
    try:
        test_vector_store()
    finally:
        # Clean up test database directory
        import gc
        import time
        import app.services.vector_store
        
        # Release the persistent client and run garbage collection
        app.services.vector_store._client = None
        gc.collect()
        time.sleep(0.5)
        
        if test_chroma_dir.exists():
            try:
                shutil.rmtree(test_chroma_dir)
                print("Test vector database cleaned up.")
            except Exception as e:
                print(f"Warning: Could not clean up test chroma DB directory: {e}")
