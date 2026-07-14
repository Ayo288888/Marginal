# Marginal — Local Research Paper Reader

**Marginal** is a local, lightweight research paper reader and AI companion designed for scholars, students, and researchers. It allows you to build a local library of academic PDFs, automatically extracts structured information (TL;DR, methodology, key contributions, results, limitations, keywords, and bibliography references), and provides an interactive Q&A reading companion grounded in the document text.

![Marginal Logo](frontend/logo.png)

---

## Key Features

1. **Structured Breakdown Generation**: Automatically extracts and summarizes essential sections of uploaded PDF research papers:
   - **TL;DR (Too Long; Didn't Read)**: Concise abstract and goal summary.
   - **Methodology**: Experimental setups, algorithms, frameworks, and datasets.
   - **Key Contributions**: Bulleted lists of novel findings and technical advances.
   - **Results & Limitations**: Key evaluations and potential drawbacks.
   - **Keywords**: Auto-extracted metadata tags.
   - **Bibliography & References**: Extracted list of references, with direct links to look them up on Google Scholar.

2. **Grounded Academic Q&A**: Chat with an AI companion that reads and queries the text of your paper using strict Retrieval-Augmented Generation (RAG).
   - **Source Attribution**: Returns context-specific citations and answers.
   - **Interactive Citation Markers**: Hover or click citation markers to highlight source paragraphs and trace exactly where in the text the model retrieved information.

3. **Citation Manager**: Supports single-click copying of paper citations formatted in **APA**, **MLA**, **Chicago**, or **IEEE** styles.

4. **Parchment Theme Design Aesthetic**: Built with a classic editorial aesthetic to ensure comfortable, distraction-free reading sessions.

---

## Tech Stack

### Frontend
- **Structure**: Vanilla HTML5.
- **Styling**: Vanilla CSS3 using custom HSL CSS custom properties for theme colors (Parchment background, Charcoal ink, Brass and Burgundy highlights).
- **Logic**: ES6 Vanilla JavaScript (no heavy frontend framework dependencies).
- **Icons**: [Lucide Icons](https://lucide.dev/).

### Backend
- **Framework**: Python 3.10+ and [FastAPI](https://fastapi.tiangolo.com/).
- **Web Server**: [Uvicorn](https://www.uvicorn.org/) (ASGI).
- **PDF Extraction**: [PyPDF](https://pypi.org/project/pypdf/) for local line parsing.
- **Vector Search**: [ChromaDB](https://www.trychroma.com/) for document chunking and vector storage.
- **AI Models**: Google Gemini Generative AI (`google-genai` SDK) for structured analysis and grounding.
- **Database & Validation**: [SQLModel](https://sqlmodel.tiangolo.com/) and SQLite for local metadata storage.

---

## Setup & Running Guide

### 1. Prerequisites
- Python 3.10 or higher.
- A Gemini API Key from Google AI Studio.

### 2. Installation
Clone the repository, navigate to the `backend` directory, and create a virtual environment:
```bash
cd backend
python -m venv venv
```

Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file inside the `backend` directory and add your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Running the App
Start the Uvicorn server:
```bash
uvicorn app.main:app --reload --port 8000
```

Once running, navigate to **[http://localhost:8000](http://localhost:8000)** in your browser.
- **Upload**: Drop a PDF in the sidebar dropzone to catalog it.
- **Read**: Select any ready paper to load its structured breakdown.
- **Ask**: Enter grounding questions in the chat sidebar.
