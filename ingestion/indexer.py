"""Indexer: escritura de chunks en ChromaDB (E-06 T-04)."""

import hashlib

from rag.retriever import get_retriever


def _chunk_id(chunk, index: int) -> str:
    """ID determinista a partir de source + filename + índice del chunk."""
    source = chunk.metadata["source"]
    filename = chunk.metadata["filename"]
    digest = hashlib.sha256(f"{source}/{filename}/{index}".encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def index_chunks(chunks, embeddings, chroma_path, collection_name="family"):
    """Indexa `chunks` en la colección `collection_name` de ChromaDB.

    Abre el vectorstore vía `get_retriever` (métrica coseno, D-016) y escribe
    cada chunk con un ID determinista, de forma que reindexar el mismo
    documento hace upsert en vez de duplicar (Chroma upsertea por ID).
    Escribe chunk a chunk para poder señalar con precisión, si falla la
    escritura, qué documento y qué índice de chunk estaba escribiendo.
    """
    vectorstore = get_retriever(embeddings, chroma_path, collection_name)

    ids = []
    for index, chunk in enumerate(chunks):
        chunk_id = _chunk_id(chunk, index)
        try:
            vectorstore.add_documents([chunk], ids=[chunk_id])
        except Exception as exc:
            source = chunk.metadata.get("source")
            filename = chunk.metadata.get("filename")
            raise RuntimeError(
                f"Fallo al indexar el chunk {index} de {source}/{filename}: {exc}"
            ) from exc
        ids.append(chunk_id)

    return ids


def delete_document_chunks(source, filename, embeddings, chroma_path, collection_name="family"):
    """Borra de la colección los chunks ya indexados de un documento (source, filename).

    Se ejecuta antes de reindexar el documento (D-024, reprocesamiento completo)
    para que, si el número de chunks cambia entre ejecuciones, no queden
    huérfanos los IDs que ya no genera el chunking actual.
    """
    vectorstore = get_retriever(embeddings, chroma_path, collection_name)
    existing = vectorstore.get(
        where={"$and": [{"source": source}, {"filename": filename}]}
    )
    ids = existing["ids"]
    if ids:
        vectorstore.delete(ids=ids)
    return ids
