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
        env_file = str(Path(__file__).resolve().parent.parent / ".env")

settings = Settings()
settings.gemini_api_key = settings.gemini_api_key.strip()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
