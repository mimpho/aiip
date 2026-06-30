"""Cliente Supabase y gestión de perfiles (E-03 T-02)."""

import os

from supabase import Client, create_client


def get_supabase_client(use_service_key: bool = False) -> Client:
    """Crea un cliente Supabase.

    use_service_key=True hace bypass de RLS — solo para operaciones internas
    de servidor (p.ej. get_or_create_profile), nunca expuesto a una request
    de usuario directamente.
    """
    url = os.environ["SUPABASE_URL"]
    key = (
        os.environ["SUPABASE_SERVICE_KEY"]
        if use_service_key
        else os.environ["SUPABASE_ANON_KEY"]
    )
    return create_client(url, key)


def get_or_create_profile(user_id: str, role: str) -> dict:
    """Devuelve el perfil de user_id, creándolo con role si no existe.

    Usa la service key para poder crear el perfil en el momento del login,
    antes de que exista una sesión autenticada con la que RLS permitiría
    el INSERT.
    """
    client = get_supabase_client(use_service_key=True)

    existing = client.table("profiles").select("*").eq("id", user_id).execute()
    if existing.data:
        return existing.data[0]

    created = (
        client.table("profiles").insert({"id": user_id, "role": role}).execute()
    )
    return created.data[0]


def _get_profile(user_id: str) -> dict:
    """Devuelve el perfil de user_id. Eleva LookupError si no existe.

    A diferencia de get_or_create_profile, no crea el perfil: un usuario
    autenticado sin perfil es un estado inconsistente, no un caso a resolver
    silenciosamente.
    """
    client = get_supabase_client(use_service_key=True)
    existing = client.table("profiles").select("*").eq("id", user_id).execute()
    if not existing.data:
        raise LookupError(f"No existe perfil para user_id={user_id}")
    return existing.data[0]


def sign_in_with_oauth(provider: str, redirect_to: str | None = None) -> str:
    """Inicia el flujo OAuth. Devuelve la URL de redirección hacia el provider.

    El browser redirect y el callback son responsabilidad de Supabase Auth.
    """
    client = get_supabase_client(use_service_key=False)
    response = client.auth.sign_in_with_oauth(
        {"provider": provider, "options": {"redirect_to": redirect_to}}
    )
    return response.url


def signup(email: str, password: str, role: str) -> dict:
    """Registra un usuario en Supabase Auth y crea su perfil con role.

    Deja que AuthApiError se propague tal cual (p.ej. email ya registrado).
    """
    client = get_supabase_client(use_service_key=False)
    response = client.auth.sign_up({"email": email, "password": password})
    user_id = response.user.id
    get_or_create_profile(user_id, role)
    return {"user_id": user_id, "role": role}


def login(email: str, password: str) -> dict:
    """Inicia sesión en Supabase Auth y devuelve la sesión junto al role.

    Deja que AuthApiError se propague tal cual (p.ej. credenciales inválidas).
    """
    client = get_supabase_client(use_service_key=False)
    response = client.auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    profile = _get_profile(response.session.user.id)
    return {"session": response.session, "role": profile["role"]}
