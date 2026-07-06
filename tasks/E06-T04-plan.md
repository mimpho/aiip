# Plan — E-06 T-04 Indexer: indexación en ChromaDB (colección `family`)

## Contexto técnico

`ingestion/indexer.py` es un stub de T-01 (`index_chunks(chunks): raise NotImplementedError`) — no recibe `embeddings`, `chroma_path` ni `collection_name`, que sí necesita para escribir en ChromaDB. El patrón ya cerrado en E-04 (D-016, T-02) usa `get_retriever()` de `rag/retriever.py`, que devuelve el vectorstore `Chroma` de `langchain-chroma` directamente (no `.as_retriever()`), con `collection_metadata={"hnsw:space": "cosine"}`. El indexer de T-04 reutiliza esa misma función para abrir la colección y escribe sobre el vectorstore devuelto con `.add_documents(chunks, ids=...)`.

**Punto sin confirmar (research pendiente para Antigravity, no verificable desde Cowork por falta de entorno):** no está confirmado si la versión instalada de `langchain-chroma` usa `upsert` (sobreescribe in-place si el ID ya existe) o `add` (puede duplicar o lanzar error si el ID ya existe) en `add_documents`/`add_texts` cuando se pasan `ids` explícitos. Esto determina si basta con pasar los mismos IDs deterministas para satisfacer el Scenario "Reindexación no duplica chunks", o si el indexer necesita borrar explícitamente los IDs existentes antes de volver a añadirlos (`collection.delete(ids=...)` seguido de `add`). Confirmar leyendo el código de `langchain_chroma.Chroma.add_documents`/`add_texts` instalado en el `.venv` del proyecto antes de implementar el Scenario 3.

Per D-023: colección de producción `"family"` (test: `"family_test"`), IDs deterministas de `source + filename + índice de chunk`, y `CHROMA_PATH` reutilizando `rag.config.load_rag_config()` (no una entrada nueva en `ingestion/config.py`).

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `ingestion/indexer.py` | modificar | Implementa `index_chunks(chunks, embeddings, chroma_path, collection_name="family")`: abre el vectorstore vía `get_retriever()`, genera IDs deterministas por chunk, escribe con `add_documents()` capturando y recontextualizando errores de escritura |
| `tests/step_defs/test_e06_t04.py` | crear | Step definitions de los 4 escenarios de `tests/features/e06_t04_chromadb_indexer.feature` |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Indexación de chunks con embeddings bge-m3** — `tests/features/e06_t04_chromadb_indexer.feature`
   - Step definitions en: `tests/step_defs/test_e06_t04.py`
   - Implementación en: `ingestion/indexer.py`
   - Notas: happy path base. `index_chunks()` abre el vectorstore con `get_retriever(embeddings, chroma_path, collection_name)` y llama a `.add_documents(chunks, ids=[...])`. Verificar que los metadatos de cada chunk (`source`, `filename`, `language`, `date_indexed`, `profile` — ya generados en T-03 por D-022) se conservan tal cual, sin que el indexer añada o modifique ninguno.

2. **El ID de cada chunk es determinista, no aleatorio**
   - Step definitions en: `tests/step_defs/test_e06_t04.py`
   - Implementación en: `ingestion/indexer.py`
   - Notas: función auxiliar (p. ej. `_chunk_id(chunk, index)`) que genere el ID a partir de `chunk.metadata["source"] + chunk.metadata["filename"] + índice del chunk dentro del documento` (hash sha256, mismo estilo que `ingestion/manifest.py::compute_checksum`). Dos llamadas a `index_chunks()` sobre los mismos chunks deben producir exactamente los mismos IDs.

3. **Reindexación del mismo documento no duplica chunks**
   - Step definitions en: `tests/step_defs/test_e06_t04.py`
   - Implementación en: `ingestion/indexer.py`
   - Notas: depende del punto sin confirmar del research previo. Si `add_documents` no hace upsert automático por ID, añadir un paso explícito de borrado (`collection.delete(ids=...)`) antes de reinsertar. Verificar contando chunks de ese documento en la colección (filtrando por `source`+`filename` en los metadatos) antes y después de la segunda ejecución.

4. **Fallo de escritura en ChromaDB se propaga con contexto**
   - Step definitions en: `tests/step_defs/test_e06_t04.py`
   - Implementación en: `ingestion/indexer.py`
   - Notas: mockear el vectorstore (parchear el método de escritura, p. ej. `add_documents`) para forzar una excepción. `index_chunks()` debe capturarla y relanzar (o envolver) indicando explícitamente qué documento (`source`/`filename`) y qué índice de chunk estaba escribiendo — no silenciar ni perder ese contexto.

## Restricciones a respetar

- Continuidad de D-016: la colección se abre con métrica coseno vía `get_retriever()`, sin reconfigurar `hnsw:space`.
- Continuidad de D-021: T-04 no decide qué documentos reindexar ni cuándo borrar chunks obsoletos de un documento que cambió de chunking — eso es T-05. T-04 solo escribe lo que recibe.
- Continuidad de D-022: los metadatos (`language`, `date_indexed`, `profile`) ya vienen generados en el chunk — el indexer no los genera ni los sobreescribe.

## Lo que queda fuera de esta tarea

- Orquestación loader → chunker → indexer (T-05).
- Borrado de chunks huérfanos cuando un documento cambia de número/orden de chunks entre ejecuciones (queda como nota abierta para T-05, D-021/D-023).
- Cualquier lógica de qué hacer ante un manifest que indica documento nuevo/modificado — eso ya lo decide T-05, no T-04.
