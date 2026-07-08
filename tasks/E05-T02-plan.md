# Plan — E-05 T-02 Streaming nativo de tokens

## Contexto técnico

**`ChatGoogleGenerativeAI.astream()`** — método async nativo de LangChain, ya disponible en la integración usada por `RAGGenerator` (no requiere dependencias nuevas). Devuelve un `AsyncIterator[AIMessageChunk]`; cada chunk expone `.content` con el fragmento de texto parcial:

```python
async for chunk in self._llm.astream(prompt):
    yield chunk.content
```

**`cl.Message.stream_token()`** — API de Chainlit para renderizar tokens progresivamente (docs.chainlit.io/advanced-features/streaming). Patrón confirmado:

```python
msg = cl.Message(content="")
await msg.send()
async for token in fuente_de_tokens:
    await msg.stream_token(token)
await msg.update()
```

`stream_token()` ya es `await`-able y acumula internamente el contenido del mensaje — no hace falta reconstruir el texto a mano en `main_family.py` para mostrarlo (sí para el filtro de seguridad, ver abajo, que necesita el texto completo aparte).

**D-034 (registrada en este task-start)** fija tres cosas que el plan da por resueltas, no las repitas como puntos abiertos:
- Streaming vía generador async nativo (`astream`), no `cl.make_async()`.
- El listado de fuentes (D-026) se preserva como fragmento final tras el streaming.
- `RAGPipeline.query()` no se toca; `aquery_stream()` es un método nuevo y paralelo.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/generator.py` | modificar | Añade `agenerate_stream(question, context, language) -> AsyncIterator[str]`, usando `self._llm.astream(prompt)`. Reutiliza `_PROMPT_TEMPLATE` y `_load_system_prompt` ya existentes — no duplicar la construcción del prompt. |
| `rag/pipeline.py` | modificar | Añade `aquery_stream(question) -> AsyncIterator[str]`: retrieval + `check_alarm_signals` igual que `query()`, streaming del cuerpo vía `agenerate_stream()`, ensamblado del texto completo, `apply_safety_filter` diferido (yield solo del sufijo añadido), y `_build_sources_section()` como fragmento final. No modifica `query()`. |
| `chainlit/main_family.py` | modificar | `on_message` pasa de `cl.make_async(pipeline.query)` a `async for token in pipeline.aquery_stream(question): await response_message.stream_token(token)`. Mantiene el manejo de errores (try/except alrededor del `async for`) y el mensaje vacío inicial. |
| `tests/step_defs/test_e05_t02.py` | crear | Step definitions pytest-bdd para los 6 escenarios del `.feature`. |
| `tests/step_defs/test_e05_t01.py` | modificar (mínimo, D-034) | El mock de `_get_pipeline()` pasa de `mock_pipeline.query.return_value` a `mock_pipeline.aquery_stream` como generador async fake. Ajustar las aserciones que comprobaban `.query.assert_called_once_with(...)` para comprobar `.aquery_stream` en su lugar. El fake `cl.Message` (`_FakeMessage`) gana un método async `stream_token()` que acumula en `.content`. |
| `tests/features/e05_t01_chat_pipeline_integration.feature` | modificar (mínimo, D-034) | Solo el texto del paso "se invoca RAGPipeline.query() con esa pregunta" → "se invoca la generación en streaming del pipeline con esa pregunta". No cambia ningún otro escenario ni comportamiento. |

No se toca `rag/safety.py`, `rag/language.py`, `rag/retriever.py`, `rag/embeddings.py` — sus funciones se consumen tal cual, sin cambios de firma.

## Orden de implementación TDD

Sigue el orden de los escenarios en `tests/features/e05_t02_streaming.feature`. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente. Los escenarios 1-5 se testean a nivel de `RAGPipeline`/`RAGGenerator` (mockeando `ChatGoogleGenerativeAI` como en D-018/D-020, patcheando `rag.generator.ChatGoogleGenerativeAI` con un fake cuyo `.astream()` es un generador async que yield-ea `SimpleNamespace(content=...)` por chunk). El escenario 6 se testea a nivel de `main_family.on_message` (patrón de `test_e05_t01.py`, con `aquery_stream` fake).

1. **Los tokens de la respuesta se emiten progresivamente**
   - Implementación en: `rag/generator.py` (`agenerate_stream`), `rag/pipeline.py` (`aquery_stream`, sin lógica de filtro/fuentes todavía)
   - Notas: fake LLM que parte una respuesta fija en 3-4 chunks. Verificar que `aquery_stream()` yield-ea más de un fragmento y que `"".join(fragmentos)` reconstruye el texto completo del LLM (antes de cualquier filtro).

2. **El recordatorio de seguridad se añade tras completar el streaming**
   - Notas: pregunta con keyword de `config/alarm_triggers.json` (mismo patrón que tests de E-04 T-05/T-06). Verificar que el recordatorio de `apply_safety_filter` llega como el fragmento *después* de agotar el streaming del cuerpo, nunca intercalado — comprobar el fragmento final exacto, no solo el texto concatenado.

3. **Afirmación tranquilizadora detectada solo tras completar el streaming**
   - Notas: fake LLM que reparte la frase "no es grave" entre dos chunks (p. ej. `"no es "` + `"grave, tranquilo"`) para forzar que la detección de `apply_safety_filter` solo puede ocurrir sobre el texto ya ensamblado, no chunk a chunk.

4. **Streaming sin necesidad de filtro no añade texto adicional**
   - Notas: sin alarma en la query, sin frases tranquilizadoras en la respuesta fake. Verificar que no se yield-ea ningún fragmento extra tras el último chunk del cuerpo (aparte del posible listado de fuentes, cubierto en el siguiente escenario — usar fixtures sin metadata de fuente aquí para aislar el comportamiento).

5. **El listado de fuentes se añade tras el streaming, después del recordatorio de seguridad si aplica**
   - Notas: reutilizar fixtures indexadas con metadata `source`/`filename` (patrón de `_build_sources_section`, ya cubierto en tests de E-04 T-06/D-026). Probar dos casos: con alarma (fuentes después del recordatorio) y sin alarma (fuentes como único fragmento final).

6. **Error durante el streaming no rompe la sesión de chat**
   - Step definitions en: `tests/step_defs/test_e05_t02.py`, reutilizando el patrón de fake `chainlit` de `test_e05_t01.py` (fake module con `Message.stream_token` async)
   - Implementación en: `chainlit/main_family.py`
   - Notas: `aquery_stream` fake que yield-ea 1-2 fragmentos y luego lanza una excepción (`raise Exception("LLM no disponible")` a mitad de la iteración). Verificar que `on_message` captura la excepción, actualiza el mensaje con `_ERROR_MESSAGE`, y que una segunda llamada a `on_message` con otra pregunta funciona con normalidad (mismo patrón que Scenario 3 de T-01).
   - Ajustar en paralelo `tests/step_defs/test_e05_t01.py` y el wording del `.feature` de T-01 (ver tabla de ficheros arriba) — hazlo como parte de este mismo ciclo, no antes.

## Restricciones a respetar

- **Agnóstico de proveedor:** `astream()` es la misma abstracción de LangChain ya usada por `invoke()` — no se introduce SDK nativo de Google.
- **Falso Negativo Cero:** `apply_safety_filter`/`check_alarm_signals` no cambian de lógica ni de firma, solo el momento en que se invocan (tras ensamblar el texto completo, nunca por chunk). No optimizar aplicando el filtro chunk a chunk aunque parezca más "en streaming" — rompería la detección de frases partidas entre chunks (Escenario 3).
- **Reparto git:** implementación en `task/E05-T02-token-streaming` ya creada; el agente en Antigravity no hace `push`/`merge`.

## Lo que queda fuera de esta tarea

- Visualización de pasos intermedios / documentos recuperados en la UI (T-03) — `aquery_stream()` no expone los `raw` results a `main_family.py`, solo el texto final incluyendo fuentes.
- Perfil profesional (`main_professional.py`) — sigue bloqueado (stub).
- Cualquier cambio en la lógica de `check_alarm_signals`, `apply_safety_filter` o `_build_sources_section` — solo se consumen.
- `RAGPipeline.query()` no se modifica ni se reimplementa sobre `aquery_stream()` (D-034).
