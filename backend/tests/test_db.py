import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import settings

# Override config to use a separate test SQLite path to avoid polluting main db
test_db_path = settings.data_dir / "test_papers.db"
settings.sqlite_path = test_db_path

from app.models import init_db, get_session, Paper

def test_sqlite_db():
    print("Running SQLite database test...")
    
    # Ensure database is initialized
    init_db()
    print("Database initialized.")
    
    # 1. Create a paper
    with get_session() as session:
        paper = Paper(
            filename="attention.pdf",
            title="Attention Is All You Need",
            authors='["Ashish Vaswani", "Noam Shazeer"]',
            year="2017",
            venue="NeurIPS",
            tldr="The Transformer architecture is introduced.",
            status="processing"
        )
        session.add(paper)
        session.commit()
        session.refresh(paper)
        paper_id = paper.id
        print(f"Paper inserted with ID: {paper_id}")
        
        assert paper.id is not None, "ID should be generated"
        assert paper.status == "processing", "Default status should be processing"
        assert paper.created_at is not None, "Timestamp should be generated"

    # 2. Query and update paper
    with get_session() as session:
        queried_paper = session.get(Paper, paper_id)
        assert queried_paper is not None, "Should query paper by ID"
        assert queried_paper.title == "Attention Is All You Need", "Title should match"
        
        # Update status
        print("Updating status to 'ready'...")
        queried_paper.status = "ready"
        session.add(queried_paper)
        session.commit()

    # 3. Verify update
    with get_session() as session:
        updated_paper = session.get(Paper, paper_id)
        assert updated_paper.status == "ready", "Status should be updated to ready"
        print("Paper successfully updated.")

    # 4. Clean up test db file
    from app.models import engine
    engine.dispose()
    
    if test_db_path.exists():
        try:
            test_db_path.unlink()
            print("Test SQLite database file removed.")
        except Exception as e:
            print(f"Warning: Could not remove test database file: {e}")
        
    print("SQLite database test passed!")

if __name__ == "__main__":
    test_sqlite_db()
