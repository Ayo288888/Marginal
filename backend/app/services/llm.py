import json
import time
from google import genai
from app.config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

def _parse_json(text: str) -> dict:
    cleaned = text.strip()
    # Strip markdown block formatting if present
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json\n"):
            cleaned = cleaned[5:]
        elif cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return json.loads(cleaned)

def _generate_with_retry(prompt: str) -> str:
    for attempt in range(5):
        try:
            client = get_client()
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt == 4:
                raise e
            wait_time = (2 ** attempt) + 1
            print(f"Gemini API call failed: {e}. Retrying in {wait_time}s (attempt {attempt + 1}/5)...")
            time.sleep(wait_time)

BREAKDOWN_PROMPT = """You analyze research papers. You are given the raw \
extracted text of one paper, with page markers like [PAGE 3].
Respond with ONLY a valid JSON object, no markdown fences, no preamble, in \
exactly this shape:
{{"title": string, "authors": [string], "year": string, "venue": string, \
"tldr": string, "contributions": [string], "methodology": string, \
"results": string, "limitations": string, "keywords": [string], \
"references": [string]}}
If a field can't be determined, use "Unknown". Be concise.
For "references", extract up to 20 key bibliography reference strings from the references/bibliography section of the paper.

Paper text:
{text}
"""

def generate_breakdown(full_text: str) -> dict:
    # Truncate text to avoid model limits
    truncated = full_text[:120000]
    response_text = _generate_with_retry(BREAKDOWN_PROMPT.format(text=truncated))
    return _parse_json(response_text)

QA_PROMPT = """You answer questions about a research paper using ONLY the \
context chunks provided below, each tagged with its page number.
Respond with ONLY a valid JSON object, no markdown fences, no preamble:
{{"answer": string (cite claims inline like [1] [2]), "citations": \
[{{"marker": number, "quote": string (<20 words, verbatim from context), \
"page": number}}]}}
If the context doesn't answer the question, say so plainly and return an \
empty citations array.

Context chunks:
{context}

Question: {question}
"""

def answer_question(question: str, retrieved_chunks: list[dict]) -> dict:
    context = "\n\n---\n\n".join(
        f"[PAGE {c['page']}]\n{c['text']}" for c in retrieved_chunks
    )
    prompt = QA_PROMPT.format(context=context, question=question)
    response_text = _generate_with_retry(prompt)
    return _parse_json(response_text)
