from pydantic import BaseModel
from typing import Optional, List

class PaperOut(BaseModel):
    id: str
    filename: str
    title: Optional[str] = None
    authors: List[str] = []
    year: Optional[str] = None
    venue: Optional[str] = None
    tldr: Optional[str] = None
    contributions: List[str] = []
    methodology: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    keywords: List[str] = []
    references: List[str] = []
    status: str
    error_message: Optional[str] = None
    full_citations: dict[str, str] = {}

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
    citations: List[Citation]
