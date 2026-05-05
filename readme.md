A RAG-based PDF assistant built with a 100% free stack.

## Stack
| Tool | Purpose |
|------|---------|
| FastAPI | REST API layer |
| Ollama + Llama 3.2 | Local LLM (free, no API key) |
| HuggingFace Embeddings | Text vectorization |
| FAISS | Vector store |
| Tesseract OCR | Scanned PDF support |

## Setup

### 1. Install system dependencies
```bash
# Mac
brew install tesseract poppler

# Linux
sudo apt install tesseract-ocr poppler-utils
```

### 2. Install Ollama & pull model
```bash
# Download from https://ollama.com
ollama pull llama3.2
```

### 3. Create virtual environment
```bash
python -m venv env
source env/bin/activate  # Mac/Linux
env\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 4. Run the server
```bash
uvicorn app.main:app --reload
```

### 5. Open Swagger UI
```
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server status |
| POST | `/upload` | Upload a PDF |
| POST | `/ask` | Ask a question |
| GET | `/history` | Get chat history |
| DELETE | `/history` | Clear chat history |
| DELETE | `/documents` | Clear all documents |

## Features
- Scanned & handwritten PDF support via OCR
- Conversation memory
- Source page citations
- Multi-PDF support
- Persistent FAISS index
- 100% free — no API keys required