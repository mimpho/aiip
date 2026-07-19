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

# D-061 (E-11 T-02): peso adaptativo por consulta. Con señal léxica fuerte se
# mantiene el peso uniforme de D-057 (validado en E-09 T-05); sin señal, BM25 se
# reduce casi a cero pero no a 0.0 exacto — EnsembleRetriever exige
# any(w > 0 for w in weights) en la validación de construcción, y aunque el peso se
# reasigna por mutación (no reconstrucción), 0.05 evita depender de que ese
# comportamiento no cambie.
_SIGNAL_BM25_WEIGHT = 0.4
_SIGNAL_VECTOR_WEIGHT = 0.6
_NO_SIGNAL_BM25_WEIGHT = 0.05
_NO_SIGNAL_VECTOR_WEIGHT = 0.95


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


def has_lexical_signal(query: str, bm25_retriever: BM25Retriever) -> bool:
    """Determina si `query` tiene señal léxica fuerte (D-061), de forma determinista.

    Dos criterios, cualquiera activa la señal:
    (a) una palabra con mayúscula que no es la primera palabra de la pregunta
        (aproximación a nombre propio, sin lista de topónimos que mantener).
    (b) una palabra de baja frecuencia en el corpus indexado: IDF (ya calculado por
        `BM25Okapi` en `bm25_retriever.vectorizer`) por encima de la media del
        corpus (`average_idf`). Se tokeniza con el mismo `preprocess_func` del
        `bm25_retriever` para que las claves de búsqueda en `idf` coincidan con
        las indexadas (D-061, punto 2 del contexto técnico).
    """
    words = query.split()
    if any(word[0].isupper() for word in words[1:] if word):
        return True

    idf = bm25_retriever.vectorizer.idf
    average_idf = bm25_retriever.vectorizer.average_idf
    tokens = bm25_retriever.preprocess_func(query)
    return any(idf.get(token, 0.0) > average_idf for token in tokens)


def apply_adaptive_bm25_weight(retriever: EnsembleRetriever, query: str) -> None:
    """Ajusta `retriever.weights` para `query` antes de invocar el retriever (D-061).

    Muta el atributo `weights` de la instancia ya construida/cacheada — no
    reconstruye `retriever.retrievers` ni el índice BM25, que es la parte cara.
    Si el retriever no tiene BM25 (fallback de `get_hybrid_retriever` cuando el
    vectorstore está vacío, un único retriever vectorial), no hace nada.
    """
    if len(retriever.retrievers) < 2:
        return

    bm25_retriever = retriever.retrievers[0]
    if has_lexical_signal(query, bm25_retriever):
        retriever.weights = [_SIGNAL_BM25_WEIGHT, _SIGNAL_VECTOR_WEIGHT]
    else:
        retriever.weights = [_NO_SIGNAL_BM25_WEIGHT, _NO_SIGNAL_VECTOR_WEIGHT]


def distance_to_similarity(distance: float) -> float:
    return 1.0 - distance
