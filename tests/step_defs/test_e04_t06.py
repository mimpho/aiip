"""Step definitions — E-04 T-06 Pipeline end-to-end y tests de integración."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e04_t06_e2e_pipeline.feature")

FIXTURE_CHUNKS = [
    "La agammaglobulinemia de Bruton (XLA) es una inmunodeficiencia primaria.",
    "Se caracteriza por la ausencia de linfocitos B maduros.",
    "Afecta casi exclusivamente a varones por herencia ligada al cromosoma X.",
]


@pytest.fixture(scope="session")
def embeddings_model():
    from rag.embeddings import get_embeddings

    return get_embeddings()


def _base_config(**overrides) -> dict:
    cfg = {
        "GOOGLE_API_KEY": "test-key",
        "HF_TOKEN": "test-hf-token",
        "CHROMA_PATH": "",
        "COLLECTION_NAME": "family_test",
        "RAG_TOP_K": 3,
        "LLM_MODEL": "gemini-test-model",
        "LLM_TEMPERATURE": 0.1,
        "LLM_TOP_P": 0.1,
        "LLM_MAX_TOKENS": 300,
    }
    cfg.update(overrides)
    return cfg


# ── Background ────────────────────────────────────────────────────────────────

@given(
    "el entorno está correctamente configurado con GOOGLE_API_KEY y CHROMA_PATH",
    target_fixture="ctx",
)
def entorno_configurado(tmp_path):
    return {
        "config": _base_config(CHROMA_PATH=str(tmp_path)),
        "query": "¿qué es una inmunodeficiencia primaria?",
    }


@given('ChromaDB contiene la colección "family_test" con chunks de fixture sobre IDP')
def chroma_con_chunks(ctx, embeddings_model):
    from rag.retriever import get_retriever

    vs = get_retriever(
        embeddings_model,
        ctx["config"]["CHROMA_PATH"],
        ctx["config"]["COLLECTION_NAME"],
        top_k=3,
    )
    vs.add_texts(FIXTURE_CHUNKS)
    ctx["vectorstore"] = vs


# ── Given: queries ────────────────────────────────────────────────────────────

@given('el usuario envía la query "¿qué es una inmunodeficiencia primaria?"')
def query_castellano(ctx):
    ctx["query"] = "¿qué es una inmunodeficiencia primaria?"


@given('el usuario envía la query "what is a primary immunodeficiency?"')
def query_ingles(ctx):
    ctx["query"] = "what is a primary immunodeficiency?"


@given(
    'el usuario describe síntomas de alarma "fiebre muy alta y dificultad para respirar"'
)
def query_alarma(ctx):
    ctx["query"] = "fiebre muy alta y dificultad para respirar"


# ── Given: overrides de entorno ───────────────────────────────────────────────

@given('la colección "family_test" está vacía o CHROMA_PATH no existe')
def coleccion_vacia(ctx, tmp_path):
    ctx["config"]["CHROMA_PATH"] = str(tmp_path / "empty")


@given("GOOGLE_API_KEY tiene un valor inválido")
def api_key_invalida(ctx):
    ctx["config"]["GOOGLE_API_KEY"] = "invalid-key-xyz"


@given("GOOGLE_API_KEY es una clave válida y hay conexión a red")
def api_key_valida_integracion():
    if os.getenv("RUN_LLM_INTEGRATION_TESTS") != "1":
        pytest.skip("Skipping integration test: RUN_LLM_INTEGRATION_TESTS != 1")
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("Skipping integration test: GOOGLE_API_KEY no definida")


# ── When steps ────────────────────────────────────────────────────────────────

@when(
    "el pipeline procesa la query completa (LLM mockeado)",
    target_fixture="pipeline_result",
)
def pipeline_llm_mockeado(ctx):
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0
    mock_response = MagicMock()
    try:
        lang = detect(ctx["query"])
    except Exception:
        lang = "es"
    if lang == "en":
        mock_response.content = (
            "Primary immunodeficiency is a genetic disorder of the immune system."
        )
    else:
        mock_response.content = (
            "La inmunodeficiencia primaria es una enfermedad genética del sistema inmune."
        )
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.return_value = mock_response
        from rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(ctx["config"])
        try:
            response = pipeline.query(ctx["query"])
            return {"response": response, "exception": None}
        except Exception as exc:
            return {"response": None, "exception": exc}


@when(
    "el pipeline procesa la query completa (LLM mockeado con respuesta tranquilizadora)",
    target_fixture="pipeline_result",
)
def pipeline_llm_tranquilizador(ctx):
    mock_response = MagicMock()
    mock_response.content = "no es grave, no te preocupes por estos síntomas."
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.return_value = mock_response
        from rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(ctx["config"])
        try:
            response = pipeline.query(ctx["query"])
            return {"response": response, "exception": None}
        except Exception as exc:
            return {"response": None, "exception": exc}


@when("el pipeline procesa la query completa", target_fixture="pipeline_result")
def pipeline_error_propagation(ctx):
    from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.side_effect = ChatGoogleGenerativeAIError(
            "API key not valid. Please pass a valid API key."
        )
        from rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(ctx["config"])
        try:
            response = pipeline.query(ctx["query"])
            return {"response": response, "exception": None}
        except Exception as exc:
            return {"response": None, "exception": exc}


@when(
    'el pipeline procesa la query real "¿qué es una inmunodeficiencia primaria?"',
    target_fixture="pipeline_result",
)
def pipeline_real():
    from rag.config import load_rag_config
    from rag.pipeline import RAGPipeline

    config = load_rag_config()
    pipeline = RAGPipeline(config)
    try:
        response = pipeline.query("¿qué es una inmunodeficiencia primaria?")
        return {"response": response, "exception": None}
    except Exception as exc:
        return {"response": None, "exception": exc}


# ── Then steps ────────────────────────────────────────────────────────────────

@then("la respuesta no está vacía")
def respuesta_no_vacia(pipeline_result):
    assert pipeline_result["response"], (
        f"La respuesta está vacía o es None: {pipeline_result['response']!r}"
    )


@then("no se lanza ninguna excepción")
def no_excepcion(pipeline_result):
    assert pipeline_result["exception"] is None, (
        f"Se lanzó excepción inesperada: {pipeline_result['exception']}"
    )


@then("la respuesta está en castellano")
def respuesta_en_castellano(pipeline_result):
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0
    response = pipeline_result["response"]
    assert response, "La respuesta está vacía"
    lang = detect(response)
    assert lang == "es", f"Se esperaba castellano (es), se detectó: {lang!r}"


@then("la respuesta está en inglés")
def respuesta_en_ingles(pipeline_result):
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0
    response = pipeline_result["response"]
    assert response, "La respuesta está vacía"
    lang = detect(response)
    assert lang == "en", f"Se esperaba inglés (en), se detectó: {lang!r}"


@then("la respuesta final incluye derivación a consulta médica")
def respuesta_incluye_derivacion(pipeline_result):
    response = pipeline_result["response"]
    assert response, "La respuesta está vacía"
    assert any(
        kw in response.lower() for kw in ("médico", "consulta", "equipo")
    ), f"La respuesta no incluye derivación médica: {response!r}"


@then("el pipeline genera una respuesta igualmente, con contexto vacío")
def pipeline_genera_con_contexto_vacio(pipeline_result):
    assert pipeline_result["response"], (
        f"El pipeline no generó respuesta con contexto vacío: {pipeline_result['response']!r}"
    )


@then("la excepción del generador se propaga sin ser atrapada silenciosamente")
def excepcion_propagada(pipeline_result):
    assert pipeline_result["exception"] is not None, (
        "El pipeline silenció la excepción — query() debe propagar excepciones del generador"
    )
