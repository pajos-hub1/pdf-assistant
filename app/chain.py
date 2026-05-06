from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from sqlalchemy.orm import Session as DBSession
from app.database import SessionLocal, ChatHistory
import requests
from dotenv import load_dotenv
import os
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


# ─────────────────────────────────────────
# DB-BACKED SESSION HISTORY
# ─────────────────────────────────────────

class DBChatMessageHistory(BaseChatMessageHistory):
    """
    Replaces the in-memory store = {} with database-backed history.
    Each session_id loads its own history from the DB.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._messages = []
        self._load_from_db()

    def _load_from_db(self):
        """Load existing chat history from DB on initialization."""
        from langchain_core.messages import HumanMessage, AIMessage
        db = SessionLocal()
        try:
            records = (
                db.query(ChatHistory)
                .filter(ChatHistory.session_id == self.session_id)
                .order_by(ChatHistory.created_at.asc())
                .all()
            )
            for record in records:
                self._messages.append(HumanMessage(content=record.question))
                self._messages.append(AIMessage(content=record.answer))
            print(f"📚 Loaded {len(records)} messages from DB for session {self.session_id}")
        finally:
            db.close()

    @property
    def messages(self):
        return self._messages

    def add_message(self, message):
        self._messages.append(message)

    def clear(self):
        """Clear in-memory messages — DB records cleared separately via endpoint."""
        self._messages = []


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Returns DB-backed chat history for a session.
    Each user gets their own isolated history.
    """
    return DBChatMessageHistory(session_id=session_id)


# ─────────────────────────────────────────
# OLLAMA HELPER
# ─────────────────────────────────────────

def ollama_call(prompt: str) -> str:
    """Generic reusable Ollama call."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"⚠️  Ollama call failed: {e}")
        return ""


# ─────────────────────────────────────────
# PHASE 2 FEATURES
# ─────────────────────────────────────────

def detect_language(text: str) -> str:
    """Detect the language of the user's question."""
    if not text or not text.strip():
        return "English"
    
    result = ollama_call(
        f"Detect the language of this text and return ONLY the language name, "
        f"nothing else. For example: 'English', 'French', 'Spanish', 'Arabic'.\n\n"
        f"Text: {text}"
    )
    
    # Clean result and fallback to English if empty or None
    cleaned = result.strip() if result else ""
    if not cleaned or cleaned.lower() == "none":
        return "English"
    
    print(f"🌐 Detected language: {cleaned}")
    return cleaned


def generate_summary(chunks: list) -> str:
    """Summarize the document using the first few chunks."""
    sample_text = "\n\n".join([c.page_content for c in chunks[:6]])
    summary = ollama_call(
        f"You are a document summarizer. Read the following text extracted from a document "
        f"and provide a clear, concise summary in 3-5 sentences covering the main topics.\n\n"
        f"Text:\n{sample_text}\n\nSummary:"
    )
    return summary or "Summary not available."


def generate_suggestions(question: str, answer: str) -> list:
    """Generate 3 follow-up question suggestions based on the Q&A."""
    result = ollama_call(
        f"Based on this question and answer, suggest exactly 3 short follow-up questions "
        f"the user might want to ask next. Return ONLY the 3 questions, one per line, "
        f"no numbering, no extra text.\n\n"
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        f"3 Follow-up questions:"
    )
    suggestions = [q.strip() for q in result.split("\n") if q.strip()][:3]
    return suggestions


def calculate_confidence(scores: list) -> str:
    """Convert FAISS similarity scores to a confidence percentage."""
    if not scores:
        return "0%"
    similarities = [1 / (1 + score) for score in scores]
    avg = sum(similarities) / len(similarities)
    percentage = round(avg * 100, 1)  # round to 1 decimal
    return f"{percentage}%"


# ─────────────────────────────────────────
# RAG CHAIN
# ─────────────────────────────────────────

SYSTEM_PROMPT = """
You are a helpful document assistant.
Use the context below to answer the question as thoroughly as possible.
Always answer in {language}.
If the answer is partially in the context, use what is available and indicate 
if more detail is not in the document.
Only say "I don't have enough information in this document" if there is 
absolutely nothing relevant in the context.

Context:
{context}
"""

def build_qa_chain(vector_store: FAISS):
    """Build the RAG chain with DB-backed memory."""
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    llm = ChatOllama(
        model="llama3.2",
        temperature=0
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    def get_context(inputs):
        question = inputs.get("question", "")
        docs = retriever.invoke(question)
        return "\n\n".join([doc.page_content for doc in docs])

    def get_language(inputs):
        lang = inputs.get("language", "English")
        if not lang or lang.lower() == "none":
            return "English"
        return lang

    chain = (
        RunnablePassthrough.assign(
            context=get_context,
            language=get_language,
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    return chain_with_history, retriever