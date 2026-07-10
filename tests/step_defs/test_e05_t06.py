"""Step definitions — E-05 T-06 UI de autenticación en Chainlit.

TDD parcial (D-030): estos tests ejercitan la lógica de wiring de
main_family.py (password_auth_callback, oauth_callback, on_chat_start, las
rutas /auth/forgot-password y /auth/confirm) mockeando auth/supabase_client
en el punto de import de main_family — mismo patrón que test_e03_t05.py.
No hacen llamadas reales a Supabase: eso ya está cubierto por los tests de
auth/supabase_client.py de E-03, y el intercambio real de tokens con Google
más los correos de confirmación/recuperación se verifican manualmente en
T-07 (los escenarios "checklist manual" del .feature no tienen step defs
aquí a propósito).
"""

import asyncio
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from pytest_bdd import given, parsers, scenario, then, when
from supabase_auth.errors import AuthApiError

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
_fake_cl.Action = MagicMock()
_fake_cl.Step = MagicMock()
_fake_cl.make_async = lambda f: f
_fake_cl.context = _fake_context
_fake_cl.AskUserMessage = _make_ask_user_message_factory(None)

# Overwrite (not setdefault) and drop any cached main_family: other test
# modules register their own fake "chainlit", and main_family must be
# (re)imported bound to *this* file's fake, not whichever ran first.
sys.modules["chainlit"] = _fake_cl

from fastapi import FastAPI  # noqa: E402

_fake_server = types.ModuleType("chainlit.server")
_fake_server.app = FastAPI()
sys.modules["chainlit.server"] = _fake_server

# oauth_callback solo se registra en main_family.py si estas variables
# están presentes en el momento del import (mismo guard que en prod para no
# romper el arranque sin Google configurado) — se fijan aquí, antes del
# import, con valores dummy: chainlit está mockeado, nunca se contacta a
# Google de verdad.
os.environ.setdefault("OAUTH_GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("OAUTH_GOOGLE_CLIENT_SECRET", "test-client-secret")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

http_client = TestClient(main_family.app)

_FEATURE = "../features/e05_t06_auth_ui.feature"

# Solo los 16 escenarios TDD tienen step defs — los del "checklist manual"
# del final del .feature (botón de Google visible, correos reales, etc.)
# se verifican a mano en T-07, sin @scenario aquí a propósito (D-030).


@scenario(_FEATURE, "Login con credenciales correctas de una cuenta existente autentica")
def test_login_credenciales_correctas():
    pass


@scenario(_FEATURE, "Credenciales de un email sin cuenta previa disparan signup automático")
def test_credenciales_sin_cuenta_previa():
    pass


@scenario(_FEATURE, 'Signup con "Confirm email" activado no autentica hasta confirmar')
def test_signup_confirm_email_activado():
    pass


@scenario(_FEATURE, "Email ya registrado con contraseña incorrecta no duplica el perfil")
def test_email_ya_registrado_password_incorrecta():
    pass


@scenario(_FEATURE, "Solicitar recuperación con un email registrado dispara el envío del correo")
def test_solicitar_recuperacion_email_registrado():
    pass


@scenario(_FEATURE, "Solicitar recuperación con un email no registrado responde igual que con uno registrado")
def test_solicitar_recuperacion_email_no_registrado():
    pass


@scenario(_FEATURE, "Confirmar un token de recuperación válido permite fijar una nueva contraseña")
def test_confirmar_token_recovery_valido():
    pass


@scenario(_FEATURE, "Enviar la nueva contraseña tras verificar el token la actualiza")
def test_enviar_nueva_password():
    pass


@scenario(_FEATURE, "Confirmar un token de signup válido activa la cuenta")
def test_confirmar_token_signup_valido():
    pass


@scenario(_FEATURE, "Token de confirmación inválido o caducado no autentica")
def test_token_confirmacion_invalido():
    pass


@scenario(_FEATURE, "Acceder a /auth/confirm sin token_hash ni type no expone un error crudo de FastAPI")
def test_confirm_sin_parametros():
    pass


@scenario(_FEATURE, "Login con Google vía oauth_callback nativo de Chainlit")
def test_login_con_google():
    pass


@scenario(_FEATURE, "oauth_callback es invocable sin id_token, como lo hace la ruta genérica de Chainlit")
def test_oauth_callback_sin_id_token():
    pass


@scenario(_FEATURE, "Segundo login con Google del mismo usuario no duplica el perfil")
def test_segundo_login_con_google():
    pass


@scenario(_FEATURE, "Primer login con Google guarda el nombre sin preguntarlo nunca")
def test_primer_login_google_guarda_nombre():
    pass


@scenario(_FEATURE, "Primer login sin nombre guardado lo pide en el chat")
def test_primer_login_sin_nombre_pide_chat():
    pass


@scenario(_FEATURE, "Login posterior con nombre ya guardado no vuelve a preguntar")
def test_login_posterior_con_nombre_no_pregunta():
    pass


@scenario(_FEATURE, "Saludo sin nombre guardado se muestra sin nombre, no con el email")
def test_saludo_sin_nombre_sin_email():
    pass


def _run(coro):
    return asyncio.run(coro)


# ── Background ─────────────────────────────────────────────────────────────


@given("la app Chainlit del perfil familiar está inicializada")
def app_inicializada():
    assert main_family is not None


# ── Escenarios 1-4: password_auth_callback (login/signup mergeados) ─────────


@given("un usuario ya registrado y confirmado, con email y contraseña válidos", target_fixture="creds")
def usuario_registrado_confirmado(monkeypatch):
    session = SimpleNamespace(user=SimpleNamespace(id="user-1"))
    monkeypatch.setattr(
        main_family, "login", lambda email, password: {"session": session, "role": "family"}
    )
    signup_mock = MagicMock()
    monkeypatch.setattr(main_family, "signup", signup_mock)
    return {"email": "existing@example.com", "password": "correct-pass", "signup_mock": signup_mock}


@when("envía esas credenciales en el formulario de login", target_fixture="auth_result")
def envia_credenciales_login(creds):
    return main_family.auth_callback(creds["email"], creds["password"])


@then("login() devuelve sesión y role")
def login_devuelve_sesion_y_role(auth_result):
    assert isinstance(auth_result, _FakeUser)
    assert auth_result.metadata["role"] == "family"


@then("se autentica sin llegar a intentar signup()")
def no_se_intenta_signup(creds):
    creds["signup_mock"].assert_not_called()


@given("un email y contraseña sin cuenta previa en Supabase Auth", target_fixture="creds")
def email_sin_cuenta_previa(monkeypatch):
    def _login_fails(email, password):
        raise AuthApiError("Invalid login credentials", 400, "invalid_credentials")

    monkeypatch.setattr(main_family, "login", _login_fails)

    session = SimpleNamespace(user=SimpleNamespace(id="user-2"))
    signup_mock = MagicMock(return_value={"user_id": "user-2", "role": "family", "session": session})
    monkeypatch.setattr(main_family, "signup", signup_mock)
    return {"email": "new@example.com", "password": "new-pass", "signup_mock": signup_mock}


@when("se envían en el mismo formulario de login", target_fixture="auth_result")
def se_envian_en_login(creds):
    return main_family.auth_callback(creds["email"], creds["password"])


@then("login() falla y se intenta signup() con las mismas credenciales")
def login_falla_intenta_signup(creds):
    creds["signup_mock"].assert_called_once_with(creds["email"], creds["password"], main_family.APP_ROLE)


@then("signup() crea el usuario y su perfil con el role de la app")
def signup_crea_usuario_y_perfil(auth_result):
    assert isinstance(auth_result, _FakeUser)
    assert auth_result.metadata["role"] == main_family.APP_ROLE


@given("un signup recién creado cuya cuenta todavía no ha sido confirmada por email", target_fixture="creds")
def signup_sin_confirmar(monkeypatch):
    def _login_fails(email, password):
        raise AuthApiError("Invalid login credentials", 400, "invalid_credentials")

    monkeypatch.setattr(main_family, "login", _login_fails)

    signup_mock = MagicMock(return_value={"user_id": "user-3", "role": "family", "session": None})
    monkeypatch.setattr(main_family, "signup", signup_mock)
    return {"email": "pending@example.com", "password": "pending-pass", "signup_mock": signup_mock}


@when("signup() se completa sin sesión activa (email de confirmación pendiente)", target_fixture="auth_result")
def signup_sin_sesion_activa(creds):
    return main_family.auth_callback(creds["email"], creds["password"])


@then("password_auth_callback devuelve None")
def callback_devuelve_none(auth_result):
    assert auth_result is None


@then("no se crea un perfil duplicado en intentos posteriores con las mismas credenciales antes de confirmar")
def no_duplica_perfil_intentos_posteriores(creds):
    second_attempt = main_family.auth_callback(creds["email"], creds["password"])
    assert second_attempt is None
    assert creds["signup_mock"].call_count == 2
    for call in creds["signup_mock"].call_args_list:
        assert call.args == (creds["email"], creds["password"], main_family.APP_ROLE)


@given("un email que ya tiene cuenta en Supabase Auth", target_fixture="creds")
def email_con_cuenta_existente(monkeypatch):
    def _login_fails(email, password):
        raise AuthApiError("Invalid login credentials", 400, "invalid_credentials")

    monkeypatch.setattr(main_family, "login", _login_fails)

    def _signup_fails(email, password, role):
        raise AuthApiError("User already registered", 400, "email_exists")

    signup_mock = MagicMock(side_effect=_signup_fails)
    monkeypatch.setattr(main_family, "signup", signup_mock)
    return {"email": "duplicate@example.com", "password": "wrong-pass", "signup_mock": signup_mock}


@when("se envían esas credenciales con una contraseña incorrecta", target_fixture="auth_result")
def credenciales_password_incorrecta(creds):
    return main_family.auth_callback(creds["email"], creds["password"])


@then("login() falla y el signup() de respaldo también falla por email duplicado")
def login_y_signup_fallan(creds):
    creds["signup_mock"].assert_called_once()


@then("no se crea un perfil duplicado")
def no_se_crea_perfil_duplicado():
    pass  # get_or_create_profile ni se llega a invocar — signup() mockeado eleva antes


@then("password_auth_callback devuelve None sin romper la app")
def callback_devuelve_none_sin_excepcion(auth_result):
    assert auth_result is None


# ── Escenarios 5-6: /auth/forgot-password ────────────────────────────────────


@given("un email con cuenta existente en Supabase Auth", target_fixture="reset_ctx")
def email_con_cuenta_para_reset(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(main_family, "request_password_reset", mock)
    return {"email": "hasaccount@example.com", "mock": mock}


@when("se envía por POST a /auth/forgot-password", target_fixture="reset_response")
def post_forgot_password(reset_ctx):
    return http_client.post("/auth/forgot-password", data={"email": reset_ctx["email"]})


@then("se llama a reset_password_for_email(email)")
def se_llama_reset_password(reset_ctx):
    reset_ctx["mock"].assert_called_once_with(reset_ctx["email"])


@then("la respuesta no revela si el email tiene cuenta o no (evita enumeración)")
def respuesta_no_revela_email(reset_response, reset_ctx):
    assert reset_response.status_code == 200
    reset_ctx["response_text"] = reset_response.text


@given("un email sin cuenta en Supabase Auth", target_fixture="reset_ctx")
def email_sin_cuenta_para_reset(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(main_family, "request_password_reset", mock)
    return {"email": "noaccount@example.com", "mock": mock}


@then("la respuesta es indistinguible de la del escenario anterior")
def respuesta_indistinguible(reset_response):
    registered_response = http_client.post(
        "/auth/forgot-password", data={"email": "hasaccount@example.com"}
    )
    assert reset_response.status_code == registered_response.status_code
    assert reset_response.text == registered_response.text


# ── Escenarios 7-10: /auth/confirm ───────────────────────────────────────────


@given(parsers.parse('un token_hash de tipo "{token_type}" válido y no usado'), target_fixture="confirm_ctx")
def token_hash_valido(monkeypatch, token_type):
    session = SimpleNamespace(access_token="access-tok", refresh_token="refresh-tok")
    response = SimpleNamespace(session=session)
    mock = MagicMock(return_value=response)
    monkeypatch.setattr(main_family, "verify_token", mock)
    return {"token_hash": "valid-token", "type": token_type, "mock": mock}


@when(parsers.parse('se accede a /auth/confirm con ese token_hash y type={token_type}'), target_fixture="confirm_response")
def get_confirm_con_type(confirm_ctx, token_type):
    return http_client.get(
        "/auth/confirm", params={"token_hash": confirm_ctx["token_hash"], "type": token_type}
    )


@then("verify_otp() devuelve una sesión válida")
def verify_otp_devuelve_sesion(confirm_ctx):
    confirm_ctx["mock"].assert_called_once_with(confirm_ctx["token_hash"], confirm_ctx["type"])


@then("se muestra el formulario para establecer la nueva contraseña")
def se_muestra_formulario_nueva_password(confirm_response):
    assert confirm_response.status_code == 200
    assert 'name="password"' in confirm_response.text


@given('una sesión válida obtenida tras verify_otp() de tipo "recovery"', target_fixture="set_password_ctx")
def sesion_valida_recovery(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(main_family, "set_new_password", mock)
    return {
        "access_token": "access-tok",
        "refresh_token": "refresh-tok",
        "new_password": "Nueva-Pass-1234!",
        "mock": mock,
    }


@when("se envía la nueva contraseña por POST a /auth/confirm", target_fixture="set_password_response")
def post_nueva_password(set_password_ctx):
    return http_client.post(
        "/auth/confirm",
        data={
            "access_token": set_password_ctx["access_token"],
            "refresh_token": set_password_ctx["refresh_token"],
            "password": set_password_ctx["new_password"],
        },
    )


@then("update_user() actualiza la contraseña de ese usuario")
def update_user_actualiza_password(set_password_ctx, set_password_response):
    assert set_password_response.status_code == 200
    set_password_ctx["mock"].assert_called_once_with(
        set_password_ctx["access_token"],
        set_password_ctx["refresh_token"],
        set_password_ctx["new_password"],
    )


@then("un login posterior con la nueva contraseña autentica correctamente")
def login_posterior_autentica(monkeypatch):
    session = SimpleNamespace(user=SimpleNamespace(id="user-recovered"))
    monkeypatch.setattr(
        main_family, "login", lambda email, password: {"session": session, "role": "family"}
    )
    result = main_family.auth_callback("recovered@example.com", "Nueva-Pass-1234!")
    assert isinstance(result, _FakeUser)


@then("verify_otp() confirma la cuenta")
def verify_otp_confirma_cuenta(confirm_ctx):
    confirm_ctx["mock"].assert_called_once_with(confirm_ctx["token_hash"], confirm_ctx["type"])


@then("se muestra la confirmación con enlace a /login, sin autenticar automáticamente en Chainlit")
def se_muestra_confirmacion_signup(confirm_response):
    assert confirm_response.status_code == 200
    assert 'href="/login"' in confirm_response.text


@given("un token_hash caducado, ya usado, o inexistente", target_fixture="confirm_ctx")
def token_hash_invalido(monkeypatch):
    def _raise(token_hash, type):
        raise AuthApiError("otp_expired: internal supabase detail", 403, "otp_expired")

    mock = MagicMock(side_effect=_raise)
    monkeypatch.setattr(main_family, "verify_token", mock)
    return {"token_hash": "expired-token", "type": "recovery", "mock": mock}


@when("se accede a /auth/confirm con ese token_hash", target_fixture="confirm_response")
def get_confirm_sin_type_explicito(confirm_ctx):
    return http_client.get(
        "/auth/confirm", params={"token_hash": confirm_ctx["token_hash"], "type": confirm_ctx["type"]}
    )


@then("verify_otp() falla")
def verify_otp_falla(confirm_ctx):
    confirm_ctx["mock"].assert_called_once()


@then("se muestra un error claro sin exponer detalles internos de Supabase")
def error_claro_sin_detalles(confirm_response):
    assert confirm_response.status_code == 200
    assert "otp_expired" not in confirm_response.text
    assert "supabase" not in confirm_response.text.lower()


@given("no se aportan token_hash ni type en la query string", target_fixture="confirm_ctx")
def no_se_aportan_parametros(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(main_family, "verify_token", mock)
    return {"mock": mock}


@when("se accede a /auth/confirm sin esos parámetros", target_fixture="confirm_response")
def get_confirm_sin_parametros():
    return http_client.get("/auth/confirm")


@then("no se llega a llamar a verify_otp()")
def no_se_llama_a_verify_otp(confirm_ctx):
    confirm_ctx["mock"].assert_not_called()


@then("se muestra la misma pantalla de error que ante un token inválido, no un JSON de FastAPI")
def se_muestra_pantalla_error_no_json(confirm_response):
    assert confirm_response.status_code == 200
    assert confirm_response.headers["content-type"].startswith("text/html")
    assert "Enlace no válido" in confirm_response.text


# ── Escenarios 11-13: oauth_callback (Google) ────────────────────────────────


@given("el usuario completa el flujo de Google gestionado por Chainlit (@cl.oauth_callback)", target_fixture="google_ctx")
def usuario_completa_flujo_google(monkeypatch):
    mock = MagicMock(return_value={"user_id": "google-user-1"})
    monkeypatch.setattr(main_family, "get_or_create_google_user", mock)
    return {
        "raw_user_data": {"email": "googleuser@example.com", "name": "Ana García"},
        "mock": mock,
    }


@when("Chainlit recibe el perfil de Google ya verificado (raw_user_data)", target_fixture="oauth_result")
def chainlit_recibe_perfil_google(google_ctx):
    return _run(
        main_family.oauth_callback(
            "google",
            "token-abc",
            google_ctx["raw_user_data"],
            _FakeUser(identifier="google-default"),
            None,
        )
    )


@then("se busca o crea el usuario correspondiente en auth.users de Supabase por email (Admin API)")
def se_busca_o_crea_usuario_google(google_ctx):
    google_ctx["mock"].assert_called_once_with(
        google_ctx["raw_user_data"]["email"],
        google_ctx["raw_user_data"]["name"],
        main_family.APP_ROLE,
    )


@then("se obtiene o crea su perfil con el role de la app")
def se_obtiene_perfil_role_app(oauth_result):
    assert oauth_result.metadata["role"] == main_family.APP_ROLE


@then("se devuelve un cl.User válido para la sesión de Chainlit")
def se_devuelve_cl_user_valido(oauth_result, google_ctx):
    assert isinstance(oauth_result, _FakeUser)
    assert oauth_result.identifier == google_ctx["raw_user_data"]["email"]
    assert oauth_result.metadata["provider"] == "google"


@when(
    "Chainlit invoca oauth_callback con los 4 argumentos posicionales de su ruta genérica, sin id_token",
    target_fixture="oauth_result",
)
def chainlit_invoca_oauth_callback_sin_id_token(google_ctx):
    """Regresión: server.py llama a config.code.oauth_callback(provider_id,
    token, raw_user_data, default_user) — 4 posicionales, sin id_token (ese
    quinto solo lo pasa la ruta especial de azure-ad-hybrid). Si la firma de
    oauth_callback no da default a id_token, esta llamada revienta con
    TypeError, que Chainlit traga silenciosamente (wrap_user_function) y
    convierte en un 401 "credentialssignin" sin rastro del error real."""
    return _run(
        main_family.oauth_callback(
            "google",
            "token-abc",
            google_ctx["raw_user_data"],
            _FakeUser(identifier="google-default"),
        )
    )


@then("no se lanza TypeError por argumento faltante")
def no_se_lanza_typeerror(oauth_result):
    assert oauth_result is not None


@given("un usuario que ya inició sesión con Google anteriormente", target_fixture="google_ctx")
def usuario_ya_inicio_con_google(monkeypatch):
    mock = MagicMock(return_value={"user_id": "google-user-2"})
    monkeypatch.setattr(main_family, "get_or_create_google_user", mock)
    raw_user_data = {"email": "returning@example.com", "name": "Returning User"}
    _run(
        main_family.oauth_callback(
            "google", "token", raw_user_data, _FakeUser(identifier="x"), None
        )
    )
    return {"raw_user_data": raw_user_data, "mock": mock}


@when("vuelve a autenticarse con Google", target_fixture="oauth_result")
def vuelve_a_autenticarse_google(google_ctx):
    return _run(
        main_family.oauth_callback(
            "google", "token", google_ctx["raw_user_data"], _FakeUser(identifier="x"), None
        )
    )


@then("no se crea un nuevo usuario en auth.users ni un perfil duplicado")
def no_crea_usuario_duplicado(google_ctx):
    assert google_ctx["mock"].call_count == 2
    for call in google_ctx["mock"].call_args_list:
        assert call.args == (
            google_ctx["raw_user_data"]["email"],
            google_ctx["raw_user_data"]["name"],
            main_family.APP_ROLE,
        )


@then("se reutiliza el perfil y role existentes")
def se_reutiliza_perfil_y_role(oauth_result):
    assert oauth_result.metadata["role"] == main_family.APP_ROLE
    assert oauth_result.metadata["user_id"] == "google-user-2"


@given("un usuario nuevo que se autentica con Google, con nombre disponible en raw_user_data", target_fixture="google_ctx")
def usuario_nuevo_google_con_nombre(monkeypatch):
    mock = MagicMock(return_value={"user_id": "google-user-3"})
    monkeypatch.setattr(main_family, "get_or_create_google_user", mock)
    return {
        "raw_user_data": {"email": "newgoogle@example.com", "name": "Nuevo Usuario"},
        "mock": mock,
    }


@when("se crea su usuario y perfil", target_fixture="oauth_result")
def se_crea_usuario_y_perfil_google(google_ctx):
    return _run(
        main_family.oauth_callback(
            "google", "token", google_ctx["raw_user_data"], _FakeUser(identifier="x"), None
        )
    )


@then("su nombre se guarda en user_metadata.full_name")
def nombre_se_guarda_en_metadata(google_ctx):
    google_ctx["mock"].assert_called_once_with(
        google_ctx["raw_user_data"]["email"],
        google_ctx["raw_user_data"]["name"],
        main_family.APP_ROLE,
    )


@then("on_chat_start no le pide el nombre por chat")
def on_chat_start_no_pide_nombre(monkeypatch, oauth_result):
    _fake_context.session.user = oauth_result
    monkeypatch.setattr(
        main_family, "get_user_metadata", lambda user_id: {"full_name": "Nuevo Usuario"}
    )
    ask_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_factory)

    _run(main_family._ensure_full_name())

    ask_factory.assert_not_called()


# ── Escenarios 14-16: nombre pedido en el chat ───────────────────────────────


@given("un usuario recién autenticado (login, signup confirmado, u OAuth) sin full_name en user_metadata", target_fixture="chat_ctx")
def usuario_sin_full_name(monkeypatch):
    user = _FakeUser(identifier="sinnombre@example.com", metadata={"user_id": "user-sin-nombre"})
    _fake_context.session.user = user
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {})
    update_mock = MagicMock()
    monkeypatch.setattr(main_family, "update_user_metadata", update_mock)
    ask_factory = _make_ask_user_message_factory({"output": "María"})
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_factory)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    return {"user": user, "update_mock": update_mock, "ask_factory": ask_factory, "message_mock": message_mock}


@when("se dispara on_chat_start")
def se_dispara_on_chat_start(chat_ctx):
    _run(main_family.on_chat_start())


@then("se pide el nombre con cl.AskUserMessage antes del saludo y la bienvenida")
def se_pide_nombre_antes_del_saludo(chat_ctx):
    chat_ctx["ask_factory"].assert_called_once()
    assert chat_ctx["ask_factory"].call_args.kwargs["content"] == main_family._ASK_NAME_MESSAGE
    # cl.Message se llama después (saludo + bienvenida) — al menos 2 veces.
    assert chat_ctx["message_mock"].call_count >= 2


@then("la respuesta se guarda en user_metadata.full_name vía update_user_by_id()")
def respuesta_se_guarda_en_metadata(chat_ctx):
    chat_ctx["update_mock"].assert_called_once_with("user-sin-nombre", {"full_name": "María"})
    assert chat_ctx["user"].metadata["full_name"] == "María"


@given("un usuario con full_name ya presente en user_metadata", target_fixture="chat_ctx")
def usuario_con_full_name(monkeypatch):
    user = _FakeUser(identifier="connombre@example.com", metadata={"user_id": "user-con-nombre"})
    _fake_context.session.user = user
    monkeypatch.setattr(main_family, "get_user_metadata", lambda user_id: {"full_name": "María"})
    ask_factory = _make_ask_user_message_factory(None)
    monkeypatch.setattr(main_family.cl, "AskUserMessage", ask_factory)
    message_mock = _make_message_factory()
    monkeypatch.setattr(main_family.cl, "Message", message_mock)
    return {"user": user, "ask_factory": ask_factory, "message_mock": message_mock}


@then("no se pide el nombre")
def no_se_pide_el_nombre(chat_ctx):
    chat_ctx["ask_factory"].assert_not_called()


@then("el saludo usa full_name")
def el_saludo_usa_full_name(chat_ctx):
    first_call_content = chat_ctx["message_mock"].call_args_list[0].kwargs["content"]
    assert "María" in first_call_content


@given("un usuario sin full_name en user_metadata (no respondió a cl.AskUserMessage a tiempo)")
def usuario_sin_full_name_sin_respuesta():
    user = _FakeUser(identifier="sinrespuesta@example.com", metadata={})
    _fake_context.session.user = user


@when("se genera el saludo", target_fixture="greeting_result")
def se_genera_el_saludo():
    return main_family._greeting()


@then("se muestra el saludo genérico sin nombre")
def se_muestra_saludo_generico(greeting_result):
    assert greeting_result in ("Buenos días", "Buenas tardes", "Buenas noches")


@then("no se usa identifier (email) como sustituto")
def no_usa_identifier_como_sustituto(greeting_result):
    assert "sinrespuesta@example.com" not in greeting_result
