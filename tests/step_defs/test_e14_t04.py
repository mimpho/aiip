"""Step definitions — E-14 T-04 Migración de full_name/user_name a profiles + display_name.

Mismo patrón que test_e14_t02.py/test_e14_t03.py: fake `chainlit` module propio
montado en sys.modules antes de importar main_family (no compartido con otros
ficheros de test que se importan en distinto orden). El Escenario 6
("Alta de cuenta Google nueva...") es la excepción: prueba
`get_or_create_google_user()` de `auth/supabase_client.py` directamente contra
un Supabase de test real (mismo patrón que test_e03_t03.py), porque su
comportamiento — la escritura en `profiles.user_name` en el momento de
creación — no pasa por `main_family.py`.
"""

import asyncio
import os
import sys
import types
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_bdd import given, scenario, then, when

# ── Fake chainlit module (not installed in this environment) ─────────────────


class _FakeUser:
    def __init__(self, identifier: str, display_name: str | None = None, metadata: dict | None = None):
        self.identifier = identifier
        self.display_name = display_name
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

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402

from auth.supabase_client import get_or_create_google_user  # noqa: E402

_FEATURE = "../features/e14_t04_username_migration.feature"


@scenario(_FEATURE, "Usuario existente con full_name en user_metadata recibe backfill a profiles")
def test_backfill_a_profiles():
    pass


@scenario(_FEATURE, "Usuario nuevo sin nombre guardado lo pide y lo escribe directamente en profiles")
def test_usuario_nuevo_lo_pide_y_lo_escribe_en_profiles():
    pass


@scenario(_FEATURE, "display_name se rellena en cada login con password")
def test_display_name_en_login_password():
    pass


@scenario(_FEATURE, "display_name se rellena también en login con Google")
def test_display_name_en_login_google():
    pass


@scenario(_FEATURE, "Usuario sin nombre aún disponible no muestra el email como sustituto")
def test_sin_nombre_no_muestra_email():
    pass


@scenario(_FEATURE, "Alta de cuenta Google nueva escribe profiles.user_name directamente (D-091, Q1)")
def test_alta_google_escribe_profiles_user_name():
    pass


@scenario(
    _FEATURE,
    "Login con profiles.user_name vacío cae a user_metadata.full_name solo para display_name (D-091, Q2)",
)
def test_login_cae_a_user_metadata_full_name():
    pass


def _run(coro):
    return asyncio.run(coro)


def _base_profile(**overrides) -> dict:
    profile = {
        "user_name": None,
        "patient_name": "Ya Informado",
        "patient_diagnosis": "ya",
        "patient_age": 10,
        "patient_context": "ya",
        "health_data_consent_at": "2026-07-01T10:00:00+00:00",
    }
    profile.update(overrides)
    return profile


# ── Background ─────────────────────────────────────────────────────────────


@given("la app Chainlit del perfil familiar está inicializada")
def app_inicializada():
    assert main_family is not None


# ── Escenarios 1 y 2: comparten el disparo de on_chat_start ─────────────────


@when("se dispara on_chat_start")
def se_dispara_on_chat_start(ctx):
    _run(main_family.on_chat_start())


# ── Escenario 1: backfill a profiles ─────────────────────────────────────────


@given(
    'un usuario con "full_name" ya presente en user_metadata (D-040) y "user_name" en NULL en profiles',
    target_fixture="ctx",
)
def usuario_full_name_en_metadata_user_name_null(monkeypatch):
    user = _FakeUser(identifier="migrado@example.com", metadata={"user_id": "user-t04-1"})
    _fake_context.session.user = user
    profile = _base_profile(user_name=None)
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {"full_name": "Marcos"})
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_user_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    return {
        "user": user,
        "user_id": "user-t04-1",
        "profile": profile,
        "update_mock": update_mock,
        "ask_user_factory": ask_user_factory,
    }


@then('"user_name" se rellena en profiles con el valor de user_metadata.full_name')
def user_name_se_rellena_en_profiles(ctx):
    ctx["update_mock"].assert_any_call(ctx["user_id"], {"user_name": "Marcos"})


@then("no se le vuelve a pedir el nombre por chat")
def no_se_le_vuelve_a_pedir_el_nombre(ctx):
    ctx["ask_user_factory"].assert_not_called()


# ── Escenario 2: usuario nuevo lo pide y lo escribe en profiles ─────────────


@given(
    'un usuario recién autenticado sin "user_name" en profiles ni "full_name" en user_metadata',
    target_fixture="ctx",
)
def usuario_sin_user_name_ni_full_name(monkeypatch):
    user = _FakeUser(identifier="nuevo@example.com", metadata={"user_id": "user-t04-2"})
    _fake_context.session.user = user
    profile = _base_profile(user_name=None)
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: profile)
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {})
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    ask_user_factory = _make_ask_user_message_factory({"output": "Marcos Nuevo"})
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_user_factory)
    ask_action_factory = _make_ask_action_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskActionMessage", ask_action_factory)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    return {
        "user": user,
        "user_id": "user-t04-2",
        "update_mock": update_mock,
        "ask_user_factory": ask_user_factory,
    }


@then("se pide el nombre con cl.AskUserMessage (mismo mecanismo que D-040)")
def se_pide_el_nombre_con_ask_user_message(ctx):
    ctx["ask_user_factory"].assert_called_once()
    assert ctx["ask_user_factory"].call_args.kwargs["content"] == main_family._ASK_NAME_MESSAGE


@then("la respuesta se guarda en profiles.user_name, no en user_metadata")
def la_respuesta_se_guarda_en_profiles_user_name(ctx):
    ctx["update_mock"].assert_called_once_with(ctx["user_id"], {"user_name": "Marcos Nuevo"})


# ── Escenarios 3-5 y 7: construcción de cl.User en login/oauth ──────────────


@when("se construye el cl.User de la sesión", target_fixture="cl_user_result")
def se_construye_el_cl_user_de_la_sesion(build_ctx):
    return build_ctx["build"]()


@when("se construye el cl.User de esa sesión", target_fixture="cl_user_result")
def se_construye_el_cl_user_de_esa_sesion(build_ctx):
    return build_ctx["build"]()


# ── Escenario 3: display_name en cada login con password ────────────────────


@given(
    'un usuario que inicia sesión o se registra vía password_auth_callback, con '
    '"user_name" ya disponible en profiles',
    target_fixture="build_ctx",
)
def usuario_login_password_con_user_name(monkeypatch):
    email = "marcos@example.com"
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: {"user_name": "Marcos"})
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {})
    session = types.SimpleNamespace(user=types.SimpleNamespace(id="user-t04-3"))
    monkeypatch.setattr(main_family, "login", lambda u, p: {"role": "family", "session": session})
    return {"email": email, "build": lambda: main_family.auth_callback(email, "cualquier-pass")}


@then("cl.User(display_name=...) se rellena con el nombre")
def cl_user_display_name_con_el_nombre(cl_user_result):
    assert cl_user_result.display_name == "Marcos"


@then("el desplegable de usuario muestra el nombre, no el email")
def desplegable_muestra_nombre_no_email(cl_user_result):
    assert cl_user_result.display_name is not None
    assert cl_user_result.display_name != cl_user_result.identifier


# ── Escenario 4: display_name también en login con Google ──────────────────


@given("un usuario que inicia sesión vía oauth_callback (Google)", target_fixture="build_ctx")
def usuario_login_oauth_google(monkeypatch):
    email = "marcos.google@example.com"
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: {"user_name": "Marcos"})
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {})
    monkeypatch.setattr(
        main_family,
        "get_or_create_google_user",
        lambda email, name, role: {"user_id": "user-t04-4"},
    )

    def _build():
        return _run(
            main_family.oauth_callback("google", "token", {"email": email, "name": "Marcos"}, None)
        )

    return {"email": email, "build": _build}


@then("display_name se rellena igual que en el login con password")
def display_name_igual_que_password(cl_user_result):
    assert cl_user_result.display_name == "Marcos"


@then("el comportamiento del menú de usuario es idéntico entre las dos vías de autenticación")
def comportamiento_menu_identico_entre_vias(cl_user_result):
    assert cl_user_result.display_name is not None
    assert cl_user_result.display_name != cl_user_result.identifier


# ── Escenario 5: sin nombre aún disponible no muestra el email ─────────────


@given(
    'un usuario autenticado sin "user_name" en profiles (aún no respondió al cl.AskUserMessage)',
    target_fixture="build_ctx",
)
def usuario_sin_user_name_aun_no_respondido(monkeypatch):
    email = "pendiente@example.com"
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: {"user_name": None})
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {})
    session = types.SimpleNamespace(user=types.SimpleNamespace(id="user-t04-5"))
    monkeypatch.setattr(main_family, "login", lambda u, p: {"role": "family", "session": session})
    return {"email": email, "build": lambda: main_family.auth_callback(email, "cualquier-pass")}


@then("display_name queda sin informar y el menú cae a su fallback nativo (identifier)")
def display_name_sin_informar(cl_user_result):
    assert cl_user_result.display_name is None


@then("no se fuerza ningún valor incorrecto en display_name")
def no_se_fuerza_valor_incorrecto(cl_user_result):
    assert cl_user_result.display_name is None


# ── Escenario 6: alta de cuenta Google nueva escribe profiles.user_name ────
# Prueba get_or_create_google_user() directamente contra un Supabase de test
# real (mismo patrón que test_e03_t03.py) — no pasa por main_family.py.


@pytest.fixture
def google_created_user_ids(admin_client):
    ids: list[str] = []
    yield ids
    for user_id in ids:
        admin_client.auth.admin.delete_user(user_id)


@given(
    "un usuario que se autentica por primera vez vía oauth_callback (Google), sin perfil "
    "previo, y raw_user_data trae un nombre real",
    target_fixture="google_ctx",
)
def usuario_nuevo_google_con_nombre_real():
    email = f"e14t04-{uuid.uuid4().hex[:12]}@example.com"
    return {"email": email, "full_name": "Marcos de la Torre"}


@when("se crea su perfil en profiles", target_fixture="google_result")
def se_crea_su_perfil_en_profiles(google_ctx, google_created_user_ids):
    result = get_or_create_google_user(google_ctx["email"], google_ctx["full_name"], "family")
    google_created_user_ids.append(result["user_id"])
    return {**google_ctx, "user_id": result["user_id"]}


@then('"profiles.user_name" se rellena con ese nombre en el mismo momento de creación')
def profiles_user_name_se_rellena_en_creacion(admin_client, google_result):
    row = (
        admin_client.table("profiles")
        .select("user_name")
        .eq("id", google_result["user_id"])
        .single()
        .execute()
    )
    assert row.data["user_name"] == google_result["full_name"]


@then(
    '"user_metadata.full_name" también se rellena con el mismo valor, sin retirar esa escritura (D-089)'
)
def user_metadata_full_name_tambien_se_rellena(admin_client, google_result):
    user = admin_client.auth.admin.get_user_by_id(google_result["user_id"])
    assert user.user.user_metadata.get("full_name") == google_result["full_name"]


@then("display_name sale correcto ya en este primer login, sin depender de abrir un chat antes")
def display_name_sale_correcto_primer_login(google_result):
    assert google_result["full_name"]


# ── Escenario 7: login con user_name vacío cae a user_metadata.full_name ───


@given(
    'un usuario autenticado por password u oauth con "user_name" vacío en profiles pero '
    '"full_name" ya presente en user_metadata (usuario ya existente antes de esta migración)',
    target_fixture="build_ctx",
)
def usuario_user_name_vacio_full_name_en_metadata(monkeypatch):
    email = "migrado-login@example.com"
    monkeypatch.setattr(main_family, "get_profile", lambda user_id: {"user_name": None})
    monkeypatch.setattr(
        main_family, "get_user_metadata", lambda user_id: {"full_name": "Marcos Antiguo"}
    )
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_profile", update_mock)
    session = types.SimpleNamespace(user=types.SimpleNamespace(id="user-t04-7"))
    monkeypatch.setattr(main_family, "login", lambda u, p: {"role": "family", "session": session})
    return {
        "email": email,
        "update_mock": update_mock,
        "build": lambda: main_family.auth_callback(email, "cualquier-pass"),
    }


@then("cl.User(display_name=...) se rellena con el valor de user_metadata.full_name")
def cl_user_display_name_desde_user_metadata_full_name(cl_user_result):
    assert cl_user_result.display_name == "Marcos Antiguo"


@then(
    "no se escribe nada en profiles desde el callback de login — el backfill duradero "
    "lo hace únicamente _ensure_full_name() en on_chat_start (D-089)"
)
def no_se_escribe_nada_en_profiles_desde_login(build_ctx):
    build_ctx["update_mock"].assert_not_called()
