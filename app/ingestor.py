from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
import requests
import os

FAISS_INDEX_PATH = "data/faiss_index"


def clean_ocr_text(text: str) -> str:
    """Use Ollama to clean noisy OCR text."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": f"Clean up this OCR-extracted text. Fix obvious spelling errors and garbled words. Return only the cleaned text, nothing else:\n\n{text}",
                "stream": False
            },
            timeout=60
        )
        cleaned = response.json().get("response", text)
        print(f"LLM cleaned page text successfully")
        return cleaned
    except Exception as e:
        print(f"LLM cleanup failed, using raw OCR text: {e}")
        return text


def ingest_pdf(pdf_path: str, existing_store: FAISS = None) -> FAISS:
    """
    Load pdf, chunk it, embed it using HuggingFace
    and store in a FAISS vector database.
    Supports merging into an existing store for multi-PDF support.
    Auto-detects scanned PDFs and applies OCR + LLM cleanup if needed.
    """
    # Step 1: Try normal text extraction first
    loader = PyPDFLoader(pdf_path)
    document = loader.load()

    # Step 2: Check if we actually got real text
    total_text = " ".join([d.page_content for d in document]).strip()
    clean_text = total_text.replace("Scanned by CamScanner", "").strip()

    print(f"DEBUG: Clean text length = {len(clean_text)}")

    if len(clean_text) < 50:
        print("No real text detected — running OCR on scanned PDF...")
        images = convert_from_path(pdf_path, dpi=300)
        document = []

        for i, image in enumerate(images):
            print(f" Processing page {i + 1}/{len(images)}...")
            image = image.convert("L")
            image = ImageEnhance.Contrast(image).enhance(2.0)
            image = image.filter(ImageFilter.SHARPEN)

            raw_text = pytesseract.image_to_string(
                image,
                config="--psm 6 --oem 3"
            )

            if raw_text.strip():
                cleaned_text = clean_ocr_text(raw_text)
                document.append(Document(
                    page_content=cleaned_text,
                    metadata={"page": i + 1, "source": pdf_path}
                ))

        print(f"OCR + LLM cleanup complete — processed {len(document)} pages")

    # Step 3: Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunk = splitter.split_documents(document)

    # Step 4: Embed using HuggingFace
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Step 5: Build or merge into FAISS store
    new_store = FAISS.from_documents(chunk, embeddings)

    if existing_store is not None:
        existing_store.merge_from(new_store)
        vector_store = existing_store
    else:
        vector_store = new_store

    # Step 6: Persist to disk
    os.makedirs("data", exist_ok=True)
    vector_store.save_local(FAISS_INDEX_PATH)
    print(f"FAISS index saved to disk at {FAISS_INDEX_PATH}")

    return vector_store