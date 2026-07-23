"""Cliente Supabase y gestión de perfiles (E-03 T-02)."""

import os

from supabase import Client, create_client
from supabase_auth.errors import AuthApiError


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


def get_profile(user_id: str) -> dict:
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


def update_profile(user_id: str, data: dict) -> dict:
    """Actualiza las columnas de `data` en el perfil de user_id.

    A diferencia de update_user_metadata, .update() sobre una tabla normal
    de Supabase solo toca las columnas pasadas — no hace falta mergear a
    mano con el resto del perfil.
    """
    client = get_supabase_client(use_service_key=True)
    updated = client.table("profiles").update(data).eq("id", user_id).execute()
    return updated.data[0]


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
    Incluye session en el retorno: con "Confirm email" activado (D-040) es
    None hasta que el usuario confirma su correo — quien llama decide si
    autentica ya o no en función de eso.
    """
    client = get_supabase_client(use_service_key=False)
    response = client.auth.sign_up({"email": email, "password": password})

    # Con "Confirm email" activado (D-040), Supabase no eleva error para un
    # email ya existente y confirmado — por protección anti-enumeración,
    # devuelve un usuario ofuscado con identities=[] y sin sesión, en vez de
    # AuthApiError. Sin este chequeo, get_or_create_profile revienta contra
    # la FK de `profiles` con un user_id que no existe de verdad en
    # auth.users. Se normaliza al mismo AuthApiError que ya se propagaba
    # cuando "Confirm email" estaba desactivado, para no cambiar el
    # contrato de cara a quien llama.
    if not response.user.identities:
        raise AuthApiError(
            "User already registered", status=400, code="user_already_exists"
        )

    user_id = response.user.id
    get_or_create_profile(user_id, role)
    return {"user_id": user_id, "role": role, "session": response.session}


def login(email: str, password: str) -> dict:
    """Inicia sesión en Supabase Auth y devuelve la sesión junto al role.

    Deja que AuthApiError se propague tal cual (p.ej. credenciales inválidas).
    """
    client = get_supabase_client(use_service_key=False)
    response = client.auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    profile = get_profile(response.session.user.id)
    return {"session": response.session, "role": profile["role"]}


def request_password_reset(email: str) -> None:
    """Dispara el email de recuperación de contraseña (D-040).

    reset_password_for_email no revela si el email tiene cuenta o no —
    comportamiento de fábrica de Supabase (previene enumeración), no hace
    falta lógica propia para ocultar el resultado.
    """
    client = get_supabase_client(use_service_key=False)
    client.auth.reset_password_for_email(email)


def verify_token(token_hash: str, type: str):
    """Verifica un token_hash de confirmación de signup o recuperación (D-040).

    Deja que AuthApiError se propague tal cual (token inválido, caducado o
    ya usado). Devuelve la AuthResponse completa (incluye session).
    """
    client = get_supabase_client(use_service_key=False)
    return client.auth.verify_otp({"token_hash": token_hash, "type": type})


def set_new_password(access_token: str, refresh_token: str, new_password: str) -> None:
    """Fija una nueva contraseña usando la sesión obtenida de verify_token() (D-040)."""
    client = get_supabase_client(use_service_key=False)
    client.auth.set_session(access_token, refresh_token)
    client.auth.update_user({"password": new_password})


def get_user_metadata(user_id: str) -> dict:
    """Devuelve el user_metadata de user_id (Admin API)."""
    client = get_supabase_client(use_service_key=True)
    user = client.auth.admin.get_user_by_id(user_id)
    return user.user.user_metadata or {}


def update_user_metadata(user_id: str, data: dict) -> dict:
    """Actualiza el user_metadata de user_id mergeando con el existente.

    update_user_by_id sobrescribe user_metadata por completo (no lo mergea
    Supabase) — se lee el valor actual y se combina con `data` antes de
    escribir, para no perder claves ya guardadas (p.ej. full_name).
    """
    client = get_supabase_client(use_service_key=True)
    merged = {**get_user_metadata(user_id), **data}
    updated = client.auth.admin.update_user_by_id(user_id, {"user_metadata": merged})
    return updated.user.user_metadata or {}


def _find_user_by_email(client: Client, email: str):
    """Busca un usuario por email vía Admin API paginada.

    Sin get_user_by_email en la Admin API (verificado contra
    supabase_auth/_sync/gotrue_admin_api.py) — list_users() pagina de 200 en
    200 filtrando por email en memoria. Suficiente a la escala del TFM;
    documentado como coste a revisar si el proyecto creciera.
    """
    page = 1
    while True:
        users = client.auth.admin.list_users(page=page, per_page=200)
        if not users:
            raise LookupError(f"No existe usuario con email={email}")
        match = next((u for u in users if u.email == email), None)
        if match:
            return match
        page += 1


def get_or_create_google_user(email: str, full_name: str | None, role: str) -> dict:
    """Obtiene o crea el usuario y perfil de Supabase Auth para un login de Google.

    create_user() primero; si el email ya existe (AuthApiError), cae a
    _find_user_by_email(). El nombre de Google se guarda en
    user_metadata.full_name solo en el primer login, y solo si no está ya
    presente — nunca se pregunta por chat para cuentas de Google (D-040).
    """
    client = get_supabase_client(use_service_key=True)
    try:
        created = client.auth.admin.create_user(
            {
                "email": email,
                "email_confirm": True,
                "user_metadata": {"full_name": full_name} if full_name else {},
            }
        )
        user = created.user
    except AuthApiError:
        user = _find_user_by_email(client, email)
        if full_name and not (user.user_metadata or {}).get("full_name"):
            update_user_metadata(user.id, {"full_name": full_name})

    get_or_create_profile(user.id, role)
    return {"user_id": user.id}
