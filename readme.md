# 📄 PDF Assistant

A production-grade RAG (Retrieval-Augmented Generation) PDF assistant.
Ask questions about your documents using a 100% free, local AI stack.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![React](https://img.shields.io/badge/React-18-blue)

---

## ✨ Features

- 📄 **PDF Upload** — supports both typed and scanned/handwritten PDFs via OCR
- 🤖 **Local AI** — powered by Ollama + Llama 3.2, no API keys required
- 💬 **Multiple Chats** — create, rename, delete chat sessions
- 🔄 **Streaming** — answers stream token by token like ChatGPT
- 🔐 **JWT Auth** — secure login with access + refresh tokens
- 📊 **Confidence Scores** — know how reliable each answer is
- 💡 **Suggestions** — auto-generated follow-up questions
- 🌐 **Multi-language** — detects and responds in user's language
- 📤 **Export** — download chat history as PDF or TXT
- 🌙 **Dark/Light Mode** — full theme support
- 🔒 **Input Sanitization** — all inputs validated and sanitized

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Tailwind CSS + Vite |
| Backend | FastAPI + Python 3.12 |
| LLM | Ollama + Llama 3.2 (local) |
| Embeddings | HuggingFace sentence-transformers |
| Vector Store | FAISS |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (access + refresh tokens) |
| OCR | Tesseract + pdf2image |
| Password | Argon2id hashing |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/pajos-hub1/pdf-assistant.git
cd pdf-assistant
```

### 2. Install system dependencies

**Mac:**
```bash
brew install tesseract poppler
```

**Linux/Ubuntu:**
```bash
sudo apt install tesseract-ocr poppler-utils
```

### 3. Install Ollama + pull model
```bash
# Download from https://ollama.com
ollama pull llama3.2
```

### 4. Setup backend
```bash
# Create virtual environment
python -m venv env
source env/bin/activate  # Mac/Linux
env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Generate JWT secrets and add to .env
python -c "import secrets; print(secrets.token_hex(32))"
# Run twice — one for JWT_SECRET_KEY, one for JWT_REFRESH_SECRET_KEY
```

### 5. Setup frontend
```bash
cd frontend
npm install
```

### 6. Run the app

**Terminal 1 — Backend:**
```bash
source env/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

### 7. Open in browser
```
http://localhost:5173
```

## 📁 Project Structure
```
pdf-assistant/
├── app/
│   ├── main.py              # FastAPI app setup
│   ├── database.py          # SQLAlchemy models + helpers
│   ├── auth.py              # JWT validation middleware
│   ├── jwt_handler.py       # Token creation + verification
│   ├── sanitizer.py         # Input sanitization
│   ├── chain.py             # RAG chain + Ollama integration
│   ├── ingestor.py          # PDF loading + OCR + FAISS
│   ├── tasks.py             # Background OCR processing
│   ├── logger.py            # Analytics logging
│   ├── routers/
│   │   ├── auth.py          # /auth/* endpoints
│   │   ├── chats.py         # /chats/* endpoints
│   │   ├── documents.py     # /upload, /status endpoints
│   │   ├── qa.py            # /ask/stream endpoint
│   │   └── admin.py         # /admin/* endpoints
│   └── services/
│       └── export.py        # PDF + TXT export
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Auth/        # Login + Register
│   │   │   ├── Chat/        # ChatWindow, ChatMessage, ChatInput
│   │   │   ├── Sidebar/     # ChatList, ChatListItem
│   │   │   ├── Documents/   # DocumentPreview
│   │   │   ├── Layout/      # Header
│   │   │   └── UI/          # Toast, Skeleton
│   │   ├── context/
│   │   │   ├── AuthContext  # JWT token management
│   │   │   ├── ChatContext  # Active chat state
│   │   │   ├── ThemeContext # Dark/light mode
│   │   │   └── ToastContext # Notifications
│   │   ├── hooks/
│   │   │   └── useStream    # SSE streaming
│   │   └── services/
│   │       └── api.js       # All API calls + interceptors
│   └── vite.config.js
├── data/                    # FAISS indexes + SQLite DB
├── logs/                    # Analytics logs
├── .env.example             # Environment template
├── requirements.txt
└── README.md
```


### API Endpoints

#### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server status |
| POST | `/auth/register` | Register new account |
| POST | `/auth/login` | Login + get tokens |
| POST | `/auth/refresh` | Refresh access token |

#### Protected (requires `Authorization: Bearer <token>`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/me` | Current user info |
| GET | `/chats` | List all chats |
| POST | `/chats/new` | Create new chat |
| PATCH | `/chats/{id}/rename` | Rename chat |
| DELETE | `/chats/{id}` | Delete chat |
| GET | `/chats/{id}/history` | Chat history |
| GET | `/chats/{id}/documents` | Chat documents |
| GET | `/chats/{id}/export?format=pdf` | Export chat |
| POST | `/upload` | Upload PDF |
| GET | `/status/{doc_id}` | Processing status |
| POST | `/ask/stream` | Stream answer (SSE) |
| GET | `/history` | Session history |
| DELETE | `/history` | Clear history |


### How RAG Works

```
Upload PDF
│
▼
OCR (if scanned) → Extract text
│
▼
Split into chunks (500 tokens, 50 overlap)
│
▼
Embed with HuggingFace (all-MiniLM-L6-v2)
│
▼
Store in FAISS vector index
│
▼
User asks question
│
▼
Embed question → similarity search
│
▼
Retrieve top 5 relevant chunks
│
▼
Send chunks + question to Llama 3.2
│
▼
Stream answer token by token
```

## 🧪 Running Tests

```bash
# Backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v

# Frontend
cd frontend
npm run test
```

---

## 🐳 Docker

```bash
docker-compose up --build
```

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

Built by **Joseph Ogunye** as part of a full-stack AI engineering project.