"""Step definitions — E-14 T-05 Edición de perfil desde el panel de ajustes.

Mismo patrón que test_e14_t02.py/test_e14_t03.py/test_e14_t04.py: fake
`chainlit` module propio montado en sys.modules antes de importar
main_family (no compartido con otros ficheros de test que se importan en
distinto orden). Añade además un fake `chainlit.input_widget` (TextInput/
NumberInput) y `cl.ChatSettings`/`cl.on_settings_update` — primer uso de
`cl.ChatSettings` en el proyecto (D-092).

Solo lleva step defs los 5 escenarios TDD — los dos últimos del .feature
(icono de ajustes junto al avatar, desplegable con nombre+email) quedan
como checklist manual, mismo precedente que test_e05_t06.py/
test_e14_t02.py para hallazgos de UI que solo se verifican en vivo.
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
    """MagicMock que imita `cl.Message(...).send()` (coroutine)."""

    def _build(*args, **kwargs):
        instance = MagicMock()
        instance.send = AsyncMock(return_value=None)
        return instance

    return MagicMock(side_effect=_build)


def _make_chat_settings_factory():
    """MagicMock que imita `cl.ChatSettings(inputs).send()` (coroutine).

    Guarda `inputs` en la instancia devuelta para que los steps puedan
    inspeccionar la lista de widgets construida, sin depender de
    `call_args` del factory (más legible en los Then).
    """

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
_fake_cl.user_session = MagicMock()
_fake_cl.Message = _make_message_factory()
_fake_cl.Action = MagicMock(side_effect=lambda **kwargs: types.SimpleNamespace(**kwargs))
_fake_cl.Step = MagicMock()
_fake_cl.make_async = lambda f: f
_fake_cl.context = _fake_context
_fake_cl.AskUserMessage = _make_ask_user_message_factory(None)
_fake_cl.AskActionMessage = _make_ask_action_message_factory(None)
_fake_cl.ChatSettings = _make_chat_settings_factory()

# Overwrite (not setdefault) and drop any cached main_family: other test
# modules register their own fake "chainlit", y main_family debe (re)importarse
# ligado al fake de este fichero, no al de otro que haya corrido antes.
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

_FEATURE = "../features/e14_t05_profile_settings_panel.feature"


@scenario(_FEATURE, "El panel de ajustes muestra los datos actuales prellenados")
def test_panel_muestra_datos_prellenados():
    pass


@scenario(_FEATURE, "Guardar cambios en el panel los persiste en profiles")
def test_guardar_cambios_persiste_en_profiles():
    pass


@scenario(_FEATURE, "patient_age fuera de rango no se persiste, el resto de campos sí")
def test_patient_age_fuera_de_rango_no_se_persiste():
    pass


@scenario(_FEATURE, "El panel también sirve para completar un onboarding no terminado")
def test_panel_completa_onboarding_no_terminado():
    pass


@scenario(_FEATURE, "Un usuario sin consentimiento de datos de salud no ve los campos clínicos en el panel")
def test_sin_consentimiento_no_ve_campos_clinicos():
    pass


def _run(coro):
    return asyncio.run(coro)


def _base_profile(**overrides) -> dict:
    profile = {
        "user_name": "Marcos",
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable",
        "patient_age": 8,
        "patient_context": "Va al cole sin problema",
        "health_data_consent_at": "2026-07-01T10:00:00+00:00",
    }
    profile.update(overrides)
    return profile


def _widgets_by_id(chat_settings) -> dict:
    return {widget.id: widget for widget in chat_settings.inputs}


# ── Background ─────────────────────────────────────────────────────────────


@given("la app Chainlit del perfil familiar está inicializada")
def app_inicializada():
    assert main_family is not None


@given("un usuario autenticado", target_fixture="ctx")
def usuario_autenticado():
    user = _FakeUser(identifier="familia@example.com", metadata={"user_id": "user-t05"})
    _fake_context.session.user = user
    return {"user": user, "user_id": "user-t05"}


# ── Escenario 1: panel prellenado ────────────────────────────────────────────


@given(
    "un usuario con user_name, patient_name, patient_diagnosis, patient_age y patient_context "
    "ya guardados en profiles",
    target_fixture="ctx",
)
def usuario_con_todos_los_campos_guardados(ctx):
    profile = _base_profile()
    ctx.update({"profile": profile})
    return ctx


@when("abre el panel de ajustes (cl.ChatSettings)", target_fixture="ctx")
@when("abre el panel de ajustes", target_fixture="ctx")
def abre_el_panel_de_ajustes(ctx):
    ctx["chat_settings"] = main_family._build_chat_settings(ctx["profile"])
    return ctx


@then("ve un campo por cada dato, con su valor actual como \"initial\"")
def ve_un_campo_por_cada_dato(ctx):
    widgets = _widgets_by_id(ctx["chat_settings"])
    assert set(widgets) == {
        "user_name",
        "patient_name",
        "patient_diagnosis",
        "patient_age",
        "patient_context",
    }
    for field, widget in widgets.items():
        assert widget.initial == ctx["profile"][field]


# ── Escenario 2: guardar persiste + confirmación ─────────────────────────────


@given("el panel de ajustes abierto con datos prellenados", target_fixture="ctx")
def panel_abierto_con_datos_prellenados(ctx, monkeypatch):
    profile = _base_profile()
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    chat_settings = main_family._build_chat_settings(profile)
    ctx.update(
        {
            "profile": profile,
            "update_mock": update_mock,
            "message_mock": message_mock,
            "chat_settings": chat_settings,
        }
    )
    return ctx


@when("el usuario modifica uno o más campos y guarda", target_fixture="ctx")
def usuario_modifica_campos_y_guarda(ctx):
    new_settings = {
        "user_name": "Marcos",
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable, revisado",
        "patient_age": 9,
        "patient_context": "Va al cole sin problema, ya no toma el jarabe",
    }
    ctx["new_settings"] = new_settings
    _run(main_family.on_settings_update(new_settings))
    return ctx


@then("se dispara @cl.on_settings_update con el dict completo de valores")
def se_dispara_on_settings_update_con_dict_completo(ctx):
    assert callable(main_family.on_settings_update)
    ctx["update_mock"].assert_called_once()


@then("profiles se actualiza con los nuevos valores para ese usuario")
def profiles_se_actualiza_con_los_nuevos_valores(ctx):
    ctx["update_mock"].assert_called_once_with(ctx["user_id"], ctx["new_settings"])


@then("el usuario ve un mensaje de confirmación de que el perfil se ha actualizado")
def usuario_ve_mensaje_de_confirmacion(ctx):
    contents = [c.kwargs.get("content") for c in ctx["message_mock"].call_args_list]
    assert main_family._PROFILE_UPDATED_MESSAGE in contents


# ── Escenario 3: patient_age fuera de rango ──────────────────────────────────


@when("el usuario guarda con patient_age fuera de 0-120", target_fixture="ctx")
def usuario_guarda_con_patient_age_fuera_de_rango(ctx):
    new_settings = {
        "user_name": "Marcos",
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable, revisado",
        "patient_age": 200,
        "patient_context": "Va al cole sin problema, ya no toma el jarabe",
    }
    ctx["new_settings"] = new_settings
    _run(main_family.on_settings_update(new_settings))
    return ctx


@then("ese campo no se persiste en profiles (se mantiene el valor anterior)")
def ese_campo_no_se_persiste(ctx):
    ctx["update_mock"].assert_called_once()
    saved = ctx["update_mock"].call_args.args[1]
    assert "patient_age" not in saved


@then("el resto de campos modificados sí se guardan")
def el_resto_de_campos_si_se_guardan(ctx):
    saved = ctx["update_mock"].call_args.args[1]
    assert saved == {
        "user_name": "Marcos",
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable, revisado",
        "patient_context": "Va al cole sin problema, ya no toma el jarabe",
    }


@then("el usuario ve un mensaje de error específico sobre patient_age")
def usuario_ve_mensaje_de_error_sobre_patient_age(ctx):
    contents = [c.kwargs.get("content") for c in ctx["message_mock"].call_args_list]
    assert main_family._PATIENT_AGE_OUT_OF_RANGE_MESSAGE in contents


# ── Escenario 4: completar onboarding no terminado desde el panel ───────────


@given(
    'un usuario con "health_data_consent_at" informado pero con patient_diagnosis, patient_age '
    "o patient_context en NULL (saltó preguntas de T-03)",
    target_fixture="ctx",
)
def usuario_con_onboarding_incompleto(ctx, monkeypatch):
    profile = _base_profile(patient_diagnosis=None, patient_age=None, patient_context=None)
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    ctx.update({"profile": profile, "update_mock": update_mock, "message_mock": message_mock})
    return ctx


@then("puede rellenar ahí los campos que faltan, con el mismo backend que usa T-03")
def puede_rellenar_los_campos_que_faltan(ctx):
    widgets = _widgets_by_id(ctx["chat_settings"])
    assert widgets["patient_diagnosis"].initial is None
    assert widgets["patient_age"].initial is None
    assert widgets["patient_context"].initial is None


@then("guardar desde el panel evita que el chat le vuelva a preguntar esos mismos datos")
def guardar_evita_que_el_chat_repregunte(ctx):
    completed_settings = {
        "user_name": "Marcos",
        "patient_name": "Lucía",
        "patient_diagnosis": "Inmunodeficiencia común variable",
        "patient_age": 8,
        "patient_context": "Va al cole sin problema",
    }
    _run(main_family.on_settings_update(completed_settings))
    ctx["update_mock"].assert_called_once_with(ctx["user_id"], completed_settings)


# ── Escenario 5: sin consentimiento, solo user_name ──────────────────────────


@given('un usuario con "health_data_consent_at" en NULL', target_fixture="ctx")
def usuario_sin_consentimiento(ctx):
    profile = _base_profile(
        health_data_consent_at=None,
        patient_name=None,
        patient_diagnosis=None,
        patient_age=None,
        patient_context=None,
    )
    ctx.update({"profile": profile})
    return ctx


@then("solo ve el campo de user_name (cuenta), no patient_name/patient_diagnosis/patient_age/patient_context")
def solo_ve_el_campo_de_user_name(ctx):
    widgets = _widgets_by_id(ctx["chat_settings"])
    assert set(widgets) == {"user_name"}
    assert widgets["user_name"].initial == ctx["profile"]["user_name"]


@then(
    "no se le fuerza a dar el consentimiento desde este panel (el gate sigue siendo "
    "responsabilidad de T-02 en on_chat_start)"
)
def no_se_fuerza_el_consentimiento_desde_el_panel(ctx):
    ctx["chat_settings"].send.assert_not_called()
