"""Step definitions — E-03 T-04 Login con Google OAuth, rol fijo por app."""

import os
import sys
from pathlib import Path

import httpx
from pytest_bdd import given, parsers, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from auth.supabase_client import get_or_create_profile, sign_in_with_oauth  # noqa: E402

scenarios("../features/e03_t04_google_oauth.feature")


# ── Background ──────────────────────────────────────────────────

@given("las variables de entorno SUPABASE_URL y SUPABASE_ANON_KEY están configuradas")
def env_vars_configuradas():
    assert "SUPABASE_URL" in os.environ
    assert "SUPABASE_ANON_KEY" in os.environ


@given("Google OAuth está habilitado en Supabase Auth")
def google_oauth_habilitado():
    pass


# ── Scenario 1: sign_in_with_oauth devuelve URL hacia Google ────

@when(
    parsers.parse('llamo a sign_in_with_oauth con provider "{provider}"'),
    target_fixture="oauth_url",
)
def llamo_sign_in_with_oauth(provider):
    supabase_url = sign_in_with_oauth(provider=provider)
    # sign_in_with_oauth devuelve la URL de Supabase /auth/v1/authorize,
    # que redirige al provider OAuth. Seguimos un hop para obtener la URL
    # final de Google y verificar que el provider está habilitado en Supabase.
    resp = httpx.get(supabase_url, follow_redirects=False)
    return resp.headers.get("location", supabase_url)


@then("la respuesta contiene una URL")
def respuesta_contiene_url(oauth_url):
    assert oauth_url is not None
    assert isinstance(oauth_url, str)
    assert oauth_url.startswith("https://")


@then(parsers.parse('la URL empieza por "{prefix}"'))
def url_empieza_por(oauth_url, prefix):
    assert oauth_url.startswith(prefix)


# ── Scenarios 2-4: get_or_create_profile vía OAuth ─────────────
# Fixture names goc_target_user_id / goc_result son intencionalmente
# iguales a T-02 para que los Then compartidos sean compatibles.

@given(parsers.parse('APP_ROLE es "{role}"'))
def app_role_es(monkeypatch, role):
    monkeypatch.setenv("APP_ROLE", role)


@given(
    "un user_id de prueba sin perfil en la tabla profiles",
    target_fixture="goc_target_user_id",
)
def user_id_prueba_sin_perfil(user_without_profile):
    return user_without_profile


@given(
    parsers.parse('un user_id de prueba con perfil existente y role "{role}"'),
    target_fixture="goc_target_user_id",
)
def user_id_prueba_con_perfil(test_user, role):
    return test_user["id"]


@when(
    parsers.parse('llamo a get_or_create_profile con ese user_id y APP_ROLE "{role}"'),
    target_fixture="goc_result",
)
def llamo_get_or_create_profile_oauth(goc_target_user_id, role):
    return get_or_create_profile(goc_target_user_id, role)


@then(parsers.parse('se crea un perfil en la tabla profiles con role "{role}"'))
def se_crea_perfil_en_profiles(admin_client, goc_target_user_id, role):
    rows = (
        admin_client.table("profiles")
        .select("*")
        .eq("id", goc_target_user_id)
        .execute()
        .data
    )
    assert len(rows) == 1
    assert rows[0]["role"] == role


@then("la función devuelve el perfil creado")
def funcion_devuelve_perfil_creado(goc_result, goc_target_user_id):
    assert goc_result["id"] == goc_target_user_id


@then("no se crea un perfil duplicado")
def no_se_crea_perfil_duplicado(admin_client, goc_target_user_id):
    rows = (
        admin_client.table("profiles")
        .select("*")
        .eq("id", goc_target_user_id)
        .execute()
        .data
    )
    assert len(rows) == 1


@then(parsers.parse('la función devuelve el perfil existente con role "{role}"'))
def funcion_devuelve_perfil_existente_con_role(goc_result, goc_target_user_id, role):
    assert goc_result["id"] == goc_target_user_id
    assert goc_result["role"] == role
