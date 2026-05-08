from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from app.database import SessionLocal, ChatHistory
import requests
import json as json_lib

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

VALID_LANGUAGES = {
    "english", "french", "spanish", "arabic", "portuguese",
    "german", "italian", "chinese", "japanese", "korean",
    "russian", "hindi", "dutch", "swedish", "norwegian",
    "danish", "finnish", "polish", "turkish", "greek"
}


# ─────────────────────────────────────────
# DB-BACKED SESSION HISTORY
# ─────────────────────────────────────────

class DBChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._messages = []
        self._load_from_db()

    def _load_from_db(self):
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
        self._messages = []


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return DBChatMessageHistory(session_id=session_id)


# ─────────────────────────────────────────
# OLLAMA HELPERS — defined first so all
# functions below can use them
# ─────────────────────────────────────────

def ollama_call(prompt: str) -> str:
    """Generic reusable Ollama call — no streaming."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"⚠️  Ollama call failed: {e}")
        return ""


def ollama_stream(prompt: str, context: str, chat_history: list):
    """Stream response tokens from Ollama one by one."""
    messages = []

    for msg in chat_history:
        if hasattr(msg, 'content'):
            role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
            messages.append({"role": role, "content": msg.content})

    system = f"""You are a helpful document assistant.
Use the context below to answer the question as thoroughly as possible.
If the answer is partially in the context, use what is available.
Only say "I don't have enough information in this document" if there is absolutely nothing relevant.

Context:
{context}"""

    messages = [{"role": "system", "content": system}] + messages
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": True
            },
            stream=True,
            timeout=120
        )

        for line in response.iter_lines():
            if not line:
                continue
            try:
                if isinstance(line, bytes):
                    raw = line.decode('utf-8', errors='replace')
                else:
                    raw = line

                data = json_lib.loads(raw)
                token = data.get("message", {}).get("content", "")
                done = data.get("done", False)

                if token:
                    yield token
                if done:
                    break

            except json_lib.JSONDecodeError:
                continue
            except Exception:
                continue

    except Exception as e:
        print(f"⚠️  Ollama stream failed: {e}")
        yield f"Error: {str(e)}"


# ─────────────────────────────────────────
# PHASE 2 FEATURES
# ─────────────────────────────────────────

def detect_language(text: str) -> str:
    """Fast language detection — skips Ollama for English text."""
    if not text or not text.strip():
        return "English"

    # If more than 90% ASCII — it's English, no need to call Ollama
    ascii_ratio = sum(c.isascii() for c in text) / len(text)
    if ascii_ratio > 0.90:
        return "English"

    # Only call Ollama for non-Latin scripts
    result = ollama_call(
        f"Detect the language of this text. Reply with ONLY the language name:\n{text}"
    )
    cleaned = result.strip() if result else ""
    if not cleaned or cleaned.lower() not in VALID_LANGUAGES:
        return "English"
    return cleaned.capitalize()


def generate_summary(chunks: list) -> str:
    sample_text = "\n\n".join([c.page_content for c in chunks[:6]])
    summary = ollama_call(
        f"You are a document summarizer. Read the following text extracted from a document "
        f"and provide a clear, concise summary in 3-5 sentences covering the main topics.\n\n"
        f"Text:\n{sample_text}\n\nSummary:"
    )
    return summary or "Summary not available."


def generate_suggestions(question: str, answer: str) -> list:
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
    if not scores:
        return "0%"
    similarities = [1 / (1 + score) for score in scores]
    avg = sum(similarities) / len(similarities)
    percentage = round(avg * 100, 1)
    return f"{percentage}%"


# ─────────────────────────────────────────
# RAG CHAIN
# ─────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful document assistant.
Use the context below to answer the question as thoroughly as possible.
Always answer in {language}.
If the answer is partially in the context, use what is available and indicate
if more detail is not in the document.
Only say "I don't have enough information in this document" if there is
absolutely nothing relevant in the context.

Context:
{context}"""


def build_qa_chain(vector_store: FAISS):
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)

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