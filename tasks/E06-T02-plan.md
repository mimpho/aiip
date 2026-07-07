# Plan — E-06 T-02 Loader de documentos fuente

## Contexto técnico

**Comportamiento de metadatos de los loaders de `langchain-community` (research T-02):**

- `PyPDFLoader(file_path).load()` devuelve una lista de `Document` (uno por página), cada uno con `metadata["source"] = file_path` (ruta completa del fichero) y `metadata["page"]`. **No** hay carpeta de fuente ni `filename` en el metadato por defecto.
- `BSHTMLLoader(file_path).load()` devuelve un único `Document` con `metadata["source"] = file_path` y `metadata["title"]` (si el HTML tiene `<title>`).

En ambos casos el `.feature` exige `metadata["source"]` = **nombre de la carpeta de fuente** (p. ej. `"ipopi"`, no la ruta completa) y `metadata["filename"]` = nombre del fichero. Por tanto **hay que sobrescribir `metadata["source"]` y añadir `metadata["filename"]` explícitamente después de cada `load()`** — el valor que ponen los loaders de LangChain por defecto no sirve tal cual.

**Sin precedente de logging/warnings en el repo:** ningún módulo existente (`rag/`, `ingestion/`) usa `logging` ni `warnings`. Para los "avisos" que piden los Scenarios 3, 6, 7 y 8, se usa `warnings.warn(..., UserWarning)` (stdlib, sin dependencia nueva, fácil de capturar en tests con `pytest.warns` o el fixture `recwarn`).

**Estructura del manifest — módulo dedicado:** para no sobrecargar `loader.py` con lógica de checksum/lectura/escritura de JSON, y porque T-05 (D-021) también necesitará leer el estado del manifest para decidir qué reindexar, se crea `ingestion/manifest.py` como módulo separado con la lógica de manifest, importado por `loader.py`. No estaba en el stub de T-01 (que solo prevé `loader.py`, `chunker.py`, `indexer.py`) — es un fichero nuevo, coherente con el patrón de módulos pequeños y de responsabilidad única ya usado en `rag/`.

**Schema del manifest (aprobado por Marcos):**
```json
{
  "documents": {
    "<fuente>/<filename>": {
      "checksum": "sha256:...",
      "url": null,
      "fecha": "YYYY-MM-DD"
    }
  }
}
```
Clave = ruta relativa `<fuente>/<filename>` dentro de `KB_RAW_DATA_PATH`. `checksum` vía `hashlib.sha256` sobre el contenido binario del fichero. `fecha` vía `datetime.date.today().isoformat()`.

**Comportamiento del manifest (D-021):**
- Entrada nueva → se crea con `checksum` + `fecha`, `url: null`, aviso "fuente nueva sin URL documentada".
- Entrada existente con checksum distinto → se actualiza `checksum` + `fecha`, aviso "el contenido de la fuente cambió".
- `manifest.json` ausente por completo → se trata como si todas las entradas fueran nuevas (se crea el fichero con todas), aviso "no había manifest previo".
- En ningún caso el loader bloquea la carga del fichero — el manifest es informativo, no una validación bloqueante.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `ingestion/manifest.py` | crear | `compute_checksum(path)`, `load_manifest(path)`, `save_manifest(path, data)`, `sync_entry(manifest, key, file_path)` — crea/actualiza una entrada y devuelve el mensaje de aviso si aplica (o `None`) |
| `ingestion/loader.py` | modificar | Implementa `load_documents(source_path)`: recorre subcarpetas de `source_path` (cada una = una fuente), despacha PDF/HTML al loader correspondiente, sobrescribe `source`/`filename` en metadata, omite formatos no soportados con aviso, sincroniza cada fichero contra el manifest, lanza errores claros si `source_path` no existe o está vacío |
| `tests/step_defs/test_e06_t02.py` | crear | Step definitions pytest-bdd para `e06_t02_document_loader.feature` |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Carga de un PDF válido** — `tests/features/e06_t02_document_loader.feature`
   - Step definitions en: `tests/step_defs/test_e06_t02.py`
   - Implementación en: `ingestion/loader.py`
   - Notas: fixture crea un PDF real minimo en `tmp_path/<fuente>/doc.pdf` (p. ej. con `reportlab` si ya está disponible, o un PDF de una página escrito a mano con bytes válidos — confirmar en el ciclo rojo qué genera `PyPDFLoader` sin fallos). `load_documents()` despacha a `PyPDFLoader`, luego reescribe `metadata["source"] = <nombre carpeta>` y añade `metadata["filename"] = <nombre fichero>` en cada `Document` devuelto.

2. **Carga de un documento HTML válido** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e06_t02.py`
   - Implementación en: `ingestion/loader.py`
   - Notas: fixture crea un `.html` con texto y marcado simple en `tmp_path/<fuente>/doc.html`. Igual que el PDF: `BSHTMLLoader` + reescritura de `source`/`filename`. Verificar que el texto extraído no contiene tags (`BSHTMLLoader` ya limpia el marcado vía BeautifulSoup).

3. **Carpeta de datos crudos ausente** — mismo `.feature`
   - Implementación en: `ingestion/loader.py`
   - Notas: si `Path(source_path)` no existe, `raise FileNotFoundError` con mensaje que incluya la ruta esperada (`str(source_path)`).

4. **Carpeta de datos crudos vacía** — mismo `.feature`
   - Implementación en: `ingestion/loader.py`
   - Notas: si `source_path` existe pero no contiene subcarpetas (fuentes) con ficheros, `raise ValueError` indicando que no hay documentos que cargar. Distinguir de (3): la ruta existe, el contenido no.

5. **Fichero con formato no soportado se omite sin interrumpir la carga** — mismo `.feature`
   - Implementación en: `ingestion/loader.py`
   - Notas: dispatch por extensión (`.pdf` → PyPDFLoader, `.html`/`.htm` → BSHTMLLoader, cualquier otra → `warnings.warn(f"Formato no soportado, omitido: {file}")` y continúa con el resto de ficheros de la misma carpeta.

6. **Fichero nuevo sin entrada en el manifest se documenta automáticamente** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e06_t02.py`
   - Implementación en: `ingestion/manifest.py` + integración en `ingestion/loader.py`
   - Notas: `sync_entry()` calcula el checksum del fichero, si la clave `<fuente>/<filename>` no está en `manifest["documents"]`, crea la entrada (`checksum`, `url: None`, `fecha` de hoy) y devuelve el mensaje de aviso "fuente nueva sin URL documentada". `loader.py` llama a `sync_entry()` por cada fichero cargado y emite el aviso con `warnings.warn` si no es `None`. Al final de `load_documents()`, `save_manifest()` persiste los cambios.

7. **Fichero documentado cuyo contenido ha cambiado actualiza el manifest** — mismo `.feature`
   - Implementación en: `ingestion/manifest.py`
   - Notas: si la clave existe pero el checksum calculado difiere del guardado, `sync_entry()` actualiza `checksum`/`fecha` (conserva `url` existente) y devuelve el aviso "el contenido de la fuente cambió". Si el checksum coincide, no hay aviso ni cambio.

8. **Manifest de trazabilidad ausente por completo** — mismo `.feature`
   - Implementación en: `ingestion/manifest.py`
   - Notas: `load_manifest(path)` devuelve `{"documents": {}}` si el fichero no existe (en vez de lanzar excepción). `loader.py` emite un aviso adicional "no había manifest previo" solo en este caso (fichero ausente, no solo entradas ausentes), distinguible de los avisos de entrada individual del Scenario 6.

## Restricciones a respetar

- **Falso Negativo Cero (D-002):** no aplica directamente — este módulo no genera respuestas al usuario final.
- **Agnóstico de proveedor (D-010):** ninguna dependencia de esta tarea acopla a un proveedor de LLM.
- **Convenciones del repo:** `KB_RAW_DATA_PATH` ya definida en `ingestion/config.py` (T-01) — no redefinir, reutilizar `load_ingestion_config()`.
- **D-021:** el loader detecta y registra cambios en el manifest, pero **no decide** si eso implica reindexar — esa lógica es de T-05, no se anticipa aquí.

## Lo que queda fuera de esta tarea

- Soporte de texto plano (`.txt`) — descartado explícitamente para T-02 (revisión de tarea, ver `decisions.md` si se retoma en el futuro).
- Estrategia de chunking — T-03.
- Indexación en ChromaDB — T-04.
- Decidir qué documentos reindexar a partir de los cambios detectados en el manifest — T-05 (D-021).
- Rellenar manualmente el campo `url` de las entradas nuevas del manifest — tarea manual de Marcos cuando añade fuentes a Drive, fuera del alcance del código.
