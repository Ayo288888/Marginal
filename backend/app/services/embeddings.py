from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None

def get_embedder():
    global _model
    if _model is None:
        # Load the sentence transformer model lazily
        _model = SentenceTransformer(settings.embedding_model)
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    # Generate embeddings and convert to list of floats
    return get_embedder().encode(texts, convert_to_numpy=True).tolist()
