# Plan — E-06 T-03 Estrategia de chunking multiidioma

## Contexto técnico

**Research confirmado (Cowork, previo a este plan):** `langchain-text-splitters==1.1.2` (ya en `requirements.txt`) expone `RecursiveCharacterTextSplitter.from_huggingface_tokenizer(tokenizer, **kwargs) -> TextSplitter` — classmethod confirmado por inspección directa del paquete instalado. Acepta cualquier `PreTrainedTokenizerBase` de `transformers` (ya instalado vía `sentence-transformers`, sin dependencia nueva) y cuenta longitud en tokens reales del tokenizer, no en caracteres. Cargar solo el tokenizer (`AutoTokenizer.from_pretrained("BAAI/bge-m3")`) es liviano — no requiere cargar el modelo completo de embeddings (`SentenceTransformer`, usado en `rag/embeddings.py` y reutilizado por el indexer en T-04).

**Metadatos que ya llegan del loader (T-02, cerrado):** cada `Document` trae `metadata["source"]` (nombre de carpeta de fuente) y `metadata["filename"]`. `PyPDFLoader` añade además `metadata["page"]`; `BSHTMLLoader` puede añadir `metadata["title"]`. Ninguno de los dos añade `language`, `date_indexed` ni `profile` — estos tres los genera esta tarea (D-022).

**Reutilización de `rag/language.py` (D-017):** `detect_language(text: str, default: str = "es") -> str` ya existe y fija `DetectorFactory.seed = 0` a nivel de módulo (determinismo). Se reutiliza tal cual para detectar el idioma de cada documento completo antes de trocear — no hace falta un detector nuevo ni tocar `rag/language.py`.

**Ver D-022 en `decisions.md`** para la justificación completa de cada decisión de esta sección.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `ingestion/chunker.py` | modificar | Implementa `chunk_documents(documents, profile="familiar")`: detecta idioma por documento, trocea con `RecursiveCharacterTextSplitter.from_huggingface_tokenizer` (tokenizer bge-m3), añade `language`/`date_indexed`/`profile` a los metadatos de cada chunk resultante |
| `ingestion/config.py` | modificar | Añade `RAG_CHUNK_SIZE` (default `512`) y `RAG_CHUNK_OVERLAP` (default `64`) a `load_ingestion_config()`, mismo patrón que `KB_RAW_DATA_PATH` |
| `.env.example` | modificar | Añade `RAG_CHUNK_SIZE=512` y `RAG_CHUNK_OVERLAP=64` bajo la sección "Ingesta de la KB (E-06)" |
| `tests/step_defs/test_e06_t03.py` | crear | Step definitions pytest-bdd para `e06_t03_chunking_strategy.feature` |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Chunking de un documento largo** — `tests/features/e06_t03_chunking_strategy.feature`
   - Step definitions en: `tests/step_defs/test_e06_t03.py`
   - Implementación en: `ingestion/chunker.py`, `ingestion/config.py`
   - Notas: fixture con un `Document` de texto largo (>512 tokens del tokenizer bge-m3 — confirmar en el ciclo rojo cuántos caracteres hacen falta para superar ese umbral, no asumir una equivalencia caracteres/token de antemano). `chunk_documents()` construye el splitter con `RecursiveCharacterTextSplitter.from_huggingface_tokenizer(AutoTokenizer.from_pretrained("BAAI/bge-m3"), chunk_size=config["RAG_CHUNK_SIZE"], chunk_overlap=config["RAG_CHUNK_OVERLAP"], separators=["\n\n", "\n", ". ", " "])`. Verificar tamaño y solapamiento con el mismo tokenizer en el test (no contando caracteres).

2. **Metadatos de trazabilidad conservados y generados en el chunk** — mismo `.feature`
   - Implementación en: `ingestion/chunker.py`
   - Notas: tras `split_documents()` (que ya propaga `source`/`filename` automáticamente a cada chunk resultante, comportamiento nativo de LangChain), añadir explícitamente `language` (ver escenario 4), `date_indexed` (`datetime.date.today().isoformat()`) y `profile` (el parámetro `profile` de la función, default `"familiar"`) a `chunk.metadata` de cada chunk.

3. **Documento más corto que el tamaño de chunk** — mismo `.feature`
   - Implementación en: `ingestion/chunker.py`
   - Notas: comportamiento nativo de `RecursiveCharacterTextSplitter` — no requiere lógica especial, solo confirmar que el resultado es una lista de un único chunk con el contenido íntegro.

4. **El idioma del chunk respeta el idioma original de la fuente** — mismo `.feature`
   - Implementación en: `ingestion/chunker.py`
   - Notas: fixture con `Document(page_content="<texto en español, >10 caracteres>", metadata={"source": "upiip", "filename": "doc.html"})`. Llamar a `rag.language.detect_language(document.page_content)` **antes** de trocear ese documento, y asignar el resultado a todos los chunks que salgan de él. Confirmar que el texto no se altera (no hay traducción en ningún punto del chunker).

5. **El idioma se detecta una vez por documento, no por chunk** — mismo `.feature`
   - Implementación en: `ingestion/chunker.py`
   - Notas: fixture con un documento largo en inglés que produce ≥2 chunks. Verificar que `detect_language()` se invoca una vez por `Document` de entrada (no una vez por chunk de salida) y que todos los chunks resultantes de un mismo documento comparten idéntico `metadata["language"]`. Si se implementa con un mock/spy sobre `rag.language.detect_language`, este escenario también sirve de guarda de regresión frente a una implementación futura que detecte por chunk.

## Restricciones a respetar

- **D-022:** `date_indexed` se genera aquí (T-03), no en el indexer (T-04) — no anticipar lógica de indexación real en este chunker.
- **D-011 / D-022:** no traducir ningún texto en ningún punto del chunker — el idioma se detecta y se etiqueta, el contenido permanece en su idioma original.
- **Convenciones del repo:** `RAG_CHUNK_SIZE`/`RAG_CHUNK_OVERLAP` en `.env`/`ingestion/config.py`, nunca hardcodeados en `chunker.py`.
- **Agnóstico de proveedor (D-010):** no aplica de forma directa — el tokenizer es de bge-m3 (embeddings), no de un proveedor de LLM.

## Lo que queda fuera de esta tarea

- Cálculo de embeddings de los chunks — T-04 (indexer).
- Indexación real en ChromaDB — T-04.
- Decidir qué documentos (re)trocear a partir del estado del manifest — T-05 (D-021).
- Ajuste empírico de `chunk_size`/`chunk_overlap`/separadores a partir de resultados RAGAS — E-07/E-09, ya anticipado en `docs/tech-spec.md` sección 13.
