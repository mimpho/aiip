from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings


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


def distance_to_similarity(distance: float) -> float:
    return 1.0 - distance
