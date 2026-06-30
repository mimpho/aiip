"""Step definitions — E-03 T-05 Integración de autenticación en Chainlit."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

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
_fake_cl.User = _FakeUser
_fake_cl.user_session = MagicMock()
_fake_cl.Message = MagicMock()

sys.modules.setdefault("chainlit", _fake_cl)

# ── Import entrypoint under test ─────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import main_familiar  # noqa: E402

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
        main_familiar,
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
    return main_familiar.auth_callback(email, "cualquier-pass")


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
    def _raise(email, password):
        raise AuthApiError("Invalid login credentials", 400, "invalid_credentials")

    monkeypatch.setattr(main_familiar, "login", _raise)


@when(
    parsers.parse(
        'llamo a password_auth_callback con email "{email}" y contraseña incorrecta'
    ),
    target_fixture="auth_result",
)
def call_auth_callback_invalid(email):
    return main_familiar.auth_callback(email, "wrong-pass")


@then("la función devuelve None")
def result_is_none(auth_result):
    assert auth_result is None
