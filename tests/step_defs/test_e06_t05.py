"""Step definitions — E-06 T-05 Pipeline de ingesta end-to-end."""

import sys
from pathlib import Path

from langchain_core.embeddings import Embeddings
from pytest_bdd import given, scenarios, then, when
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e06_t05_e2e_ingestion_pipeline.feature")

_TOKENIZER = AutoTokenizer.from_pretrained("BAAI/bge-m3")


def _token_count(text: str) -> int:
    return len(_TOKENIZER.encode(text, add_special_tokens=False))


def _long_text(paragraph: str, min_tokens: int) -> str:
    """Repite `paragraph` (separado por dobles saltos de línea) hasta superar `min_tokens`."""
    parts = [paragraph]
    while _token_count("\n\n".join(parts)) <= min_tokens:
        parts.append(paragraph)
    return "\n\n".join(parts)


class _DummyEmbeddings(Embeddings):
    """Embeddings deterministas y rápidas: el pipeline no valida calidad semántica."""

    def embed_documents(self, texts):
        return [[float(len(text) % 7 + 1)] * 4 for text in texts]

    def embed_query(self, text):
        return [float(len(text) % 7 + 1)] * 4


def _write_html(path: Path, text: str) -> None:
    path.write_text(
        f"<html><body><p>{text}</p></body></html>", encoding="utf-8"
    )


# ── Background ───────────────────────────────────────────────────────────────

@given(
    "data/raw/ contiene fuentes de fixture organizadas por carpeta",
    target_fixture="ctx",
)
def fuentes_de_fixture(tmp_path):
    root = tmp_path / "raw"
    root.mkdir()

    ipopi_dir = root / "ipopi"
    ipopi_dir.mkdir()
    _write_html(ipopi_dir / "doc.html", "Contenido de prueba de la fuente ipopi.")

    upiip_dir = root / "upiip"
    upiip_dir.mkdir()
    _write_html(upiip_dir / "doc.html", "Contenido de ejemplo de la fuente upiip.")

    return {
        "root": root,
        "source_path": str(root),
        "chroma_path": str(tmp_path / "chroma"),
        "collection_name": "family_test",
        "embeddings": _DummyEmbeddings(),
        "source_names": ["ipopi", "upiip"],
    }


# ── Scenario 1: Ejecución completa puebla la colección family ──────────────────

@when("se ejecuta el pipeline de ingesta completo", target_fixture="resultado")
def ejecuta_pipeline_completo(ctx):
    from ingestion.pipeline import run_ingestion_pipeline

    return run_ingestion_pipeline(
        ctx["source_path"], ctx["chroma_path"], ctx["embeddings"], ctx["collection_name"]
    )


@then('la colección "family_test" queda poblada con chunks')
def coleccion_poblada_con_chunks(ctx):
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get()
    assert len(stored["ids"]) > 0


@then("cada chunk es trazable a su fichero de origen y a su idioma")
def chunk_trazable_origen_idioma(ctx):
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get()
    assert stored["metadatas"]
    for metadata in stored["metadatas"]:
        assert metadata["source"]
        assert metadata["filename"]
        assert metadata["language"]


# ── Scenario 2: Ejecución repetida no duplica chunks ────────────────────────────

@given(
    "el pipeline de ingesta ya se ejecutó una vez sobre las fuentes de fixture",
    target_fixture="ctx",
)
def pipeline_ya_ejecutado_una_vez(ctx):
    from ingestion.pipeline import run_ingestion_pipeline
    from rag.retriever import get_retriever

    run_ingestion_pipeline(
        ctx["source_path"], ctx["chroma_path"], ctx["embeddings"], ctx["collection_name"]
    )
    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    ctx["total_antes"] = len(vs.get()["ids"])
    return ctx


@when(
    "se ejecuta el pipeline de ingesta una segunda vez sobre las mismas fuentes",
    target_fixture="resultado",
)
def ejecuta_pipeline_segunda_vez(ctx):
    from ingestion.pipeline import run_ingestion_pipeline

    return run_ingestion_pipeline(
        ctx["source_path"], ctx["chroma_path"], ctx["embeddings"], ctx["collection_name"]
    )


@then("el número total de chunks indexados no aumenta")
def numero_total_no_aumenta(ctx):
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    total_despues = len(vs.get()["ids"])
    assert total_despues == ctx["total_antes"]


# ── Scenario 3: Documento que cambia de número de chunks no deja huérfanos ─────

@given(
    "un documento ya indexado con un número de chunks determinado",
    target_fixture="ctx",
)
def documento_ya_indexado_con_n_chunks(ctx):
    from ingestion.pipeline import run_ingestion_pipeline
    from rag.retriever import get_retriever

    largo_path = ctx["root"] / "ipopi" / "largo.html"
    texto_largo = _long_text(
        "Este es un párrafo largo en español que se repite varias veces para "
        "superar con holgura el tamaño de chunk configurado en la ingesta.",
        520,
    )
    _write_html(largo_path, texto_largo)

    run_ingestion_pipeline(
        ctx["source_path"], ctx["chroma_path"], ctx["embeddings"], ctx["collection_name"]
    )

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get(
        where={"$and": [{"source": "ipopi"}, {"filename": "largo.html"}]}
    )
    ctx["chunks_antes"] = len(stored["ids"])
    assert ctx["chunks_antes"] >= 2
    ctx["largo_path"] = largo_path
    return ctx


@when("el documento cambia de contenido y genera menos chunks tras el chunking")
def documento_cambia_menos_chunks(ctx):
    _write_html(ctx["largo_path"], "Contenido corto tras la actualización del documento.")


@when("se ejecuta el pipeline de ingesta de nuevo", target_fixture="resultado")
def ejecuta_pipeline_de_nuevo(ctx):
    from ingestion.pipeline import run_ingestion_pipeline

    return run_ingestion_pipeline(
        ctx["source_path"], ctx["chroma_path"], ctx["embeddings"], ctx["collection_name"]
    )


@then("el número de chunks de ese documento en la colección coincide con el nuevo número")
def chunks_documento_coincide_nuevo_numero(ctx):
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get(
        where={"$and": [{"source": "ipopi"}, {"filename": "largo.html"}]}
    )
    ctx["chunks_despues"] = len(stored["ids"])
    assert ctx["chunks_despues"] == 1
    assert ctx["chunks_despues"] < ctx["chunks_antes"]


@then("no quedan chunks huérfanos de la versión anterior del documento")
def no_quedan_chunks_huerfanos(ctx):
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get(
        where={"$and": [{"source": "ipopi"}, {"filename": "largo.html"}]}
    )
    assert len(stored["ids"]) == ctx["chunks_despues"]


# ── Scenario 4: Fallo en una fuente no detiene el procesamiento de las demás ───

@given("una de las fuentes de fixture está corrupta o no se puede leer")
def fuente_corrupta(ctx):
    corrupta_dir = ctx["root"] / "corrupta"
    corrupta_dir.mkdir()
    (corrupta_dir / "roto.pdf").write_bytes(b"esto no es un PDF valido")
    ctx["corrupt_source"] = "corrupta"
    ctx["corrupt_file"] = "roto.pdf"


@then("las fuentes restantes se procesan e indexan igualmente")
def fuentes_restantes_procesadas(ctx):
    from rag.retriever import get_retriever

    vs = get_retriever(ctx["embeddings"], ctx["chroma_path"], ctx["collection_name"])
    stored = vs.get()
    sources_indexados = {metadata["source"] for metadata in stored["metadatas"]}
    for source_name in ctx["source_names"]:
        assert source_name in sources_indexados


@then("el fallo de la fuente corrupta queda registrado en el resumen final de la ejecución")
def fallo_registrado_en_resumen(ctx, resultado):
    assert resultado["failures"]
    assert any(
        ctx["corrupt_source"] in failure and ctx["corrupt_file"] in failure
        for failure in resultado["failures"]
    )
