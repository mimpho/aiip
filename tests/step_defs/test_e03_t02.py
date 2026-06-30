"""Step definitions — E-03 T-02 tabla profiles + RLS + get_or_create_profile."""

import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from postgrest.exceptions import APIError
from pytest_bdd import given, parsers, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from auth.supabase_client import get_or_create_profile  # noqa: E402

scenarios("../features/e03_t02_profiles_schema.feature")


# ── Background ──────────────────────────────────────────────────

@given("la migración de profiles está aplicada en Supabase")
def migracion_aplicada(admin_client):
    admin_client.table("profiles").select("id").limit(1).execute()


# ── Escenario: esquema correcto ─────────────────────────────────

@when("consulto la estructura de la tabla profiles", target_fixture="schema_probe_user")
def consulto_estructura(test_user):
    return test_user


@then("existe la columna id como FK a auth.users")
def fk_a_auth_users(admin_client):
    fake_id = str(uuid.uuid4())
    try:
        admin_client.table("profiles").insert({"id": fake_id, "role": "familiar"}).execute()
        assert False, "se esperaba un error de foreign key"
    except APIError as e:
        assert e.code == "23503"


@then(parsers.parse('existe la columna role con CHECK que solo admite "{role_a}" o "{role_b}"'))
def role_con_check(admin_client, schema_probe_user, role_a, role_b):
    try:
        admin_client.table("profiles").update({"role": "invalido"}).eq(
            "id", schema_probe_user["id"]
        ).execute()
        assert False, "se esperaba un error de check constraint"
    except APIError as e:
        assert e.code == "23514"

    for role in (role_a, role_b):
        result = (
            admin_client.table("profiles")
            .update({"role": role})
            .eq("id", schema_probe_user["id"])
            .execute()
        )
        assert result.data[0]["role"] == role


@then("existe la columna created_at")
def columna_created_at(admin_client, schema_probe_user):
    row = (
        admin_client.table("profiles")
        .select("created_at")
        .eq("id", schema_probe_user["id"])
        .single()
        .execute()
    )
    assert row.data["created_at"] is not None


@then("existe la columna updated_at")
def columna_updated_at(admin_client, schema_probe_user):
    row = (
        admin_client.table("profiles")
        .select("updated_at")
        .eq("id", schema_probe_user["id"])
        .single()
        .execute()
    )
    assert row.data["updated_at"] is not None


# ── Escenario: updated_at automático ────────────────────────────

@given("un perfil existente con un updated_at conocido", target_fixture="profile_state")
def perfil_con_updated_at_conocido(admin_client, test_user):
    row = (
        admin_client.table("profiles")
        .select("updated_at")
        .eq("id", test_user["id"])
        .single()
        .execute()
    )
    return {"user": test_user, "updated_at_before": row.data["updated_at"]}


@when("actualizo cualquier campo del perfil")
def actualizo_campo_del_perfil(admin_client, profile_state):
    time.sleep(1)
    admin_client.table("profiles").update({"role": "profesional"}).eq(
        "id", profile_state["user"]["id"]
    ).execute()


@then("updated_at tiene un valor más reciente que el anterior")
def updated_at_mas_reciente(admin_client, profile_state):
    row = (
        admin_client.table("profiles")
        .select("updated_at")
        .eq("id", profile_state["user"]["id"])
        .single()
        .execute()
    )
    before = datetime.fromisoformat(profile_state["updated_at_before"])
    after = datetime.fromisoformat(row.data["updated_at"])
    assert after > before


# ── Escenarios: RLS bloquea lectura/escritura ajena ─────────────

@given("dos usuarios autenticados A y B con perfiles distintos", target_fixture="two_users_authed")
def dos_usuarios_autenticados(two_test_users, authed_client_factory):
    user_a, user_b = two_test_users
    return {
        "user_a": user_a,
        "user_b": user_b,
        "client_a": authed_client_factory(user_a),
    }


@when("el usuario A intenta leer el perfil del usuario B", target_fixture="rls_result")
def usuario_a_lee_b(two_users_authed):
    try:
        result = (
            two_users_authed["client_a"]
            .table("profiles")
            .select("*")
            .eq("id", two_users_authed["user_b"]["id"])
            .execute()
        )
        return {"data": result.data, "error": None}
    except APIError as e:
        return {"data": None, "error": e}


@when("el usuario A intenta escribir en el perfil del usuario B", target_fixture="rls_result")
def usuario_a_escribe_b(two_users_authed, admin_client):
    user_b_id = two_users_authed["user_b"]["id"]
    before_role = (
        admin_client.table("profiles").select("role").eq("id", user_b_id).single().execute().data["role"]
    )
    new_role = "familiar" if before_role != "familiar" else "profesional"
    try:
        result = (
            two_users_authed["client_a"]
            .table("profiles")
            .update({"role": new_role})
            .eq("id", user_b_id)
            .execute()
        )
        return {"data": result.data, "error": None, "user_b_id": user_b_id, "before_role": before_role}
    except APIError as e:
        return {"data": None, "error": e, "user_b_id": user_b_id, "before_role": before_role}


@then("la operación es rechazada por RLS")
def operacion_rechazada_por_rls(rls_result, admin_client):
    if rls_result["error"] is not None:
        assert rls_result["error"].code in ("42501", "PGRST116")
    else:
        assert rls_result["data"] == []

    if "user_b_id" in rls_result:
        after_role = (
            admin_client.table("profiles")
            .select("role")
            .eq("id", rls_result["user_b_id"])
            .single()
            .execute()
            .data["role"]
        )
        assert after_role == rls_result["before_role"]


# ── Escenario: RLS permite operar sobre el propio perfil ────────

@given("un usuario autenticado con perfil propio", target_fixture="own_user")
def usuario_con_perfil_propio(test_user, authed_client_factory):
    return {"user": test_user, "client": authed_client_factory(test_user)}


@when("lee su propio perfil", target_fixture="own_read_result")
def lee_propio_perfil(own_user):
    result = (
        own_user["client"].table("profiles").select("*").eq("id", own_user["user"]["id"]).execute()
    )
    return result.data


@then("obtiene los datos correctamente")
def obtiene_datos_correctamente(own_read_result, own_user):
    assert len(own_read_result) == 1
    assert own_read_result[0]["id"] == own_user["user"]["id"]


@when("actualiza su propio perfil", target_fixture="own_update_result")
def actualiza_propio_perfil(own_user):
    result = (
        own_user["client"]
        .table("profiles")
        .update({"role": "profesional"})
        .eq("id", own_user["user"]["id"])
        .execute()
    )
    return result.data


@then("la actualización se aplica correctamente")
def actualizacion_se_aplica_correctamente(own_update_result):
    assert len(own_update_result) == 1
    assert own_update_result[0]["role"] == "profesional"


# ── Escenarios: get_or_create_profile ────────────────────────────

@given("un user_id válido sin perfil en la tabla profiles", target_fixture="goc_target_user_id")
def user_id_sin_perfil(user_without_profile):
    return user_without_profile


@given(
    parsers.parse('un user_id válido con perfil existente y role "{role}"'),
    target_fixture="goc_target_user_id",
)
def user_id_con_perfil_existente(test_user, role):
    return test_user["id"]


@when(
    parsers.parse('llamo a get_or_create_profile con ese user_id y role "{role}"'),
    target_fixture="goc_result",
)
def llamo_get_or_create_profile(goc_target_user_id, role):
    return get_or_create_profile(goc_target_user_id, role)


@then(parsers.parse('se crea un perfil con role "{role}"'))
def se_crea_perfil_con_role(admin_client, goc_target_user_id, role):
    rows = admin_client.table("profiles").select("*").eq("id", goc_target_user_id).execute().data
    assert len(rows) == 1
    assert rows[0]["role"] == role


@then("la función devuelve el perfil creado")
def funcion_devuelve_perfil_creado(goc_result, goc_target_user_id):
    assert goc_result["id"] == goc_target_user_id


@then("no se crea un perfil duplicado")
def no_se_crea_perfil_duplicado(admin_client, goc_target_user_id):
    rows = admin_client.table("profiles").select("*").eq("id", goc_target_user_id).execute().data
    assert len(rows) == 1


@then("la función devuelve el perfil existente")
def funcion_devuelve_perfil_existente(goc_result, goc_target_user_id):
    assert goc_result["id"] == goc_target_user_id
