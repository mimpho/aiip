"""Step definitions — E-05 T-01 Integración del pipeline RAG en el chat familiar."""

import asyncio
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

from fastapi import FastAPI
from pytest_bdd import given, parsers, scenarios, then, when

# ── Fake chainlit module (not installed in this environment) ─────────────────

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
_fake_cl.oauth_callback = lambda f: f
_fake_cl.on_chat_start = lambda f: f
_fake_cl.on_message = lambda f: f
_fake_cl.action_callback = lambda name: (lambda f: f)
_fake_cl.User = _FakeUser
_fake_cl.user_session = MagicMock()
_fake_cl.Message = _FakeMessage
_fake_cl.Step = _FakeStep
_fake_cl.Action = MagicMock()

# Overwrite (not setdefault) and drop any cached main_family: other test
# modules register their own fake "chainlit", and main_family must be
# (re)imported bound to *this* file's fake, not whichever ran first.
sys.modules["chainlit"] = _fake_cl

# main_family.py hace `from chainlit.server import app` (E-05 T-06, D-040)
# para registrar rutas propias sobre la app de Chainlit — sin este stub,
# el import falla porque el "chainlit" fake de arriba no es un paquete de
# verdad y no tiene submódulo `server`.
_fake_server = types.ModuleType("chainlit.server")
_fake_server.app = FastAPI()
sys.modules["chainlit.server"] = _fake_server

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402

scenarios("../features/e05_t01_chat_pipeline_integration.feature")


class _FakeChatMessage:
    """Emula cl.Message tal y como llega a on_message (mensaje entrante)."""

    def __init__(self, content: str):
        self.content = content


def _run_on_message(content: str):
    _sent_messages.clear()
    asyncio.run(main_family.on_message(_FakeChatMessage(content)))


# ── Background ───────────────────────────────────────────────────────────────


@given("la app Chainlit del perfil familiar está inicializada", target_fixture="ctx")
def app_initialized():
    return {}


def _make_stream_mock(text: str) -> MagicMock:
    """Fake de aquery_stream(): emite `text` como único fragmento."""

    async def _gen(question, raw_results=None):
        yield text

    return MagicMock(side_effect=_gen)


@given("existe una instancia de RAGPipeline disponible para la sesión")
def rag_pipeline_available(monkeypatch, ctx):
    mock_pipeline = MagicMock()
    mock_pipeline.aquery_stream = _make_stream_mock("respuesta fake")
    mock_pipeline.retrieve.return_value = []
    monkeypatch.setattr(main_family, "_get_pipeline", lambda: mock_pipeline)
    ctx["pipeline"] = mock_pipeline
    ctx["expected_answer"] = "respuesta fake"


# ── Scenario 1: Pregunta del usuario devuelve la respuesta del pipeline ──────


@given(parsers.parse('un usuario autenticado con perfil "{role}"'))
def usuario_autenticado_con_perfil(role):
    pass


@when(parsers.parse('el usuario envía el mensaje "{message}"'))
def usuario_envia_mensaje(ctx, message):
    ctx["question"] = message
    _run_on_message(message)


@then("se invoca la generación en streaming del pipeline con esa pregunta")
def se_invoca_query_con_pregunta(ctx):
    ctx["pipeline"].aquery_stream.assert_called_once_with(
        ctx["question"], raw_results=[]
    )


@then("el chat muestra la respuesta devuelta por el pipeline")
def chat_muestra_respuesta(ctx):
    assert _sent_messages, "No se envió ningún mensaje al chat"
    assert _sent_messages[-1].content == ctx["expected_answer"]


# ── Scenario 2: Indicador de "escribiendo" ────────────────────────────────────


@given("un usuario autenticado envía una pregunta")
def usuario_autenticado_envia_pregunta(ctx):
    ctx.setdefault("question", "¿qué es una IDP?")


@when("el pipeline todavía no ha devuelto la respuesta")
def pipeline_no_ha_respondido(ctx):
    indicator_seen_before_query = {"value": False}

    async def _gen(question, raw_results=None):
        # El cuerpo del generador async solo se ejecuta al consumir el primer
        # token (lazy), es decir, después de que on_message haya enviado el
        # indicador de "escribiendo".
        indicator_seen_before_query["value"] = any(
            m.content == "" for m in _sent_messages
        )
        yield "respuesta fake"

    ctx["pipeline"].aquery_stream = MagicMock(side_effect=_gen)
    _run_on_message(ctx["question"])
    ctx["indicator_seen_before_query"] = indicator_seen_before_query["value"]


@then("el chat muestra un indicador de que el asistente está generando la respuesta")
def chat_muestra_indicador(ctx):
    assert ctx["indicator_seen_before_query"], (
        "El indicador de 'escribiendo' no se envió antes de invocar query()"
    )


# ── Scenario 3: Error del pipeline no rompe la sesión de chat ────────────────


@when(
    "RAGPipeline.query() lanza una excepción, por ejemplo porque el LLM no está disponible"
)
def pipeline_lanza_excepcion(ctx):
    async def _gen(question, raw_results=None):
        raise Exception("LLM no disponible")
        yield  # pragma: no cover — inalcanzable, necesario para que sea un generador async

    ctx["pipeline"].retrieve.return_value = []
    ctx["pipeline"].aquery_stream = MagicMock(side_effect=_gen)
    _run_on_message(ctx["question"])


@then("el chat muestra un mensaje de error legible en español")
def chat_muestra_error(ctx):
    assert _sent_messages, "No se envió ningún mensaje al chat"
    assert _sent_messages[-1].content == main_family._ERROR_MESSAGE


@then("la sesión de chat sigue activa para la siguiente pregunta")
def sesion_sigue_activa(ctx):
    ctx["pipeline"].aquery_stream = _make_stream_mock("segunda respuesta fake")
    _run_on_message("otra pregunta")
    assert _sent_messages[-1].content == "segunda respuesta fake"


# ── Scenario 4: Mensajes vacíos no invocan el pipeline ───────────────────────


@given("un usuario autenticado")
def usuario_autenticado():
    pass


@when("envía un mensaje vacío o compuesto solo por espacios")
def envia_mensaje_vacio(ctx):
    _run_on_message("")
    _run_on_message("   ")


@then("no se invoca RAGPipeline.query()")
def no_se_invoca_query(ctx):
    assert not ctx["pipeline"].aquery_stream.called
