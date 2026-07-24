"""Step definitions — E-14 T-03 Flujo de onboarding por chat (perfil de paciente).

Mismo patrón que test_e14_t02.py: fake `chainlit` module propio montado en
sys.modules antes de importar main_family (no compartido con otros ficheros
de test que se importan en distinto orden).
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


def _make_ask_user_message_factory(responses):
    """MagicMock que imita `cl.AskUserMessage(...).send()` (coroutine).

    `responses` es un único valor devuelto en todas las llamadas, o una
    lista consumida en orden llamada a llamada (para simular varias
    preguntas seguidas, p.ej. diagnóstico → edad → contexto, o las dos
    vueltas de la repregunta de edad).
    """
    instance = MagicMock()
    if isinstance(responses, list):
        instance.send = AsyncMock(side_effect=responses)
    else:
        instance.send = AsyncMock(return_value=responses)
    return MagicMock(return_value=instance)


def _make_message_factory():
    """MagicMock que imita `cl.Message(...).send()` (coroutine)."""

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
# modules register their own fake "chainlit", y main_family debe (re)importarse
# ligado al fake de este fichero, no al de otro que haya corrido antes.
sys.modules["chainlit"] = _fake_cl

from fastapi import FastAPI  # noqa: E402

_fake_server = types.ModuleType("chainlit.server")
_fake_server.app = FastAPI()
sys.modules["chainlit.server"] = _fake_server

os.environ.setdefault("OAUTH_GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("OAUTH_GOOGLE_CLIENT_SECRET", "test-client-secret")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402

_FEATURE = "../features/e14_t03_onboarding_flow.feature"


@scenario(
    _FEATURE,
    "Se pregunta primero si los datos son sobre el propio usuario o sobre otra persona",
)
def test_se_pregunta_sobre_quien_son_los_datos():
    pass


@scenario(_FEATURE, "Si los datos son sobre el propio usuario, no se pregunta un nombre aparte")
def test_sobre_mi_no_pregunta_nombre_aparte():
    pass


@scenario(_FEATURE, "Si los datos son sobre otra persona, se pregunta su nombre")
def test_sobre_otra_persona_pregunta_su_nombre():
    pass


@scenario(
    _FEATURE,
    'Diagnóstico, edad y contexto se piden por el nombre del paciente, no como "el paciente"',
)
def test_preguntas_usan_nombre_real():
    pass


@scenario(_FEATURE, "Edad no numérica o fuera de rango se repregunta una vez (D-088, D-089)")
def test_edad_invalida_se_repregunta_una_vez():
    pass


@scenario(_FEATURE, "Solo se pregunta lo que falte")
def test_solo_se_pregunta_lo_que_falte():
    pass


@scenario(_FEATURE, "Perfil completo no vuelve a preguntarse")
def test_perfil_completo_no_vuelve_a_preguntarse():
    pass


def _run(coro):
    return asyncio.run(coro)


def _base_profile(**overrides) -> dict:
    profile = {
        "patient_name": None,
        "patient_diagnosis": None,
        "patient_age": None,
        "patient_context": None,
        "health_data_consent_at": "2026-07-01T10:00:00+00:00",
    }
    profile.update(overrides)
    return profile


# ── Background ─────────────────────────────────────────────────────────────


@given("la app Chainlit del perfil familiar está inicializada")
def app_inicializada():
    assert main_family is not None


@given(
    'un usuario autenticado con "health_data_consent_at" y "full_name" ya informados (T-02, D-040)',
    target_fixture="ctx",
)
def usuario_autenticado_con_consentimiento_y_nombre(monkeypatch):
    user = _FakeUser(
        identifier="familia@example.com",
        metadata={"user_id": "user-t03", "full_name": "Marcos"},
    )
    _fake_context.session.user = user
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {"full_name": "Marcos"})
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    ask_user_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    return {
        "user": user,
        "user_id": "user-t03",
        "message_mock": message_mock,
        "ask_action_factory": ask_action_factory,
        "ask_user_factory": ask_user_factory,
    }


# ── Escenario 1: se pregunta primero sobre quién son los datos ──────────────


@given('un usuario con "patient_name" en NULL', target_fixture="ctx")
def usuario_patient_name_null(ctx, monkeypatch):
    profile = _base_profile()
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ctx.update({"profile": profile, "update_mock": update_mock})
    return ctx


@when("se dispara on_chat_start")
def se_dispara_on_chat_start(ctx):
    _run(main_family.on_chat_start())


@then(
    'se pregunta con cl.AskActionMessage, con botones "Sobre mí" y "Sobre otra persona", '
    "si los datos son sobre sí mismo o sobre otra persona (ej. su hijo/a)"
)
def se_pregunta_sobre_quien_son_los_datos(ctx):
    ctx["ask_action_factory"].assert_called_once()
    call = ctx["ask_action_factory"].call_args
    # D-090 punto 2: la pregunta completa se envía como su propio cl.Message
    # ANTES del AskActionMessage, que lleva solo el texto corto de llamada
    # a la acción — mismo motivo que en _ensure_health_consent (T-02).
    who_message_calls = [
        c for c in ctx["message_mock"].call_args_list if c.kwargs.get("content") == main_family._PATIENT_WHO_MESSAGE
    ]
    assert len(who_message_calls) == 1
    assert call.kwargs["content"] == main_family._PATIENT_WHO_PROMPT
    actions = call.kwargs["actions"]
    assert {a.label for a in actions} == {"Sobre mí", "Sobre otra persona"}
    assert {a.name for a in actions} == {"patient_self", "patient_other"}
    assert call.kwargs["timeout"] == main_family._PATIENT_PROFILE_TIMEOUT


# ── Escenario 2: sobre mí no pregunta nombre aparte ──────────────────────────


@given('el usuario pulsa el botón "Sobre mí"', target_fixture="ctx")
def usuario_pulsa_sobre_mi(ctx, monkeypatch):
    # Diagnóstico/edad/contexto ya informados: aísla la aserción a la
    # resolución de patient_name, sin que se disparen más preguntas.
    profile = _base_profile(patient_diagnosis="ya", patient_age=5, patient_context="ya")
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_action_factory = _make_ask_action_message_factory(
        {"name": "patient_self", "payload": {}}
    )
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    ask_user_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    ctx.update(
        {
            "profile": profile,
            "update_mock": update_mock,
            "ask_action_factory": ask_action_factory,
            "ask_user_factory": ask_user_factory,
        }
    )
    return ctx


@when("se guarda la respuesta")
def se_guarda_la_respuesta(ctx):
    _run(main_family._ensure_patient_profile())


@then(
    '"patient_name" se rellena con el valor de "full_name" en la sesión en curso '
    "(cl.context.session.user.metadata, D-089), sin preguntar de nuevo"
)
def patient_name_se_rellena_con_full_name(ctx):
    ctx["update_mock"].assert_called_once_with(ctx["user_id"], {"patient_name": "Marcos"})
    ctx["ask_user_factory"].assert_not_called()


# ── Escenario 3: sobre otra persona pregunta su nombre ───────────────────────


@given('el usuario pulsa el botón "Sobre otra persona"', target_fixture="ctx")
def usuario_pulsa_sobre_otra_persona(ctx, monkeypatch):
    profile = _base_profile(patient_diagnosis="ya", patient_age=5, patient_context="ya")
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_action_factory = _make_ask_action_message_factory(
        {"name": "patient_other", "payload": {}}
    )
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    ask_user_factory = _make_ask_user_message_factory({"output": "Lucía"})
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    ctx.update(
        {
            "profile": profile,
            "update_mock": update_mock,
            "ask_action_factory": ask_action_factory,
            "ask_user_factory": ask_user_factory,
        }
    )
    return ctx


@then("se pregunta el nombre de esa persona con cl.AskUserMessage")
def se_pregunta_el_nombre_de_esa_persona(ctx):
    ctx["ask_user_factory"].assert_called_once()
    assert ctx["ask_user_factory"].call_args.kwargs["content"] == main_family._PATIENT_OTHER_NAME_MESSAGE


@then('la respuesta se guarda en "patient_name"')
def la_respuesta_se_guarda_en_patient_name(ctx):
    ctx["update_mock"].assert_called_once_with(ctx["user_id"], {"patient_name": "Lucía"})


# ── Escenario 4: preguntas usan el nombre real ───────────────────────────────


@given('"patient_name" ya resuelto (propio usuario u otra persona)', target_fixture="ctx")
def patient_name_ya_resuelto_variante(ctx, monkeypatch):
    profile = _base_profile(patient_name="Lucía")
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_user_factory = _make_ask_user_message_factory(
        [{"output": "Inmunodeficiencia común variable"}, {"output": "8"}, {"output": "Va al cole sin problema"}]
    )
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    ctx.update({"profile": profile, "update_mock": update_mock, "ask_user_factory": ask_user_factory})
    return ctx


@when("se preguntan diagnóstico, edad y contexto pendientes")
def se_preguntan_diagnostico_edad_y_contexto(ctx):
    _run(main_family._ensure_patient_profile())


@then(
    'las preguntas usan el nombre real (ej. "¿qué diagnóstico tiene Lucía?"), nunca la '
    'palabra "paciente"'
)
def las_preguntas_usan_el_nombre_real(ctx):
    contents = [c.kwargs["content"] for c in ctx["ask_user_factory"].call_args_list]
    assert len(contents) == 3
    for content in contents:
        assert "Lucía" in content
        assert "paciente" not in content.lower()


@then(
    'las respuestas se guardan en "patient_diagnosis" (texto libre, sin validar contra '
    'ninguna lista cerrada), "patient_age" y "patient_context"'
)
def las_respuestas_se_guardan(ctx):
    calls = {tuple(c.args[1].items())[0] for c in ctx["update_mock"].call_args_list}
    assert ("patient_diagnosis", "Inmunodeficiencia común variable") in calls
    assert ("patient_age", 8) in calls
    assert ("patient_context", "Va al cole sin problema") in calls


# ── Escenario 5: edad inválida se repregunta una vez ─────────────────────────


@given('"patient_name" ya resuelto', target_fixture="ctx")
def patient_name_ya_resuelto(ctx, monkeypatch):
    profile = _base_profile(patient_name="Lucía", patient_diagnosis="ya", patient_context="ya")
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ctx.update({"profile": profile, "update_mock": update_mock})
    return ctx


@when('se pregunta "patient_age" y la primera respuesta no es un entero válido entre 0 y 120')
def se_pregunta_patient_age_primera_respuesta_invalida(ctx, monkeypatch):
    ask_user_factory = _make_ask_user_message_factory(
        [{"output": "no-es-un-numero"}, {"output": "200"}]
    )
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    ctx.update({"ask_user_factory": ask_user_factory, "message_mock": message_mock})
    _run(main_family._ensure_patient_profile())


@then("se informa del error y se repregunta una única vez")
def se_informa_del_error_y_se_repregunta_una_vez(ctx):
    assert ctx["ask_user_factory"].call_count == 2
    error_sent = any(
        c.kwargs.get("content") == main_family._PATIENT_AGE_INVALID_MESSAGE
        for c in ctx["message_mock"].call_args_list
    )
    assert error_sent


@then(
    'si la segunda respuesta tampoco es válida, se sigue sin guardar "patient_age" '
    "(no bloquea el resto del onboarding ni se repregunta hasta el próximo chat)"
)
def segunda_respuesta_tampoco_valida_no_guarda_edad(ctx):
    saved_keys = {key for c in ctx["update_mock"].call_args_list for key in c.args[1]}
    assert "patient_age" not in saved_keys
    assert ctx["ask_user_factory"].call_count == 2


# ── Escenario 6: solo se pregunta lo que falte ───────────────────────────────


@given(
    'un usuario con "patient_name" y "patient_diagnosis" ya guardados, pero '
    '"patient_age" y "patient_context" en NULL',
    target_fixture="ctx",
)
def usuario_con_nombre_y_diagnostico_guardados(ctx, monkeypatch):
    profile = _base_profile(patient_name="Lucía", patient_diagnosis="ya guardado")
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    ask_user_factory = _make_ask_user_message_factory(
        [{"output": "40"}, {"output": "contexto libre"}]
    )
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    ctx.update(
        {
            "profile": profile,
            "update_mock": update_mock,
            "ask_action_factory": ask_action_factory,
            "ask_user_factory": ask_user_factory,
        }
    )
    return ctx


@then('solo se preguntan "patient_age" y "patient_context"')
def solo_se_preguntan_edad_y_contexto(ctx):
    ctx["ask_action_factory"].assert_not_called()
    contents = [c.kwargs["content"] for c in ctx["ask_user_factory"].call_args_list]
    assert len(contents) == 2
    assert contents[0] == main_family._PATIENT_AGE_MESSAGE.format(patient_name="Lucía")
    assert contents[1] == main_family._PATIENT_CONTEXT_MESSAGE.format(patient_name="Lucía")


@then("no se repiten las preguntas ya respondidas")
def no_se_repiten_las_preguntas_ya_respondidas(ctx):
    saved_keys = {key for c in ctx["update_mock"].call_args_list for key in c.args[1]}
    assert "patient_name" not in saved_keys
    assert "patient_diagnosis" not in saved_keys


# ── Escenario 7: perfil completo no vuelve a preguntarse ─────────────────────


@given(
    'un usuario con "patient_name", "patient_diagnosis", "patient_age" y '
    '"patient_context" ya informados',
    target_fixture="ctx",
)
def usuario_con_perfil_completo(ctx, monkeypatch):
    profile = _base_profile(
        patient_name="Lucía",
        patient_diagnosis="ya guardado",
        patient_age=8,
        patient_context="ya guardado",
    )
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    ask_user_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    ctx.update(
        {
            "profile": profile,
            "update_mock": update_mock,
            "ask_action_factory": ask_action_factory,
            "ask_user_factory": ask_user_factory,
        }
    )
    return ctx


@then("no se pregunta nada de onboarding")
def no_se_pregunta_nada_de_onboarding(ctx):
    ctx["ask_action_factory"].assert_not_called()
    ctx["ask_user_factory"].assert_not_called()
    ctx["update_mock"].assert_not_called()


@then("se pasa directamente al saludo y la bienvenida")
def se_pasa_directamente_al_saludo_y_la_bienvenida(ctx):
    assert ctx["message_mock"].call_count >= 2
