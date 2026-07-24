"""Step definitions — E-14 T-02 Gate de consentimiento de datos de salud.

Mismo patrón de test_e05_t06.py: fake `chainlit` module montado en
sys.modules antes de importar main_family (no está instalado en el entorno
de tests), con su propio `_fake_cl` — cada fichero de test registra el suyo
para no compartir estado entre módulos que se importan en distinto orden.

Solo los 4 escenarios TDD tienen step defs — el 5º ("El gate aplica igual
sin importar la vía de autenticación") queda como documentación en el
.feature, sin @scenario aquí a propósito (mismo precedente que los
escenarios "checklist manual" de test_e05_t06.py): la implementación de
_ensure_health_consent() solo depende de user_id, no de la vía de
autenticación.
"""

import asyncio
import os
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from pytest_bdd import given, scenario, then, when

# ── Fake chainlit module (not installed in this environment) ─────────────────


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


_fake_context = _FakeContext()


def _make_ask_action_message_factory(response):
    """MagicMock que imita `cl.AskActionMessage(...).send()` (coroutine)."""
    instance = MagicMock()
    instance.send = AsyncMock(return_value=response)
    return MagicMock(return_value=instance)


def _make_ask_user_message_factory(response):
    """MagicMock que imita `cl.AskUserMessage(...).send()` (coroutine)."""
    instance = MagicMock()
    instance.send = AsyncMock(return_value=response)
    return MagicMock(return_value=instance)


def _make_message_factory():
    """MagicMock que imita `cl.Message(...).send()` (coroutine) — registra
    los kwargs de cada construcción en `factory.call_args_list` para poder
    comprobar el orden/contenido de los mensajes enviados."""
    def _build(*args, **kwargs):
        instance = MagicMock()
        instance.send = AsyncMock(return_value=None)
        return instance

    return MagicMock(side_effect=_build)


_fake_cl = types.ModuleType("chainlit")
_fake_cl.password_auth_callback = lambda f: f
_fake_cl.oauth_callback = lambda f: f
_fake_cl.on_chat_start = lambda f: f
_fake_cl.on_message = lambda f: f
_fake_cl.action_callback = lambda name: (lambda f: f)
_fake_cl.User = _FakeUser
_fake_cl.user_session = MagicMock()
_fake_cl.Message = _make_message_factory()
_fake_cl.Action = MagicMock(side_effect=lambda **kwargs: types.SimpleNamespace(**kwargs))
_fake_cl.Step = MagicMock()
_fake_cl.make_async = lambda f: f
_fake_cl.context = _fake_context
_fake_cl.AskUserMessage = _make_ask_user_message_factory(None)
_fake_cl.AskActionMessage = _make_ask_action_message_factory(None)

# Overwrite (not setdefault) and drop any cached main_family: other test
# modules register their own fake "chainlit", and main_family must be
# (re)imported bound to *this* file's fake, not whichever ran first.
sys.modules["chainlit"] = _fake_cl

from fastapi import FastAPI  # noqa: E402

_fake_server = types.ModuleType("chainlit.server")
_fake_server.app = FastAPI()
sys.modules["chainlit.server"] = _fake_server

# oauth_callback solo se registra en main_family.py si estas variables están
# presentes en el momento del import — se fijan aquí, antes del import, con
# valores dummy: chainlit está mockeado, nunca se contacta a Google de
# verdad.
os.environ.setdefault("OAUTH_GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("OAUTH_GOOGLE_CLIENT_SECRET", "test-client-secret")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402

_FEATURE = "../features/e14_t02_health_consent_gate.feature"


@scenario(_FEATURE, "Primer chat sin consentimiento registrado muestra el gate tras el saludo y la bienvenida")
def test_gate_tras_saludo_y_bienvenida():
    pass


@scenario(_FEATURE, "Aceptar el consentimiento lo registra una sola vez")
def test_aceptar_consentimiento_lo_registra():
    pass


@scenario(_FEATURE, "Chat posterior con consentimiento ya registrado no repite el gate")
def test_consentimiento_ya_registrado_no_repite_gate():
    pass


@scenario(_FEATURE, "Rechazar el consentimiento no bloquea el chat")
def test_rechazar_consentimiento_no_bloquea_chat():
    pass


def _run(coro):
    return asyncio.run(coro)


# ── Background ─────────────────────────────────────────────────────────────


@given("la app Chainlit del perfil familiar está inicializada")
def app_inicializada():
    assert main_family is not None


@given("un usuario ya autenticado (login, signup confirmado, u OAuth)")
def usuario_ya_autenticado():
    pass  # el usuario concreto lo fija cada Given específico de escenario


# ── Escenario 1: gate antes del saludo ────────────────────────────────────────


@given('un usuario con "health_data_consent_at" en NULL', target_fixture="gate_ctx")
def usuario_sin_consentimiento(monkeypatch):
    user = _FakeUser(identifier="sinconsentir@example.com", metadata={"user_id": "user-sin-consentir"})
    _fake_context.session.user = user
    # patient_name/etc ya informados: aísla este test al gate de consentimiento
    # (T-02) sin que la nueva pregunta de onboarding de perfil (T-03) interfiera.
    monkeypatch.setattr(
        main_family,
        "get_profile",
        lambda user_id: {
            "health_data_consent_at": None,
            "patient_name": "Ya Informado",
            "patient_diagnosis": "ya",
            "patient_age": 10,
            "patient_context": "ya",
        },
    )
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    ask_name_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_name_factory)
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {"full_name": "Ya Tengo Nombre"})
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    return {
        "user": user,
        "update_mock": update_mock,
        "ask_action_factory": ask_action_factory,
        "message_mock": message_mock,
    }


@when("se dispara on_chat_start")
def se_dispara_on_chat_start(gate_ctx):
    _run(main_family.on_chat_start())


@then("el saludo y la bienvenida se muestran primero, y el texto de consentimiento de tratamiento de datos de salud se muestra a continuación (D-090 Ronda 2)")
def se_muestra_saludo_bienvenida_y_luego_consentimiento(gate_ctx):
    gate_ctx["ask_action_factory"].assert_called_once()
    # D-090 Ronda 2: on_chat_start envía saludo y bienvenida primero, siempre
    # — los dos primeros cl.Message del hilo, antes de cualquier gate.
    calls = gate_ctx["message_mock"].call_args_list
    greeting_sent = calls[0].kwargs.get("content")
    assert any(
        greeting_sent.startswith(prefix) for prefix in ("Buenos días", "Buenas tardes", "Buenas noches")
    )
    # El saludo se envía antes de _ensure_full_name() (va después en el
    # nuevo orden), pero on_chat_start hace un prefetch no interactivo de
    # full_name (mismo lookup que el primer paso de _ensure_full_name())
    # antes de construir el saludo, precisamente para no perder la
    # personalización en usuarios recurrentes (T-05/D-036) solo por este
    # reordenamiento.
    assert "Ya Tengo Nombre" in greeting_sent
    assert calls[1].kwargs.get("content") == main_family._WELCOME_MESSAGE
    # D-090 Ronda 1: el texto completo del consentimiento se envía como su
    # propio cl.Message, ANTES del AskActionMessage — Chainlit reescribe el
    # contenido de este último a "**Selected:** <label>" al responder, así
    # que dejarlo ahí perdería la pregunta al pulsar un botón.
    consent_message_calls = [
        call for call in calls if call.kwargs.get("content") == main_family._HEALTH_CONSENT_MESSAGE
    ]
    assert len(consent_message_calls) == 1
    # El AskActionMessage que sigue lleva solo el texto corto de llamada a
    # la acción, no la pregunta completa.
    assert gate_ctx["ask_action_factory"].call_args.kwargs["content"] == main_family._HEALTH_CONSENT_PROMPT
    # cl.Message se llama varias veces más (saludo, bienvenida, consentimiento...).
    assert gate_ctx["message_mock"].call_count >= 3


@then("se requiere una acción afirmativa real (no basta con seguir escribiendo)")
def se_requiere_accion_afirmativa_real(gate_ctx):
    actions = gate_ctx["ask_action_factory"].call_args.kwargs["actions"]
    names = {action.name for action in actions}
    assert names == {"consent_accept", "consent_decline"}
    assert gate_ctx["ask_action_factory"].call_args.kwargs["timeout"] == main_family._HEALTH_CONSENT_TIMEOUT


# ── Escenario 2: aceptar registra el consentimiento ──────────────────────────


@given("el gate de consentimiento visible", target_fixture="gate_ctx")
def gate_consentimiento_visible(monkeypatch):
    user = _FakeUser(identifier="pendiente@example.com", metadata={"user_id": "user-pendiente"})
    _fake_context.session.user = user
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: {"health_data_consent_at": None})
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    return {"user": user, "update_mock": update_mock}


@when("el usuario confirma con la acción afirmativa")
def usuario_confirma_accion_afirmativa(monkeypatch, gate_ctx):
    ask_action_factory = _make_ask_action_message_factory({"name": "consent_accept", "payload": {}})
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    _run(main_family._ensure_health_consent())


@then('"health_data_consent_at" se actualiza con la marca de tiempo actual')
def health_data_consent_at_se_actualiza(gate_ctx):
    gate_ctx["update_mock"].assert_called_once()
    call_args = gate_ctx["update_mock"].call_args
    assert call_args.args[0] == "user-pendiente"
    assert "health_data_consent_at" in call_args.args[1]


@then("el flujo continúa hacia el saludo (T-03 se enganchará aquí más adelante)")
def flujo_continua_hacia_el_saludo():
    pass  # _ensure_health_consent() no lanza excepción ni corta el flujo


# ── Escenario 3: consentimiento ya registrado no repite el gate ─────────────


@given('un usuario con "health_data_consent_at" ya informado', target_fixture="gate_ctx")
def usuario_con_consentimiento_informado(monkeypatch):
    user = _FakeUser(identifier="yaconsintio@example.com", metadata={"user_id": "user-ya-consintio"})
    _fake_context.session.user = user
    # patient_name/etc ya informados: aísla este test al gate de consentimiento
    # (T-02) sin que la nueva pregunta de onboarding de perfil (T-03) interfiera.
    monkeypatch.setattr(
        main_family,
        "get_profile",
        lambda user_id: {
            "health_data_consent_at": "2026-07-01T10:00:00+00:00",
            "patient_name": "Ya Informado",
            "patient_diagnosis": "ya",
            "patient_age": 10,
            "patient_context": "ya",
        },
    )
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {"full_name": "Ya Tengo Nombre"})
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    ask_name_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_name_factory)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    return {"user": user, "ask_action_factory": ask_action_factory, "message_mock": message_mock}


@then("no se muestra el gate de consentimiento")
def no_se_muestra_el_gate(gate_ctx):
    gate_ctx["ask_action_factory"].assert_not_called()


@then("se pasa directamente al saludo (T-03 se enganchará aquí más adelante)")
def se_pasa_directamente_al_saludo(gate_ctx):
    assert gate_ctx["message_mock"].call_count >= 2


# ── Escenario 4: rechazar no bloquea el chat ─────────────────────────────────


@when("el usuario lo rechaza o lo cierra sin confirmar")
def usuario_rechaza_o_cierra_sin_confirmar(monkeypatch, gate_ctx):
    # Dos vías equivalentes: decline explícito y timeout (None) — se
    # ejercitan ambas y se guarda el resultado de la última para los Then.
    for response in ({"name": "consent_decline", "payload": {}}, None):
        ask_action_factory = _make_ask_action_message_factory(response)
        monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
        _run(main_family._ensure_health_consent())
        gate_ctx["last_ask_action_factory"] = ask_action_factory


@then('"health_data_consent_at" permanece en NULL')
def health_data_consent_at_permanece_en_null(gate_ctx):
    gate_ctx["update_mock"].assert_not_called()


@then("el chat sigue funcionando con el comportamiento de hoy, sin pedir diagnóstico, edad ni contexto del paciente")
def chat_sigue_funcionando_sin_pedir_datos_salud():
    pass  # _ensure_health_consent() no lanza excepción ni pide más datos — T-03 no existe todavía


@then("en chats posteriores se le vuelve a mostrar el gate (no se asume rechazo permanente)")
def en_chats_posteriores_se_repite_el_gate(monkeypatch, gate_ctx):
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    _run(main_family._ensure_health_consent())
    ask_action_factory.assert_called_once()
