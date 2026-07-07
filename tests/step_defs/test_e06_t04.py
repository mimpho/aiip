"""Step definitions — E-06 T-04 Indexer: indexación en ChromaDB."""

import sys
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e06_t04_chromadb_indexer.feature")


class _DummyEmbeddings(Embeddings):
    """Embeddings deterministas y rápidas: el indexer no valida calidad semántica."""

    def embed_documents(self, texts):
        return [[float(len(text) % 7 + 1)] * 4 for text in texts]

    def embed_query(self, text):
        return [float(len(text) % 7 + 1)] * 4


def _make_chunks(source: str, filename: str, count: int) -> list[Document]:
    return [
        Document(
            page_content=f"Contenido del chunk {i} de {filename}.",
            metadata={
                "source": source,
                "filename": filename,
                "language": "es",
                "date_indexed": "2026-07-07",
                "profile": "family",
            },
        )
        for i in range(count)
    ]


# ── Background ───────────────────────────────────────────────────────────────

@given(
    'ChromaDB está inicializado con la colección "family_test" y métrica coseno',
    target_fixture="ctx",
)
def chroma_inicializado(tmp_path):
    return {
        "chroma_path": str(tmp_path),
        "collection_name": "family_test",
        "embeddings": _DummyEmbeddings(),
    }


# ── Scenario 1: Indexación de chunks con embeddings bge-m3 ─────────────────────

@given("un conjunto de chunks con su embedding bge-m3 ya calculado", target_fixture="ctx")
def chunks_con_embedding(ctx):
    ctx["chunks"] = _make_chunks("ipopi", "doc.html", 3)
    return ctx


# ── Scenario 2: Reindexación del mismo documento no duplica chunks ──────────────

@given("un documento ya indexado previamente en la colección", target_fixture="ctx")
def documento_ya_indexado(ctx):
    from ingestion.indexer import index_chunks

    ctx["chunks"] = _make_chunks("ipopi", "reindexado.html", 3)
    index_chunks(ctx["chunks"], ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    return ctx


@when(
    "se ejecuta el indexer de nuevo sobre el mismo documento",
    target_fixture="resultado",
)
def ejecuta_indexer_de_nuevo(ctx):
    from ingestion.indexer import index_chunks

    ids = index_chunks(ctx["chunks"], ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    return {"ids": ids, "exception": None}


@then("el número total de chunks de ese documento en la colección no aumenta")
def chunks_no_aumentan(ctx):
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get(
        where={
            "$and": [
                {"source": ctx["chunks"][0].metadata["source"]},
                {"filename": ctx["chunks"][0].metadata["filename"]},
            ]
        }
    )
    assert len(stored["ids"]) == len(ctx["chunks"])


# ── Scenario 3: El ID de cada chunk es determinista, no aleatorio ──────────────

@given(
    "los mismos chunks de un documento (source, filename e índice de chunk sin cambios)",
    target_fixture="ctx",
)
def mismos_chunks_documento(ctx):
    ctx["chunks"] = _make_chunks("upiip", "determinista.html", 2)
    return ctx


@when("se ejecuta el indexer en dos ejecuciones distintas", target_fixture="resultado")
def ejecuta_dos_veces(ctx):
    from ingestion.indexer import index_chunks

    ids_primera = index_chunks(
        ctx["chunks"], ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"]
    )
    ids_segunda = index_chunks(
        ctx["chunks"], ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"]
    )
    return {"ids_primera": ids_primera, "ids_segunda": ids_segunda}


@then("el ID asignado a cada chunk es idéntico en ambas ejecuciones")
def ids_identicos(resultado):
    assert resultado["ids_primera"] == resultado["ids_segunda"]
    assert len(resultado["ids_primera"]) == 2


# ── Scenario 4: Fallo de escritura en ChromaDB se propaga con contexto ──────────

@given("una escritura en ChromaDB que falla durante la indexación", target_fixture="ctx")
def escritura_falla(ctx, monkeypatch):
    from langchain_chroma import Chroma

    def _add_documents_falla(self, documents, ids=None, **kwargs):
        raise RuntimeError("fallo simulado de escritura en ChromaDB")

    monkeypatch.setattr(Chroma, "add_documents", _add_documents_falla)
    ctx["chunks"] = _make_chunks("ipopi", "falla.html", 2)
    return ctx


@then("el error se propaga indicando qué documento y qué chunk fallaron")
def error_propagado_con_contexto(resultado):
    assert resultado["exception"] is not None
    message = str(resultado["exception"])
    assert "ipopi" in message
    assert "falla.html" in message
    assert "0" in message


# ── When / Then compartidos (escenarios 1 y 4) ──────────────────────────────────

@when("se ejecuta el indexer", target_fixture="resultado")
def ejecuta_indexer(ctx):
    from ingestion.indexer import index_chunks

    try:
        ids = index_chunks(
            ctx["chunks"], ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"]
        )
        return {"ids": ids, "exception": None}
    except Exception as exc:
        return {"ids": None, "exception": exc}


@then('los chunks quedan persistidos en la colección "family_test"')
def chunks_persistidos(ctx, resultado):
    assert resultado["exception"] is None, resultado["exception"]
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get()
    assert len(stored["ids"]) == len(ctx["chunks"])


@then("cada chunk indexado conserva sus metadatos de origen")
def chunk_conserva_metadatos(ctx, resultado):
    assert resultado["exception"] is None, resultado["exception"]
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get()
    original_metadatas = {
        (chunk.metadata["source"], chunk.metadata["filename"]): chunk.metadata
        for chunk in ctx["chunks"]
    }
    assert stored["metadatas"]
    for metadata in stored["metadatas"]:
        expected = original_metadatas[(metadata["source"], metadata["filename"])]
        assert metadata == expected
