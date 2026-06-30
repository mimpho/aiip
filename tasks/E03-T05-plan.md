# Plan — E-03 T-05 Integración de autenticación en Chainlit

## Contexto técnico

### API de Chainlit: password_auth_callback

```python
@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    ...
```

- Recibe `username` (email) y `password` como strings.
- Retornar `cl.User` → autenticación OK.
- Retornar `None` → Chainlit rechaza el acceso.
- `cl.User(identifier=..., metadata={...})` — `identifier` es el string que Chainlit usa como ID de sesión.

### Por qué Google OAuth queda fuera de esta tarea

El flujo OAuth con D-014 es 100% browser→Supabase. No hay hook Python en Chainlit que lo intercepte. `sign_in_with_oauth()` ya existe en `supabase_client.py` y está testeada en T-04. No hay código nuevo de OAuth en T-05.

### Estrategia de tests

Tests unitarios con mock de `login()` de `auth/supabase_client.py`. No se levanta Chainlit ni se conecta a Supabase real. El `password_auth_callback` es una función Python ordinaria — se puede llamar directamente en el test sin necesidad de un servidor Chainlit.

Razón: `login()` ya está testeada contra Supabase real en T-03. En T-05 solo se testea que `password_auth_callback` orquesta correctamente: llama a `login()`, construye `cl.User` con los datos correctos y retorna `None` ante error.

---

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `main_familiar.py` | crear | Entrypoint Chainlit perfil familiar con `@cl.password_auth_callback` y `@cl.on_chat_start` mínimo |
| `tests/step_defs/test_e03_t05.py` | crear | Step definitions pytest-bdd para T-05 |

`tests/features/e03_t05_chainlit_auth.feature` — ya creado en Cowork, solo lectura.
`auth/supabase_client.py` — sin cambios.
`tests/conftest.py` — sin cambios.

---

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

### 1. Login con credenciales válidas devuelve cl.User con role

- Feature: Scenario 1 (`Login con credenciales válidas devuelve cl.User con role`)
- Step definitions: `tests/step_defs/test_e03_t05.py`
- Implementación: `main_familiar.py` — función `auth_callback` con `@cl.password_auth_callback`

Notas de implementación:
- El step `Given login() devuelve una sesión válida con role "familiar"` hace `monkeypatch` de `main_familiar.auth_callback.__wrapped__` o mejor: parchea `auth.supabase_client.login` con `mocker.patch` — la función `auth_callback` importará `login` desde `auth.supabase_client`.
- El mock de `login()` debe devolver `{"session": MagicMock(user=MagicMock(email="user@example.com")), "role": "familiar"}`.
- El test llama directamente a `auth_callback("user@example.com", "cualquier-pass")` — no hace falta un servidor Chainlit.
- Assert: el retorno es instancia de `cl.User`, con `identifier == "user@example.com"` y `metadata["role"] == "familiar"`.

Estructura de `main_familiar.py`:
```bash
git checkout epic/E03-auth
git pull origin epic/E03-auth
git checkout -b task/E03-T05-chainlit-auth
```

```python
import os
import chainlit as cl
from auth.supabase_client import login
from supabase_auth.errors import AuthApiError

APP_ROLE = os.environ.get("APP_ROLE", "familiar")

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    try:
        result = login(username, password)
        return cl.User(
            identifier=username,
            metadata={"role": result["role"], "provider": "credentials"},
        )
    except AuthApiError:
        return None

@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    role = user.metadata.get("role") if user else "unknown"
    # El role estará disponible para E-04 via cl.user_session.get("user").metadata["role"]
    await cl.Message(content=f"Sesión iniciada. Perfil: {role}").send()
```

### 2. Login con credenciales inválidas devuelve None

- Feature: Scenario 2 (`Login con credenciales inválidas devuelve None`)
- Step definitions: añadir steps en `tests/step_defs/test_e03_t05.py`
- Implementación: el bloque `except AuthApiError` de `auth_callback` ya lo cubre

Notas:
- El mock de `login()` debe elevar `AuthApiError` (importar desde `supabase_auth.errors`).
- Assert: el retorno de `auth_callback(...)` es `None`.

---

## Restricciones a respetar

- **D-010 (Agnóstico de proveedor):** `APP_ROLE` viene de variable de entorno, nunca hardcodeado.
- **D-014:** `auth_callback` llama a `login()` de `supabase_client.py`. Nunca implementar lógica de autenticación directamente en `main_familiar.py`.
- **AGENTS.md:** `main_familiar.py` es el entrypoint sobre el que T-06 clonará `main_profesional.py`. No añadir lógica de separación de perfiles aquí — eso es T-06.

## Lo que queda fuera de esta tarea

- Botón "Continuar con Google" en la UI de Chainlit → T-06 o E-05.
- Gestión de `redirect_to` por entorno → T-06.
- `main_profesional.py` → T-06.
- Theming visual del formulario de login → E-05.
- Lógica del pipeline RAG en `on_chat_start` → E-04.
