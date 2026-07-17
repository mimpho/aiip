from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# D-057 (E-09 T-05, hallazgo D): pesos de partida para la fusión RRF entre BM25 y
# búsqueda vectorial — a ajustar contra Context Precision/Recall en la re-medición,
# no es un valor cerrado.
_BM25_WEIGHT = 0.4
_VECTOR_WEIGHT = 0.6


def get_retriever(
    embeddings: Embeddings,
    chroma_path: str,
    collection_name: str,
    top_k: int = 5,
) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=chroma_path,
        collection_metadata={"hnsw:space": "cosine"},
    )


def get_hybrid_retriever(vectorstore: Chroma, top_k: int = 5) -> EnsembleRetriever:
    """Ensambla un retriever léxico (BM25) con el vectorial ya indexado en Chroma.

    D-057: el Search()/hybrid search nativo de Chroma es exclusivo de Chroma Cloud
    (docs.trychroma.com/cloud/search-api/overview); el proyecto usa Chroma local
    persistente, así que la fusión se hace en LangChain vía EnsembleRetriever (RRF)
    en vez de delegarla al vectorstore.
    """
    stored = vectorstore.get(include=["documents", "metadatas"])
    documents = [
        Document(page_content=doc, metadata=metadata or {})
        for doc, metadata in zip(stored["documents"], stored["metadatas"])
    ]

    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    if not documents:
        return EnsembleRetriever(
            retrievers=[vector_retriever], weights=[1.0]
        )

    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = top_k

    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[_BM25_WEIGHT, _VECTOR_WEIGHT],
    )


def distance_to_similarity(distance: float) -> float:
    return 1.0 - distance
