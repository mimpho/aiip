"""Step definitions — E-14 T-08 Pulido UI del onboarding.

Mismo patrón que test_e14_t02.py/test_e14_t03.py: fake `chainlit` module
propio montado en sys.modules antes de importar main_family (no compartido
con otros ficheros de test que se importan en distinto orden).

Solo lleva step defs el punto 5 (parseo de edad, lógica Python pura). Los
5 escenarios de checklist manual (puntos 1-4 y acumulación conversacional)
quedan sin @scenario aquí a propósito — documentados en el .feature, mismo
precedente que test_e05_t06.py/test_e14_t02.py para hallazgos de UI que
solo se verifican en vivo.
"""

import os
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from pytest_bdd import given, parsers, scenario, then, when

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

_FEATURE = "../features/e14_t08_onboarding_ui_polish.feature"


@scenario(_FEATURE, "Edad válida con texto adicional se reconoce")
def test_edad_valida_con_texto_adicional_se_reconoce():
    pass


@scenario(_FEATURE, "Edad puramente numérica se sigue reconociendo (regresión)")
def test_edad_puramente_numerica_se_sigue_reconociendo():
    pass


@scenario(_FEATURE, "Entrada sin ningún número se rechaza")
def test_entrada_sin_ningun_numero_se_rechaza():
    pass


@scenario(_FEATURE, "Número fuera de rango se rechaza aunque el formato sea válido")
def test_numero_fuera_de_rango_se_rechaza():
    pass


# ── Steps ──────────────────────────────────────────────────────────────────


@given(parsers.parse('la respuesta del usuario es "{raw}"'), target_fixture="ctx")
def la_respuesta_del_usuario_es(raw):
    return {"raw": raw}


@when("se parsea con _parse_patient_age")
def se_parsea_con_parse_patient_age(ctx):
    ctx["result"] = main_family._parse_patient_age(ctx["raw"])


@then(parsers.parse("devuelve {expected:d}"))
def devuelve_entero(ctx, expected):
    assert ctx["result"] == expected


@then("devuelve None")
def devuelve_none(ctx):
    assert ctx["result"] is None
