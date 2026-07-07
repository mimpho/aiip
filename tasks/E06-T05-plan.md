# Plan — E-06 T-05 Pipeline de ingesta end-to-end

## Contexto técnico

Per D-024: reprocesamiento completo (no incremental) en cada ejecución, con borrado de chunks existentes de cada documento (`source`+`filename`) antes de reinsertar sus chunks nuevos, y aislamiento de fallos de carga movido a `ingestion/loader.py` (no al pipeline).

`ingestion/indexer.py::index_chunks()` (T-04) ya expone `get_retriever()` reutilizado y el patrón `vectorstore.get(where={"$and": [...]})` para filtrar por metadatos — ya verificado y en verde en `tests/step_defs/test_e06_t04.py` (Scenario "Reindexación no duplica"). El nuevo `delete_document_chunks()` reutiliza el mismo patrón de filtro añadiendo `vectorstore.delete(ids=...)`. Sin research pendiente adicional: el comportamiento de `.get(where=...)` y el upsert por ID en `add_documents()` ya quedaron confirmados al cerrar T-04.

`ingestion/loader.py::load_documents()` ya captura y continúa ante formato no soportado (`warnings.warn` + `continue`, sin try/except porque no hay llamada que pueda fallar en ese caso). El nuevo caso (fichero de formato soportado pero corrupto) sí necesita try/except alrededor de `load_fn(file_path)`, con el mismo patrón de warning.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `ingestion/loader.py` | modificar | Envuelve `load_fn(file_path)` en try/except: si falla, `warnings.warn("Fallo al cargar el fichero, omitido: ...")` + continúa con el resto |
| `ingestion/indexer.py` | modificar | Añade `delete_document_chunks(source, filename, embeddings, chroma_path, collection_name="family")`: busca IDs existentes de ese documento vía `vectorstore.get(where=...)` y los borra con `vectorstore.delete(ids=...)` |
| `ingestion/pipeline.py` | crear | `run_ingestion_pipeline(source_path, chroma_path, embeddings, collection_name="family", profile="family")`: orquesta `load_documents()` → `chunk_documents()` → agrupa chunks por `(source, filename)` → por cada documento, `delete_document_chunks()` + `index_chunks()` → construye resumen final a partir de los warnings capturados del loader |
| `tests/step_defs/test_e06_t05.py` | crear | Step definitions de los 4 escenarios de `tests/features/e06_t05_e2e_ingestion_pipeline.feature` |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Ejecución completa puebla la colección family** — `tests/features/e06_t05_e2e_ingestion_pipeline.feature`
   - Step definitions en: `tests/step_defs/test_e06_t05.py`
   - Implementación en: `ingestion/pipeline.py`
   - Notas: fixtures de `data/raw/` en `tmp_path` (2-3 fuentes/carpetas con 1-2 ficheros HTML válidos cada una, mismo patrón que `test_e06_t02.py`). `run_ingestion_pipeline()` en su versión mínima: `load_documents(source_path)` → `chunk_documents(documents)` → agrupar por `(source, filename)` → por cada grupo, `delete_document_chunks()` (no-op si no había nada) + `index_chunks()`. Verificar que la colección `family_test` queda poblada y que cada chunk conserva `source`, `filename`, `language` en sus metadatos (ya generados en T-02/T-03, el pipeline no los toca).

2. **Ejecución repetida no duplica chunks**
   - Step definitions en: `tests/step_defs/test_e06_t05.py`
   - Implementación en: `ingestion/pipeline.py` (sin cambios si el paso 1 ya agrupa y borra-antes-de-insertar por documento)
   - Notas: ejecutar `run_ingestion_pipeline()` dos veces sobre las mismas fuentes de fixture y comparar el total de chunks en la colección antes/después de la segunda ejecución — debe ser idéntico.

3. **Un documento que cambia de número de chunks no deja huérfanos**
   - Step definitions en: `tests/step_defs/test_e06_t05.py`
   - Implementación en: `ingestion/indexer.py` (`delete_document_chunks`)
   - Notas: indexar un documento fixture con N chunks (llamando directamente a `index_chunks` o vía una primera ejecución del pipeline), modificar el fichero fuente para que genere M < N chunks, volver a ejecutar el pipeline, y verificar con `vectorstore.get(where={"$and": [{"source":...},{"filename":...}]})` que el conteo de chunks de ese documento es exactamente M (sin restos de los `N - M` chunks antiguos).

4. **Fallo en una fuente no detiene el procesamiento de las demás**
   - Step definitions en: `tests/step_defs/test_e06_t05.py`
   - Implementación en: `ingestion/loader.py`
   - Notas: fixture con una fuente cuyo fichero HTML/PDF está corrupto (p. ej. bytes inválidos con extensión `.pdf` para que `PyPDFLoader` falle al parsear) junto a otra fuente válida. Verificar que `run_ingestion_pipeline()` no lanza excepción, que la fuente válida queda indexada, y que el resumen final devuelto (`resultado["failures"]` o similar) menciona la fuente/fichero que falló. Capturar los warnings del loader dentro del pipeline (`warnings.catch_warnings(record=True)`) para construir esa lista de fallos — mismo patrón que ya usan los tests de T-02.

## Restricciones a respetar

- Continuidad de D-016/D-023: la colección se abre siempre vía `get_retriever()`, sin reconfigurar métrica ni `CHROMA_PATH` propio.
- Continuidad de D-021: el pipeline es quien decide qué se reindexa (aquí: todo el corpus, per D-024) — el indexer (T-04) solo ejecuta lo que se le pasa.
- Continuidad de D-022: el pipeline no genera ni modifica metadatos (`language`, `date_indexed`, `profile`) — ya vienen del chunker.
- D-024: no introducir lógica incremental basada en manifest en esta tarea — queda anotada como optimización futura, no la implementes aunque parezca "más correcta".
- Los cambios en `loader.py`/`indexer.py` son aditivos: no deben romper ningún test ya cerrado de `test_e06_t02.py` / `test_e06_t04.py`.

## Lo que queda fuera de esta tarea

- Estrategia incremental de reindexación basada en manifest (D-024, futuro).
- Ejecución del pipeline contra la KB real de `data/raw/` — eso es T-07 (smoke test manual), que corre sobre `RAGPipeline`, no sobre este pipeline de ingesta directamente. Si T-07 necesita antes poblar la colección real, hará falta un script/CLI que invoque `run_ingestion_pipeline()` con las rutas de producción — no está en el alcance de T-05, que solo entrega la función y sus tests.
- Datasheet DAIMS de la KB — T-06.
