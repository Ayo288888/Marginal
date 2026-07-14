import json
import shutil
import os
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.config import settings
from app.models import Paper, engine
from app.schemas import PaperOut
from app.services import pdf_extraction, vector_store, llm, citations
from sqlmodel import Session, select

router = APIRouter()

def process_paper(paper_id: str, file_path: str):
    with Session(engine) as session:
        paper = session.get(Paper, paper_id)
        if not paper:
            return
        try:
            # 1. Extract pages
            pages = pdf_extraction.extract_pages(file_path)
            full_text = "\n\n".join(f"[PAGE {p['page']}]\n{p['text']}" for p in pages)
            if not full_text.strip():
                raise ValueError("No extractable text — this may be a scanned PDF without a text layer.")

            # 2. Add chunks to vector store
            chunks = pdf_extraction.chunk_pages(pages)
            vector_store.add_chunks(paper_id, chunks)

            # 3. Generate breakdown via Gemini LLM
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
            paper.references = json.dumps(breakdown.get("references", []))
            paper.status = "ready"
        except Exception as e:
            paper.status = "error"
            paper.error_message = str(e)
            
        session.add(paper)
        session.commit()

@router.post("/upload", response_model=PaperOut)
async def upload_paper(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are supported.")

    with Session(engine) as session:
        paper = Paper(filename=file.filename, status="processing")
        session.add(paper)
        session.commit()
        session.refresh(paper)
        paper_id = paper.id

    dest = settings.upload_dir / f"{paper_id}.pdf"
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        with Session(engine) as session:
            paper = session.get(Paper, paper_id)
            if paper:
                paper.status = "error"
                paper.error_message = f"Failed to save file: {str(e)}"
                session.add(paper)
                session.commit()
        raise HTTPException(500, f"Could not upload file: {str(e)}")

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

@router.delete("/{paper_id}")
def delete_paper_endpoint(paper_id: str):
    with Session(engine) as session:
        paper = session.get(Paper, paper_id)
        if not paper:
            raise HTTPException(404, "Paper not found")
        
        # 1. Delete from ChromaDB
        try:
            vector_store.delete_paper(paper_id)
        except Exception as e:
            print(f"Warning: Failed to delete vector chunks for {paper_id}: {e}")
            
        # 2. Delete PDF file
        dest = settings.upload_dir / f"{paper_id}.pdf"
        if dest.exists():
            try:
                os.remove(dest)
            except Exception as e:
                print(f"Warning: Failed to delete file {dest}: {e}")
                
        # 3. Delete SQLite row
        session.delete(paper)
        session.commit()
        
    return {"status": "success", "message": f"Paper {paper_id} deleted successfully."}

def _to_out(paper: Paper) -> PaperOut:
    # Safely parse JSON strings
    def safe_json_load(val: str | None) -> list:
        if not val:
            return []
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except Exception:
            return [val]

    full_citations = {}
    if paper.status == "ready":
        for style in ["apa", "mla", "chicago", "ieee"]:
            try:
                full_citations[style] = citations.format_full_citation(paper, style)
            except Exception as e:
                print(f"Warning: Failed to format citation: {e}")

    return PaperOut(
        id=paper.id,
        filename=paper.filename,
        title=paper.title,
        authors=safe_json_load(paper.authors),
        year=paper.year,
        venue=paper.venue,
        tldr=paper.tldr,
        contributions=safe_json_load(paper.contributions),
        methodology=paper.methodology,
        results=paper.results,
        limitations=paper.limitations,
        keywords=safe_json_load(paper.keywords),
        references=safe_json_load(paper.references),
        status=paper.status,
        error_message=paper.error_message,
        full_citations=full_citations,
    )
