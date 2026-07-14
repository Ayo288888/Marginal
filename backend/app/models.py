from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
from datetime import datetime
import uuid
from app.config import settings

class Paper(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    title: Optional[str] = None
    authors: Optional[str] = None   # JSON-encoded list (e.g., ["Author A", "Author B"])
    year: Optional[str] = None
    venue: Optional[str] = None
    tldr: Optional[str] = None
    contributions: Optional[str] = None  # JSON-encoded list
    methodology: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    keywords: Optional[str] = None       # JSON-encoded list
    references: Optional[str] = None     # JSON-encoded list of references (citations bibliography)
    status: str = "processing"           # processing | ready | error
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Ensure parent directory for database exists
settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.sqlite_path}",
    connect_args={"check_same_thread": False} # Required for SQLite with FastAPI multi-threading
)

def init_db():
    SQLModel.metadata.create_all(engine)
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    try:
        columns = [col['name'] for col in inspector.get_columns('paper')]
        if 'references' not in columns:
            with Session(engine) as session:
                session.exec(text("ALTER TABLE paper ADD COLUMN references TEXT"))
                session.commit()
    except Exception as e:
        print(f"Database migration note: {e}")

def get_session():
    return Session(engine)
