from google import genai
from app.config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = get_client()
    try:
        response = client.models.embed_content(
            model='text-embedding-004',
            contents=texts,
        )
        return [embedding.values for embedding in response.embeddings]
    except Exception as e:
        print(f"Error calling Gemini Embeddings API: {e}")
        raise e
