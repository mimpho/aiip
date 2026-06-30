# Plan — E-03 T-04 Login con Google OAuth, rol fijo por app

## Contexto técnico

### SDK Supabase Python (sync)

`client.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": ...}}) -> OAuthResponse`
- `.url` — URL de redirección hacia Google (accounts.google.com)
- No devuelve sesión directamente: el usuario completa el flujo en el browser y Supabase hace el callback a su propio endpoint (`/auth/v1/callback`)
- El browser redirect y el callback son responsabilidad de Supabase Auth — no se testean con pytest (requerirían e2e con Playwright)

### Decisión de arquitectura (D-014)

Supabase es el único broker OAuth. Chainlit **nunca** usa `@cl.oauth_callback` nativo.
El flujo es: Chainlit llama a `sign_in_with_oauth` → usuario completa en browser → Supabase callback → sesión disponible en Supabase Auth.

### Qué se testea en esta tarea

1. **Que `sign_in_with_oauth` funciona contra Supabase real** y devuelve una URL válida hacia Google — verifica que el provider OAuth está habilitado en el proyecto Supabase de T-01.
2. **Que `get_or_create_profile` asigna APP_ROLE correctamente** cuando Supabase crea el usuario vía OAuth — simulando el `user_id` que Supabase generaría (usando `admin_client` para crear el usuario, exactamente igual que T-02/T-03).

`get_or_create_profile` ya está implementada en T-02/T-03. El origen del usuario (email/password vs OAuth) es irrelevante para esta función — T-04 solo añade el escenario de que el caller es el flujo OAuth, no `signup`.

### Patrón de tests (mismo que T-02/T-03)

- Integración real contra Supabase, sin mocks.
- `conftest.py` ya tiene `admin_client` y `user_without_profile` — reutilizar sin modificar.
- Email de prueba: `f"e03t04-{uuid.uuid4().hex[:12]}@example.com"` para distinguirlos.
- Cleanup automático via `admin_client.auth.admin.delete_user(user_id)`.

---

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `auth/supabase_client.py` | modificar | Añadir función `sign_in_with_oauth` |
| `tests/step_defs/test_e03_t04.py` | crear | Step definitions pytest-bdd para T-04 |

`tests/conftest.py` y `tests/features/e03_t04_google_oauth.feature` — solo lectura.

---

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo → verde antes de pasar al siguiente.

### 1. sign_in_with_oauth devuelve una URL de redirección hacia Google

- Feature: Scenario 1
- Step definitions: `tests/step_defs/test_e03_t04.py`
- Implementación: añadir `sign_in_with_oauth(redirect_to=None)` en `auth/supabase_client.py`

Notas:
- Usa `get_supabase_client(use_service_key=False)` — es una operación pública.
- Flujo: `client.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": redirect_to}})` → devolver `response.url`.
- El test verifica que `response.url` empieza por `"https://accounts.google.com"` — si el provider no está habilitado en Supabase, la llamada fallará aquí.
- `redirect_to` puede ser `None` en el test (Supabase usará el redirect configurado por defecto).

### 2. Primer login OAuth crea perfil con el rol de la app (familiar)

- Feature: Scenario 2
- Step definitions: nuevo step `Given un user_id de prueba sin perfil en la tabla profiles`
- Implementación: ninguna adicional — `get_or_create_profile` ya existe

Notas:
- Usar `_create_auth_user(admin_client)` de `conftest.py` para generar el `user_id` (mismo patrón que T-02).
- El step `When llamo a get_or_create_profile con ese user_id y APP_ROLE "familiar"` es reutilizable del feature de T-02 — pero aquí va en el contexto de que el usuario habría llegado vía OAuth.
- Cleanup: eliminar el usuario al final del test con `admin_client.auth.admin.delete_user`.

### 3. Login OAuth repetido no duplica ni sobreescribe el perfil

- Feature: Scenario 3
- Step definitions: nuevo step `Given un user_id de prueba con perfil existente y role "familiar"`
- Implementación: ninguna — `get_or_create_profile` ya es idempotente (verificado en T-02)

Notas:
- Usar fixture `test_user` de `conftest.py` (ya crea usuario + perfil con role familiar).
- Verificar que hay exactamente una fila en `profiles` después de la segunda llamada.

### 4. Login OAuth desde la app profesional crea perfil con rol profesional

- Feature: Scenario 4
- Step definitions: reutilizar steps del Scenario 2 — solo cambia el valor de APP_ROLE
- Implementación: ninguna adicional

Notas:
- Mismo patrón que Scenario 2 con `APP_ROLE = "profesional"`.
- Usar `monkeypatch.setenv("APP_ROLE", "profesional")` en el step Given.

---

## Restricciones a respetar

- **D-014:** `sign_in_with_oauth` usa `get_supabase_client()` de `auth/supabase_client.py`. Chainlit nunca llama al OAuth nativo — eso lo gestiona esta función.
- **D-010 (Agnóstico de proveedor):** el provider `"google"` se pasa como parámetro, no hardcodeado en la lógica de negocio.
- **AGENTS.md:** credenciales OAuth (Client ID/Secret de Google) están en Supabase Auth > Providers, nunca en `.env` del repo ni en código. No confundir con `GOOGLE_API_KEY` (Gemini).

---

## Lo que queda fuera de esta tarea

- El browser redirect y el callback de Supabase → responsabilidad de Supabase Auth
- Tests e2e del flujo OAuth completo (browser redirect → callback → sesión de Chainlit) → T-05, cuando el botón "Continuar con Google" ya existe en la UI y hay una URL de callback accesible
- Integración del flujo OAuth con Chainlit (el botón "Continuar con Google") → T-05
- Gestión de `redirect_to` por entorno (dev/prod) → T-05 o T-06
