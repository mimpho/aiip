"""Step definitions — E-14 T-06 Memoria de perfil en el pipeline de generación.

Dos capas de escenarios, con fixtures/mocking distintos:

- Escenarios 1-5 (formato de `profile_context`, aislamiento de retrieval,
  contenido de `system_prompt_family.txt`): ejercitan `rag/generator.py` y
  `rag/pipeline.py` directamente, mismo patrón que `test_e04_t06.py`
  (`patch("rag.generator.ChatGoogleGenerativeAI")`).
- Escenarios 6-7 (cacheo en `cl.user_session`, sincronización en
  `on_settings_update`): mismo patrón de fake `chainlit` module que
  `test_e14_t02.py`/`test_e14_t03.py`/`test_e14_t04.py`/`test_e14_t05.py`,
  pero con `cl.user_session` respaldado por un dict real (`get`/`set`) en
  vez de un `MagicMock()` puro — un `MagicMock().get(...)` devolvería otro
  `MagicMock` en lugar de `None`/el valor guardado, lo que rompería las
  aserciones de "no hay perfil todavía"/"perfil cacheado".
"""

import asyncio
import inspect
import os
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_bdd import given, scenario, then, when

# ── Fake chainlit module (mismo patrón que test_e14_t05.py) ──────────────────


class _FakeUser:
    def __init__(self, identifier: str, metadata: dict | None = None):
        self.identifier = identifier
        self.metadata = metadata or {}


class _FakeSession:
    def __init__(self):
        self.user = None


class _FakeContext:
    def __init__(self):
        self.session = _FakeSession()


class _FakeUserSession:
    """Respaldado por un dict real — `cl.user_session.get()` sin caché
    previa debe devolver `None` (o el `default` explícito), no un
    `MagicMock`, para que las aserciones de "no hay perfil" no den falsos
    positivos (D-093, ver docstring del módulo)."""

    def __init__(self):
        self._data: dict = {}

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


_fake_context = _FakeContext()


def _make_ask_user_message_factory(response):
    instance = MagicMock()
    instance.send = AsyncMock(return_value=response)
    return MagicMock(return_value=instance)


def _make_message_factory():
    def _build(*args, **kwargs):
        instance = MagicMock()
        instance.send = AsyncMock(return_value=None)
        instance.update = AsyncMock(return_value=None)
        instance.stream_token = AsyncMock(return_value=None)
        return instance

    return MagicMock(side_effect=_build)


def _make_chat_settings_factory():
    def _build(inputs):
        instance = MagicMock()
        instance.inputs = inputs
        instance.send = AsyncMock(return_value=None)
        return instance

    return MagicMock(side_effect=_build)


class _FakeTextInput:
    def __init__(self, id, label, initial=None, multiline=False, **kwargs):
        self.id = id
        self.label = label
        self.initial = initial
        self.multiline = multiline


class _FakeNumberInput:
    def __init__(self, id, label, initial=None, **kwargs):
        self.id = id
        self.label = label
        self.initial = initial


_fake_cl = types.ModuleType("chainlit")
_fake_cl.password_auth_callback = lambda f: f
_fake_cl.oauth_callback = lambda f: f
_fake_cl.on_chat_start = lambda f: f
_fake_cl.on_message = lambda f: f
_fake_cl.on_settings_update = lambda f: f
_fake_cl.action_callback = lambda name: (lambda f: f)
_fake_cl.User = _FakeUser
_fake_cl.user_session = _FakeUserSession()
_fake_cl.Message = _make_message_factory()
_fake_cl.Action = MagicMock(side_effect=lambda **kwargs: types.SimpleNamespace(**kwargs))
_fake_cl.Step = MagicMock()
_fake_cl.make_async = lambda f: f
_fake_cl.context = _fake_context
_fake_cl.AskUserMessage = _make_ask_user_message_factory(None)
_fake_cl.AskActionMessage = _make_ask_user_message_factory(None)
_fake_cl.ChatSettings = _make_chat_settings_factory()

sys.modules["chainlit"] = _fake_cl

_fake_input_widget = types.ModuleType("chainlit.input_widget")
_fake_input_widget.TextInput = _FakeTextInput
_fake_input_widget.NumberInput = _FakeNumberInput
sys.modules["chainlit.input_widget"] = _fake_input_widget

from fastapi import FastAPI  # noqa: E402

_fake_server = types.ModuleType("chainlit.server")
_fake_server.app = FastAPI()
sys.modules["chainlit.server"] = _fake_server

os.environ.setdefault("OAUTH_GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("OAUTH_GOOGLE_CLIENT_SECRET", "test-client-secret")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402

_FEATURE = "../features/e14_t06_profile_memory_in_prompt.feature"


@scenario(_FEATURE, "Perfil completo se formatea como bloque de contexto en el prompt")
def test_perfil_completo_se_formatea():
    pass


@scenario(_FEATURE, "El contexto de perfil no participa en la consulta de retrieval")
def test_perfil_no_participa_en_retrieval():
    pass


@scenario(_FEATURE, "Perfil parcial se inyecta solo con los campos disponibles")
def test_perfil_parcial():
    pass


@scenario(
    _FEATURE,
    "Usuario sin perfil (rechazó el consentimiento de T-02) no cambia el comportamiento actual",
)
def test_usuario_sin_perfil():
    pass


@scenario(_FEATURE, "system_prompt_family.txt se actualiza para explicar cómo usar profile_context")
def test_system_prompt_actualizado():
    pass


@scenario(
    _FEATURE,
    "El perfil se cachea en sesión y se usa en cada mensaje sin releer Supabase (D-093)",
)
def test_perfil_cacheado_en_sesion():
    pass


@scenario(_FEATURE, "Editar el perfil desde ajustes actualiza la copia en sesión (D-093)")
def test_editar_perfil_actualiza_copia_en_sesion():
    pass


def _run(coro):
    return asyncio.run(coro)


# ── Background ─────────────────────────────────────────────────────────────


@given(
    "RAGGenerator con su _PROMPT_TEMPLATE actual (system_prompt, context, question, "
    "language_instruction)"
)
def rag_generator_con_template_actual():
    from rag.generator import _PROMPT_TEMPLATE

    assert "{system_prompt}" in _PROMPT_TEMPLATE
    assert "{context}" in _PROMPT_TEMPLATE
    assert "{question}" in _PROMPT_TEMPLATE
    assert "{language_instruction}" in _PROMPT_TEMPLATE


# ── Escenario 1: perfil completo ─────────────────────────────────────────────


def _perfil_completo() -> dict:
    return {
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable",
        "patient_age": 8,
        "patient_context": "Va al cole sin problema",
    }


@given(
    "un usuario con patient_name, patient_diagnosis, patient_age y patient_context todos "
    "informados",
    target_fixture="ctx",
)
def usuario_con_perfil_completo():
    return {"profile": _perfil_completo(), "question": "¿qué cuidados necesita?", "context": "Chunk de contexto recuperado."}


@when(
    "pipeline.aquery_stream()/query() construye la llamada a generate()/agenerate_stream()",
    target_fixture="ctx",
)
def construye_llamada_a_generate(ctx):
    mock_response = MagicMock()
    mock_response.content = "Respuesta de prueba."
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.return_value = mock_response
        from rag.generator import RAGGenerator

        generator = RAGGenerator({"GOOGLE_API_KEY": "test-key"})
        generator.generate(
            question=ctx["question"],
            context=ctx["context"],
            language="es",
            profile=ctx["profile"],
        )
        ctx["prompt"] = MockLLM.return_value.invoke.call_args.args[0]
    return ctx


@then(
    'se añade un nuevo placeholder (profile_context) al _PROMPT_TEMPLATE con esos cuatro '
    'datos, usando el nombre real del paciente, nunca la palabra "paciente"'
)
def valida_placeholder_profile_context(ctx):
    prompt = ctx["prompt"]
    assert "[PERFIL DEL PACIENTE]" in prompt

    # El propio system_prompt (prompts/system_prompt_family.txt) menciona
    # "[PERFIL DEL PACIENTE]" al explicar cómo usarlo (Scenario 5) — el
    # bloque realmente inyectado es el que precede inmediatamente a
    # "[CONTEXTO]" (así arma _PROMPT_TEMPLATE: "{profile_context}[CONTEXTO]"),
    # no la primera aparición del texto en todo el prompt.
    end = prompt.index("[CONTEXTO]")
    start = prompt.rindex("[PERFIL DEL PACIENTE]", 0, end)
    profile_block = prompt[start:end]

    assert "Nombre: Lucía" in profile_block
    assert "Diagnóstico: Inmunodeficiencia común variable" in profile_block
    assert "Edad: 8 años" in profile_block
    assert "Contexto: Va al cole sin problema" in profile_block
    assert "paciente" not in profile_block.lower().replace("[perfil del paciente]", "")


@then('el placeholder existente "context" (los chunks recuperados) no cambia de contenido')
def context_no_cambia(ctx):
    assert ctx["context"] in ctx["prompt"]


# ── Escenario 2: perfil no participa en retrieval ────────────────────────────


@pytest.fixture(scope="session")
def embeddings_model():
    from rag.embeddings import get_embeddings

    return get_embeddings()


@given("un usuario con perfil completo y una pregunta cualquiera", target_fixture="ctx")
def perfil_completo_y_pregunta(tmp_path, embeddings_model):
    from rag.retriever import get_retriever

    config = {
        "GOOGLE_API_KEY": "test-key",
        "CHROMA_PATH": str(tmp_path),
        "COLLECTION_NAME": "e14_t06_test",
        "RAG_TOP_K": 3,
    }
    vs = get_retriever(embeddings_model, config["CHROMA_PATH"], config["COLLECTION_NAME"], top_k=3)
    vs.add_texts(
        [
            "La agammaglobulinemia de Bruton (XLA) es una inmunodeficiencia primaria.",
            "Se caracteriza por la ausencia de linfocitos B maduros.",
        ]
    )
    return {
        "config": config,
        "question": "¿qué es una inmunodeficiencia primaria?",
        "profile": _perfil_completo(),
    }


@when("se ejecuta pipeline.retrieve()", target_fixture="ctx")
def ejecuta_pipeline_retrieve(ctx):
    mock_response = MagicMock()
    mock_response.content = "Respuesta de prueba."
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.return_value = mock_response
        from rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(ctx["config"])
        spy = MagicMock(wraps=pipeline._retriever.invoke)
        # EnsembleRetriever es un modelo pydantic — no admite setattr arbitrario
        # de campos no declarados (ValueError: "no field 'invoke'"). object.__setattr__
        # bypassa esa validación y añade "invoke" al __dict__ de la instancia, que
        # sombrea al método de la clase en la resolución normal de atributos.
        object.__setattr__(pipeline._retriever, "invoke", spy)

        pipeline.query(ctx["question"], profile=ctx["profile"])

        ctx["retriever_invoke_calls"] = spy.call_args_list
    return ctx


@then(
    "la consulta enviada al EnsembleRetriever (BM25 + vectorial) es la pregunta original, "
    "sin el contexto de perfil añadido ni como texto ni como filtro de metadata"
)
def consulta_al_retriever_sin_perfil(ctx):
    assert len(ctx["retriever_invoke_calls"]) == 1
    call = ctx["retriever_invoke_calls"][0]
    sent = call.args[0] if call.args else call.kwargs.get("input")
    assert sent == ctx["question"]
    assert "[PERFIL DEL PACIENTE]" not in sent
    assert ctx["profile"]["patient_name"] not in sent


# ── Escenario 3: perfil parcial ───────────────────────────────────────────────


@given(
    "un usuario con patient_name y patient_diagnosis informados, pero patient_age y "
    "patient_context en NULL",
    target_fixture="ctx",
)
def usuario_con_perfil_parcial():
    return {
        "profile": {
            "patient_name": "Marcos",
            "patient_diagnosis": "Diagnóstico X",
            "patient_age": None,
            "patient_context": None,
        }
    }


@when("se construye profile_context", target_fixture="ctx")
def construye_profile_context(ctx):
    from rag.generator import _format_profile_context

    ctx["profile_context"] = _format_profile_context(ctx["profile"])
    return ctx


@then(
    "el bloque incluye solo los datos disponibles, sin mencionar los campos vacíos ni "
    "inventar valores para ellos"
)
def bloque_solo_con_datos_disponibles(ctx):
    profile_context = ctx["profile_context"]
    assert "Nombre: Marcos" in profile_context
    assert "Diagnóstico: Diagnóstico X" in profile_context
    assert "Edad" not in profile_context
    assert "Contexto" not in profile_context


# ── Escenario 4: usuario sin perfil ──────────────────────────────────────────


@given("un usuario con patient_name en NULL (sin onboarding completado)", target_fixture="ctx")
def usuario_sin_perfil():
    return {
        "profile": {
            "patient_name": None,
            "patient_diagnosis": None,
            "patient_age": None,
            "patient_context": None,
        },
        "question": "¿qué cuidados necesita?",
        "context": "Chunk de contexto recuperado.",
    }


@when("se genera una respuesta", target_fixture="ctx")
def genera_respuesta_sin_perfil(ctx):
    from rag.language import build_language_instruction

    mock_response = MagicMock()
    mock_response.content = "Respuesta de prueba."
    with patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM:
        MockLLM.return_value.invoke.return_value = mock_response
        from rag.generator import RAGGenerator

        generator = RAGGenerator({"GOOGLE_API_KEY": "test-key"})
        generator.generate(
            question=ctx["question"],
            context=ctx["context"],
            language="es",
            profile=ctx["profile"],
        )
        prompt = MockLLM.return_value.invoke.call_args.args[0]

        old_template = (
            "{system_prompt}\n\n[CONTEXTO]\n{context}\n\n[PREGUNTA]\n{question}\n\n"
            "[INSTRUCCIÓN DE IDIOMA]\n{language_instruction}"
        )
        ctx["expected_prompt"] = old_template.format(
            system_prompt=generator._system_prompt,
            context=ctx["context"],
            question=ctx["question"],
            language_instruction=build_language_instruction("es"),
        )
        ctx["prompt"] = prompt
    return ctx


@then(
    "el bloque [PERFIL DEL PACIENTE] se omite por completo del _PROMPT_TEMPLATE (D-093) — "
    "ni cabecera ni contenido"
)
def bloque_perfil_omitido(ctx):
    # El propio system_prompt puede mencionar el marcador al explicar cómo
    # usarlo (Scenario 5) — lo que D-093 exige es que _format_profile_context()
    # no inyecte cabecera ni contenido cuando no hay patient_name, verificado
    # directamente y por la igualdad byte a byte del siguiente Then.
    from rag.generator import _format_profile_context

    assert _format_profile_context(ctx["profile"]) == ""


@then("el pipeline se comporta exactamente igual que antes de E-14")
def pipeline_igual_que_antes(ctx):
    assert ctx["prompt"] == ctx["expected_prompt"]


# ── Escenario 5: system_prompt_family.txt actualizado ────────────────────────


@given("el placeholder profile_context ya soportado por _PROMPT_TEMPLATE", target_fixture="ctx")
def placeholder_profile_context_soportado():
    from rag.generator import _PROMPT_TEMPLATE

    assert "{profile_context}" in _PROMPT_TEMPLATE
    return {}


@when("se revisa prompts/system_prompt_family.txt", target_fixture="ctx")
def revisa_system_prompt(ctx):
    path = Path(__file__).resolve().parents[2] / "prompts" / "system_prompt_family.txt"
    ctx["system_prompt"] = path.read_text(encoding="utf-8")
    return ctx


@then(
    "incluye una instrucción explícita sobre cómo usar esos datos (ej. no repetir el "
    "diagnóstico como si fuera nuevo, ajustar el registro si la edad es relevante) sin "
    "contradecir la instrucción ya existente de no asumir que quien escribe es el paciente"
)
def incluye_instruccion_sobre_profile_context(ctx):
    system_prompt = ctx["system_prompt"]
    assert "[PERFIL DEL PACIENTE]" in system_prompt
    assert "diagnóstico" in system_prompt.lower()
    assert "edad" in system_prompt.lower()
    # No contradice la instrucción existente de no asumir que quien escribe es el paciente.
    assert "No asumas que quien escribe" in system_prompt or "no asumas que quien escribe" in system_prompt.lower()


# ── Escenarios 6-7: cacheo en cl.user_session ────────────────────────────────


class _FakePipeline:
    def __init__(self):
        self.retrieve_calls: list = []
        self.aquery_stream_calls: list = []

    def retrieve(self, question):
        self.retrieve_calls.append(question)
        return []

    async def aquery_stream(self, question, raw_results=None, profile=None):
        self.aquery_stream_calls.append(
            {"question": question, "raw_results": raw_results, "profile": profile}
        )
        yield "Respuesta de prueba."


def _profile_completo_sesion() -> dict:
    return {
        "user_name": "Marcos",
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable",
        "patient_age": 8,
        "patient_context": "Va al cole sin problema",
        "health_data_consent_at": "2026-07-01T10:00:00+00:00",
    }


@given("la app Chainlit del perfil familiar está inicializada", target_fixture="ctx")
def app_inicializada(monkeypatch):
    fresh_session = _FakeUserSession()
    monkeypatch.setattr(main_family.cl, "user_session", fresh_session)
    user = _FakeUser(identifier="familia@example.com", metadata={"user_id": "user-t06"})
    _fake_context.session.user = user
    return {"user": user, "user_id": "user-t06", "session": fresh_session}


@given("on_chat_start ya leyó profile vía _ensure_patient_profile()", target_fixture="ctx")
def on_chat_start_ya_leyo_profile(ctx, monkeypatch):
    profile = _profile_completo_sesion()
    get_profile_mock = MagicMock(return_value=profile)
    monkeypatch.setattr(main_family, "get_profile", get_profile_mock)
    monkeypatch.setattr(main_family.cl, "Message", _make_message_factory())
    monkeypatch.setattr(main_family.cl, "ChatSettings", _make_chat_settings_factory())

    _run(main_family.on_chat_start())

    ctx.update({"profile": profile, "get_profile_mock": get_profile_mock})
    return ctx


@when(
    "se guarda ese profile en cl.user_session y se envía un mensaje de chat (on_message)",
    target_fixture="ctx",
)
def envia_mensaje_de_chat(ctx, monkeypatch):
    fake_pipeline = _FakePipeline()
    monkeypatch.setattr(main_family, "_get_pipeline", MagicMock(return_value=fake_pipeline))

    calls_before = ctx["get_profile_mock"].call_count

    message = types.SimpleNamespace(content="¿qué cuidados necesita?")
    _run(main_family.on_message(message))

    ctx["fake_pipeline"] = fake_pipeline
    ctx["get_profile_calls_before_answer"] = calls_before
    return ctx


@then("_answer() lee el perfil desde cl.user_session, sin volver a llamar a get_profile()")
def answer_lee_perfil_de_sesion(ctx):
    assert len(ctx["fake_pipeline"].aquery_stream_calls) == 1
    assert ctx["fake_pipeline"].aquery_stream_calls[0]["profile"] == ctx["profile"]
    assert ctx["get_profile_mock"].call_count == ctx["get_profile_calls_before_answer"]


@then(
    "pipeline.query()/aquery_stream() recibe ese perfil como argumento opcional (default "
    "None, retrocompatible con las llamadas existentes de test_e04_t06.py y "
    "smoke_test_rag.py)"
)
def profile_es_argumento_opcional_default_none(ctx):
    from rag.pipeline import RAGPipeline

    query_params = inspect.signature(RAGPipeline.query).parameters
    assert query_params["profile"].default is None

    aquery_stream_params = inspect.signature(RAGPipeline.aquery_stream).parameters
    assert aquery_stream_params["profile"].default is None


# ── Escenario 7: editar perfil desde ajustes ─────────────────────────────────


@given("un usuario con perfil ya cacheado en cl.user_session", target_fixture="ctx")
def usuario_con_perfil_cacheado(monkeypatch):
    fresh_session = _FakeUserSession()
    monkeypatch.setattr(main_family.cl, "user_session", fresh_session)
    user = _FakeUser(identifier="familia@example.com", metadata={"user_id": "user-t06-b"})
    _fake_context.session.user = user

    profile = _profile_completo_sesion()
    fresh_session.set("profile", profile)

    return {"user": user, "user_id": "user-t06-b", "session": fresh_session, "profile": profile}


@when("on_settings_update (T-05) persiste un cambio en profiles", target_fixture="ctx")
def on_settings_update_persiste_cambio(ctx, monkeypatch):
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    monkeypatch.setattr(main_family.cl, "Message", _make_message_factory())

    new_settings = {
        "user_name": "Marcos",
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable, revisado",
        "patient_age": 9,
        "patient_context": "Va al cole sin problema, ya no toma el jarabe",
    }
    _run(main_family.on_settings_update(new_settings))

    ctx["new_settings"] = new_settings
    ctx["update_mock"] = update_mock
    return ctx


@then("la copia de profile en cl.user_session se actualiza con los mismos campos")
def copia_de_profile_se_actualiza(ctx):
    cached = ctx["session"].get("profile")
    for key, value in ctx["new_settings"].items():
        assert cached[key] == value
    # health_data_consent_at no formaba parte de new_settings — se conserva de antes.
    assert cached["health_data_consent_at"] == ctx["profile"]["health_data_consent_at"]


@then(
    "el siguiente mensaje de ese chat ya usa los datos nuevos, sin esperar a un nuevo "
    "on_chat_start"
)
def siguiente_mensaje_usa_datos_nuevos(ctx, monkeypatch):
    fake_pipeline = _FakePipeline()
    monkeypatch.setattr(main_family, "_get_pipeline", MagicMock(return_value=fake_pipeline))

    message = types.SimpleNamespace(content="¿algo ha cambiado?")
    _run(main_family.on_message(message))

    assert len(fake_pipeline.aquery_stream_calls) == 1
    used_profile = fake_pipeline.aquery_stream_calls[0]["profile"]
    assert used_profile["patient_diagnosis"] == "Inmunodeficiencia común variable, revisado"
    assert used_profile["patient_age"] == 9
