# Plan — E-05 T-06 UI de autenticación en Chainlit: login, signup, recuperación de contraseña y Google

## Contexto técnico

### Chainlit — formulario de login fijo, sin signup ni mensajes custom nativos

Verificado contra `docs.chainlit.io/authentication/password`, `.venv/.../chainlit` y
`.chainlit/translations/es.json` (chainlit==2.11.1): `password_auth_callback(username, password)`
solo recibe esos dos campos y devuelve `cl.User | None`. No hay canal para mensajes de error
custom, ni campo de confirmación de contraseña, ni enlace de "olvidé mi contraseña" nativo. De
ahí el diseño mergeado de D-040 y las rutas propias.

### Rutas propias sobre la misma app de Chainlit, sin `mount_chainlit()`

`chainlit/cli/__init__.py::run_chainlit()` hace `from chainlit.server import app` y luego
`load_module(target)` (importa `main_family.py`) **antes** de arrancar uvicorn sobre esa misma
`app`. Por tanto, `main_family.py` puede hacer `from chainlit.server import app` y registrar
`@app.get(...)`/`@app.post(...)` a nivel de módulo — se registran en el import, antes de que
uvicorn sirva. No hace falta `mount_chainlit()`, no cambia el comando de arranque de D-039, no
hay prefijo de path nuevo que revisar en Google Console/Supabase.

### `oauth_callback` — firma exacta

```python
@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_app_user: cl.User,
    id_token: Optional[str],
) -> Optional[cl.User]:
```
(`chainlit/callbacks.py:107`). Para Google, `raw_user_data` es la respuesta estándar de
`userinfo` de Google (`email`, `name`, `given_name`, `picture`, `email_verified`, ...).
`default_app_user` es un `cl.User` que Chainlit ya construye con valores por defecto — no es
obligatorio usarlo, se puede devolver uno propio.

Variables de entorno del provider (`chainlit/oauth_providers.py:120-122`):
`OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET` — nombres fijos de Chainlit, no elegibles.

### Supabase — verify_otp server-side, sin JS

Patrón oficial (`supabase.com/docs/guides/auth/auth-email-templates`, sección "Redirecting the
user to a server-side endpoint"): la plantilla de email enlaza a
`{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=signup|recovery` en vez del
`{{ .ConfirmationURL }}` por defecto. La ruta propia lee `token_hash`/`type` de la query string
(no del fragmento de URL, no requiere JS) y llama a `verify_otp({token_hash, type})`
(`supabase_auth/_sync/gotrue_client.py:612`), que devuelve una `AuthResponse` con sesión.

**Paso manual de Marcos, bloqueante para probar el flujo real:** reescribir en el dashboard de
Supabase (Auth > Email Templates) las plantillas "Confirm signup" y "Reset password" con esa
URL. Sin esto, los tests de wiring (que mockean `verify_otp`) funcionan igual, pero el flujo
real con un correo de verdad no.

`reset_password_for_email(email)` (`gotrue_client.py:820`) no revela si el email existe —
Supabase ya lo diseña así por seguridad (previene enumeración). No hay que añadir lógica propia
para ocultar el resultado, el comportamiento ya es uniforme de fábrica.

### Admin API — sin `get_user_by_email`

`supabase_auth/_sync/gotrue_admin_api.py` no tiene `get_user_by_email`. Solo `create_user`,
`list_users(page, per_page)` (paginado, sin filtro), `get_user_by_id`, `update_user_by_id`. Para
el signup vía Google (get-or-create por email): `create_user()` primero; si Supabase responde
que el email ya existe, caer a `list_users()` paginado filtrando por email. Suficiente a la
escala del TFM (no hay miles de usuarios), documentar el coste si el proyecto creciera.

### Jinja2 ya está en `requirements.txt`

`Jinja2==3.1.6` ya está pinneado (no es una dependencia nueva). FastAPI trae
`fastapi.templating.Jinja2Templates` de serie (Starlette). Las tres pantallas propias
(`/auth/forgot-password`, `/auth/confirm` signup, `/auth/confirm` recovery) se sirven con
`Jinja2Templates` sobre una plantilla base compartida (D-040 punto 8: componentes reutilizables,
sin estilos en línea) — layout con tarjeta, macro de campo de formulario (label + input + slot
de error), macro de botón. CSS propio en `design/public/auth-pages.css`, usando los tokens de
`design/public/tokens.css` (ya servido en `/public/...` vía el symlink de D-039, sin ruta nueva
que montar).

### `signup()` actual no expone si hay sesión

`auth/supabase_client.py::signup()` (E-03 T-03) devuelve `{"user_id":..., "role":...}`, sin
`response.session`. Con "Confirm email" activado, `response.session` es `None` hasta que el
usuario confirma. Hay que ampliar `signup()` para incluir `"session": response.session` en el
retorno, así `password_auth_callback` puede decidir si autentica ya o no.

---

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `auth/supabase_client.py` | modificar | `signup()` devuelve también `session`; nuevas funciones: `request_password_reset(email)`, `verify_token(token_hash, type)`, `set_new_password(access_token, refresh_token, new_password)`, `get_or_create_google_user(email, user_metadata)`, `get_user_metadata(user_id)`, `update_user_metadata(user_id, data)` |
| `chainlit/main_family.py` | modificar | `password_auth_callback` mergeado login/signup; `oauth_callback` nuevo; rutas `/auth/forgot-password` y `/auth/confirm` sobre `from chainlit.server import app`; `on_chat_start` pide el nombre si falta; `_greeting()` usa `full_name`, sin fallback a email |
| `chainlit/family/templates/auth_base.html` | crear | Layout base Jinja2 (tarjeta, macros de campo de formulario y botón) para las 3 pantallas propias |
| `chainlit/family/templates/forgot_password.html` | crear | Formulario de solicitud de recuperación |
| `chainlit/family/templates/confirm.html` | crear | Cubre las 3 variantes de resultado: token inválido, signup confirmado, formulario de nueva contraseña — vía condicionales, un único fichero |
| `design/public/auth-pages.css` | crear | CSS de las 3 pantallas propias, sin estilos en línea, tokens de `tokens.css` |
| `design/public/auth.js` | crear | `custom_js`: inyecta el enlace "¿Olvidaste tu contraseña?" en el login nativo de Chainlit |
| `design/public/style.css` | modificar | Selectores reales de la pantalla de login de Chainlit (verificados con devtools en Antigravity, mismo patrón D-038) |
| `chainlit/family/.chainlit/config.toml` | modificar | Añadir `custom_js = "/public/auth.js"` |
| `design/auth/style.css` | eliminar | Retirado (D-031/D-040 — sin selectores reutilizables, Chainlit no usa el widget de Supabase Auth UI) |
| `.env.example` | modificar | Añadir `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET` |
| `tests/step_defs/test_e05_t06.py` | crear | Step definitions pytest-bdd (solo los escenarios TDD, no el checklist manual) |

`tests/conftest.py` — reutilizar fixtures existentes (`admin_client`, `_create_auth_user`,
`TEST_PASSWORD`); si hace falta un usuario sin confirmar para el Scenario de "Confirm email
activado", crear un fixture nuevo con `email_confirm: False` (opuesto al patrón habitual de
`True`), documentando por qué es la excepción.

---

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo → verde antes de pasar al siguiente.

### 1. Login con credenciales correctas autentica sin intentar signup

- Feature: Scenario "Login con credenciales correctas de una cuenta existente autentica"
- Implementación: reescribir `password_auth_callback` en `main_family.py` — intenta `login()`,
  si tiene éxito devuelve `cl.User` directamente sin más.

### 2. Email sin cuenta previa dispara signup automático

- Feature: Scenario "Credenciales de un email sin cuenta previa disparan signup automático"
- Implementación: `password_auth_callback` — si `login()` lanza `AuthApiError`, intenta
  `signup()` con las mismas credenciales y `role=APP_ROLE`.

### 3. Signup con "Confirm email" activado no autentica hasta confirmar

- Feature: Scenario correspondiente
- Implementación: `signup()` en `auth/supabase_client.py` amplía su retorno con `session`. Si
  `session` es `None`, `password_auth_callback` devuelve `None` (Chainlit muestra su mensaje
  genérico ya en español).

### 4. Email ya registrado con contraseña incorrecta no duplica perfil

- Feature: Scenario correspondiente
- Implementación: `signup()` de respaldo lanza `AuthApiError` (email duplicado) →
  `password_auth_callback` la captura y devuelve `None`.

### 5. Solicitar recuperación — con y sin cuenta responde igual

- Feature: los dos scenarios de `/auth/forgot-password`
- Implementación: `request_password_reset(email)` en `auth/supabase_client.py` (wrapper de
  `reset_password_for_email`). Ruta `GET/POST /auth/forgot-password` en `main_family.py` sobre
  `app` de `chainlit.server`, usando `forgot_password.html`. Aquí se construyen también
  `auth_base.html` y `auth-pages.css` (primera pantalla propia).

### 6. Confirmar token de recuperación válido muestra el formulario de nueva contraseña

- Feature: Scenario correspondiente
- Implementación: `verify_token(token_hash, type)` (wrapper de `verify_otp`). Ruta
  `GET /auth/confirm?token_hash=...&type=recovery` → `confirm.html` rama "nueva contraseña".

### 7. Enviar la nueva contraseña la actualiza

- Feature: Scenario correspondiente
- Implementación: `set_new_password(access_token, refresh_token, new_password)` (establece la
  sesión obtenida de `verify_otp` en un cliente y llama a `update_user`). Ruta
  `POST /auth/confirm` (rama recovery).

### 8. Confirmar token de signup válido activa la cuenta

- Feature: Scenario correspondiente
- Implementación: mismo `GET /auth/confirm` con `type=signup` → rama "cuenta confirmada" de
  `confirm.html`, enlace a `/login`. Reutiliza `verify_token()` del paso 6, sin lógica nueva.

### 9. Token inválido o caducado no autentica

- Feature: Scenario correspondiente
- Implementación: `verify_token()` deja propagar `AuthApiError` → la ruta la captura y renderiza
  `confirm.html` rama "error", sin exponer el mensaje interno de Supabase.

### 10. Login con Google crea/obtiene usuario y perfil

- Feature: Scenario "Login con Google vía oauth_callback nativo de Chainlit"
- Implementación: `get_or_create_google_user(email, user_metadata)` en `auth/supabase_client.py`
  — `create_user()`; si ya existe, `list_users()` paginado filtrando por email; después
  `get_or_create_profile(user_id, role=APP_ROLE)`. `oauth_callback` en `main_family.py` la
  invoca con los datos de `raw_user_data` y devuelve `cl.User`.

### 11. Segundo login con Google no duplica

- Feature: Scenario correspondiente
- Implementación: ninguna adicional — `get_or_create_google_user`/`get_or_create_profile` ya son
  idempotentes (mismo patrón verificado en E-03 T-04).

### 12. Primer login con Google guarda el nombre sin preguntar

- Feature: Scenario correspondiente
- Implementación: `get_or_create_google_user` escribe `raw_user_data.get("name")` en
  `user_metadata.full_name` (vía `update_user_by_id`) solo si `full_name` no está ya presente.

### 13. Primer login sin nombre lo pide en el chat

- Feature: Scenario correspondiente
- Implementación: `get_user_metadata(user_id)` / `update_user_metadata(user_id, data)`
  (wrappers de `update_user_by_id`/lectura del user). `on_chat_start` en `main_family.py`: antes
  del saludo, si `full_name` no está en los metadatos del usuario autenticado, pregunta con
  `cl.AskUserMessage` y guarda la respuesta. `user_id` viaja en `cl.User.metadata` desde
  `password_auth_callback`/`oauth_callback` (login() expone `session.user.id`).

### 14. Login posterior con nombre ya guardado no repregunta

- Feature: Scenario correspondiente
- Implementación: ninguna adicional — mismo chequeo del paso 13 ya cubre este caso.

### 15. Saludo sin nombre no usa el email

- Feature: Scenario correspondiente
- Implementación: `_greeting()` — si no hay `full_name`, saludo genérico sin nombre, sin caer a
  `identifier`.

### 16. Cancelar Google no crea usuario ni perfil (checklist manual)

- No automatizable — `oauth_callback` de Chainlit ni siquiera se invoca si el usuario cancela en
  la pantalla de consentimiento de Google. Verificar manualmente en T-07.

### Resto del checklist manual (sin implementación de código nueva, solo verificación)

Botón de Google visible, enlace de recuperación visible (requiere el `auth.js` del paso 5),
correos reales de confirmación/recuperación llegando y funcionando, coherencia visual entre las
3 pantallas propias y el login nativo (requiere `style.css` del login, verificado con devtools
igual que D-038), retirada de `design/auth/style.css`. Todo esto se verifica en Antigravity /
T-07, no con pytest.

---

## Restricciones a respetar

- **D-009 (privacy by design):** el formulario de signup no puede llevar consentimiento
  informado específico (limitación del formulario único de Chainlit, ya documentada como deuda
  en D-040) — no intentar forzarlo con JS ni añadir campos que Chainlit no soporta.
- **D-040 punto 8 (frontend):** las 3 pantallas propias comparten `auth_base.html` y
  `auth-pages.css`, sin estilos en línea. El login nativo de Chainlit solo se toca vía
  `design/public/style.css` (no hay componentización posible ahí).
- **D-039:** no cambiar el comando de arranque (`CHAINLIT_APP_ROOT=chainlit/family ... chainlit
  run chainlit/main_family.py`). Las rutas nuevas cuelgan de `from chainlit.server import app`,
  no de `mount_chainlit()`.
- **AGENTS.md:** credenciales de Google (Client ID/Secret) van en `.env`, nunca hardcodeadas;
  reutilizan el mismo proyecto de Google Cloud que Supabase (D-014), solo añaden un redirect URI
  nuevo — paso manual de Marcos en Google Cloud Console.
- **Service key vs anon key:** `create_user`, `list_users`, `update_user_by_id` (Admin API) usan
  siempre `get_supabase_client(use_service_key=True)`, nunca expuesta a una request de usuario
  directamente — mismo patrón que `get_or_create_profile`.

---

## Lo que queda fuera de esta tarea

- Consentimiento informado específico de datos de salud (D-009) — deuda documentada en D-040,
  no resoluble con el formulario único de Chainlit; revisar si algún día se aborda con una
  superficie propia (reabriría D-031).
- Migrar `full_name` de `user_metadata` a un esquema de perfil propio — E-08 (memoria de
  perfil), ya anotado en `backlog/epics.md`.
- Perfil profesional (`main_professional.py`) — sigue siendo el stub bloqueado, sin tocar.
- Rate limiting/CAPTCHA propios en signup o recuperación — Supabase ya aplica límites por
  defecto (`docs/guides/auth/rate-limits`), no se añade lógica propia en esta tarea.
- Verificación end-to-end real (Google OAuth completo en navegador, correos de confirmación y
  recuperación llegando de verdad, plantillas de Supabase reescritas) — T-07, smoke test manual.
- Cambio de contraseña estando ya autenticado dentro del chat (distinto de "olvidé mi
  contraseña") — no está en el alcance, backlog/ideas.md si se quiere en el futuro.
