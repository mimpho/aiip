# Plan — E-03 T-03 Registro y login con email/password, rol fijo por app

## Contexto técnico

### SDK Supabase Python (sync)

`client.auth.sign_up({"email": ..., "password": ...}) -> AuthResponse`
- `.user.id` — UUID del usuario creado
- `.user.email` — email confirmado
- Si el email ya existe, lanza `AuthApiError` (status 400, message contiene "already registered")

`client.auth.sign_in_with_password({"email": ..., "password": ...}) -> AuthResponse`
- `.session.access_token` — JWT de sesión
- `.session.user.id` — UUID del usuario
- Si las credenciales son incorrectas, lanza `AuthApiError` (status 400, message contiene "Invalid login credentials")

### Patrón de tests de integración (ya establecido en T-02)

- `conftest.py` ya tiene `admin_client`, `_create_auth_user`, `TEST_PASSWORD` y fixtures con cleanup automático via `admin_client.auth.admin.delete_user(user_id)`.
- Los tests de T-03 reutilizan `conftest.py` — no duplicar fixtures.
- Email de prueba: `f"e03t03-{uuid.uuid4().hex[:12]}@example.com"` para distinguirlos de los de T-02.

### APP_ROLE

Variable de entorno por instancia de app: `"familiar"` o `"profesional"`. Se lee en `signup` via `os.environ["APP_ROLE"]`. No tiene valor por defecto — si no está definida, debe fallar explícitamente (error de configuración, no de lógica de negocio).

### get_or_create_profile

Ya implementada en `auth/supabase_client.py` (T-02). `signup` la llama tras el sign_up exitoso para crear el perfil con el rol correcto. `login` la llama también: garantiza que existe perfil aunque el usuario se hubiera creado por otro medio (p.ej. admin).

---

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `auth/supabase_client.py` | modificar | Añadir funciones `signup` y `login` |
| `tests/step_defs/test_e03_t03.py` | crear | Step definitions pytest-bdd para T-03 |

`tests/conftest.py` — solo lectura, reutilizar fixtures existentes sin modificar.

---

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo → verde antes de pasar al siguiente.

### 1. Registro desde la app familiar crea perfil con rol familiar

- Feature: `tests/features/e03_t03_email_auth.feature` — Scenario 1
- Step definitions: `tests/step_defs/test_e03_t03.py`
- Implementación: añadir `signup(email, password, role)` en `auth/supabase_client.py`

Notas:
- `signup` recibe `role` como parámetro (no lee `APP_ROLE` directamente — eso lo hace el caller, en este caso el step def que lo lee de la variable de entorno).
- Flujo: `client.auth.sign_up({"email": email, "password": password})` → extraer `user.id` → llamar `get_or_create_profile(user_id, role)` → devolver `{"user_id": user.id, "role": role}`.
- Usar `get_supabase_client(use_service_key=False)` para el sign_up (operación pública). `get_or_create_profile` ya usa service key internamente.
- Cleanup en el step def: registrar el `user_id` creado y eliminarlo con `admin_client.auth.admin.delete_user` al finalizar (fixture de pytest o `yield`).

### 2. Registro desde la app profesional crea perfil con rol profesional

- Feature: Scenario 2 (mismo fichero)
- Step definitions: reutilizar steps del Scenario 1 — solo cambia el valor de `APP_ROLE`
- Implementación: ninguna adicional si `signup` ya recibe `role` como parámetro

Notas: el step `Given APP_ROLE es "profesional"` simplemente setea la variable de entorno para ese test. Usar `monkeypatch.setenv` de pytest.

### 3. Registro con email ya existente eleva un error claro

- Feature: Scenario 3
- Step definitions: nuevo step `Given un usuario ya registrado con el email de prueba` + `Then se eleva una excepción con mensaje que indica email duplicado`
- Implementación: `signup` debe dejar que `AuthApiError` se propague (no capturar genéricamente). Opcionalmente: re-lanzar como excepción propia del dominio (`AuthError`) para desacoplar del SDK — **no hacerlo en T-03**, es sobreingeniería prematura.

Notas: pytest-bdd captura excepciones con `pytest.raises` en el step `Then`. El step `And no se crea un perfil duplicado en profiles` verifica via `admin_client.table("profiles").select("*").eq("id", user_id).execute()` que hay exactamente una fila.

### 4. Login con credenciales correctas devuelve sesión y rol

- Feature: Scenario 4
- Step definitions: nuevo step `Given un usuario registrado con el email de prueba y role "familiar"`
- Implementación: añadir `login(email, password)` en `auth/supabase_client.py`

Notas:
- Reutilizar fixture `_create_auth_user` de `conftest.py` para el Given (crear usuario con `email_confirm: True`).
- `login` flujo: `client.auth.sign_in_with_password({"email": email, "password": password})` → extraer `session` → llamar `get_or_create_profile(user_id, role=None)` — pero `get_or_create_profile` necesita un `role` para el caso de creación. **Decisión:** `login` llama a `get_or_create_profile` solo para recuperar el perfil existente, no para crearlo. Si no existe, es un estado inconsistente — elevar error. Implementar `get_profile(user_id)` como helper privado o extender `get_or_create_profile` con `role=None` que falle si no existe perfil.
- Devolver `{"session": response.session, "role": profile["role"]}`.

### 5. Login con credenciales incorrectas eleva un error claro

- Feature: Scenario 5
- Step definitions: reutilizar el step `When llamo a login` — solo cambia la contraseña
- Implementación: `login` deja que `AuthApiError` se propague

Notas: no es necesario crear usuario para este scenario — se puede llamar directamente con email/contraseña incorrectos sobre cualquier email.

---

## Restricciones a respetar

- **D-010 (Agnóstico de proveedor):** `signup` y `login` usan `get_supabase_client()` de `auth/supabase_client.py`, nunca importan el SDK de Supabase directamente en otros módulos.
- **D-009 (Privacy by design):** `signup` no almacena ningún dato adicional más allá de `id` y `role` en `profiles`.
- **AGENTS.md:** modelo y configuración siempre en `.env`, nunca hardcodeados. `APP_ROLE` es una variable de entorno.

---

## Lo que queda fuera de esta tarea

- Reset / recuperación de contraseña → T-05 (cuando haya UI en Chainlit)
- Cambio de contraseña desde dentro de la app → backlog/ideas.md
- Integración de `signup`/`login` con Chainlit (`password_auth_callback`) → T-05
- Login con Google OAuth → T-04
- Validación de formato de email o política de contraseña → Supabase lo gestiona, no es lógica nuestra
