# Marginal — local research paper reader

A build spec for a FastAPI backend + local vector store + Gemini API research
paper reader: upload a PDF, get an AI breakdown, ask questions grounded in the
paper with formatted citations. Built to start with one paper at a time, with
the storage layer already shaped so it scales into a multi-paper library later
without a rewrite.

Each step below has: what you're building, why, the exact files to create,
and a **"Prompt to use"** block — if you want to hand this off to Claude Code
(or paste it into any coding assistant) instead of typing the code by hand,
copy that block as-is. Otherwise just follow the instructions directly.

---

## 0. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn | async, typed, auto-generates OpenAPI docs for free |
| PDF extraction | `pypdf` | pure Python, no system dependencies |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | free, runs on CPU, ~80MB, no GPU needed |
| Vector store | `ChromaDB` (persistent, local) | zero-config local DB, metadata filtering built in |
| Paper metadata | `SQLite` via `sqlmodel` | tracks title/authors/year per paper — this is what lets you scale to a library later |
| LLM | Gemini API (`google-genai` SDK), model `gemini-2.5-flash` | free tier, 1M token context, plenty for a whole paper |
| Frontend | Plain HTML/CSS/JS served as static files by FastAPI | no build step, no Node required; upgrade to React later if you want |
| Dev tooling | `venv`, `python-dotenv` | standard, no extra services |

Nothing here needs Docker, a cloud database, or your GPU. Everything runs on
`localhost` with one terminal command.

---

## 1. Prerequisites

1. **Python 3.11 or newer** — check with `python3 --version`.
2. **A free Gemini API key**:
   - Go to https://aistudio.google.com/apikey
   - Sign in with your Google account (the same one your Pro subscription is on — doesn't matter, it's unrelated)
   - Click "Create API key" — no billing setup required for the free tier
   - Copy the key, you'll paste it into a `.env` file in Step 2
3. **A code editor** (VS Code, or Claude Code in your terminal if you have it).
4. That's it — no Docker, no Node, no cloud account.

---

## 2. Project scaffolding

**What you're building:** the folder structure and environment everything else lives in.

```
paper-reader/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app entrypoint
│   │   ├── config.py              # settings (API keys, paths) from .env
│   │   ├── models.py               # SQLModel tables (papers)
│   │   ├── schemas.py              # Pydantic request/response shapes
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_extraction.py   # PDF -> chunked, page-tagged text
│   │   │   ├── embeddings.py       # local embedding model wrapper
│   │   │   ├── vector_store.py     # Chroma wrapper (add/query chunks)
│   │   │   ├── llm.py              # Gemini calls (breakdown + Q&A)
│   │   │   └── citations.py        # APA/MLA/Chicago/IEEE formatting
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── papers.py           # upload, get breakdown, list papers
│   │       └── chat.py             # ask a question about a paper
│   ├── data/
│   │   ├── uploads/                # saved PDF files
│   │   ├── chroma_db/               # persistent vector store (auto-created)
│   │   └── papers.db                # SQLite file (auto-created)
│   ├── requirements.txt
│   └── .env                        # GEMINI_API_KEY=... (never commit this)
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── .gitignore
```

Run these commands:

```bash
mkdir -p paper-reader/backend/app/services paper-reader/backend/app/routers
mkdir -p paper-reader/backend/data/uploads paper-reader/backend/data/chroma_db
mkdir -p paper-reader/frontend
cd paper-reader
python3 -m venv backend/venv
source backend/venv/bin/activate    # Windows: backend\venv\Scripts\activate
```

Create `paper-reader/.gitignore`:
```
backend/venv/
backend/data/uploads/*
backend/data/chroma_db/*
backend/data/papers.db
backend/.env
__pycache__/
*.pyc
```

Create `paper-reader/backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
pydantic-settings==2.4.0
sqlmodel==0.0.21
pypdf==4.3.1
sentence-transformers==3.0.1
chromadb==0.5.5
google-genai==0.3.0
python-dotenv==1.0.1
```

Install everything:
```bash
pip install -r backend/requirements.txt
```

Create `paper-reader/backend/.env`:
```
GEMINI_API_KEY=paste_your_key_here
```

> **Prompt to use** (if handing this step to an AI coding assistant):
> "Create the folder structure and files described below for a FastAPI
> project called paper-reader, with a Python virtual environment, a
> requirements.txt with these exact packages [paste table above], and a
> .gitignore that excludes venv, data files, and .env. Don't write any
> application logic yet — just scaffold empty files with a one-line
> docstring in each saying what will go there."

---

## 3. Step 1 — Config and app skeleton

**What you're building:** a FastAPI app that boots, loads your API key from
`.env`, and serves the frontend's static files.

`backend/app/config.py`:
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    gemini_api_key: str
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    upload_dir: Path = data_dir / "uploads"
    chroma_dir: Path = data_dir / "chroma_db"
    sqlite_path: Path = data_dir / "papers.db"
    embedding_model: str = "all-MiniLM-L6-v2"
    gemini_model: str = "gemini-2.5-flash"
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 4

    class Config:
        env_file = ".env"

settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
```

`backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.routers import papers, chat

app = FastAPI(title="Marginal — paper reader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
```

Leave `papers.py` and `chat.py` as empty `APIRouter()` stubs for now so the
app boots:

```python
# backend/app/routers/papers.py
from fastapi import APIRouter
router = APIRouter()
```
```python
# backend/app/routers/chat.py
from fastapi import APIRouter
router = APIRouter()
```

**Test it:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` — you should see the (empty) OpenAPI page.

> **Prompt to use:** "Build a FastAPI app skeleton with a pydantic-settings
> Config class reading GEMINI_API_KEY from .env, a main.py that mounts a
> static frontend folder at '/' and includes two empty routers ('papers' and
> 'chat') under /api/papers and /api/chat. It should boot cleanly with
> `uvicorn app.main:app --reload` and serve /docs."

---

## 4. Step 2 — PDF extraction and chunking

**What you're building:** a service that takes an uploaded PDF and returns
page-tagged, chunked text — the same chunking approach as the earlier
version of this project, just moved server-side.

`backend/app/services/pdf_extraction.py`:
```python
from pypdf import PdfReader
from app.config import settings

def extract_pages(file_path) -> list[dict]:
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
            start += size - overlap
    return chunks
```

Note the deliberate choice: **chunks never span two pages**. This costs a
little chunk-boundary precision but means every citation's page number is
always exactly right — worth the tradeoff for a citation-focused tool.

> **Prompt to use:** "Write a pdf_extraction.py service with two functions:
> extract_pages(file_path) using pypdf that returns a list of {page, text}
> dicts (one per PDF page), and chunk_pages(pages, size, overlap) that
> slides a character window over each page's text independently (never
> spanning two pages) and returns {text, page, chunk_index} dicts."

---

## 5. Step 3 — Local embeddings + Chroma vector store

**What you're building:** the retrieval layer. This is the piece that scales
you from "one paper" to "a library" — every chunk gets a `paper_id` in its
metadata, so querying can be scoped to one paper now, or opened up to search
across all papers later by just... not filtering.

`backend/app/services/embeddings.py`:
```python
from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None

def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_embedder().encode(texts, convert_to_numpy=True).tolist()
```

`backend/app/services/vector_store.py`:
```python
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
    collection = get_collection()
    documents = [c["text"] for c in chunks]
    metadatas = [{"paper_id": paper_id, "page": c["page"], "chunk_index": c["chunk_index"]} for c in chunks]
    ids = [f"{paper_id}_{c['chunk_index']}" for c in chunks]
    embeddings = embed_texts(documents)
    collection.add(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings)

def query_chunks(paper_id: str, question: str, top_k=None):
    top_k = top_k or settings.top_k
    collection = get_collection()
    query_embedding = embed_texts([question])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"paper_id": paper_id},   # <- scoping to one paper. Drop this
                                        #    filter later to search everything.
    )
    return [
        {"text": doc, "page": meta["page"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]

def delete_paper(paper_id: str):
    get_collection().delete(where={"paper_id": paper_id})
```

> **Prompt to use:** "Write embeddings.py wrapping a lazily-loaded
> SentenceTransformer('all-MiniLM-L6-v2'), and vector_store.py wrapping a
> single persistent ChromaDB collection called 'chunks' where every chunk is
> stored with paper_id, page, and chunk_index metadata. Include add_chunks,
> query_chunks (filtered by paper_id with a `where` clause), and
> delete_paper functions."

---

## 6. Step 4 — Paper metadata (SQLite)

**What you're building:** a small table tracking each uploaded paper's
title/authors/year/venue and processing status. This is what turns "a
folder of PDFs" into "a library" — it's the list you'll eventually render
as a sidebar of papers to search across.

`backend/app/models.py`:
```python
from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
from datetime import datetime
import uuid
from app.config import settings

class Paper(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    title: Optional[str] = None
    authors: Optional[str] = None   # JSON-encoded list, kept simple for sqlite
    year: Optional[str] = None
    venue: Optional[str] = None
    tldr: Optional[str] = None
    contributions: Optional[str] = None  # JSON-encoded list
    methodology: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    keywords: Optional[str] = None       # JSON-encoded list
    status: str = "processing"           # processing | ready | error
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

engine = create_engine(f"sqlite:///{settings.sqlite_path}")

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
```

Call `init_db()` once at startup — add this line to `main.py` right after
the `app = FastAPI(...)` line:
```python
from app.models import init_db
init_db()
```

> **Prompt to use:** "Write a SQLModel table called Paper with fields: id
> (uuid string primary key), filename, title, authors (store as a JSON
> string), year, venue, tldr, contributions (JSON string), methodology,
> results, limitations, keywords (JSON string), status (default
> 'processing'), error_message, created_at. Include an init_db() that
> creates the sqlite file and tables, and a get_session() helper."

---

## 7. Step 5 — Gemini integration

**What you're building:** the two Gemini calls this app needs — the paper
breakdown, and question-answering with citation markers. Both ask Gemini to
return strict JSON so the backend never has to guess how to parse prose.

`backend/app/services/llm.py`:
```python
import json
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
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    return json.loads(cleaned)

BREAKDOWN_PROMPT = """You analyze research papers. You are given the raw \
extracted text of one paper, with page markers like [PAGE 3].
Respond with ONLY a valid JSON object, no markdown fences, no preamble, in \
exactly this shape:
{{"title": string, "authors": [string], "year": string, "venue": string, \
"tldr": string, "contributions": [string], "methodology": string, \
"results": string, "limitations": string, "keywords": [string]}}
If a field can't be determined, use "Unknown". Be concise.

Paper text:
{text}
"""

def generate_breakdown(full_text: str) -> dict:
    truncated = full_text[:120000]
    response = get_client().models.generate_content(
        model=settings.gemini_model,
        contents=BREAKDOWN_PROMPT.format(text=truncated),
    )
    return _parse_json(response.text)

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
    response = get_client().models.generate_content(
        model=settings.gemini_model,
        contents=QA_PROMPT.format(context=context, question=question),
    )
    return _parse_json(response.text)
```

> **Prompt to use:** "Write llm.py using the google-genai SDK
> (genai.Client(api_key=...).models.generate_content(model=..., \
> contents=...)) with two functions: generate_breakdown(full_text) that \
> asks Gemini for a JSON paper summary (title, authors, year, venue, tldr, \
> contributions, methodology, results, limitations, keywords), and \
> answer_question(question, retrieved_chunks) that asks Gemini to answer \
> using only the given page-tagged chunks and return JSON with an answer \
> string containing [n] markers plus a citations array of {marker, quote, \
> page}. Both must instruct the model to output raw JSON with no markdown \
> fences, and both must be parsed defensively (strip code fences before \
> json.loads)."

---

## 8. Step 6 — Citation formatting

**What you're building:** pure-Python formatting functions — no LLM call
needed here, since citation style rules are deterministic and it's more
reliable to compute them yourself than trust a model to get "p. 4" right
every time.

`backend/app/services/citations.py`:
```python
import json

def _authors_list(authors_json: str | None) -> list[str]:
    return json.loads(authors_json) if authors_json else []

def _last_names(authors: list[str]) -> list[str]:
    return [a.strip().split(" ")[-1] for a in authors if a.strip()]

def format_full_citation(paper, style: str) -> str:
    authors = _authors_list(paper.authors)
    year = paper.year or "n.d."
    title = paper.title or "Untitled"
    venue = paper.venue or "Unknown venue"

    if style == "apa":
        if authors:
            formatted = ", ".join(
                f"{a.split()[-1]}, {' '.join(p[0]+'.' for p in a.split()[:-1])}"
                for a in authors
            )
        else:
            formatted = "Unknown author"
        return f"{formatted} ({year}). {title}. {venue}."
    if style == "mla":
        first = authors[0] if authors else "Unknown author"
        suffix = ", et al." if len(authors) > 1 else ""
        return f'{first}{suffix}. "{title}." {venue}, {year}.'
    if style == "chicago":
        formatted = ", ".join(authors) if authors else "Unknown author"
        return f'{formatted}. "{title}." {venue} ({year}).'
    if style == "ieee":
        formatted = ", ".join(authors) if authors else "Unknown author"
        return f'{formatted}, "{title}," {venue}, {year}.'
    return title

def format_in_text(paper, style: str, page: int) -> str:
    last = _last_names(_authors_list(paper.authors))
    year = paper.year or "n.d."
    if style == "apa":
        who = ("Unknown" if not last else last[0] if len(last) == 1
               else f"{last[0]} & {last[1]}" if len(last) == 2
               else f"{last[0]} et al.")
        return f"({who}, {year}, p. {page})"
    if style == "mla":
        return f"({last[0] if last else 'Unknown'} {page})"
    if style == "chicago":
        return f"({last[0] if last else 'Unknown'} {year}, {page})"
    if style == "ieee":
        return f"[1, p. {page}]"
    return f"(p. {page})"
```

Write a quick test to sanity-check this in isolation before wiring it to the
API — it's pure logic, easy to get right in a REPL:
```bash
python -c "
from app.models import Paper
from app.services.citations import format_full_citation
p = Paper(filename='x.pdf', title='Attention Is All You Need', authors='[\"Ashish Vaswani\", \"Noam Shazeer\"]', year='2017', venue='NeurIPS')
print(format_full_citation(p, 'apa'))
"
```

> **Prompt to use:** "Write citations.py with format_full_citation(paper,
> style) and format_in_text(paper, style, page) supporting 'apa', 'mla',
> 'chicago', 'ieee'. Authors are stored as a JSON string on the paper
> object; parse them and handle 0, 1, 2, and 3+ author cases distinctly for
> APA (et al. at 3+)."

---

## 9. Step 7 — Wiring the API routes

**What you're building:** the actual endpoints the frontend calls.

`backend/app/schemas.py`:
```python
from pydantic import BaseModel

class PaperOut(BaseModel):
    id: str
    filename: str
    title: str | None
    authors: list[str]
    year: str | None
    venue: str | None
    tldr: str | None
    contributions: list[str]
    methodology: str | None
    results: str | None
    limitations: str | None
    keywords: list[str]
    status: str
    error_message: str | None

class AskRequest(BaseModel):
    paper_id: str
    question: str
    style: str = "apa"

class Citation(BaseModel):
    marker: int
    quote: str
    page: int
    formatted: str

class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
```

`backend/app/routers/papers.py`:
```python
import json, shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.config import settings
from app.models import Paper, get_session, engine
from app.schemas import PaperOut
from app.services import pdf_extraction, vector_store, llm
from sqlmodel import Session, select

router = APIRouter()

def process_paper(paper_id: str, file_path: str):
    with Session(engine) as session:
        paper = session.get(Paper, paper_id)
        try:
            pages = pdf_extraction.extract_pages(file_path)
            full_text = "\n\n".join(f"[PAGE {p['page']}]\n{p['text']}" for p in pages)
            if not full_text.strip():
                raise ValueError("No extractable text — this may be a scanned PDF without a text layer.")

            chunks = pdf_extraction.chunk_pages(pages)
            vector_store.add_chunks(paper_id, chunks)

            breakdown = llm.generate_breakdown(full_text)
            paper.title = breakdown.get("title")
            paper.authors = json.dumps(breakdown.get("authors", []))
            paper.year = breakdown.get("year")
            paper.venue = breakdown.get("venue")
            paper.tldr = breakdown.get("tldr")
            paper.contributions = json.dumps(breakdown.get("contributions", []))
            paper.methodology = breakdown.get("methodology")
            paper.results = breakdown.get("results")
            paper.limitations = breakdown.get("limitations")
            paper.keywords = json.dumps(breakdown.get("keywords", []))
            paper.status = "ready"
        except Exception as e:
            paper.status = "error"
            paper.error_message = str(e)
        session.add(paper)
        session.commit()

@router.post("/upload", response_model=PaperOut)
async def upload_paper(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are supported.")

    with Session(engine) as session:
        paper = Paper(filename=file.filename)
        session.add(paper)
        session.commit()
        session.refresh(paper)
        paper_id = paper.id

    dest = settings.upload_dir / f"{paper_id}.pdf"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(process_paper, paper_id, str(dest))

    with Session(engine) as session:
        paper = session.get(Paper, paper_id)
        return _to_out(paper)

@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: str):
    with Session(engine) as session:
        paper = session.get(Paper, paper_id)
        if not paper:
            raise HTTPException(404, "Paper not found")
        return _to_out(paper)

@router.get("/", response_model=list[PaperOut])
def list_papers():
    with Session(engine) as session:
        papers = session.exec(select(Paper)).all()
        return [_to_out(p) for p in papers]

def _to_out(paper: Paper) -> PaperOut:
    return PaperOut(
        id=paper.id, filename=paper.filename, title=paper.title,
        authors=json.loads(paper.authors) if paper.authors else [],
        year=paper.year, venue=paper.venue, tldr=paper.tldr,
        contributions=json.loads(paper.contributions) if paper.contributions else [],
        methodology=paper.methodology, results=paper.results,
        limitations=paper.limitations,
        keywords=json.loads(paper.keywords) if paper.keywords else [],
        status=paper.status, error_message=paper.error_message,
    )
```

`backend/app/routers/chat.py`:
```python
from fastapi import APIRouter, HTTPException
from app.models import Paper, engine
from app.schemas import AskRequest, AskResponse, Citation
from app.services import vector_store, llm, citations
from sqlmodel import Session

router = APIRouter()

@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    with Session(engine) as session:
        paper = session.get(Paper, req.paper_id)
        if not paper or paper.status != "ready":
            raise HTTPException(400, "Paper not ready yet.")

        retrieved = vector_store.query_chunks(req.paper_id, req.question)
        if not retrieved:
            return AskResponse(answer="I couldn't find anything relevant in this paper.", citations=[])

        result = llm.answer_question(req.question, retrieved)
        cites = [
            Citation(
                marker=c["marker"], quote=c["quote"], page=c["page"],
                formatted=citations.format_in_text(paper, req.style, c["page"]),
            )
            for c in result.get("citations", [])
        ]
        return AskResponse(answer=result["answer"], citations=cites)
```

**Why upload is a background task:** processing a paper (extraction +
embedding + a Gemini call) takes several seconds — you don't want the HTTP
request to hang open that long. The frontend polls `GET /api/papers/{id}`
until `status` flips to `"ready"`.

**Test it end to end** with the auto-generated docs UI:
```bash
uvicorn app.main:app --reload --port 8000
```
Go to `http://localhost:8000/docs`, try `POST /api/papers/upload` with a
real PDF, then poll `GET /api/papers/{id}` until status is `ready`, then try
`POST /api/chat/ask`.

> **Prompt to use:** "Wire up two FastAPI routers: papers.py with POST
> /upload (saves the file, creates a Paper row with status='processing',
> kicks off a BackgroundTask that extracts+chunks+embeds+asks Gemini for a
> breakdown and updates the row to status='ready' or 'error'), GET /{id},
> and GET / (list all). And chat.py with POST /ask that retrieves chunks
> for a paper_id via vector_store, calls llm.answer_question, and formats
> each citation with citations.format_in_text before returning."

---

## 10. Step 8 — Frontend

**What you're building:** the UI. This reuses the same visual approach as
the earlier browser-only version, but now every AI call goes through your
own backend instead of calling Gemini/Claude directly from the browser —
which also means your API key never touches the client.

Key differences from the previous artifact version:
- `fetch('/api/papers/upload', {method:'POST', body: formData})` instead of client-side PDF parsing
- Poll `GET /api/papers/{id}` every ~1.5s until `status === 'ready'`
- `fetch('/api/chat/ask', {...})` for each question — citations come back
  already formatted, no client-side formatting logic needed anymore

Scaffold `frontend/index.html`, `frontend/styles.css`, and `frontend/app.js`
with the same layout as before (upload zone → paper breakdown panel + chat
panel), swapping every direct-to-LLM `fetch` call for a call to your local
API instead.

> **Prompt to use:** "Build a static frontend (index.html, styles.css,
> app.js, no build step, no framework) with an upload dropzone, a paper
> breakdown panel (title/authors/tldr/collapsible sections/keywords/full
> citation with a style selector), and a chat panel. On upload, POST to
> /api/papers/upload as multipart form data, then poll GET
> /api/papers/{id} every 1.5s until status is 'ready' or 'error'. For each
> chat question, POST {paper_id, question, style} to /api/chat/ask and
> render the returned answer with [n] markers plus a citations list
> showing each quote and its pre-formatted citation string."

---

## 11. Step 9 — Run it

```bash
cd paper-reader/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` in your browser. Upload a PDF, wait for
processing, ask it questions.

---

## 12. Already built for scaling to a library

You said you want room to grow into a multi-paper library — here's exactly
what in this design already supports that, and what's left to add when
you're ready:

**Already in place:**
- Every chunk in Chroma carries `paper_id` — searching across *all* papers
  instead of one is just dropping the `where={"paper_id": ...}` filter.
- `Paper` is already its own SQLite table — listing papers, searching by
  title, or paginating is already just SQL queries away.
- `GET /api/papers/` already returns the full list — a sidebar UI is a
  thin layer on top of an endpoint you already have.

**Left to add later (each is additive, not a rewrite):**
1. A `GET /api/chat/ask-all` endpoint that queries across every paper's
   chunks and includes `paper_id`/title in each citation, so answers can
   say "found in *Paper A*, page 4" and "*Paper B*, page 2."
2. A library sidebar in the frontend listing all uploaded papers with
   status badges.
3. Optionally, a `tags` or `collections` field on `Paper` for organizing a
   large library.

---

## Troubleshooting

- **"No extractable text" error** — the PDF is scanned images without a
  text layer. You'd need OCR (e.g. `pytesseract`) to handle those; out of
  scope for v1.
- **Gemini 429 errors** — you've hit the free tier's requests-per-minute
  cap. Add a short retry-with-backoff around `generate_content` calls.
- **Chroma "collection already exists" errors** — safe to ignore;
  `get_or_create_collection` handles this, but if you see it from raw
  Chroma calls elsewhere, switch to `get_or_create_collection`.
- **CORS errors in the browser console** — only relevant if you serve the
  frontend from a different port/origin than the API; the CORS middleware
  in `main.py` already allows all origins for local dev.
