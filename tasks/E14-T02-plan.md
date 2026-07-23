# Plan — E-14 T-02 Gate de consentimiento de datos de salud (D-009)

## Contexto técnico

### `cl.AskActionMessage` — firma y comportamiento exactos

Verificado contra `chainlit==2.11.1` instalado en un entorno limpio (no estaba documentado en
ningún plan anterior del repo, primera vez que se usa):

```python
cl.AskActionMessage(content: str, actions: List[cl.Action], author='Assistant',
                     timeout=90, raise_on_timeout=False)
```

`.send()` bloquea hasta que el usuario pulsa una acción o expira el `timeout`, y devuelve:

```python
class AskActionResponse(TypedDict):
    name: str      # el `name` del cl.Action pulsado
    payload: Dict
    label: str
    tooltip: str
    forId: str
    id: str
```

o `None` si expira el timeout (con `raise_on_timeout=False`, que es el default — no hace falta
try/except). Esto encaja exactamente con lo que pide D-009 ("acción afirmativa real") y el
`.feature` ("lo rechaza o lo cierra sin confirmar" → mismo tratamiento que un `None`).

`cl.Action` ya se usa en el repo (`starter_question`, D-036) con `name`/`payload`/`label` — sin
sorpresas ahí.

### `health_data_consent_at` no tiene acceso desde Python todavía

La columna existe desde T-01 (`supabase/migrations/20260723002559_e14_t01_add_profile_onboarding_columns.sql`,
`timestamptz` nullable), pero `auth/supabase_client.py` no tiene ninguna función que la lea o
escriba. Hoy solo hay:
- `get_or_create_profile(user_id, role)` — crea si no existe, no sirve para un simple read.
- `_get_profile(user_id)` — privada, ya hace exactamente el `SELECT` que necesita el gate, pero
  solo la usa `login()` internamente.

Decisión de `task-start`: promocionar `_get_profile` a pública (`get_profile`, sin guion bajo) y
añadir `update_profile(user_id, data)` genérica. A diferencia de `update_user_metadata` (que
tiene que mergear a mano porque `update_user_by_id` sobrescribe `user_metadata` entero), el
`.update(dict)` de Supabase sobre una tabla normal solo toca las columnas que se le pasan — no
hace falta merge. Ambas con `service_key` (D-088: sin ruta de cliente directo contra Supabase en
el stack actual, mismo patrón que `role`/`user_metadata`).

### Orden en `on_chat_start`

El gate va **antes** de `_ensure_full_name()` (D-040): el nombre de cuenta no es dato de salud y
no necesita este gate. Orden final: `_ensure_health_consent()` → `_ensure_full_name()` →
`_greeting()` / mensaje de bienvenida.

### Patrón de test — mock de `chainlit` como módulo falso

`tests/step_defs/test_e05_t06.py` monta un `types.ModuleType("chainlit")` completo en
`sys.modules["chainlit"]` antes de importar `main_family` (chainlit no está instalado en el
entorno de tests). Hay que añadir a ese patrón — en un fichero de test nuevo, con su propio
`_fake_cl` (cada fichero de test registra el suyo, ver comentario en `test_e05_t06.py` sobre por
qué no se comparte) — un factory para `AskActionMessage` análogo a
`_make_ask_user_message_factory`:

```python
def _make_ask_action_message_factory(response):
    """MagicMock que imita `cl.AskActionMessage(...).send()` (coroutine)."""
    instance = MagicMock()
    instance.send = AsyncMock(return_value=response)
    return MagicMock(return_value=instance)
```

`response` es o bien `None` (timeout/rechazo) o bien un dict `{"name": "consent_accept", ...}`
(aceptación) — no hace falta instanciar `AskActionResponse` de verdad, un dict basta porque el
código de producción solo lee `res.get("name")`.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `auth/supabase_client.py` | modificar | `_get_profile` → `get_profile` (pública, sin cambiar su cuerpo); `login()` actualiza la llamada; nueva `update_profile(user_id, data)` (`service_key`, `.table("profiles").update(data).eq("id", user_id).execute()`, devuelve la fila actualizada) |
| `chainlit/main_family.py` | modificar | Importa `get_profile`, `update_profile`; añade `_HEALTH_CONSENT_MESSAGE`, `_HEALTH_CONSENT_TIMEOUT = 300`, `_ensure_health_consent()`; `on_chat_start` la llama antes de `_ensure_full_name()` |
| `tests/step_defs/test_e14_t02.py` | crear | Step definitions pytest-bdd de los 4 escenarios automatizables (el 5º queda como documentación, ver `.feature`) |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo → verde antes de pasar al siguiente.

1. **Primer chat sin consentimiento registrado muestra el gate antes del saludo**
   - Feature: `tests/features/e14_t02_health_consent_gate.feature`
   - Step definitions en: `tests/step_defs/test_e14_t02.py`
   - Implementación: `get_profile(user_id)` en `auth/supabase_client.py` (renombrar
     `_get_profile`, actualizar la única llamada interna en `login()`). En `main_family.py`,
     `_ensure_health_consent()`: si `get_profile(user_id)["health_data_consent_at"]` es `None`,
     llama `cl.AskActionMessage(content=_HEALTH_CONSENT_MESSAGE, actions=[...], timeout=300)`.
     `on_chat_start` la invoca antes de `_ensure_full_name()`. Verificar en el test que el mensaje
     del gate se envía antes que el mensaje de bienvenida (mismo patrón de aserción sobre
     `message_mock.call_args_list` que usa `test_e05_t06.py` para `_ensure_full_name`).

2. **Aceptar el consentimiento lo registra una sola vez**
   - Feature: mismo fichero, scenario correspondiente
   - Implementación: si `res and res.get("name") == "consent_accept"`, llama
     `update_profile(user_id, {"health_data_consent_at": datetime.now(timezone.utc).isoformat()})`.
     Verificar en el test el payload exacto de la llamada a `update_profile`.

3. **Chat posterior con consentimiento ya registrado no repite el gate**
   - Feature: scenario correspondiente
   - Implementación: ninguna adicional — el chequeo `is None` del paso 1 ya cubre este caso.
     Test: mockear `get_profile` devolviendo un `health_data_consent_at` no nulo, comprobar que
     `AskActionMessage` no se llama.

4. **Rechazar el consentimiento no bloquea el chat**
   - Feature: scenario correspondiente
   - Implementación: ninguna adicional — si `res` es `None` (timeout) o
     `res.get("name") != "consent_accept"` (botón "Ahora no"), `_ensure_health_consent()` no
     llama `update_profile` y retorna sin excepción; `on_chat_start` sigue su curso normal hacia
     `_ensure_full_name()` y el saludo. Test: dos casos (timeout con `response=None`, y decline
     explícito con `response={"name": "consent_decline", ...}`), comprobar en ambos que
     `update_profile` no se llama y que el flujo llega al mensaje de bienvenida.

5. **El gate aplica igual sin importar la vía de autenticación** — sin step def, documentación
   (ver nota en el `.feature`). No requiere ciclo TDD: la implementación de los pasos 1-4 ya es
   agnóstica de cómo se autenticó (`_ensure_health_consent()` solo usa `user_id`).

## Restricciones a respetar

- **D-009 / privacy by design:** el texto del gate es el aprobado en `task-start` (ver
  `.feature`), no cambiarlo sin volver a pasar por Marcos — D-009 deja explícito que el texto
  final requiere revisión legal antes de cualquier uso real, esto es una propuesta razonada para
  el TFM.
- **D-088:** sin `CHECK` de rango ni `REVOKE`/`GRANT` por columna — no añadir nada de eso aquí,
  ya se decidió explícitamente que no aplica.
- **Falso Negativo Cero (D-002) / Falso Negativo Cero espíritu en D-009:** rechazar o cerrar el
  gate sin confirmar nunca debe bloquear el resto del chat. Si algo falla en `update_profile`
  (excepción de red, etc.), no debe romper `on_chat_start` — capturar y loguear, dejar que el
  flujo siga (mismo criterio que el resto de `on_chat_start`, que no tiene try/except propio
  hoy porque `_ensure_full_name` tampoco lo necesita, pero aquí sí hay una escritura nueva a
  Supabase que puede fallar de forma que antes no existía).
- **Service key:** `update_profile`/`get_profile` siempre con `use_service_key=True`, igual que
  el resto de escrituras a `profiles`.

## Lo que queda fuera de esta tarea

- El onboarding real (preguntar nombre de quien escribe, del paciente, diagnóstico, edad,
  contexto) — T-03. T-02 solo dispara el gate y, tras aceptar o rechazar, continúa hacia el
  saludo actual.
- Edición del consentimiento desde ajustes — T-05.
- Migración de `full_name`/`user_name` — T-04, no relacionado con esta tarea salvo que ambas
  tocan `on_chat_start` (T-04 no está planificada para tocar el orden que fija T-02).
- Revisión legal del texto de consentimiento — fuera del alcance del TFM (ver nota en D-009).
