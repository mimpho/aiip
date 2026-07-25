# Plan — E-14 T-06 Memoria de perfil en el pipeline de generación

## Contexto técnico

Verificado contra el código actual del repo (no asumido de memoria):

- **`_PROMPT_TEMPLATE`** (`rag/generator.py`) es un string fijo formateado con `.format()` —no hay
  lógica condicional en la plantilla misma. Para que el bloque `[PERFIL DEL PACIENTE]` desaparezca
  por completo cuando no hay perfil (D-093), la cabecera va **dentro** del valor que se calcula para
  el placeholder `profile_context`, no en el template. Diseño:

  ```python
  _PROMPT_TEMPLATE = """{system_prompt}

  {profile_context}[CONTEXTO]
  {context}

  [PREGUNTA]
  {question}

  [INSTRUCCIÓN DE IDIOMA]
  {language_instruction}"""
  ```

  `_format_profile_context(profile: dict | None) -> str` devuelve `""` si `profile` es `None` o
  `profile.get("patient_name")` está vacío (mismo criterio de "hay onboarding" que usa
  `_ensure_patient_profile()`: `patient_name` es el único campo que se pide siempre primero, los
  demás dependen de que exista). Si hay `patient_name`, devuelve el bloque completo con cabecera:

  ```python
  "[PERFIL DEL PACIENTE]\nNombre: {patient_name}\n...(resto de campos informados)...\n\n"
  ```

  Con `profile_context=""`, el template renderiza exactamente igual que antes de E-14 (el
  placeholder desaparece sin dejar línea en blanco extra, porque no hay salto de línea antes de
  `[CONTEXTO]` en el propio template). Con contenido, aporta su propio `\n\n` final para separarse
  de `[CONTEXTO]`.

- **Campos y orden de renderizado:** `Nombre` (siempre si `patient_name` existe) → `Diagnóstico` (si
  `patient_diagnosis`) → `Edad` (si `patient_age`, con sufijo "años") → `Contexto` (si
  `patient_context`). Cada línea se omite individualmente si el campo es `None`/vacío — nunca se
  inventa ni se menciona como "no disponible" (Scenario "Perfil parcial").

- **`generate()`/`agenerate_stream()`** (`rag/generator.py`) ganan un parámetro
  `profile: dict | None = None` al final de la firma (después de `language`), para no romper las
  llamadas posicionales existentes por nombre de parámetro (ya se llaman todas con keyword args:
  `question=`, `context=`, `language=` — confirmado en `rag/pipeline.py`).

- **`query()`/`aquery_stream()`** (`rag/pipeline.py`) ganan el mismo parámetro `profile: dict | None
  = None`, que se limita a reenviarse a `self._generator.generate()`/`agenerate_stream()` — no toca
  `_retrieve_with_scores()`/`retrieve()` en ningún punto (Scenario "no participa en retrieval").
  `pipeline.query(ctx["query"])` (posicional, sin perfil) en `tests/step_defs/test_e04_t06.py` y
  `scripts/smoke_test_rag.py` sigue funcionando sin cambios por ser parámetro opcional con default.

- **`cl.user_session`** (Chainlit): API `get(key, default=None)`/`set(key, value)`, ámbito de sesión
  de chat — no hay precedente de uso en el proyecto todavía (T-01 a T-05 de E-14 pasan `profile`
  como variable local entre funciones dentro del mismo `on_chat_start`). En los tests, el fake
  `chainlit` module (patrón ya usado en `test_e14_t03.py`/`test_e14_t04.py`/`test_e14_t05.py`) debe
  exponer un `user_session` con `get`/`set` reales sobre un dict, no un `MagicMock()` puro —
  `MagicMock().get(...)` devuelve otro `MagicMock` en vez de `None`/el valor guardado, lo que
  rompería las aserciones de "no hay perfil" o "perfil actualizado". Un `SimpleNamespace` con dos
  funciones cerradas sobre un dict compartido por test es suficiente.

- **`on_chat_start`** ya tiene `profile` disponible como variable local (retorno de
  `_ensure_patient_profile()`, línea ~846 de `chainlit/main_family.py`) — cachearlo es una línea
  nueva justo después de esa llamada, sin reestructurar la función.

- **`_answer(question)`** (`chainlit/main_family.py`) es la única función que llama a
  `pipeline.retrieve()`/`aquery_stream()` hoy (compartida por `on_message` y
  `on_starter_question`) — el cambio de leer el perfil de `cl.user_session` se hace una sola vez
  ahí, cubre ambos callers sin tocarlos.

- **`on_settings_update`** (T-05, ya implementado) solo persiste en Supabase hoy — se le añade
  sincronizar `cl.user_session["profile"]` con los mismos campos que sí se persistieron (excluyendo
  `patient_age` si quedó fuera de rango, mismo dict `data` ya usado para `update_profile()`).

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/generator.py` | modificar | Nueva función `_format_profile_context(profile)`. Placeholder `profile_context` añadido a `_PROMPT_TEMPLATE`. `generate()`/`agenerate_stream()` ganan parámetro `profile: dict \| None = None` y lo pasan a `_format_profile_context()` antes de `.format()`. |
| `rag/pipeline.py` | modificar | `query()`/`aquery_stream()` ganan parámetro `profile: dict \| None = None`, reenviado a `self._generator.generate()`/`agenerate_stream()`. `retrieve()`/`_retrieve_with_scores()` sin cambios. |
| `chainlit/main_family.py` | modificar | `on_chat_start`: cachea `profile` en `cl.user_session` tras `_ensure_patient_profile()`. `_answer()`: lee `cl.user_session.get("profile")` y lo pasa a `pipeline.aquery_stream(..., profile=profile)`. `on_settings_update`: sincroniza `cl.user_session["profile"]` con los campos persistidos. |
| `prompts/system_prompt_family.txt` | modificar | Nueva instrucción explicando cómo usar el bloque `[PERFIL DEL PACIENTE]` cuando está presente en el contexto (no repetir el diagnóstico como si fuera nuevo, ajustar registro si la edad es relevante) sin contradecir la instrucción ya existente (líneas 41-46) de no asumir que quien escribe es el paciente. |
| `tests/step_defs/test_e14_t06.py` | crear | Step definitions pytest-bdd para los 7 escenarios de `e14_t06_profile_memory_in_prompt.feature`. Mocking del LLM vía `patch("rag.generator.ChatGoogleGenerativeAI")` (mismo patrón que `test_e04_t06.py`) para los escenarios de `generator`/`pipeline`; fake `chainlit` con `user_session` respaldado por dict real (no `MagicMock` puro) para los escenarios de `main_family.py`. |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Perfil completo se formatea como bloque de contexto en el prompt** — Scenario 1
   - Step definitions en: `tests/step_defs/test_e14_t06.py`
   - Implementación en: `rag/generator.py` (`_format_profile_context()`, placeholder en
     `_PROMPT_TEMPLATE`, parámetro `profile` en `generate()`/`agenerate_stream()`)
   - Notas: verificar el prompt real pasado a `MockLLM.return_value.invoke`/`.astream` (`call_args`)
     contiene `"[PERFIL DEL PACIENTE]"`, el nombre real del paciente, y que `"context"` (los chunks)
     no cambia de contenido frente a una llamada sin perfil.

2. **Perfil parcial se inyecta solo con los campos disponibles** — Scenario 3
   - Step definitions en: `tests/step_defs/test_e14_t06.py`
   - Implementación en: `rag/generator.py` (`_format_profile_context()`)
   - Notas: perfil con `patient_age`/`patient_context` en `None` → el prompt no menciona "Edad" ni
     "Contexto", no inventa valores ni escribe placeholders vacíos para esos campos.

3. **Usuario sin perfil no cambia el comportamiento actual** — Scenario 4
   - Step definitions en: `tests/step_defs/test_e14_t06.py`
   - Implementación en: `rag/generator.py` (`_format_profile_context()` devuelve `""` si no hay
     `patient_name`)
   - Notas: comparar byte a byte el prompt generado con `profile=None` frente al prompt que se
     generaba antes de esta tarea (mismo test que ya cubre `test_e04_t06.py`, sin perfil) — deben
     ser idénticos.

4. **El contexto de perfil no participa en la consulta de retrieval** — Scenario 2
   - Step definitions en: `tests/step_defs/test_e14_t06.py`
   - Implementación en: ninguna (guarda de regresión) — `rag/pipeline.py::retrieve()`/
     `_retrieve_with_scores()` no ganan parámetro `profile`
   - Notas: espiar `self._retriever.invoke` (o el mock del retriever ya usado en tests de pipeline)
     y comprobar que el argumento sigue siendo `question` tal cual, incluso cuando `pipeline.query()`
     se llama con `profile` informado.

5. **`system_prompt_family.txt` se actualiza para explicar cómo usar `profile_context`** — Scenario 5
   - Step definitions en: `tests/step_defs/test_e14_t06.py`
   - Implementación en: `prompts/system_prompt_family.txt`
   - Notas: test de contenido (busca la instrucción nueva en el fichero), no de comportamiento del
     LLM. Redactar la instrucción con cuidado de no contradecir las líneas 41-46 existentes — este
     fichero se despliega a producción con esta tarea (nota de proceso del `.feature`), revisar la
     redacción exacta en el QA de cierre de la tarea (mismo criterio que D-078: fijar la redacción
     antes de darla por buena, no solo confiar en que "suena bien").

6. **El perfil se cachea en sesión y se usa en cada mensaje sin releer Supabase** — Scenario 6
   - Step definitions en: `tests/step_defs/test_e14_t06.py`
   - Implementación en: `chainlit/main_family.py` (`on_chat_start` cachea; `_answer()` lee de
     `cl.user_session` y pasa `profile=` a `pipeline.aquery_stream()`)
   - Notas: fake `cl.user_session` respaldado por dict; mockear `_get_pipeline()`/`RAGPipeline` para
     capturar con qué `profile` se llamó `aquery_stream()`; aserción explícita de que
     `get_profile()` (Supabase) no se invoca de nuevo dentro de `_answer()`.

7. **Editar el perfil desde ajustes actualiza la copia en sesión** — Scenario 7
   - Step definitions en: `tests/step_defs/test_e14_t06.py`
   - Implementación en: `chainlit/main_family.py::on_settings_update()`
   - Notas: tras `update_profile()`, sincronizar `cl.user_session["profile"]` solo con las claves de
     `data` que sí se persistieron (si `patient_age` quedó excluido por estar fuera de rango, no se
     escribe esa clave en la caché tampoco). Verificar que una llamada posterior a `_answer()` en el
     mismo test ve los valores nuevos.

## Restricciones a respetar

- **Agnóstico de proveedor / prompts en fichero separado (AGENTS.md):** el nuevo texto de
  personalización va en `prompts/system_prompt_family.txt`, nunca embebido en `rag/generator.py`.
- **Falso Negativo Cero:** la instrucción nueva sobre `profile_context` no debe abrir una vía para
  que el agente confirme seguridad o dé consejo clínico basado en la edad/diagnóstico — solo ajusta
  tono y evita redundancia, no el contenido de las restricciones absolutas ya existentes.
- **D-059 (no aflojar grounding):** `profile_context` nunca participa en retrieval ni cambia qué
  documentos se recuperan — solo en la llamada de generación, ya cubierto por Scenario 2/4.
- **Privacy by design:** no se añade almacenamiento nuevo — `cl.user_session` es memoria de proceso
  por sesión de chat (no persiste en disco ni en Supabase), se pierde al cerrar la sesión igual que
  cualquier otro dato en `cl.context.session`.
- **Retrocompatibilidad de firma:** `profile` siempre como último parámetro opcional con default
  `None` en `generate()`/`agenerate_stream()`/`query()`/`aquery_stream()` — no reordenar los
  parámetros existentes.

## Lo que queda fuera de esta tarea

- Memoria conversacional de corto plazo (enlazar preguntas del mismo hilo) — capa 1 de E-08, sigue
  bloqueada (D-059/D-087), no se aborda ni se deja preparada en esta tarea.
- Regresión completa (tests + RAGAS acotado) tras tocar `system_prompt_family.txt` en producción —
  es T-07 (cierre de la épica), no esta tarea.
- Cualquier campo de perfil nuevo no contemplado en el esquema de T-01 (`patient_name`,
  `patient_diagnosis`, `patient_age`, `patient_context`).
- Actualizar `docs/security.md` — también T-07.
