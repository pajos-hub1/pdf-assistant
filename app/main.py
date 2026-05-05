from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
import os
from app.ingestor import ingest_pdf, FAISS_INDEX_PATH
from app.chain import build_qa_chain, store
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

app = FastAPI(title="PDF Document Assistant")

qa_chain = None
retriever = None
vector_store = None
uploaded_files = []
chat_history = []
SESSION_ID = "default_session"


class QuestionRequest(BaseModel):
    question: str


@app.on_event("startup")
async def startup():
    global qa_chain, retriever, vector_store
    if os.path.exists(FAISS_INDEX_PATH):
        print("Found existing FAISS index — loading from disk...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        vector_store = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        qa_chain, retriever = build_qa_chain(vector_store)
        print("FAISS index loaded — ready to answer questions")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": "llama3.2",
        "cost": "$0.00",
        "documents_loaded": len(uploaded_files),
        "files": uploaded_files
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global qa_chain, retriever, vector_store, uploaded_files

    file_path = f"data/{file.filename}"
    os.makedirs("data", exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    vector_store = ingest_pdf(file_path, existing_store=vector_store)
    qa_chain, retriever = build_qa_chain(vector_store)

    if file.filename not in uploaded_files:
        uploaded_files.append(file.filename)

    return {
        "message": f"{file.filename} ingested successfully.",
        "total_documents": len(uploaded_files),
        "files": uploaded_files
    }


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    global chat_history

    if not qa_chain:
        return {"error": "No document uploaded yet. POST to /upload first."}

    # Get source pages before invoking chain
    docs = retriever.invoke(request.question)
    sources = sorted(set([
        doc.metadata.get("page", "unknown") for doc in docs
    ]))

    answer = qa_chain.invoke(
        {"question": request.question},
        config={"configurable": {"session_id": SESSION_ID}}
    )

    chat_history.append({
        "question": request.question,
        "answer": answer,
        "sources": sources
    })

    return {
        "answer": answer,
        "sources": f"Pages: {sources}"
    }


@app.get("/history")
async def get_history():
    return {"history": chat_history}


@app.delete("/history")
async def clear_history():
    global chat_history
    chat_history.clear()
    # Clear LangChain memory store
    if SESSION_ID in store:
        store[SESSION_ID].clear()
    return {"message": "Chat history cleared and memory reset."}


@app.delete("/documents")
async def clear_documents():
    global qa_chain, retriever, vector_store, uploaded_files, chat_history
    qa_chain = None
    retriever = None
    vector_store = None
    uploaded_files.clear()
    chat_history.clear()
    if SESSION_ID in store:
        store[SESSION_ID].clear()
    if os.path.exists(FAISS_INDEX_PATH):
        shutil.rmtree(FAISS_INDEX_PATH)
    return {"message": "All documents and history cleared."}