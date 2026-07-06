"""Step definitions — E-04 T-04 Generador LLM Gemini Flash."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e04_t04_llm_generator.feature")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _base_config(**overrides) -> dict:
    cfg = {
        "GOOGLE_API_KEY": "test-key",
        "LLM_MODEL": "gemini-test-model",
        "LLM_TEMPERATURE": 0.7,
        "LLM_TOP_P": 0.9,
        "LLM_MAX_TOKENS": 512,
    }
    cfg.update(overrides)
    return cfg


# ── Background ────────────────────────────────────────────────────────────────

@given("GOOGLE_API_KEY está definida en el entorno")
def google_api_key_defined(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")


# ── Scenario: Generación de respuesta con contexto válido ─────────────────────

@given("tengo 3 chunks de contexto sobre inmunodeficiencias primarias", target_fixture="context_str")
def context_chunks():
    return (
        "Chunk 1: La agammaglobulinemia de Bruton (XLA) es una inmunodeficiencia primaria.\n"
        "Chunk 2: Se caracteriza por la ausencia de linfocitos B maduros.\n"
        "Chunk 3: Afecta casi exclusivamente a varones por herencia ligada al cromosoma X."
    )


@given('tengo la query "¿Qué es la agammaglobulinemia de Bruton?"', target_fixture="query")
def query_bruton():
    return "¿Qué es la agammaglobulinemia de Bruton?"


@when("llamo al generador", target_fixture="generation_result")
def llamo_al_generador(context_str, query):
    mock_response = MagicMock()
    mock_response.content = "La agammaglobulinemia de Bruton es una inmunodeficiencia primaria."
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.return_value = mock_response
        from rag.generator import RAGGenerator
        generator = RAGGenerator(_base_config())
        try:
            result = generator.generate(question=query, context=context_str, language="es")
            return {"response": result, "exception": None}
        except Exception as exc:
            return {"response": None, "exception": exc}


@then("la respuesta no está vacía")
def respuesta_no_vacia(generation_result):
    assert generation_result["response"], (
        f"La respuesta está vacía o es None: {generation_result['response']!r}"
    )


@then("no se lanza ninguna excepción")
def no_se_lanza_excepcion(generation_result):
    assert generation_result["exception"] is None, (
        f"Se lanzó excepción inesperada: {generation_result['exception']}"
    )


# ── Scenario: Parámetros de inferencia leídos de entorno ──────────────────────

@given("LLM_MODEL, LLM_TEMPERATURE, LLM_TOP_P y LLM_MAX_TOKENS están definidos en el entorno", target_fixture="llm_config")
def llm_params_defined():
    return _base_config()


@when("inicializo el LLM", target_fixture="llm_init_call_kwargs")
def inicializo_el_llm(llm_config):
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        from rag.generator import RAGGenerator
        RAGGenerator(llm_config)
        _, call_kwargs = MockLLM.call_args
        return call_kwargs


@then("el modelo usa los valores del entorno, no valores hardcodeados")
def modelo_usa_valores_entorno(llm_config, llm_init_call_kwargs):
    assert llm_init_call_kwargs["model"] == llm_config["LLM_MODEL"]
    assert llm_init_call_kwargs["temperature"] == llm_config["LLM_TEMPERATURE"]
    assert llm_init_call_kwargs["top_p"] == llm_config["LLM_TOP_P"]
    assert llm_init_call_kwargs["max_output_tokens"] == llm_config["LLM_MAX_TOKENS"]


# ── Scenario: System prompt leído de fichero ──────────────────────────────────

@given("existe el fichero prompts/system_prompt_family.txt", target_fixture="system_prompt_path")
def system_prompt_file_exists():
    path = Path(__file__).resolve().parents[2] / "prompts" / "system_prompt_family.txt"
    assert path.exists(), f"El fichero no existe: {path}"
    return path


# ── Scenario: Error claro cuando GOOGLE_API_KEY no está definida ──────────────

@given("GOOGLE_API_KEY no está definida en el entorno")
def google_api_key_not_defined(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


# ── Shared When: "inicializo el generador" (scenarios: system prompt + error) ─
# Both scenarios use this exact step text. A single function handles both:
# reads GOOGLE_API_KEY from the environment (set or unset by the preceding Given)
# and returns a dict with both the instance and the error so each Then can check
# only the key it cares about.

@when("inicializo el generador", target_fixture="generator_init_result")
def inicializo_el_generador():
    api_key = os.getenv("GOOGLE_API_KEY", "")
    config = _base_config(GOOGLE_API_KEY=api_key)
    try:
        with patch("rag.generator.ChatGoogleGenerativeAI"):
            from rag.generator import RAGGenerator
            instance = RAGGenerator(config)
            return {"instance": instance, "error": None}
    except EnvironmentError as exc:
        return {"instance": None, "error": exc}


@then("el system prompt se carga desde el fichero")
def system_prompt_cargado(generator_init_result, system_prompt_path):
    instance = generator_init_result["instance"]
    assert instance is not None, "El generador no se inicializó correctamente"
    expected = system_prompt_path.read_text(encoding="utf-8")
    assert instance._system_prompt == expected


@then("se lanza EnvironmentError con mensaje que menciona GOOGLE_API_KEY")
def error_menciona_api_key(generator_init_result):
    error = generator_init_result["error"]
    assert isinstance(error, EnvironmentError), (
        f"Se esperaba EnvironmentError, se obtuvo: {type(error)}"
    )
    assert "GOOGLE_API_KEY" in str(error), (
        f"El mensaje no menciona GOOGLE_API_KEY: {error!r}"
    )


# ── Scenario: Error de autenticación con clave inválida ───────────────────────

@given("GOOGLE_API_KEY está definida con un valor inválido", target_fixture="invalid_key_config")
def api_key_invalida():
    return _base_config(GOOGLE_API_KEY="invalid-key-xyz")


@when("llamo al generador con cualquier query", target_fixture="auth_error_result")
def llamo_con_clave_invalida(invalid_key_config):
    from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.side_effect = ChatGoogleGenerativeAIError(
            "API key not valid. Please pass a valid API key."
        )
        from rag.generator import RAGGenerator
        generator = RAGGenerator(invalid_key_config)
        try:
            generator.generate(question="¿Qué es una IDP?", context="ctx", language="es")
            return None
        except Exception as exc:
            return exc


@then("se lanza una excepción de autenticación")
def se_lanza_excepcion_autenticacion(auth_error_result):
    from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
    assert isinstance(auth_error_result, ChatGoogleGenerativeAIError), (
        f"Se esperaba ChatGoogleGenerativeAIError, se obtuvo: {type(auth_error_result)}"
    )


@then("el error no es silencioso ni un timeout")
def error_no_silencioso(auth_error_result):
    assert auth_error_result is not None, (
        "El error fue silenciado — generate() no debe atrapar excepciones"
    )


# ── Scenario @integration: llamada real a la API ──────────────────────────────

@given("GOOGLE_API_KEY es una clave válida y hay conexión a red")
def api_key_valida_con_red():
    """Requiere RUN_LLM_INTEGRATION_TESTS=1 y GOOGLE_API_KEY real para ejecutarse."""
    if os.getenv("RUN_LLM_INTEGRATION_TESTS") != "1":
        pytest.skip("Skipping integration test: RUN_LLM_INTEGRATION_TESTS != 1")
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("Skipping integration test: GOOGLE_API_KEY no definida")


@when('llamo al generador real con la query "¿Qué es una inmunodeficiencia primaria?"', target_fixture="generation_result")
def llamo_al_generador_real():
    """Para activar: RUN_LLM_INTEGRATION_TESTS=1 GOOGLE_API_KEY=<clave-real> pytest -m integration"""
    from rag.config import load_rag_config
    from rag.generator import RAGGenerator
    config = load_rag_config()
    generator = RAGGenerator(config)
    try:
        result = generator.generate(
            question="¿Qué es una inmunodeficiencia primaria?",
            context="Contexto de prueba: Las inmunodeficiencias primarias son enfermedades raras del sistema inmune.",
            language="es",
        )
        return {"response": result, "exception": None}
    except Exception as exc:
        return {"response": None, "exception": exc}
