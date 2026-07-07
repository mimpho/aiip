"""Step definitions — E-06 T-08 Citación de fuentes con URL original."""

import json
import sys
from pathlib import Path

from langchain_core.documents import Document
from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e06_t08_source_url_citation.feature")


def _write_manifest(root: Path, documents: dict) -> None:
    (root / "manifest.json").write_text(
        json.dumps({"documents": documents}, ensure_ascii=False), encoding="utf-8"
    )


# ── Escenarios 1 y 2: loader ─────────────────────────────────────────────────

@given(
    'un documento cargado desde una fuente con "url" documentada en el manifest',
    target_fixture="ctx",
)
def documento_con_url_en_manifest(tmp_path):
    root = tmp_path / "raw"
    source_dir = root / "ipopi"
    source_dir.mkdir(parents=True)
    (source_dir / "doc.html").write_text(
        "<html><body><p>Contenido de prueba.</p></body></html>", encoding="utf-8"
    )
    _write_manifest(
        root,
        {
            "ipopi/doc.html": {
                "checksum": "sha256:" + "0" * 64,
                "url": "https://example.org/ipopi",
                "fecha": "2025-01-01",
            }
        },
    )
    return {"source_path": str(root), "expected_url": "https://example.org/ipopi"}


@given(
    'un documento cargado desde una fuente sin "url" documentada en el manifest',
    target_fixture="ctx",
)
def documento_sin_url_en_manifest(tmp_path):
    root = tmp_path / "raw"
    source_dir = root / "ipopi"
    source_dir.mkdir(parents=True)
    (source_dir / "doc.html").write_text(
        "<html><body><p>Contenido nuevo.</p></body></html>", encoding="utf-8"
    )
    _write_manifest(root, {})
    return {"source_path": str(root), "expected_url": None}


@when("se ejecuta el loader", target_fixture="load_result")
def ejecuta_loader(ctx):
    from ingestion.loader import load_documents

    documents = load_documents(ctx["source_path"])
    return {"documents": documents}


@then('el metadato "url" del documento coincide con el valor del manifest')
def url_coincide_con_manifest(load_result, ctx):
    docs = load_result["documents"]
    assert docs
    for doc in docs:
        assert doc.metadata["url"] == ctx["expected_url"]


@then('el metadato "url" del documento es None')
def url_es_none(load_result):
    docs = load_result["documents"]
    assert docs
    for doc in docs:
        assert doc.metadata["url"] is None


# ── Escenario 3: chunker ──────────────────────────────────────────────────────

@given(
    'un documento cargado con el metadato "url" ya asignado',
    target_fixture="ctx",
)
def documento_con_url_asignado():
    return {
        "documents": [
            Document(
                page_content="Texto de prueba con url ya asignada.",
                metadata={"source": "ipopi", "filename": "doc.html", "url": "https://ejemplo.org/doc"},
            )
        ]
    }


@when("se aplica el chunker", target_fixture="chunks")
def aplica_chunker(ctx):
    from ingestion.chunker import chunk_documents

    return chunk_documents(ctx["documents"])


@then('cada chunk resultante conserva el metadato "url" del documento')
def chunks_conservan_url(chunks, ctx):
    original_url = ctx["documents"][0].metadata["url"]
    assert chunks
    for chunk in chunks:
        assert chunk.metadata["url"] == original_url


# ── Escenarios 4 y 5: sección de fuentes ─────────────────────────────────────

@given(
    'chunks recuperados cuyo metadata incluye "url"',
    target_fixture="ctx",
)
def chunks_con_url():
    raw_results = [
        (
            Document(
                page_content="contenido",
                metadata={"source": "ipopi", "filename": "doc.html", "url": "https://ejemplo.org/doc"},
            ),
            0.1,
        )
    ]
    return {"raw_results": raw_results, "expected_url": "https://ejemplo.org/doc", "filename": "doc.html"}


@given(
    'chunks recuperados cuyo metadata no incluye "url"',
    target_fixture="ctx",
)
def chunks_sin_url():
    raw_results = [
        (
            Document(
                page_content="contenido",
                metadata={"source": "ipopi", "filename": "doc.html"},
            ),
            0.1,
        )
    ]
    return {"raw_results": raw_results, "source": "ipopi", "filename": "doc.html"}


@when("se construye la sección de fuentes", target_fixture="sources_section")
def construye_seccion_fuentes(ctx):
    from rag.pipeline import _build_sources_section

    return _build_sources_section(ctx["raw_results"], "es")


@then("la sección de fuentes incluye un enlace markdown a esa URL")
def seccion_incluye_enlace_markdown(sources_section, ctx):
    assert f"[{ctx['filename']}]({ctx['expected_url']})" in sources_section


@then('la sección de fuentes muestra "source/filename" sin enlace')
def seccion_muestra_source_filename_sin_enlace(sources_section, ctx):
    assert f"- {ctx['source']}/{ctx['filename']}" in sources_section
    assert "[" not in sources_section
    assert "(" not in sources_section
