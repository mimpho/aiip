"""Chunker multiidioma de documentos cargados (E-06 T-03)."""

import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

from ingestion.config import load_ingestion_config
from rag.language import detect_language


def chunk_documents(documents, profile="familiar"):
    """Divide los documentos cargados en chunks para su indexación.

    Detecta el idioma una vez por documento (no por chunk) y lo propaga junto con
    `date_indexed` y `profile` a los metadatos de cada chunk resultante.
    """
    config = load_ingestion_config()
    tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")
    splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer,
        chunk_size=config["RAG_CHUNK_SIZE"],
        chunk_overlap=config["RAG_CHUNK_OVERLAP"],
        separators=["\n\n", "\n", ". ", " "],
    )

    date_indexed = datetime.date.today().isoformat()
    chunks = []
    for document in documents:
        language = detect_language(document.page_content)
        document_chunks = splitter.split_documents([document])
        for chunk in document_chunks:
            chunk.metadata["language"] = language
            chunk.metadata["date_indexed"] = date_indexed
            chunk.metadata["profile"] = profile
        chunks.extend(document_chunks)
    return chunks
