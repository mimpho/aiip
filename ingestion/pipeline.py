"""Pipeline de ingesta end-to-end: loader -> chunker -> indexer (E-06 T-05)."""

import warnings
from collections import defaultdict

from ingestion.chunker import chunk_documents
from ingestion.indexer import delete_document_chunks, index_chunks
from ingestion.loader import load_documents


def run_ingestion_pipeline(
    source_path, chroma_path, embeddings, collection_name="family", profile="family"
):
    """Ejecuta loader -> chunker -> indexer sobre todas las fuentes de `source_path`.

    Reprocesamiento completo (D-024): en cada ejecución se borran los chunks ya
    indexados de cada documento antes de reinsertar sus chunks nuevos, así el
    número de chunks de un documento puede cambiar entre ejecuciones sin dejar
    huérfanos. El aislamiento de fallos por fuente vive en `ingestion.loader`
    (un fichero que no carga se omite con un aviso); aquí solo se recogen esos
    avisos para el resumen final, sin que detengan el resto del procesamiento.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        documents = load_documents(source_path)

    failures = [
        str(w.message)
        for w in caught
        if "fallo al cargar el fichero" in str(w.message).lower()
    ]

    chunks = chunk_documents(documents, profile=profile)

    chunks_by_document = defaultdict(list)
    for chunk in chunks:
        key = (chunk.metadata["source"], chunk.metadata["filename"])
        chunks_by_document[key].append(chunk)

    indexed_ids = {}
    for (source, filename), document_chunks in chunks_by_document.items():
        delete_document_chunks(source, filename, embeddings, chroma_path, collection_name)
        indexed_ids[(source, filename)] = index_chunks(
            document_chunks, embeddings, chroma_path, collection_name
        )

    return {"indexed": indexed_ids, "failures": failures}
