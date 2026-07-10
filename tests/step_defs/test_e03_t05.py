"""Step definitions — E-03 T-05 Integración de autenticación en Chainlit."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

from fastapi import FastAPI
from pytest_bdd import given, parsers, scenarios, then, when
from supabase_auth.errors import AuthApiError

# ── Fake chainlit module (not installed in this environment) ─────────────────


class _FakeUser:
    def __init__(self, identifier: str, metadata: dict | None = None):
        self.identifier = identifier
        self.metadata = metadata or {}


_fake_cl = types.ModuleType("chainlit")
_fake_cl.password_auth_callback = lambda f: f
_fake_cl.on_chat_start = lambda f: f
_fake_cl.on_message = lambda f: f
_fake_cl.action_callback = lambda name: (lambda f: f)
_fake_cl.User = _FakeUser
_fake_cl.user_session = MagicMock()
_fake_cl.Message = MagicMock()
_fake_cl.Action = MagicMock()
_fake_cl.make_async = lambda f: f

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

scenarios("../features/e03_t05_chainlit_auth.feature")


# ── Background ───────────────────────────────────────────────────────────────


@given(parsers.parse('la variable APP_ROLE es "{role}"'))
def app_role_env(monkeypatch, role):
    monkeypatch.setenv("APP_ROLE", role)


# ── Scenario 1: Login con credenciales válidas ────────────────────────────────


@given(parsers.parse('login() devuelve una sesión válida con role "{role}"'))
def login_returns_valid_session(monkeypatch, role):
    mock_session = MagicMock()
    monkeypatch.setattr(
        main_family,
        "login",
        lambda email, password: {"session": mock_session, "role": role},
    )


@when(
    parsers.parse(
        'llamo a password_auth_callback con email "{email}" y contraseña correcta'
    ),
    target_fixture="auth_result",
)
def call_auth_callback_valid(email):
    return main_family.auth_callback(email, "cualquier-pass")


@then(
    parsers.parse('la función devuelve un cl.User con identifier "{identifier}"')
)
def result_is_cl_user(auth_result, identifier):
    assert isinstance(auth_result, _FakeUser)
    assert auth_result.identifier == identifier


@then(parsers.parse('el metadata del cl.User contiene role "{role}"'))
def result_metadata_contains_role(auth_result, role):
    assert auth_result.metadata.get("role") == role


# ── Scenario 2: Login con credenciales inválidas ─────────────────────────────


@given("login() eleva AuthApiError por credenciales inválidas")
def login_raises_auth_api_error(monkeypatch):
    def _raise_login(email, password):
        raise AuthApiError("Invalid login credentials", 400, "invalid_credentials")

    monkeypatch.setattr(main_family, "login", _raise_login)

    # auth_callback ahora intenta signup() como respaldo tras un login()
    # fallido (login/signup mergeados, E-05 T-06/D-040) — para que este
    # escenario siga probando "None ante credenciales inválidas" sin crear
    # un usuario real en Supabase, el respaldo también debe fallar (email
    # ya registrado, mismo caso que el Scenario 4 de e05_t06_auth_ui.feature).
    def _raise_signup(email, password, role):
        raise AuthApiError("User already registered", 400, "email_exists")

    monkeypatch.setattr(main_family, "signup", _raise_signup)


@when(
    parsers.parse(
        'llamo a password_auth_callback con email "{email}" y contraseña incorrecta'
    ),
    target_fixture="auth_result",
)
def call_auth_callback_invalid(email):
    return main_family.auth_callback(email, "wrong-pass")


@then("la función devuelve None")
def result_is_none(auth_result):
    assert auth_result is None
