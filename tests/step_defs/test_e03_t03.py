"""Step definitions — E-03 T-03 signup/login con email/password."""

import os
import sys
import uuid
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from supabase_auth.errors import AuthApiError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from auth.supabase_client import login, signup  # noqa: E402

scenarios("../features/e03_t03_email_auth.feature")

TEST_PASSWORD = "Aiip-Test-Pass-1234!"


# ── Background ──────────────────────────────────────────────────

@given("las variables de entorno SUPABASE_URL, SUPABASE_ANON_KEY y SUPABASE_SERVICE_KEY están configuradas")
def variables_de_entorno_configuradas():
    import os

    assert os.environ["SUPABASE_URL"]
    assert os.environ["SUPABASE_ANON_KEY"]
    assert os.environ["SUPABASE_SERVICE_KEY"]


@given("existe un email de prueba único generado para esta ejecución", target_fixture="test_email")
def email_de_prueba_unico():
    return f"e03t03-{uuid.uuid4().hex[:12]}@example.com"


@given("al finalizar el test el usuario de prueba es eliminado de Supabase Auth", target_fixture="created_user_ids")
def cleanup_usuario_de_prueba(admin_client):
    created_user_ids = []
    yield created_user_ids
    for user_id in created_user_ids:
        admin_client.auth.admin.delete_user(user_id)


# ── Scenarios 1 y 2: signup crea perfil con el role de la app ──────

@given(parsers.parse('APP_ROLE es "{role}"'), target_fixture="app_role")
def app_role_es(monkeypatch, role):
    monkeypatch.setenv("APP_ROLE", role)
    return role


@when("llamo a signup con el email de prueba y contraseña válida", target_fixture="signup_result")
def llamo_a_signup(test_email, app_role, created_user_ids):
    result = signup(test_email, TEST_PASSWORD, app_role)
    created_user_ids.append(result["user_id"])
    return result


@then("el usuario existe en Supabase Auth")
def usuario_existe_en_auth(admin_client, signup_result):
    user = admin_client.auth.admin.get_user_by_id(signup_result["user_id"])
    assert user.user.id == signup_result["user_id"]


@then(parsers.parse('existe un perfil en la tabla profiles con role "{role}"'))
def existe_perfil_con_role(admin_client, signup_result, role):
    row = (
        admin_client.table("profiles")
        .select("*")
        .eq("id", signup_result["user_id"])
        .single()
        .execute()
    )
    assert row.data["role"] == role


# ── Scenario 3: signup con email ya existente ───────────────────

@given("un usuario ya registrado con el email de prueba", target_fixture="signup_result")
def usuario_ya_registrado(test_email, created_user_ids):
    result = signup(test_email, TEST_PASSWORD, "familiar")
    created_user_ids.append(result["user_id"])
    return result


@when("llamo a signup con el mismo email", target_fixture="signup_error")
def llamo_a_signup_email_duplicado(test_email):
    with pytest.raises(AuthApiError) as exc_info:
        signup(test_email, TEST_PASSWORD, "familiar")
    return exc_info.value


@then("se eleva una excepción con mensaje que indica email duplicado")
def excepcion_email_duplicado(signup_error):
    assert "already registered" in signup_error.message.lower()


@then("no se crea un perfil duplicado en profiles")
def no_se_crea_perfil_duplicado(admin_client, signup_result):
    rows = (
        admin_client.table("profiles")
        .select("*")
        .eq("id", signup_result["user_id"])
        .execute()
        .data
    )
    assert len(rows) == 1


# ── Scenario 4: login con credenciales correctas ────────────────

@given(
    parsers.parse('un usuario registrado con el email de prueba y role "{role}"'),
    target_fixture="signup_result",
)
def usuario_registrado_con_role(test_email, created_user_ids, role):
    result = signup(test_email, TEST_PASSWORD, role)
    created_user_ids.append(result["user_id"])
    return result


@when("llamo a login con el email de prueba y contraseña correcta", target_fixture="login_result")
def llamo_a_login_correcto(test_email):
    return login(test_email, TEST_PASSWORD)


@then("la función devuelve una sesión Supabase válida")
def devuelve_sesion_valida(login_result):
    assert login_result["session"].access_token


@then(parsers.parse('la función devuelve el rol "{role}"'))
def devuelve_el_rol(login_result, role):
    assert login_result["role"] == role


# ── Scenario 5: login con credenciales incorrectas ──────────────

@when("llamo a login con el email de prueba y contraseña incorrecta", target_fixture="login_error")
def llamo_a_login_incorrecto(test_email):
    with pytest.raises(AuthApiError) as exc_info:
        login(test_email, "contraseña-incorrecta-123")
    return exc_info.value


@then("se eleva una excepción con mensaje que indica credenciales inválidas")
def excepcion_credenciales_invalidas(login_error):
    assert "invalid login credentials" in login_error.message.lower()


@then("no se devuelve sesión")
def no_se_devuelve_sesion(login_error):
    assert login_error is not None
