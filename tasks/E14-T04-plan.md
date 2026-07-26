# Plan — E-14 T-04 Migración de `full_name`/`user_name` a `profiles` + `display_name` en `cl.User`

## Contexto técnico

`profiles.user_name` ya existe (migración T-01, `20260723002559_e14_t01_add_profile_onboarding_columns.sql`,
D-088) — sin migración SQL nueva en esta tarea.

`cl.User` (`chainlit/user.py`, verificado en `.venv`) acepta `display_name: Optional[str]` como
segundo campo posicional/keyword, junto a `identifier` y `metadata`. Hoy ninguno de los tres
`cl.User(...)` de `main_family.py` (password login, password signup, oauth) lo rellena — cae al
fallback nativo de Chainlit (`identifier`, el email).

Diseño acordado en `task-start` (D-091, revisión Q1/Q2 con Marcos):
- Una única función seguirá escribiendo `profiles.user_name` de forma duradera: `_ensure_full_name()`
  en `on_chat_start` (ya existía, se reescribe en esta tarea). Los callbacks de login **no** escriben
  `profiles`, solo leen con fallback para fijar `display_name` en el momento de construir `cl.User`.
- Excepción: alta de cuenta Google nueva. `get_or_create_google_user()` sí escribe
  `profiles.user_name` en el momento de creación (aparte de `_ensure_full_name`), porque
  `raw_user_data` ya trae el nombre real en ese instante — evita depender de que se abra un chat
  para que el desplegable salga bien desde el primer login.
- La clave de sesión `user.metadata["full_name"]` (usada hoy por `_greeting`,
  `_onboarding_complete_title`, `_ensure_patient_profile`) no cambia de nombre — sigue
  poblándose igual, solo cambia de dónde se lee/escribe el valor duradero (D-089).

Sin hallazgos adicionales de librería más allá de lo anterior.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `auth/supabase_client.py` | modificar | `get_or_create_google_user()`: escribe `profiles.user_name` en la creación (y solo si viene vacío en el camino de usuario ya existente vía `_find_user_by_email`), reutilizando el `profile` que ya devuelve `get_or_create_profile()`. |
| `chainlit/main_family.py` | modificar | Nueva función `_resolve_display_name(user_id)` (lectura con fallback a `user_metadata.full_name` cuando `profiles.user_name` está vacío, sin escribir nada). Se llama desde `auth_callback()` (login y signup) y `oauth_callback()` para fijar `cl.User(display_name=...)`. `_ensure_full_name()` se reescribe para leer/escribir `profiles.user_name` en vez de `user_metadata.full_name` (con backfill desde `user_metadata` si `profiles.user_name` está vacío y `user_metadata.full_name` no). |
| `tests/step_defs/test_e14_t04.py` | crear | Step definitions pytest-bdd para los 7 escenarios de `e14_t04_username_migration.feature`, mismo patrón de fake `chainlit`/`auth.supabase_client` que `test_e14_t02.py`/`test_e14_t03.py`. |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Usuario existente con full_name en user_metadata recibe backfill a profiles** —
   `tests/features/e14_t04_username_migration.feature` (Scenario 1)
   - Step definitions en: `tests/step_defs/test_e14_t04.py`
   - Implementación en: `chainlit/main_family.py::_ensure_full_name()`
   - Notas: reescribir para que el orden de lectura sea `get_profile(user_id).get("user_name")` →
     si vacío, `get_user_metadata(user_id).get("full_name")` (backfill: si hay valor, escribir con
     `update_profile(user_id, {"user_name": full_name})` y cachear en `user.metadata["full_name"]`,
     sin preguntar por chat) → si ambos vacíos, pasar al escenario 2.

2. **Usuario nuevo sin nombre guardado lo pide y lo escribe directamente en profiles** —
   Scenario 2
   - Step definitions en: `tests/step_defs/test_e14_t04.py`
   - Implementación en: `chainlit/main_family.py::_ensure_full_name()`
   - Notas: la rama de `cl.AskUserMessage` deja de llamar a `update_user_metadata()` — pasa a
     `update_profile(user_id, {"user_name": full_name})`. El caché de sesión sigue siendo
     `user.metadata["full_name"] = full_name` (no renombrar la clave, D-089).

3. **display_name se rellena en cada login con password** — Scenario 3
   - Step definitions en: `tests/step_defs/test_e14_t04.py`
   - Implementación en: `chainlit/main_family.py::_resolve_display_name()` (nueva) +
     `auth_callback()`
   - Notas: `_resolve_display_name(user_id)` hace `get_profile(user_id).get("user_name")`; si
     vacío, `get_user_metadata(user_id).get("full_name")`; devuelve `None` si ambos vacíos.
     Se llama en las dos ramas de `auth_callback()` (login existente y signup con sesión activa)
     antes de construir `cl.User(...)`.

4. **display_name se rellena también en login con Google** — Scenario 4
   - Step definitions en: `tests/step_defs/test_e14_t04.py`
   - Implementación en: `chainlit/main_family.py::oauth_callback()`
   - Notas: mismo `_resolve_display_name()` del punto 3, llamado tras
     `get_or_create_google_user(...)`, antes de construir el `cl.User(...)` de la rama oauth.

5. **Usuario sin nombre aún disponible no muestra el email como sustituto** — Scenario 5
   - Step definitions en: `tests/step_defs/test_e14_t04.py`
   - Implementación en: `chainlit/main_family.py::_resolve_display_name()`
   - Notas: caso ya cubierto por el diseño del punto 3 (`_resolve_display_name` devuelve `None`
     si `profiles.user_name` y `user_metadata.full_name` están vacíos) — este escenario es
     puramente de verificación, sin lógica nueva.

6. **Alta de cuenta Google nueva escribe profiles.user_name directamente (D-091, Q1)** —
   Scenario 6
   - Step definitions en: `tests/step_defs/test_e14_t04.py`
   - Implementación en: `auth/supabase_client.py::get_or_create_google_user()`
   - Notas: tras `profile = get_or_create_profile(user.id, role)`, si `full_name` viene informado
     y `profile.get("user_name")` está vacío, `update_profile(user.id, {"user_name": full_name})`.
     Aplica igual en el camino de creación nueva (`profile["user_name"]` siempre `None` ahí) y en
     el camino de usuario ya existente vía `_find_user_by_email` (solo si no lo tenía ya) — una
     sola rama de código cubre ambos casos, sin duplicar el `if`.

7. **Login con profiles.user_name vacío cae a user_metadata.full_name solo para display_name
   (D-091, Q2)** — Scenario 7
   - Step definitions en: `tests/step_defs/test_e14_t04.py`
   - Implementación en: ya cubierto por `_resolve_display_name()` (punto 3) — este escenario
     verifica explícitamente que no hay escritura en `profiles` desde los callbacks de login
     (ningún `update_profile` llamado en `auth_callback`/`oauth_callback`, solo lecturas).

## Restricciones a respetar

- **Privacy by design (AGENTS.md):** no se introduce almacenamiento nuevo — solo se relee/reescribe
  una columna ya creada en T-01 bajo el mismo gate de servicio (`use_service_key=True`).
- **Una responsabilidad por commit** (AGENTS.md, convenciones): separar el commit de
  `auth/supabase_client.py` (escritura en creación de Google) del de `chainlit/main_family.py`
  (lectura con fallback + reescritura de `_ensure_full_name`) si el ciclo TDD lo permite de forma
  natural — no es obligatorio si ambos cambios son indisociables para que un escenario pase en verde.
- No renombrar la clave de sesión `user.metadata["full_name"]` (D-089) — solo cambia la persistencia
  duradera, no el contrato interno que ya consumen `_greeting()`, `_onboarding_complete_title()` y
  `_ensure_patient_profile()`.

## Lo que queda fuera de esta tarea

- Edición de perfil desde `cl.ChatSettings` (T-05).
- Cualquier cambio a `_ensure_patient_profile()` o a los campos clínicos (`patient_name`,
  `patient_diagnosis`, `patient_age`, `patient_context`) — sin relación con esta migración.
- Investigación de por qué `patient_diagnosis` volvió a preguntarse tras un refresco de página
  (nota abierta de D-090, sin resolver, no bloquea T-04).
- Backfill masivo retroactivo vía script/SQL para usuarios que nunca vuelvan a abrir un chat —
  fuera de alcance: el backfill es perezoso (se dispara en su próximo `on_chat_start` o login),
  aceptado como suficiente a la escala del TFM.
