import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.citations import format_full_citation, format_in_text
from app.services.llm import _parse_json, generate_breakdown, answer_question
from app.models import Paper

def test_citations_deterministic():
    print("Testing citation formatter...")
    p = Paper(
        filename="test.pdf",
        title="Attention Is All You Need",
        authors='["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"]',
        year="2017",
        venue="NeurIPS"
    )
    
    # APA
    apa_full = format_full_citation(p, "apa")
    apa_in = format_in_text(p, "apa", 4)
    print(f"APA Full: {apa_full}")
    print(f"APA In-Text: {apa_in}")
    assert "Vaswani, A., Shazeer, N., Parmar, N." in apa_full or "Vaswani, A." in apa_full
    assert "(Vaswani et al., 2017, p. 4)" in apa_in
    
    # MLA
    mla_full = format_full_citation(p, "mla")
    mla_in = format_in_text(p, "mla", 4)
    print(f"MLA Full: {mla_full}")
    print(f"MLA In-Text: {mla_in}")
    assert "Ashish Vaswani, et al." in mla_full
    assert "(Vaswani 4)" in mla_in
    
    # Chicago
    chicago_full = format_full_citation(p, "chicago")
    chicago_in = format_in_text(p, "chicago", 4)
    print(f"Chicago Full: {chicago_full}")
    print(f"Chicago In-Text: {chicago_in}")
    assert "Ashish Vaswani" in chicago_full
    assert "(Vaswani 2017, 4)" in chicago_in
    
    # IEEE
    ieee_full = format_full_citation(p, "ieee")
    ieee_in = format_in_text(p, "ieee", 4)
    print(f"IEEE Full: {ieee_full}")
    print(f"IEEE In-Text: {ieee_in}")
    assert "Ashish Vaswani" in ieee_full
    assert "[1, p. 4]" in ieee_in
    
    print("Citation formatter tests passed!")

def test_json_parsing_defensive():
    print("Testing defensive JSON parser...")
    raw_markdown_json = """
```json
{
  "title": "A Great Paper",
  "authors": ["John Doe"],
  "year": "2026",
  "venue": "IEEE"
}
```
"""
    parsed = _parse_json(raw_markdown_json)
    assert parsed["title"] == "A Great Paper"
    assert parsed["authors"] == ["John Doe"]
    
    # Direct JSON string
    direct_json = '{"title": "Direct Paper", "authors": []}'
    parsed_direct = _parse_json(direct_json)
    assert parsed_direct["title"] == "Direct Paper"
    
    print("Defensive JSON parser tests passed!")

def test_gemini_integration():
    # Only run if API key is configured
    key = settings.gemini_api_key
    if not key or "YOUR_GEMINI_API_KEY_HERE" in key or "paste_your_key" in key:
        print("Skipping Gemini API integration test: GEMINI_API_KEY is not configured.")
        return
        
    print("Running Gemini API integration test...")
    text = "[PAGE 1] This is a research paper titled 'A Review of Transformers'. The authors are Jane Doe and John Smith. It was published in 2025 at the AI Journal. We present the Transformer model."
    
    # Test breakdown
    print("Testing generate_breakdown...")
    breakdown = generate_breakdown(text)
    print(f"Breakdown response: {breakdown}")
    assert "title" in breakdown
    assert "authors" in breakdown
    
    # Test QA
    print("Testing answer_question...")
    chunks = [
        {"text": "We find that using a learning rate of 0.001 leads to the best convergence.", "page": 3}
    ]
    qa = answer_question("what learning rate was used?", chunks)
    print(f"QA response: {qa}")
    assert "answer" in qa
    assert "citations" in qa
    
    print("Gemini API integration tests passed!")

if __name__ == "__main__":
    test_citations_deterministic()
    test_json_parsing_defensive()
    test_gemini_integration()
