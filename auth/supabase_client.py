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
