# kb-maintenance.md — Procedimiento de mantenimiento de la KB

> Runbook operativo: qué pasos seguir cada vez que se añade, actualiza, reestructura o elimina
> algo en las fuentes de la Knowledge Base (`data/raw/`). No es un registro de decisiones — para
> el porqué de este documento, ver D-028 en `decisions.md`. No es un índice de fuentes — para
> qué fuentes existen, ver `docs/kb-sources.md`.

**Por qué importa seguir estos pasos:** `ingestion/indexer.py` calcula el ID de cada chunk como
`sha256(source/filename/índice)`, y `run_ingestion_pipeline()` (D-024) solo borra-antes-de-reindexar
los documentos que carga *en la ejecución actual* desde `data/raw/`. Si un documento cambia de
`source` (se mueve de carpeta) o desaparece, sus chunks antiguos **no se borran solos** — quedan
huérfanos y duplicados en ChromaDB hasta que se borran explícitamente.

**Comando de reingesta** (único CLI que invoca `run_ingestion_pipeline()` contra la KB real, T-05):

```bash
python scripts/smoke_test_rag.py --force-reingest
```

---

## 1. Añadir una fuente nueva

1. Crear la carpeta `data/raw/{nueva-fuente}/` con los documentos (PDF/HTML).
2. Añadir la fuente a `docs/kb-sources.md` (tabla del perfil correspondiente).
3. Ejecutar `python scripts/smoke_test_rag.py --force-reingest`.
   - El loader (`ingestion/loader.py`) crea automáticamente las entradas nuevas en
     `data/raw/manifest.json` con `url: null` (D-021).
4. Rellenar manualmente las URLs reales en `manifest.json` cuando estén disponibles —
   ver sección 6.
5. Verificar: el resumen impreso por el script no debe listar la fuente nueva en `failures`.

## 2. Añadir un documento a una fuente existente

Igual que el punto 1 pero sin tocar `kb-sources.md` si la fuente ya está listada — solo añadir
la fila del documento nuevo si se quiere trazabilidad a nivel de documento.

### Página web sin PDF descargable (copiar nodos HTML relevantes)

Para las filas de `kb-sources.md` que son páginas web (no un PDF), no hace falta guardar la
página completa. El loader (`ingestion/loader.py`) ya soporta `.html`/`.htm` con `BSHTMLLoader`:

1. En el navegador, inspecciona la página y copia el `outerHTML` solo de los nodos con contenido
   útil (evita nav/menú/footer — reduce ruido en el chunk sin tocar código).
2. Pega esos nodos en un fichero `.html` dentro de `data/raw/{fuente}/` — **no hace falta**
   envoltorio `<html>`/`<body>`, varios `<div>` sueltos funcionan igual (verificado: `html.parser`
   los procesa sin problema).
3. `_load_html()` usa `get_text_separator="\n\n"` (ver nota en el propio `loader.py`), así que el
   texto de cada nodo pegado queda separado por salto de párrafo aunque los tags estén pegados
   sin espacio en el fichero — no hace falta añadir líneas en blanco a mano entre nodos.
4. La URL en el manifest es la propia URL de la página — no hay que buscarla ni verificarla en
   Wayback Machine, ya la tienes.

## 3. Actualizar el contenido de un documento existente (mismo path)

No requiere ningún paso manual en el manifest: `ingestion/manifest.py::sync_entry()` detecta el
checksum distinto automáticamente y actualiza `checksum`/`fecha` (conserva la `url` ya
documentada). Solo hace falta:

```bash
python scripts/smoke_test_rag.py --force-reingest
```

`delete_document_chunks()` borra los chunks antiguos de ese `(source, filename)` antes de
reinsertar los nuevos (D-024) — no deja huérfanos porque el `source`/`filename` no cambia.

## 4. Renombrar o reestructurar una fuente (mover un documento a otra carpeta/fuente)

Caso real: `data/raw/cribado_neonatal/` → `data/raw/aedip/` (7 jul 2026, ver D-028).

1. Mover/renombrar la carpeta o el fichero en `data/raw/` (Drive o local).
2. Actualizar a mano la clave correspondiente en `data/raw/manifest.json`
   (`{source}/{filename}` → nueva ruta), conservando `checksum`/`url`/`fecha` si el contenido
   no cambió. El loader **no** hace esta migración automáticamente — si no se corrige, la
   siguiente ingesta crea una entrada nueva con `url: null` y pierde la URL ya documentada.
3. **Borrar los chunks huérfanos del `source` antiguo antes o durante el reindex** — no basta con
   `--force-reingest`, porque ese comando solo actúa sobre lo que existe *hoy* en `data/raw/` y
   nunca volverá a pedir el `source` viejo. Borrado explícito (una vez, script/REPL puntual):

   ```python
   from rag.embeddings import get_embeddings
   from rag.config import load_rag_config
   from ingestion.indexer import delete_document_chunks

   rag_config = load_rag_config()
   embeddings = get_embeddings()
   delete_document_chunks(
       "cribado_neonatal", "cribado-neonatal-IDCG-2021.pdf",
       embeddings, rag_config["CHROMA_PATH"], collection_name="family",
   )
   ```

4. Ejecutar `python scripts/smoke_test_rag.py --force-reingest` para indexar bajo el `source`
   nuevo.
5. Verificar: consultar la colección `family` filtrando por el `source` antiguo
   (`vectorstore.get(where={"source": "cribado_neonatal"})`) y comprobar que devuelve 0
   resultados.

## 5. Eliminar un documento o una fuente completa

El mismo problema que en el punto 4: si el fichero simplemente se borra de `data/raw/`, el
loader deja de cargarlo y sus chunks quedan huérfanos para siempre.

1. Borrar los chunks explícitamente (mismo patrón que el paso 3 de la sección 4, con el
   `source`/`filename` del documento eliminado).
2. Borrar a mano la entrada correspondiente de `data/raw/manifest.json` — nada la elimina
   automáticamente.
3. Si es una fuente completa, quitar o marcar como retirada la fila en `docs/kb-sources.md`.
4. Eliminar la carpeta/fichero de `data/raw/`.

## 6. Rellenar o actualizar la URL de un documento en el manifest

Relevante para la citación de fuentes (E-06 T-08, D-021, D-026).

1. Editar manualmente `url` en la entrada correspondiente de `data/raw/manifest.json` —
   Marcos verifica y pega la URL real documento por documento, nunca se inventan enlaces
   (ver nota de T-08 en `backlog/epics.md`).
2. Preferir el enlace directo al documento sobre el dominio genérico de la fuente cuando se
   tenga con confianza.
3. Rellenar la URL **no** dispara reindexación automática — como `url` se propaga a los metadatos
   del chunk (loader → chunker, mismo patrón que `language`/`date_indexed`/`profile`, D-022),
   hace falta `--force-reingest` para que la citación en el chat vea la URL nueva.
