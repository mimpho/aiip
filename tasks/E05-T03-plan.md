# Plan — E-05 T-03 Visualización de pasos intermedios del RAG

## Contexto técnico

### Decisión de arquitectura — D-035

El criterio de E-05 T-03 exige dos cosas distintas que esta tarea resuelve conjuntamente:

1. **Exponer `retrieve()` como método público de `RAGPipeline`** — encapsula la llamada a
   `similarity_search_with_score` que hoy está inline tanto en `query()` como en `aquery_stream()`.
   Devuelve `list[tuple[Document, float]]` (mismo tipo que devuelve Chroma directamente).

2. **`aquery_stream()` acepta `raw_results` opcional** — si el llamador ya tiene los resultados de
   retrieval (porque llamó a `pipeline.retrieve()` antes para renderizar el paso), los reutiliza
   sin volver a consultar el vectorstore. Si `raw_results=None` (por defecto), hace la llamada
   internamente como siempre — retrocompatible con todos los tests de T-01 y T-02.

3. **`main_family.on_message` usa `cl.Step`** — llama a `pipeline.retrieve(question)`, abre un
   `cl.Step` con los resultados, y pasa esos mismos resultados a `aquery_stream(question,
   raw_results=raw)`. El `cl.Step` se cierra antes de que empiece el streaming. Ver D-035.

### `cl.Step` — patrón confirmado (docs.chainlit.io/concepts/step)

```python
async with cl.Step(name="Documentos recuperados") as step:
    step.output = _format_retrieval_step(raw_results)
# El step queda cerrado automáticamente al salir del bloque
```

`cl.Step` es el componente de Chainlit pensado para visualizar pasos intermedios de un agente.
En la UI aparece como un bloque colapsable con nombre e icono propio, antes del mensaje de respuesta.

### Contenido del paso (aprobado por Marcos)

Por cada documento recuperado, el paso muestra:
- `source/filename` (metadatos ya garantizados por D-022/D-029)
- Score de similitud (float redondeado a 2 decimales)
- Extracto del chunk: primeros ~200 caracteres de `page_content` (no el chunk completo)

Formato markdown dentro del step — se renderiza con Chainlit.

### Retrocompatibilidad con T-01/T-02

`aquery_stream()` con `raw_results=None` (default) sigue haciendo `similarity_search_with_score`
internamente — exactamente como hoy. Los tests de T-01 y T-02 mockean `_get_pipeline()` devolviendo
un `MagicMock`; no invocan `retrieve()` ni pasan `raw_results`, así que no se ven afectados por
la nueva firma.

### Ajuste mínimo a `aquery_stream()`

```python
async def aquery_stream(
    self,
    question: str,
    raw_results=None,   # list[tuple[Document, float]] | None
) -> AsyncIterator[str]:
    language = detect_language(question)
    if raw_results is None:
        raw_results = self._vectorstore.similarity_search_with_score(
            question, k=self._top_k
        )
    raw = raw_results
    context = "\n\n".join(doc.page_content for doc, _ in raw)
    ...
```

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/pipeline.py` | modificar | Añade `retrieve(question) -> list[tuple[Document, float]]`. Modifica `aquery_stream()` para aceptar `raw_results=None` opcional. `query()` no se toca. |
| `chainlit/main_family.py` | modificar | `on_message` llama a `pipeline.retrieve(question)`, abre `cl.Step` con el extracto, y pasa `raw_results` a `aquery_stream()`. Añade `_format_retrieval_step()`. |
| `tests/step_defs/test_e05_t03.py` | crear | Step definitions pytest-bdd para los 4 escenarios del `.feature`. |

No se toca `rag/generator.py`, `rag/retriever.py`, `rag/safety.py`, `rag/language.py`.
No se toca `tests/step_defs/test_e05_t01.py` ni `test_e05_t02.py` — retrocompatibilidad garantizada.

## Orden de implementación TDD

Sigue el orden de los escenarios en `tests/features/e05_t03_rag_steps_visualization.feature`.
Cada ítem = un ciclo rojo → verde antes de pasar al siguiente.

### 1. El pipeline expone los documentos recuperados antes de la respuesta final

**Step definitions** en: `tests/step_defs/test_e05_t03.py`  
**Implementación** en: `rag/pipeline.py` (`retrieve()`)

Notas:
- Fixture: vectorstore fake con `similarity_search_with_score` que devuelve 2 docs con scores.
  Mismo patrón que los tests de E-04 T-06 / `test_e05_t02.py` (monkeypatch de `get_retriever`).
- Verificar que `pipeline.retrieve(question)` devuelve `list[tuple[Document, float]]` con los
  mismos docs y scores que devolvería `similarity_search_with_score`.
- Verificar que el resultado está disponible *antes* de llamar a `aquery_stream()` — la aseveración
  es estructural (retrieve es un método síncrono que devuelve inmediatamente), no temporal.

### 2. Sin resultados de retrieval no se expone un paso vacío

Notas:
- Vectorstore fake cuyo `similarity_search_with_score` devuelve lista vacía `[]`.
- Verificar que `pipeline.retrieve(question)` devuelve `[]`.
- Verificar que no se lanza ninguna excepción.

### 3. Los metadatos expuestos coinciden con los usados en la citación final

Notas:
- Instanciar `RAGPipeline` con un vectorstore fake que registra cuántas veces se llama a
  `similarity_search_with_score` (e.g. un `MagicMock` con `side_effect` contabilizado, o
  simplemente un contador en la fixture).
- Llamar a `raw = pipeline.retrieve(question)` y luego
  `pipeline.aquery_stream(question, raw_results=raw)`.
- Verificar que `similarity_search_with_score` se ha llamado **exactamente una vez** en total
  (la llamada de `retrieve()`, no una segunda dentro de `aquery_stream()`).
- Verificar que `raw` y los docs internos usados por `_build_sources_section` son el mismo objeto
  (identidad de referencia, o equivalencia estructural si se prefiere comparar contenido).

### 4. El chat muestra el paso de recuperación antes de la respuesta

**Step definitions** en: `tests/step_defs/test_e05_t03.py` — usa el patrón de fake `chainlit`
module establecido en `test_e05_t01.py` / `test_e05_t02.py`.  
**Implementación** en: `chainlit/main_family.py`

Notas:
- Fake `chainlit` module: además de `_FakeMessage` (ya existente de T-01/T-02), añade `_FakeStep`
  con soporte de context manager async (`__aenter__`/`__aexit__`) y campo `output`.
- Monkeypatch de `cl.Step` → `_FakeStep`.
- Mock de `_get_pipeline()` que expone:
  - `mock_pipeline.retrieve.return_value = [fake_doc_with_score]`
  - `mock_pipeline.aquery_stream` como generador async que yield-ea `["respuesta fake"]`
- Invocar `await on_message(fake_message)`.
- Aserciones:
  1. `mock_pipeline.retrieve.assert_called_once_with(question)` — se llamó retrieve primero.
  2. `_FakeStep` fue usado como context manager (se abrió un step).
  3. El step tiene `.output` no vacío (contiene texto del extracto).
  4. `mock_pipeline.aquery_stream.assert_called_once_with(question, raw_results=...)` — se pasó
     el mismo objeto devuelto por `retrieve()`.
  5. El `_FakeMessage` acumuló tokens (streaming funcionó).
  6. El orden es: retrieve → step → streaming (verificable con `mock_calls` o capturando el
     instante de llamada de cada componente).

## Restricciones a respetar

- **Agnóstico de proveedor:** esta tarea no toca la capa de generación ni el LLM — sin SDK nativo.
- **Falso Negativo Cero:** `check_alarm_signals`/`apply_safety_filter` no cambian de firma ni de
  momento de invocación; el nuevo `retrieve()` no tiene ningún efecto sobre la seguridad.
- **Retrocompatibilidad:** `aquery_stream()` sin `raw_results` sigue funcionando exactamente igual
  — los tests de T-01/T-02 no se modifican.
- **Reparto git:** el agente en Antigravity no hace `push`/`merge`. La rama de trabajo es
  `task/E05-T03-rag-steps-visualization` (a crear por Marcos antes de empezar).

## Lo que queda fuera de esta tarea

- Formato visual avanzado del `cl.Step` (iconos custom, colapsar por defecto) — Chainlit lo
  gestiona de forma nativa; el step aparece colapsable por defecto.
- Perfil profesional (`main_professional.py`) — sigue bloqueado (stub).
- Cualquier cambio en `rag/generator.py`, `rag/safety.py`, `rag/language.py`, `rag/retriever.py`.
- `RAGPipeline.query()` — no se modifica (D-034).
