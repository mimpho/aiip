"""Step definitions — E-05 T-02 Streaming nativo de tokens."""

import asyncio
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document
from pytest_bdd import given, parsers, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e05_t02_streaming.feature")


# ── Helpers: RAGPipeline con LLM en streaming mockeado (escenarios 1-4 y 6) ──


def _base_config(**overrides) -> dict:
    cfg = {
        "GOOGLE_API_KEY": "test-key",
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


def _fake_astream(chunks):
    async def _gen(prompt):
        for chunk in chunks:
            yield SimpleNamespace(content=chunk)

    return _gen


def _build_pipeline(chunks, raw_results):
    """RAGPipeline con retrieval y LLM controlados (D-018/D-020): solo se
    mockea ChatGoogleGenerativeAI, no la lógica de rag.safety/rag.pipeline."""
    mock_vectorstore = MagicMock()
    mock_vectorstore.similarity_search_with_score.return_value = raw_results
    with (
        patch("rag.pipeline.get_embeddings", return_value=MagicMock()),
        patch("rag.pipeline.get_retriever", return_value=mock_vectorstore),
        patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM,
    ):
        MockLLM.return_value.astream = _fake_astream(chunks)
        from rag.pipeline import RAGPipeline

        return RAGPipeline(_base_config())


async def _collect_stream(pipeline, question):
    fragments = []
    async for token in pipeline.aquery_stream(question):
        fragments.append(token)
    return fragments


def _run_full_stream(stream_ctx: dict) -> dict:
    chunks = stream_ctx["chunks"]
    raw_results = stream_ctx.get("raw_results", [])
    pipeline = _build_pipeline(chunks, raw_results)
    fragments = asyncio.run(_collect_stream(pipeline, stream_ctx["question"]))
    return {"fragments": fragments, "chunks": chunks}


# ── Fake chainlit module (solo para el escenario de error en main_family) ────

_sent_messages: list["_FakeMessage"] = []


class _FakeMessage:
    def __init__(self, content: str = ""):
        self.content = content
        _sent_messages.append(self)

    async def send(self):
        return self

    async def update(self):
        return self

    async def stream_token(self, token: str):
        self.content += token
        return self


class _FakeStep:
    def __init__(self, name: str = "", **kwargs):
        self.name = name
        self.output = ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeUser:
    def __init__(self, identifier: str, metadata: dict | None = None):
        self.identifier = identifier
        self.metadata = metadata or {}


_fake_cl = types.ModuleType("chainlit")
_fake_cl.password_auth_callback = lambda f: f
_fake_cl.on_chat_start = lambda f: f
_fake_cl.on_message = lambda f: f
_fake_cl.User = _FakeUser
_fake_cl.user_session = MagicMock()
_fake_cl.Message = _FakeMessage
_fake_cl.Step = _FakeStep

# Igual que en test_e05_t01.py: cada fichero de test registra su propia
# fake "chainlit" y (re)importa main_family bound a esa fake.
sys.modules["chainlit"] = _fake_cl
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402


class _FakeChatMessage:
    """Emula cl.Message tal y como llega a on_message (mensaje entrante)."""

    def __init__(self, content: str):
        self.content = content


def _run_on_message(content: str):
    _sent_messages.clear()
    asyncio.run(main_family.on_message(_FakeChatMessage(content)))


# ── Background ────────────────────────────────────────────────────────────────


@given("RAGPipeline expone un modo de generación en streaming", target_fixture="ctx")
def rag_pipeline_expone_streaming():
    from rag.pipeline import RAGPipeline

    assert hasattr(RAGPipeline, "aquery_stream"), (
        "RAGPipeline no expone aquery_stream()"
    )
    return {}


# ── Scenario 1: Los tokens de la respuesta se emiten progresivamente ────────


@given("una pregunta sin señales de alarma")
def pregunta_sin_alarma(ctx):
    ctx["question"] = "¿qué es una inmunodeficiencia primaria?"
    ctx["chunks"] = [
        "La inmuno",
        "deficiencia primaria ",
        "es una enfermedad rara del sistema inmune.",
    ]


@when("se invoca la generación en streaming", target_fixture="stream_result")
def se_invoca_generacion_streaming(ctx):
    return _run_full_stream(ctx)


@then("se reciben varios fragmentos de texto en orden, no un único bloque final")
def varios_fragmentos_en_orden(stream_result):
    assert len(stream_result["fragments"]) > 1, (
        f"Se esperaban varios fragmentos, se recibió: {stream_result['fragments']!r}"
    )


@then("la concatenación de los fragmentos reconstruye la respuesta completa del LLM")
def concatenacion_reconstruye_respuesta(stream_result):
    assert "".join(stream_result["fragments"]) == "".join(stream_result["chunks"])


# ── Scenario 2: El recordatorio de seguridad se añade tras completar streaming


@given("una pregunta con una señal de alarma detectada por check_alarm_signals")
def pregunta_con_alarma(ctx):
    ctx["question"] = "fiebre muy alta y dificultad para respirar"
    ctx["chunks"] = ["Es importante ", "vigilar estos síntomas de cerca."]


@when("el streaming del cuerpo de la respuesta termina", target_fixture="stream_result")
def streaming_cuerpo_termina(ctx):
    return _run_full_stream(ctx)


@then(
    "se añade el recordatorio de consulta médica de apply_safety_filter como "
    "fragmento final"
)
def se_anade_recordatorio_como_fragmento_final(stream_result):
    from rag.safety import _REFERRAL

    assert stream_result["fragments"][-1] == _REFERRAL, (
        f"El último fragmento no es el recordatorio esperado: "
        f"{stream_result['fragments'][-1]!r}"
    )


@then("ese recordatorio no aparece intercalado en medio del streaming del cuerpo")
def recordatorio_no_intercalado(stream_result):
    from rag.safety import _REFERRAL

    body_fragments = stream_result["fragments"][:-1]
    assert all(_REFERRAL not in fragment for fragment in body_fragments)
    assert "".join(body_fragments) == "".join(stream_result["chunks"])


# ── Scenario 3: Afirmación tranquilizadora detectada solo tras streaming ────


@given("una pregunta sin señales de alarma en la query")
def pregunta_sin_alarma_query(ctx):
    ctx["question"] = "¿qué es una inmunodeficiencia primaria?"


@given(parsers.parse(
    'el LLM genera en streaming una respuesta que contiene la frase "{phrase}"'
))
def llm_genera_frase_partida(ctx, phrase):
    # Reparte la frase entre dos chunks: la detección de apply_safety_filter
    # solo puede operar sobre el texto ya ensamblado, nunca chunk a chunk.
    mid = len(phrase) // 2
    ctx["chunks"] = [
        f"Sobre tu consulta, {phrase[:mid]}",
        f"{phrase[mid:]}, no hace falta nada más.",
    ]


@when(
    "el streaming termina y se ensambla el texto completo",
    target_fixture="stream_result",
)
def streaming_termina_y_ensambla(ctx):
    return _run_full_stream(ctx)


@then("apply_safety_filter añade el recordatorio de consulta médica al final")
def apply_safety_filter_anade_recordatorio(stream_result):
    from rag.safety import _REFERRAL

    assert stream_result["fragments"][-1] == _REFERRAL, (
        f"El último fragmento no es el recordatorio esperado: "
        f"{stream_result['fragments'][-1]!r}"
    )


# ── Scenario 4: Streaming sin filtro no añade texto adicional ───────────────


@given(
    "una pregunta informativa sin alarma y sin frases tranquilizadoras en la "
    "respuesta"
)
def pregunta_informativa_sin_alarma(ctx):
    ctx["question"] = "¿qué es una inmunodeficiencia primaria?"
    ctx["chunks"] = ["Es un grupo ", "de enfermedades genéticas del sistema inmune."]
    ctx["raw_results"] = []


@when("el streaming termina", target_fixture="stream_result")
def streaming_termina(ctx):
    return _run_full_stream(ctx)


@then("no se añade ningún recordatorio adicional al final de la respuesta")
def no_se_anade_recordatorio(stream_result):
    assert "".join(stream_result["fragments"]) == "".join(stream_result["chunks"])


# ── Scenario 5: Error durante el streaming no rompe la sesión de chat ───────


@when(
    "el streaming lanza una excepción antes de completarse, por ejemplo porque "
    "el LLM no está disponible",
    target_fixture="chat_result",
)
def streaming_lanza_excepcion(ctx, monkeypatch):
    async def _gen(question, raw_results=None):
        yield "Fragmento parcial "
        raise Exception("LLM no disponible")

    mock_pipeline = MagicMock()
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.aquery_stream = MagicMock(side_effect=_gen)
    monkeypatch.setattr(main_family, "_get_pipeline", lambda: mock_pipeline)

    _run_on_message(ctx["question"])
    return {"pipeline": mock_pipeline}


@then("el chat muestra un mensaje de error legible en español")
def chat_muestra_error_legible(chat_result):
    assert _sent_messages, "No se envió ningún mensaje al chat"
    assert _sent_messages[-1].content == main_family._ERROR_MESSAGE


@then("la sesión de chat sigue activa para la siguiente pregunta")
def sesion_activa_para_siguiente(chat_result):
    async def _gen_ok(question, raw_results=None):
        yield "segunda "
        yield "respuesta"

    chat_result["pipeline"].aquery_stream = MagicMock(side_effect=_gen_ok)
    _run_on_message("otra pregunta")
    assert _sent_messages[-1].content == "segunda respuesta"


# ── Scenario 6: El listado de fuentes se añade tras el streaming ────────────


@given("una pregunta cuyos documentos recuperados tienen metadatos de fuente")
def pregunta_con_metadatos_de_fuente(ctx):
    from rag.pipeline import _build_sources_section

    raw_results = [
        (
            Document(
                page_content="La inmunodeficiencia primaria es un grupo de enfermedades.",
                metadata={
                    "source": "ipopi",
                    "filename": "guia.pdf",
                    "url": "https://ejemplo.org/guia.pdf",
                },
            ),
            0.1,
        )
    ]
    ctx["raw_results"] = raw_results
    ctx["expected_sources_fragment"] = "\n\n" + _build_sources_section(
        raw_results, "es"
    )
    ctx["chunks"] = ["Respuesta ", "sobre el tema."]
    ctx["question_alarma"] = "fiebre muy alta y dificultad para respirar"
    ctx["question_sin_alarma"] = "¿qué es una inmunodeficiencia primaria?"


@when(
    "el streaming termina y se aplica apply_safety_filter",
    target_fixture="stream_results",
)
def streaming_termina_y_se_aplica_filtro(ctx):
    con_alarma = _run_full_stream(
        {
            "question": ctx["question_alarma"],
            "chunks": ctx["chunks"],
            "raw_results": ctx["raw_results"],
        }
    )
    sin_alarma = _run_full_stream(
        {
            "question": ctx["question_sin_alarma"],
            "chunks": ctx["chunks"],
            "raw_results": ctx["raw_results"],
        }
    )
    return {
        "con_alarma": con_alarma,
        "sin_alarma": sin_alarma,
        "expected_sources_fragment": ctx["expected_sources_fragment"],
    }


@then("se añade el listado de fuentes como fragmento final")
def se_anade_listado_de_fuentes(stream_results):
    expected = stream_results["expected_sources_fragment"]
    assert stream_results["con_alarma"]["fragments"][-1] == expected
    assert stream_results["sin_alarma"]["fragments"][-1] == expected


@then("si hay recordatorio de seguridad, el listado de fuentes aparece después de él")
def fuentes_aparecen_despues_del_recordatorio(stream_results):
    from rag.safety import _REFERRAL

    con_alarma_fragments = stream_results["con_alarma"]["fragments"]
    assert con_alarma_fragments[-2] == _REFERRAL, (
        "El recordatorio de seguridad debe preceder inmediatamente al listado "
        "de fuentes"
    )
    sin_alarma_fragments = stream_results["sin_alarma"]["fragments"]
    assert _REFERRAL not in sin_alarma_fragments, (
        "No debería añadirse recordatorio de seguridad sin alarma"
    )
