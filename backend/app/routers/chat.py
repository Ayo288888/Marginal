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
        if not paper:
            raise HTTPException(404, "Paper not found.")
        if paper.status != "ready":
            raise HTTPException(400, f"Paper is not ready yet. Status: {paper.status}")

        # 1. Retrieve relevant chunks from vector store
        retrieved = vector_store.query_chunks(req.paper_id, req.question)
        if not retrieved:
            return AskResponse(
                answer="I couldn't find any relevant chunks in this paper to answer your question.",
                citations=[]
            )

        # 2. Call Gemini model to answer question using retrieved chunks
        try:
            result = llm.answer_question(req.question, retrieved)
        except Exception as e:
            raise HTTPException(500, f"Failed to get answer from LLM: {str(e)}")

        answer_text = result.get("answer", "No answer generated.")
        
        # 3. Format citations
        cites = []
        for c in result.get("citations", []):
            try:
                # Ensure c has required keys
                marker = c.get("marker")
                quote = c.get("quote", "")
                page = c.get("page")
                if marker is not None and page is not None:
                    cites.append(
                        Citation(
                            marker=marker,
                            quote=quote,
                            page=page,
                            formatted=citations.format_in_text(paper, req.style, page)
                        )
                    )
            except Exception as ex:
                print(f"Warning: Failed to parse citation {c}: {ex}")

        return AskResponse(answer=answer_text, citations=cites)
