# Plan — E-06 T-08 Enlazar fuentes citadas a su URL original

## Contexto técnico

**`chunker.py` no necesita modificación** (corrige la nota original de `backlog/epics.md` línea
204, que asumía que la propagación tocaba `ingestion/chunker.py`). Verificado en el código
instalado de `langchain_text_splitters` (`base.py`, `TextSplitter.create_documents()`):
`metadata = copy.deepcopy(metadatas_[i])` — cada chunk generado por `split_documents()` hereda
automáticamente una copia del `metadata` completo del documento original. Es el mismo mecanismo
por el que `source`/`filename` ya sobreviven de documento a chunk sin código explícito en
`chunker.py` hoy. Si `ingestion/loader.py` añade `doc.metadata["url"]` antes de que el chunker
procese el documento, cada chunk resultante ya lo hereda solo.

`ingestion/loader.py::load_documents()` ya carga el manifest en memoria (`manifest =
load_manifest(manifest_path)`) y ya calcula `manifest_key = f"{source_dir.name}/{file_path.name}"`
antes de llamar a `sync_entry(manifest, manifest_key, file_path)`. `sync_entry()` (D-021) nunca
toca el campo `url` de una entrada existente — solo `checksum`/`fecha` — así que tras llamarlo,
`manifest["documents"][manifest_key]["url"]` es seguro de leer sea cual sea el resultado de
`sync_entry()` (entrada nueva con `url: None`, entrada existente sin cambios, o checksum
actualizado).

`rag/pipeline.py::_build_sources_section()` ya deduplica por `(source, filename)` y ya filtra
chunks sin `source`/`filename` (D-026). Necesita: capturar también `url` del metadata de cada
chunk, y cambiar el formato de línea a enlace markdown cuando `url` no es `None`.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `ingestion/loader.py` | modificar | Añade `doc.metadata["url"]` a partir de la entrada del manifest, junto a `source`/`filename` ya existentes |
| `rag/pipeline.py` | modificar | `_build_sources_section()` renderiza `- [{filename}]({url})` cuando hay `url`; mantiene `- {source}/{filename}` cuando no la hay (D-026, sin regresión) |
| `tests/step_defs/test_e06_t08.py` | crear | Step definitions de los 5 escenarios de `tests/features/e06_t08_source_url_citation.feature` |

`ingestion/chunker.py` no se toca — ver Contexto técnico.

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **El loader añade la URL del manifest al metadata del documento** — `tests/features/e06_t08_source_url_citation.feature`
   - Step definitions en: `tests/step_defs/test_e06_t08.py`
   - Implementación en: `ingestion/loader.py`
   - Notas: en el bucle de `load_documents()`, tras `sync_entry(manifest, manifest_key, file_path)`,
     leer `url = manifest["documents"][manifest_key].get("url")` y añadir
     `doc.metadata["url"] = url` junto a las líneas ya existentes que asignan `source`/`filename`
     (no crear una entrada de manifest nueva para este escenario — usar fixture con manifest
     preexistente conteniendo `url`, mismo patrón que `fichero_checksum_desactualizado` en
     `test_e06_t02.py`).

2. **El loader deja la URL a None si el manifest no la documenta**
   - Step definitions en: `tests/step_defs/test_e06_t08.py`
   - Implementación en: `ingestion/loader.py` (sin cambios adicionales sobre el paso 1 — mismo
     código, `entry.get("url")` ya devuelve `None` si el campo es `null` en el JSON o si la
     entrada se acaba de crear vía `sync_entry`)
   - Notas: fixture con fichero nuevo sin entrada de manifest previa (como
     `fichero_nuevo_sin_manifest_entry` de `test_e06_t02.py`) — `sync_entry` crea la entrada con
     `url: None`.

3. **El chunker propaga la URL del documento a cada chunk**
   - Step definitions en: `tests/step_defs/test_e06_t08.py`
   - Implementación: ninguna — escenario de regresión que verifica el `copy.deepcopy()` de
     LangChain documentado en Contexto técnico. Debe pasar en verde sin tocar `chunker.py`.
   - Notas: usar `chunk_documents()` directamente sobre un `Document` fixture con
     `metadata={"url": "https://ejemplo.org/doc", ...}` ya asignado a mano (sin pasar por el
     loader) y comprobar que todos los chunks resultantes conservan `url`.

4. **La sección de fuentes muestra un enlace markdown cuando el chunk tiene URL**
   - Step definitions en: `tests/step_defs/test_e06_t08.py`
   - Implementación en: `rag/pipeline.py` (`_build_sources_section`)
   - Notas: `_build_sources_section(raw_results, language)` recibe `raw_results` como lista de
     `(Document, score)` — construir el fixture con `Document(page_content=..., metadata={"source":
     ..., "filename": ..., "url": ...})`. Cambiar la deduplicación de `(source, filename)` a
     capturar también `url` del primer chunk visto de ese par; formato de línea:
     `f"- [{filename}]({url})"` cuando `url` no es `None`.

5. **La sección de fuentes cae al nombre de fichero si el chunk no tiene URL**
   - Step definitions en: `tests/step_defs/test_e06_t08.py`
   - Implementación en: `rag/pipeline.py` (mismo cambio del paso 4 — rama `else`)
   - Notas: fixture sin clave `url` en el metadata (no solo `url: None` — cubre también chunks ya
     indexados antes de T-08, que no tendrán la clave en absoluto). Usar `.get("url")` en vez de
     `["url"]` para no romper con chunks antiguos sin la clave. Verificar que el formato de línea
     coincide exactamente con el comportamiento actual (`- {source}/{filename}`, sin corchetes ni
     paréntesis) — es el escenario de no-regresión de D-026.

## Restricciones a respetar

- Continuidad de D-021: `sync_entry()` no se modifica — sigue sin tocar `url` en ninguna rama.
- Continuidad de D-026: sin `url`, la sección de fuentes debe verse exactamente igual que hoy —
  no romper los tests mockeados de E-04 T-04/T-06 (fixtures sin metadata `source`/`filename`,
  que ya hacen que `_build_sources_section` devuelva `""`).
- No introducir el fallback de nivel 2 (mapeo `source` → URL genérica) — descartado en D-029.
- No introducir verificación de vida del enlace (`url_status`) — fuera de alcance, anotado en
  `backlog/ideas.md`.

## Nota de cierre (post-implementación)

`skills/kb-maintenance/SKILL.md` y `scripts/sync_skills.sh` se crearon durante la sesión de
`task-start`/`task-close` de T-08, sin relación funcional con la citación de URLs, pero se
incluyen en el mismo commit/PR por simplicidad (separarlos no compensaba el coste de staging
por hunks). El backfill de checksums de `data/raw/manifest.json` sí queda fuera, para después
del `--force-reingest` en `epic/E06-kb-ingestion` (ver `docs/kb-maintenance.md`).

## Lo que queda fuera de esta tarea

- Reindexar la KB real (`python scripts/smoke_test_rag.py --force-reingest`) — acción manual de
  Marcos después de que el código esté en verde, no parte del ciclo TDD.
- Fallback de nivel 2 y script de verificación de vida de URL (ver D-029 y `backlog/ideas.md`).
- Cualquier cambio a `ingestion/chunker.py` — no aplica, ver Contexto técnico.
