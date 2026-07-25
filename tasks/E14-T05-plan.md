# Plan — E-14 T-05 Edición de perfil desde ajustes

## Contexto técnico

Verificado descompilando `chainlit==2.11.1` (descargado el wheel y desempaquetado, no asumido de
memoria):

- **`cl.ChatSettings`** (`chainlit/chat_settings.py`) se construye con una lista de `InputWidget` y
  se activa con `.send()` — no hay precedente en el proyecto. `@cl.on_settings_update(func)`
  (`chainlit/callbacks.py`) recibe el dict completo `{id: valor}` de todos los inputs declarados.
- **Widgets a usar** (`chainlit/input_widget.py`): `TextInput` (con `multiline=True` para
  `patient_context`) e `initial: Optional[str]`; `NumberInput` para `patient_age`, con
  `initial: Optional[float]` — **sin `min`/`max` nativos** (a diferencia de `Slider`), la
  validación de rango 0-120 es responsabilidad de `@cl.on_settings_update`, igual que
  `_parse_patient_age()` ya hace hoy en el flujo de chat.
- **Icono de ajustes:** el id `chat-settings-open-modal` (composer, ubicación por defecto) y el id
  `chat-settings-header-button` (header, cuando `chat_settings_location = "sidebar"`) son dos
  render paths distintos del mismo botón lógico — confirmado en
  `chainlit/frontend/dist/assets/index-*.js`. Con `"sidebar"`, el botón aparece en la misma fila
  `#header .flex.items-center.gap-1` que ya usa el theme-toggle (`design/public/custom.js`,
  `positionThemeToggle`), justo antes de `user-nav-button`. Es una línea de config
  (`chainlit/family/.chainlit/config.toml`), no requiere tocar `custom_css`/`custom.js` para esta
  parte.
- **Endpoint `GET /user`** (`chainlit/server.py:755`) devuelve el `User`/`PersistedUser` de la
  sesión actual — mismo objeto que ya consume el frontend internamente vía SWR
  (`hl()`/`svt()` en el bundle). Trae `identifier` (email) y `display_name`. Es la fuente de datos
  para el bloque nombre+email del desplegable, independiente de qué pinte el componente nativo
  `eWn` (que solo renderiza una única cadena: `display_name` si existe, si no `identifier`).
- **Desplegable de usuario:** el contenido pintado por Chainlit vive dentro de un portal Radix
  (`document.body`, sin id fijo salvo el trigger `user-nav-button`) — mismo problema estructural ya
  descrito para el theme-toggle/forgot-password link. Se sigue el patrón ya establecido en
  `custom.js` (`tagSourcesSections`, `tagOnboardingUi`, `positionThemeToggle`): una función
  idempotente que localiza el nodo objetivo por selector/contenido y un único
  `MutationObserver` dedicado sobre `document.body` con `{childList: true, subtree: true}`, que
  nunca se desconecta.
- **Tipografía:** `--font-display` (`design/public/tokens.css`) = Merriweather, peso 500
  (`--font-weight-medium`) — mismo token que login heading y `[data-step-type="user_message"]`.
  Reutilizar la variable CSS, no hardcodear el nombre de fuente.
- **`update_profile()`** (`auth/supabase_client.py`) ya solo toca las columnas pasadas en el dict —
  encaja directamente con el dict que entrega `@cl.on_settings_update`, sin necesitar mergear a
  mano el resto del perfil.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `chainlit/main_family.py` | modificar | Construir y enviar `cl.ChatSettings(...)` al final de `on_chat_start` (tras `_ensure_patient_profile()`, reutilizando el `profile` ya leído en memoria — no una lectura extra). Nuevo callback `@cl.on_settings_update` que valida `patient_age` (0-120; fuera de rango: no persiste ese campo, mensaje de error) y llama a `update_profile()` con el resto de campos, seguido de un mensaje de confirmación (éxito o error). Los inputs clínicos (`patient_name`/`patient_diagnosis`/`patient_age`/`patient_context`) solo se incluyen en la lista de `inputs` si `profile.get("health_data_consent_at")` está informado — sin consentimiento, el panel solo trae `user_name`. |
| `chainlit/family/.chainlit/config.toml` | modificar | Añadir `chat_settings_location = "sidebar"` en `[UI]`. |
| `design/public/custom.js` | modificar | Nueva función (p. ej. `injectUserMenuNameEmail`) que, al detectar la apertura del desplegable de usuario (mismo patrón de `MutationObserver` que el resto del fichero), hace `fetch('/user')`, y si `display_name` viene informado sustituye el `<p>` nativo por un bloque de dos líneas (nombre con `--font-display`/peso 500 + email en el estilo ya existente); si no hay `display_name`, no toca nada (degrada al comportamiento nativo, que ya muestra el email). Nuevo `MutationObserver` dedicado, igual que `tagOnboardingUi`/`positionThemeToggle` — no reutilizar los existentes para no acoplar responsabilidades distintas. |
| `tests/step_defs/test_e14_t05.py` | crear | Step definitions pytest-bdd para los escenarios automatizables de `e14_t05_profile_settings_panel.feature` (todos salvo los dos últimos, marcados como checklist manual). Mismo patrón de fakes de `chainlit`/`auth.supabase_client` que `test_e14_t03.py`/`test_e14_t04.py`. |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **El panel de ajustes muestra los datos actuales prellenados** — Scenario 1
   - Step definitions en: `tests/step_defs/test_e14_t05.py`
   - Implementación en: `chainlit/main_family.py` (nueva función `_build_chat_settings(profile)` o
     inline al final de `on_chat_start`)
   - Notas: un `TextInput`/`NumberInput` por campo, `initial` desde `profile.get(...)`
     (`None` si no existe — Chainlit lo admite). `id` de cada input = nombre de columna
     (`user_name`, `patient_name`, `patient_diagnosis`, `patient_age`, `patient_context`), así el
     dict que llega a `on_settings_update` mapea 1:1 con `update_profile()`.

2. **Guardar cambios en el panel los persiste en profiles + confirmación** — Scenario 2
   - Step definitions en: `tests/step_defs/test_e14_t05.py`
   - Implementación en: `chainlit/main_family.py::on_settings_update(settings)`
   - Notas: `update_profile(user_id, settings)` (sin filtrar todavía `patient_age` — eso es el
     punto 3) + `cl.Message(content="Perfil actualizado.").send()` en éxito;
     `logger.exception` + `cl.Message` de error si `update_profile` lanza.

3. **patient_age fuera de rango no se persiste, el resto sí** — Scenario 3
   - Step definitions en: `tests/step_defs/test_e14_t05.py`
   - Implementación en: `chainlit/main_family.py::on_settings_update(settings)`
   - Notas: validar `settings.get("patient_age")` contra `0 <= age <= 120` (reutilizar el mismo
     rango que `_PATIENT_AGE_INVALID_MESSAGE`/`_parse_patient_age` documentan, sin importar esa
     función directamente ya que aquí el valor ya llega como número, no como texto a parsear) antes
     de construir el dict que se pasa a `update_profile()`; si es inválido, se excluye esa clave del
     dict y se añade un mensaje de error específico, pero se sigue llamando a `update_profile()` con
     el resto.

4. **El panel también sirve para completar un onboarding no terminado** — Scenario 4
   - Step definitions en: `tests/step_defs/test_e14_t05.py`
   - Implementación en: ya cubierto por los puntos 1-2 — este escenario verifica que no hace falta
     lógica nueva: los campos con valor `None` se muestran vacíos y se guardan igual que los que ya
     tenían valor.

5. **Un usuario sin consentimiento no ve los campos clínicos** — Scenario 5
   - Step definitions en: `tests/step_defs/test_e14_t05.py`
   - Implementación en: `chainlit/main_family.py` (construcción condicional de `inputs`)
   - Notas: `if profile.get("health_data_consent_at")` gatea si se añaden los cuatro `InputWidget`
     clínicos a la lista — `user_name` siempre se incluye.

## Checklist manual (no TDD, verificación visual tras el punto 5)

6. **Icono de ajustes visible junto al avatar** — añadir `chat_settings_location = "sidebar"` a
   `chainlit/family/.chainlit/config.toml`, verificar en navegador contra el criterio del `.feature`.
7. **Desplegable de usuario con nombre + email** — implementar `injectUserMenuNameEmail` en
   `design/public/custom.js`, verificar contra los dos escenarios de degradación (con y sin
   `display_name` resuelto) — para probar el caso "sin nombre", usar una cuenta que no haya pasado
   por `_ensure_full_name()` todavía.

## Restricciones a respetar

- **Agnóstico de proveedor / prompts en fichero separado (AGENTS.md):** no aplica directamente a
  esta tarea (no toca LLM ni prompts).
- **Privacy by design:** no se añade almacenamiento nuevo — el panel solo lee/escribe columnas ya
  existentes de `profiles` (T-01), siempre vía `update_profile()` con service key, igual que el
  resto del onboarding.
- **`GRANT UPDATE`/`CHECK` de `profiles` (D-088):** sin cambios de esquema en esta tarea — la
  validación de `patient_age` vive en la capa de aplicación (`on_settings_update`), no en SQL,
  mismo criterio que ya fijó D-088 para T-03.
- **No tocar el bundle de Chainlit:** toda la personalización va por `config.toml` (icono) y
  `custom.js`/`custom_css` (desplegable) — cero parches al paquete `chainlit` instalado.

## Lo que queda fuera de esta tarea

- Memoria de perfil en el pipeline de generación (inyección en el prompt) — es T-06.
- Investigar por qué `patient_diagnosis` volvió a preguntarse tras un refresco de página en la
  sesión de QA de Marcos (nota abierta de D-090, sin relación directa con T-05).
- Diagnóstico de por qué el desplegable de Marcos mostraba solo el email en la captura compartida en
  `task-start` — se resuelve solo con datos reales (logout/login o `_ensure_full_name()` completado),
  no con código nuevo; si tras eso sigue sin resolverse, es un bug aparte, no de esta tarea.
- Cualquier campo de perfil nuevo no listado en D-092 (la lista de campos del panel es cerrada:
  `user_name`, `patient_name`, `patient_diagnosis`, `patient_age`, `patient_context`).
