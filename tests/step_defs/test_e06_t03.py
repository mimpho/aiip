"""Step definitions — E-06 T-03 Chunking multiidioma."""

import sys
from datetime import date
from pathlib import Path

from langchain_core.documents import Document
from pytest_bdd import given, scenarios, then, when
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e06_t03_chunking_strategy.feature")

_TOKENIZER = AutoTokenizer.from_pretrained("BAAI/bge-m3")


def _token_count(text: str) -> int:
    return len(_TOKENIZER.encode(text, add_special_tokens=False))


def _long_text(paragraph: str, min_tokens: int) -> str:
    """Repite `paragraph` (separado por dobles saltos de línea) hasta superar `min_tokens`."""
    parts = [paragraph]
    while _token_count("\n\n".join(parts)) <= min_tokens:
        parts.append(paragraph)
    return "\n\n".join(parts)


# ── Given ─────────────────────────────────────────────────────────────────────

@given(
    "un documento cargado con más de 512 tokens de texto",
    target_fixture="ctx",
)
def documento_largo():
    text = _long_text(
        "This is a long English paragraph used to exceed the chunk size threshold. "
        "It repeats several times so the tokenizer counts well over five hundred "
        "twelve tokens once concatenated with its siblings.",
        512,
    )
    return {"documents": [Document(page_content=text, metadata={})]}


@given(
    'un documento cargado con metadatos de origen "source" y "filename"',
    target_fixture="ctx",
)
def documento_con_metadatos_origen():
    return {
        "documents": [
            Document(
                page_content="Texto de prueba con metadatos de origen.",
                metadata={"source": "ipopi", "filename": "doc.html"},
            )
        ]
    }


@given(
    "un documento cargado con menos de 512 tokens de texto",
    target_fixture="ctx",
)
def documento_corto():
    text = "Este es un documento corto que no supera el tamaño de chunk configurado."
    assert _token_count(text) < 512
    return {"documents": [Document(page_content=text, metadata={})], "expected_text": text}


@given(
    "un documento en español cargado desde una fuente no inglesa",
    target_fixture="ctx",
)
def documento_en_espanol():
    text = (
        "Este documento está escrito enteramente en español y describe el "
        "seguimiento clínico habitual de las inmunodeficiencias primarias."
    )
    return {
        "documents": [
            Document(page_content=text, metadata={"source": "upiip", "filename": "doc.html"})
        ],
        "original_text": text,
    }


@given(
    "un documento largo en inglés que se divide en varios chunks",
    target_fixture="ctx",
)
def documento_largo_en_ingles():
    text = _long_text(
        "This is a long English paragraph used to exceed the chunk size threshold. "
        "It repeats several times so the tokenizer counts well over five hundred "
        "twelve tokens once concatenated with its siblings.",
        512,
    )
    return {"documents": [Document(page_content=text, metadata={})]}


# ── When ──────────────────────────────────────────────────────────────────────

@when("se aplica el chunker", target_fixture="chunks")
def aplica_chunker(ctx):
    from ingestion.chunker import chunk_documents

    return chunk_documents(ctx["documents"])


# ── Then ──────────────────────────────────────────────────────────────────────

@then("cada chunk generado tiene un tamaño aproximado de 512 tokens")
def chunk_tamano_aproximado(chunks):
    assert len(chunks) >= 2
    for chunk in chunks[:-1]:
        assert _token_count(chunk.page_content) <= 512


@then("el solapamiento entre chunks consecutivos está entre el 10% y el 20%")
def solapamiento_entre_10_y_20_pct(chunks):
    assert len(chunks) >= 2
    for previous, current in zip(chunks, chunks[1:]):
        prev_tail = previous.page_content[-400:]
        curr_head = current.page_content[:400]
        overlap_found = False
        for length in range(min(len(prev_tail), len(curr_head)), 0, -1):
            if prev_tail[-length:] == curr_head[:length]:
                overlap_tokens = _token_count(prev_tail[-length:])
                ratio = overlap_tokens / 512
                assert 0.05 <= ratio <= 0.25, f"ratio de solapamiento fuera de rango: {ratio}"
                overlap_found = True
                break
        assert overlap_found, "no se encontró solapamiento entre chunks consecutivos"


@then('cada chunk conserva los metadatos "source" y "filename"')
def chunk_conserva_metadatos_origen(chunks, ctx):
    original = ctx["documents"][0].metadata
    assert chunks
    for chunk in chunks:
        assert chunk.metadata["source"] == original["source"]
        assert chunk.metadata["filename"] == original["filename"]


@then('cada chunk incluye los metadatos generados "language", "date_indexed" y "profile"')
def chunk_incluye_metadatos_generados(chunks):
    assert chunks
    for chunk in chunks:
        assert "language" in chunk.metadata
        assert chunk.metadata["date_indexed"] == date.today().isoformat()
        assert chunk.metadata["profile"] == "familiar"


@then("se genera un único chunk con el contenido completo del documento")
def unico_chunk_contenido_completo(chunks, ctx):
    assert len(chunks) == 1
    assert chunks[0].page_content == ctx["expected_text"]


@then('el metadato "language" de cada chunk refleja el español')
def metadato_language_espanol(chunks):
    assert chunks
    for chunk in chunks:
        assert chunk.metadata["language"] == "es"


@then("el texto del chunk no se traduce al inglés")
def texto_no_traducido(chunks, ctx):
    full_text = "".join(chunk.page_content for chunk in chunks)
    assert ctx["original_text"] in full_text or full_text in ctx["original_text"]


@then("todos los chunks resultantes de ese documento comparten el mismo metadato \"language\"")
def chunks_comparten_language(chunks):
    assert len(chunks) >= 2
    languages = {chunk.metadata["language"] for chunk in chunks}
    assert len(languages) == 1
