"""Fixtures compartidas para los tests de integración con Supabase."""

import os
import uuid

import pytest
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

TEST_PASSWORD = "Aiip-Test-Pass-1234!"


@pytest.fixture(scope="session")
def admin_client() -> Client:
    """Cliente con service key — bypass RLS, solo para fixtures de test."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def _create_auth_user(admin_client: Client) -> dict:
    email = f"e03t02-{uuid.uuid4().hex[:12]}@example.com"
    created = admin_client.auth.admin.create_user(
        {"email": email, "password": TEST_PASSWORD, "email_confirm": True}
    )
    return {"id": created.user.id, "email": email}


def _authed_client(user: dict) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    session = client.auth.sign_in_with_password(
        {"email": user["email"], "password": TEST_PASSWORD}
    )
    client.postgrest.auth(session.session.access_token)
    return client


@pytest.fixture
def user_without_profile(admin_client):
    """Usuario en auth.users sin fila en profiles."""
    user = _create_auth_user(admin_client)
    yield user["id"]
    admin_client.auth.admin.delete_user(user["id"])


@pytest.fixture
def test_user(admin_client):
    """Usuario con perfil propio (role=family)."""
    user = _create_auth_user(admin_client)
    admin_client.table("profiles").insert({"id": user["id"], "role": "family"}).execute()
    yield user
    admin_client.auth.admin.delete_user(user["id"])


@pytest.fixture
def two_test_users(admin_client):
    """Dos usuarios con perfiles distintos (family / professional)."""
    user_a = _create_auth_user(admin_client)
    user_b = _create_auth_user(admin_client)
    admin_client.table("profiles").insert({"id": user_a["id"], "role": "family"}).execute()
    admin_client.table("profiles").insert({"id": user_b["id"], "role": "professional"}).execute()
    yield user_a, user_b
    admin_client.auth.admin.delete_user(user_a["id"])
    admin_client.auth.admin.delete_user(user_b["id"])


@pytest.fixture
def authed_client_factory():
    """Devuelve una función que crea un cliente anon autenticado para un usuario."""
    return _authed_client
