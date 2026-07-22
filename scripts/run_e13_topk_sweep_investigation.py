"""Investigación puntual: ¿ayuda subir RAG_TOP_K a que las fichas de MedlinePlus
Genetics (E-13, en inglés) aparezcan en preguntas en español de tipo "listado"?

Contexto: simulación de BM25 real (rank_bm25, misma librería de producción)
contra los 1324 chunks indexados mostró que medlineplus_genetics aparece 0
veces incluso en el top-50 BM25 para "dame un listado de las IDPs..." — la
parte vectorial (bge-m3) es la única vía posible, y no se puede probar sin red
desde Cowork. Este script solo usa embeddings (sin Gemini) para que sea barato
y rápido de repetir.

No cambia RAG_TOP_K en producción — solo instancia retrievers con distintos
valores para comparar, en memoria, sin tocar .env ni rag/config.py.

Uso:
    PYTHONPATH=. python scripts/run_e13_topk_sweep_investigation.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import load_rag_config
from rag.embeddings import get_embeddings
from rag.retriever import apply_adaptive_bm25_weight, get_hybrid_retriever, get_retriever

_COLLECTION_NAME = "family"

QUERIES = [
    ("Listado amplio (el caso que motivó la investigación)",
     "dame un listado de las IDPs con una frase explicativa de cada una de ellas"),
    ("Pregunta de una sola enfermedad (control — no debería empeorar)",
     "¿qué es el síndrome de Wiskott-Aldrich?"),
    ("Pregunta de una sola enfermedad nueva de E-13 (control)",
     "¿qué es el síndrome de Chediak-Higashi?"),
]


def main():
    rag_config = load_rag_config()
    embeddings = get_embeddings()
    vectorstore = get_retriever(embeddings, rag_config["CHROMA_PATH"], _COLLECTION_NAME)

    # Construye el índice BM25 (la parte cara: tokeniza los 1324 chunks) una
    # sola vez, con el top_k más alto del barrido. Para cada valor de top_k
    # más bajo, solo se mutan los límites (bm25_retriever.k y
    # search_kwargs["k"] del vectorial) en vez de reconstruir el índice desde
    # cero — mismo patrón que apply_adaptive_bm25_weight() ya usa para pesos
    # (D-061: mutar la instancia cacheada, no reconstruir).
    max_top_k = 30
    retriever = get_hybrid_retriever(vectorstore, top_k=max_top_k)
    bm25_retriever, vector_retriever = retriever.retrievers

    for label, query in QUERIES:
        print(f"=== {label!r} ===")
        print(f"Query: {query!r}")
        apply_adaptive_bm25_weight(retriever, query)
        for top_k in [5, 10, 15, 20, 30]:
            bm25_retriever.k = top_k
            vector_retriever.search_kwargs["k"] = top_k
            docs = retriever.invoke(query)
            sources = Counter(d.metadata.get("source", "?") for d in docs)
            mp = sources.get("medlineplus_genetics", 0)
            print(
                f"  top_k={top_k:2d} -> {len(docs):2d} chunks totales, "
                f"{mp} de medlineplus_genetics -- {dict(sources)}"
            )
        print()


if __name__ == "__main__":
    main()
