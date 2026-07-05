# Plan — E-04 T-02 Embeddings y retriever con ChromaDB

## Contexto técnico

**Decisión D-016 (nueva, ver `decisions.md`):**
- `get_retriever()` devuelve el vectorstore `Chroma` de `langchain-chroma` directamente (no `.as_retriever()`), para poder acceder a scores por chunk.
- La colección se crea/abre con `collection_metadata={"hnsw:space": "cosine"}` — métrica estándar para embeddings normalizados como bge-m3.
- Nueva variable de entorno opcional `RAG_TOP_K` (default `5`), ya añadida a `.env.example`. No es obligatoria en `rag/config.py` (no bloquea el arranque si falta, a diferencia de `GOOGLE_API_KEY`/`HF_TOKEN`/`CHROMA_PATH`).

**Hallazgo de research (confirmado en documentación de Chroma/LangChain):** `Chroma.similarity_search_with_score()` devuelve **distancia** coseno (menor = más similar), incluso configurando `hnsw:space="cosine"` — nunca similitud directamente. Para que el score expuesto cumpla la semántica de similitud creciente que fija D-016 y que esperan los escenarios del `.feature` ("score de similitud mayor que 0.0"), `rag/retriever.py` debe convertir explícitamente `similarity = 1 - distance` antes de devolver los resultados.

**Embeddings bge-m3:** se cargan via `sentence-transformers` (`SentenceTransformer("BAAI/bge-m3")`), envueltos en `langchain_huggingface.HuggingFaceEmbeddings` (o el wrapper equivalente que exponga la interfaz `Embeddings` de LangChain que espera `langchain-chroma`) para que `get_embeddings()` sea compatible con el constructor de `Chroma`. Dimensión esperada: 1024.

**Aislamiento de tests:** ChromaDB persiste en `CHROMA_PATH` (variable de producción). Los tests NO deben escribir ahí — cada test crea su colección en un directorio temporal (`tmp_path` de pytest) o usa un cliente Chroma efímero, para no contaminar datos reales y garantizar tests idempotentes.

**Carga del modelo:** bge-m3 es un modelo pesado (~2GB) y su descarga/carga es lenta. Usar un fixture `scope="session"` para cargarlo una sola vez y compartirlo entre los 4 escenarios, evitando recargarlo en cada uno.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/embeddings.py` | modificar | Implementar `get_embeddings()` — carga bge-m3 via sentence-transformers, expuesto como `Embeddings` compatible con LangChain |
| `rag/retriever.py` | modificar | Implementar `get_retriever(embeddings, chroma_path, collection_name, top_k=5)` — crea/abre colección Chroma con métrica coseno, devuelve vectorstore; añadir función de conversión distancia→similitud |
| `rag/config.py` | modificar | Añadir `RAG_TOP_K` como variable opcional con default `5` (no en `REQUIRED_VARS`) |
| `.env.example` | ya modificado | `RAG_TOP_K=5` añadido en la revisión de Cowork |
| `tests/step_defs/test_e04_t02.py` | crear | Step definitions pytest-bdd para `e04_t02_embeddings_retriever.feature` |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Dimensión correcta del embedding bge-m3** — `tests/features/e04_t02_embeddings_retriever.feature`
   - Step definitions en: `tests/step_defs/test_e04_t02.py`
   - Implementación en: `rag/embeddings.py`
   - Notas: usar fixture `scope="session"` para cargar el modelo una sola vez. `get_embeddings().embed_query(texto)` (o el método equivalente de la interfaz `Embeddings`) debe devolver un vector de 1024 floats.

2. **Retrieval con documentos indexados devuelve resultados** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e04_t02.py`
   - Implementación en: `rag/retriever.py`
   - Notas: el `Given` indexa 10 chunks de prueba (strings cortos hardcodeados sobre IDP, no dependen de la KB real de E-06) en una colección Chroma efímera (`tmp_path`). El `When` llama a `get_retriever(...).similarity_search_with_score(query, k=top_k)` (o el wrapper que aplique la conversión a similitud). El `Then` verifica `1 <= len(resultados) <= 5` y que cada score convertido sea `> 0.0`.

3. **Retrieval cross-lingual castellano sobre chunks en inglés** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e04_t02.py`
   - Implementación en: `rag/retriever.py` (sin cambios si el escenario 2 ya pasa — bge-m3 resuelve el cross-lingual por diseño, D-011)
   - Notas: fixture con chunks en inglés sobre "primary immunodeficiency"; query en castellano. Verifica que bge-m3 recupera al menos 1 chunk relevante sin lógica adicional de traducción.

4. **Retrieval con colección vacía devuelve lista vacía sin excepción** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e04_t02.py`
   - Implementación en: `rag/retriever.py`
   - Notas: colección Chroma creada pero sin documentos indexados. `similarity_search_with_score` sobre una colección vacía debe devolver `[]`, no lanzar excepción — verificar que el wrapper no asume que siempre hay resultados.

## Restricciones a respetar

- **D-010 (agnosticismo de proveedor):** `rag/embeddings.py` usa `sentence-transformers` directamente para bge-m3 (no es un LLM de proveedor, no aplica la restricción de "siempre via LangChain" de forma estricta aquí, pero el wrapper debe exponer la interfaz `Embeddings` de LangChain para que el resto del pipeline no dependa del detalle de implementación).
- **D-011 (multiidioma):** no introducir lógica de traducción — el cross-lingual retrieval depende exclusivamente de bge-m3.
- **Configuración:** `RAG_TOP_K` y la ruta de Chroma nunca hardcodeadas fuera de `rag/config.py` / `.env.example`.

## Lo que queda fuera de esta tarea

- Integración del retriever en el pipeline end-to-end (`rag/pipeline.py`) — eso es T-06.
- Detección de idioma antes de la query — eso es T-03.
- Creación de la colección de producción con datos reales de la KB — eso es E-06.
- Ajuste fino de `RAG_TOP_K` según resultados RAGAS — eso es E-07/E-09 (D-019 en `docs/tech-spec.md`).
