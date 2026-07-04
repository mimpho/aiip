# Plan — E-04 T-06 Pipeline end-to-end y tests de integración

## Contexto técnico

Contratos ya implementados que `RAGPipeline.query()` debe orquestar (no rediseñar, solo conectar):

- `rag/config.py::load_rag_config() -> dict` — ya expone `GOOGLE_API_KEY`, `CHROMA_PATH`, `HF_TOKEN`, `RAG_TOP_K`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_MAX_TOKENS`.
- `rag/embeddings.py::get_embeddings() -> Embeddings` — instancia real de `BGEEmbeddings` (bge-m3), sin parámetros.
- `rag/retriever.py::get_retriever(embeddings, chroma_path, collection_name, top_k=5) -> Chroma` — devuelve el vectorstore directamente. Recuperar chunks con `vectorstore.similarity_search_with_score(query, k=top_k)`, que devuelve `[(Document, distancia_coseno)]`. Convertir a similitud con `distance_to_similarity(distance)`. Con colección vacía o `CHROMA_PATH` inexistente, Chroma no lanza excepción — devuelve `[]` (confirmado en T-02, ver D-020).
- `rag/language.py::detect_language(text, default="es") -> str` y `build_language_instruction(language) -> str`.
- `rag/generator.py::RAGGenerator(config).generate(question, context, language) -> str` — construye el LLM en `__init__`; lanza `EnvironmentError` si falta `GOOGLE_API_KEY`; propaga cualquier excepción del LLM sin atraparla (confirmado en T-04).
- `rag/safety.py::check_alarm_signals(query) -> bool` y `apply_safety_filter(response, has_alarm) -> str`.

**Formato de contexto para el generador:** no hay un formato fijado explícitamente en decisions.md más allá de que `RAGGenerator.generate()` recibe `context: str`. Se construye uniendo los `page_content` de los chunks recuperados con `"\n\n"` — igual de simple que el ejemplo de contexto ya usado en `tests/step_defs/test_e04_t04.py` (chunks numerados en texto plano). Si no hay chunks, `context` es `""`.

**Mock del LLM:** igual patrón que `test_e04_t04.py` — parchear `rag.generator.ChatGoogleGenerativeAI`, no `rag.pipeline.ChatGoogleGenerativeAI`. `RAGPipeline` no importa el LLM directamente, solo instancia `RAGGenerator`, así que el punto de parcheo es el mismo de siempre.

**Fixtures de ChromaDB:** usar `tmp_path` de pytest como `chroma_path` (aislado por test, como en `test_e04_t02.py`), y el fixture `embeddings_model` de scope `session` (bge-m3 real, sin mock — es local y gratuito). Reutilizar como contenido de chunks las mismas frases ya usadas en `test_e04_t04.py` (agammaglobulinemia de Bruton) para no inventar contenido clínico nuevo.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/pipeline.py` | modificar | Implementar `RAGPipeline.__init__(config)` y `query(question) -> str`, sustituyendo el stub `NotImplementedError` |
| `tests/step_defs/test_e04_t06.py` | crear | Step definitions pytest-bdd para los 6 escenarios de `e04_t06_e2e_pipeline.feature` |
| `backlog/epics.md` | modificar (al cerrar) | Marcar T-06 como completada — lo hace `task-close`, no este plan |

## Orden de implementación TDD

1. **Pipeline completo — query en castellano produce respuesta en castellano**
   - Step definitions en: `tests/step_defs/test_e04_t06.py`
   - Implementación en: `rag/pipeline.py`
   - Notas: primer ciclo — construye `RAGPipeline.__init__` (guarda config, instancia `get_embeddings()`, `get_retriever(...)`, `RAGGenerator(config)`) y `query()` con el flujo mínimo: `detect_language` → `similarity_search_with_score` → construir `context` → `generate` → devolver respuesta sin pasar aún por `safety`. Mock de `ChatGoogleGenerativeAI` devolviendo una respuesta en castellano fija.

2. **Pipeline completo — query en inglés produce respuesta en inglés**
   - Notas: confirma que `detect_language` + `build_language_instruction` (vía `RAGGenerator.generate`) se propaga correctamente. No debería requerir cambios de implementación si el escenario 1 ya pasa la instrucción de idioma correcta — este escenario es principalmente de regresión/cableado.

3. **Pipeline completo — Falso Negativo Cero preservado end-to-end**
   - Notas: añade a `query()` la llamada a `check_alarm_signals(question)` antes de generar (o en paralelo) y `apply_safety_filter(response, has_alarm)` tras `generate()`, antes de devolver. Mock del LLM debe devolver una respuesta con lenguaje tranquilizador (p. ej. "no es grave, no te preocupes") para verificar que el filtro actúa incluso si el LLM no lo hizo bien.

4. **Retrieval sin resultados no bloquea la generación**
   - Notas: usar un `tmp_path` distinto sin `add_texts()` (colección vacía) o un `chroma_path` a un subdirectorio que no existe. `similarity_search_with_score` debe devolver `[]` sin excepción (ya garantizado por Chroma/T-02) — el pipeline solo necesita manejar `context = ""` sin fallar al construir el prompt.

5. **Propagación de error de autenticación del LLM**
   - Notas: mockear `ChatGoogleGenerativeAI.invoke` con `side_effect` de una excepción (igual que en `test_e04_t04.py`, escenario de clave inválida) y verificar que `RAGPipeline.query()` no la atrapa — se relanza tal cual. No reimplementar lógica de manejo de errores en el pipeline; debe limitarse a no interceptarla.

6. **@integration — Pipeline completo con LLM real**
   - Notas: mismo patrón que el escenario `@integration` de `test_e04_t04.py` — `pytest.skip()` si `RUN_LLM_INTEGRATION_TESTS != "1"` o falta `GOOGLE_API_KEY` real. Usa `load_rag_config()` real y una colección con al menos 1 chunk indexado.

## Restricciones a respetar

- **Agnóstico de proveedor (D-010):** el pipeline no debe importar `google.generativeai` ni ningún SDK nativo — solo consume `RAGGenerator`, que ya encapsula LangChain.
- **Falso Negativo Cero (D-002):** `apply_safety_filter` se aplica siempre sobre la respuesta final antes de devolverla, sin excepciones ni bypass condicional.
- **D-020:** no introducir manejo de errores nuevo para ChromaDB no disponible — el comportamiento correcto es no fallar.

## Lo que queda fuera de esta tarea

- Ingesta de la KB real de producción — es E-06.
- Selector explícito de idioma — evolución futura de D-011.
- Capa *pre-retrieval* de seguridad (prompt injection, filtrado PII — OWASP LLM01/LLM06) — explícitamente fuera de alcance también en T-05 (D-019), queda como backlog de seguridad pendiente.
- Integración del pipeline en Chainlit — es E-05.
