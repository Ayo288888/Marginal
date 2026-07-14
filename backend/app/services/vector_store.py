import chromadb
from app.config import settings
from app.services.embeddings import embed_texts

_client = None

def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    return _client

def get_collection():
    # ONE collection for all papers — paper_id in metadata scopes queries.
    # This is the design choice that makes multi-paper search free later.
    return get_client().get_or_create_collection("chunks")

def add_chunks(paper_id: str, chunks: list[dict]):
    if not chunks:
        return
    collection = get_collection()
    documents = [c["text"] for c in chunks]
    metadatas = [{"paper_id": paper_id, "page": c["page"], "chunk_index": c["chunk_index"]} for c in chunks]
    ids = [f"{paper_id}_{c['chunk_index']}" for c in chunks]
    embeddings = embed_texts(documents)
    collection.add(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings)

def query_chunks(paper_id: str, question: str, top_k=None) -> list[dict]:
    top_k = top_k or settings.top_k
    collection = get_collection()
    query_embedding = embed_texts([question])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"paper_id": paper_id},   # scoping to one paper. Drop this filter later to search everything.
    )
    
    # Check if results are empty
    if not results or not results.get("documents") or len(results["documents"]) == 0:
        return []
        
    return [
        {"text": doc, "page": meta["page"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]

def delete_paper(paper_id: str):
    get_collection().delete(where={"paper_id": paper_id})
