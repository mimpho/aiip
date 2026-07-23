# Plan — E-14 T-03 Flujo de onboarding por chat

## Contexto técnico

Sin hallazgos adicionales sobre APIs externas — todo el mecanismo necesario ya está en uso en el
repo:
- `cl.AskActionMessage(...).send()` devuelve `dict | None` con `{"name": ..., "payload": ...}` o
  `None` en timeout/cierre — mismo patrón que `_ensure_health_consent()` (T-02,
  `chainlit/main_family.py:335-342`).
- `cl.AskUserMessage(...).send()` devuelve `dict | None` con `{"output": str}` — mismo patrón que
  `_ensure_full_name()` (`chainlit/main_family.py:375-379`).
- Fuente de `user_name` para el caso "sobre mí": `cl.context.session.user.metadata["full_name"]`,
  ya resuelto por `_ensure_full_name()` en la misma llamada a `on_chat_start` — no `profiles.user_name`
  (D-089, sin poblar hasta T-04).
- `get_profile(user_id)` / `update_profile(user_id, data)` ya existen en `auth/supabase_client.py`
  (usados por T-02) y cubren `patient_name`, `patient_diagnosis`, `patient_age`, `patient_context`
  sin cambios de esquema (columnas de T-01, D-088).

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `chainlit/main_family.py` | modificar | Añade `_ensure_patient_profile()` y lo engancha en `on_chat_start`, entre `_ensure_full_name()` y el saludo. Nuevos mensajes/constantes de onboarding. |
| `tests/step_defs/test_e14_t03.py` | crear | Step definitions pytest-bdd de los 7 escenarios, mismo patrón de fake `chainlit` que `test_e14_t02.py` (fake module propio, no compartido). |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Se pregunta primero si los datos son sobre el propio usuario o sobre otra persona** —
   `tests/features/e14_t03_onboarding_flow.feature`
   - Step definitions en: `tests/step_defs/test_e14_t03.py`
   - Implementación en: `chainlit/main_family.py` (`_ensure_patient_profile()`, primer bloque)
   - Notas: `cl.AskActionMessage` con dos `cl.Action`: `name="patient_self"` (label "Sobre mí") y
     `name="patient_other"` (label "Sobre otra persona"). Mismo `timeout` que el resto de
     onboarding (usa una constante nueva, p. ej. `_PATIENT_PROFILE_TIMEOUT = 120`, no reutilices
     `_HEALTH_CONSENT_TIMEOUT` — son gates distintos). Si no hay respuesta (timeout/None), la
     función retorna sin preguntar nada más — no se asume ninguna rama, se repite en el próximo
     `on_chat_start` (mismo criterio que T-02).

2. **Si los datos son sobre el propio usuario, no se pregunta un nombre aparte**
   - Notas: al recibir `name="patient_self"`, `patient_name = cl.context.session.user.metadata.get("full_name")`
     (D-089). Si `full_name` no está disponible (usuario no respondió a `_ensure_full_name` en este
     mismo chat), no se guarda `patient_name` y la función retorna sin pedir el resto de campos —
     no hay un nombre real con el que formular las preguntas de diagnóstico/edad/contexto (ver
     escenario 4). Si se resuelve, persiste con `update_profile(user_id, {"patient_name": ...})`.

3. **Si los datos son sobre otra persona, se pregunta su nombre**
   - Notas: al recibir `name="patient_other"`, `cl.AskUserMessage` pidiendo el nombre. Si hay
     respuesta no vacía, se guarda en `patient_name` vía `update_profile`. Si no hay respuesta,
     igual que el punto 1: no se sigue preguntando en este chat.

4. **Diagnóstico, edad y contexto se piden por el nombre del paciente, no como "el paciente"**
   - Notas: una vez `patient_name` resuelto (ya guardado o recién resuelto en este mismo
     `on_chat_start`), pregunta cada campo pendiente (`patient_diagnosis`, `patient_age`,
     `patient_context`) con `cl.AskUserMessage`, interpolando el nombre real en la plantilla del
     mensaje (p. ej. `f"¿Qué diagnóstico tiene {patient_name}?"`). Nunca la palabra "paciente" en
     el texto de la pregunta. `patient_diagnosis` y `patient_context` se guardan como texto libre
     sin validar contra ninguna lista cerrada (decisión de `epic-start`, taxonomía IUIS
     descartada).

5. **Edad no numérica o fuera de rango se repregunta una vez (D-088, D-089)**
   - Notas: tras la respuesta a la pregunta de `patient_age`, intenta `int(respuesta.strip())` y
     valida `0 <= edad <= 120`. Si falla el parseo o el rango, envía un mensaje de error breve y
     repregunta **una sola vez** con `cl.AskUserMessage`. Si la segunda respuesta tampoco es
     válida, no se guarda `patient_age` y se continúa con el resto de campos pendientes (no
     bloquea `patient_context` ni el resto del flujo) — no se repregunta hasta el próximo
     `on_chat_start`.

6. **Solo se pregunta lo que falte**
   - Notas: antes de cada pregunta de diagnóstico/edad/contexto, comprueba el valor ya presente en
     el `profile` devuelto por `get_profile(user_id)` — si no es `None`, no se pregunta. Verifica
     que ya haber resuelto `patient_name` (o tenerlo de una llamada anterior) no dispara de nuevo
     la pregunta "¿sobre quién son los datos?".

7. **Perfil completo no vuelve a preguntarse**
   - Notas: si `patient_name`, `patient_diagnosis`, `patient_age` y `patient_context` están todos
     informados en `get_profile(user_id)`, `_ensure_patient_profile()` retorna inmediatamente sin
     ninguna llamada a `cl.AskActionMessage`/`cl.AskUserMessage`. Verifica en el test que el flujo
     sigue directamente al saludo y la bienvenida (mismo patrón de aserción que
     `test_e14_t02.py::se_pasa_directamente_al_saludo`).

## Restricciones a respetar

- **Privacy by design (D-009):** estos campos son datos de salud de categoría especial — esta
  función solo se alcanza si `health_data_consent_at` ya está informado (T-02 se ejecuta antes en
  `on_chat_start`); no dupliques la comprobación de consentimiento aquí.
- **Convenciones del proyecto:** ningún texto de pregunta embebido fuera de una constante en
  `main_family.py` (mismo patrón que `_ASK_NAME_MESSAGE`/`_HEALTH_CONSENT_MESSAGE`) — no crear
  ficheros de prompt nuevos bajo `prompts/`, esto no es texto para el LLM sino UI de Chainlit.
  Commits en inglés, una responsabilidad por commit.

## Lo que queda fuera de esta tarea

- Inyección del perfil de paciente en el prompt de generación — eso es T-06.
- Migración de `profiles.user_name` / `display_name` en `cl.User` — eso es T-04 (D-089 documenta
  por qué T-03 no depende de que T-04 esté cerrada).
- Edición posterior del perfil ya guardado desde `cl.ChatSettings` — eso es T-05.
- Cualquier taxonomía cerrada de diagnóstico (descartada en `epic-start`: texto libre en
  `patient_diagnosis`).
