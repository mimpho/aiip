# Plan — E-06 T-01 Setup de dependencias y estructura del módulo de ingesta

## Contexto técnico

**Dependencias nuevas a añadir a `requirements.txt`** (no presentes actualmente):

| Paquete | Versión | Rol |
|---|---|---|
| `langchain-community` | 0.4.2 | Loaders de documentos (`PyPDFLoader`, `BSHTMLLoader`) para T-02. Depende de `langchain-core>=1.4.0`, compatible con `langchain-core>=1.4.7` que ya trae `langchain==1.3.11`. |
| `langchain-text-splitters` | 1.1.2 | `RecursiveCharacterTextSplitter` para T-03 (chunking). Línea de versión 1.x, coherente con `langchain` 1.3.11. |
| `pypdf` | 6.14.2 | Backend de extracción de texto de `PyPDFLoader`. |
| `beautifulsoup4` | 4.15.0 | Backend de parseo HTML de `BSHTMLLoader`. |

Verificado en PyPI: `langchain-community==0.4.2` requiere `langchain-core<2.0.0,>=1.4.0` y `langchain-classic<2.0.0,>=1.0.7` (resuelto automáticamente por pip, no hace falta pin manual). `langchain` 1.3.11 ya requiere `langchain-core<2.0.0,>=1.4.7` — cadena de versiones compatible.

`chromadb`, `langchain-chroma`, `python-dotenv` ya están en `requirements.txt` (E-04) y cubren `indexer.py`.

**Formatos soportados (confirmado por el `.feature` de T-02, ya escrito):** PDF y HTML. `pypdf` + `beautifulsoup4` cubren ambos backends.

**Variable de entorno nueva:** `KB_RAW_DATA_PATH` — ruta a los datos crudos de la KB. Default `"data/raw"` si no está definida en `.env`.

**`.gitignore`:** actualmente no excluye `data/raw/` ni `data/chroma/`, pese a que `backlog/epics.md` (notas de E-06) documenta que `data/raw/` vive fuera del repo salvo `data/raw/manifest.json` (trazabilidad, versionado explícitamente). Hay que corregir esto en T-01 porque toca directamente la estructura que esta tarea define.

**Manifest de trazabilidad (`data/raw/manifest.json`):** decisión de alcance (aprobada por Marcos) — NO se crea en T-01. Queda para T-02, junto al loader que lo consume.

**Stubs del módulo `ingestion/`:** funciones con firma definida y `raise NotImplementedError`, siguiendo el mismo patrón que `rag/` en E-04-T01. Evita `AttributeError` en imports de T-02 a T-04.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `requirements.txt` | modificar | Añadir `langchain-community`, `langchain-text-splitters`, `pypdf`, `beautifulsoup4` |
| `.gitignore` | modificar | Excluir `data/raw/*` salvo `data/raw/manifest.json`; excluir `data/chroma/` |
| `ingestion/__init__.py` | crear | Marca el directorio como módulo Python |
| `ingestion/config.py` | crear | Carga `KB_RAW_DATA_PATH` con default `"data/raw"` |
| `ingestion/loader.py` | crear | Stub: import de `PyPDFLoader` y `BSHTMLLoader` de `langchain_community.document_loaders`; función `load_documents()` con `raise NotImplementedError` |
| `ingestion/chunker.py` | crear | Stub: import de `RecursiveCharacterTextSplitter` de `langchain_text_splitters`; función `chunk_documents()` con `raise NotImplementedError` |
| `ingestion/indexer.py` | crear | Stub: función `index_chunks()` con `raise NotImplementedError` (usará `langchain_chroma`, ya instalado) |
| `AGENTS.md` | modificar | Añadir `ingestion/` a la sección "Estructura del repositorio" (mismo patrón que `rag/` de E-04) |
| `tests/step_defs/test_e06_t01.py` | crear | Step definitions pytest-bdd para `e06_t01_ingestion_setup.feature` |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Importación correcta de módulos de ingesta** — `tests/features/e06_t01_ingestion_setup.feature`
   - Step definitions en: `tests/step_defs/test_e06_t01.py`
   - Implementación en: `requirements.txt` + `ingestion/loader.py` + `ingestion/chunker.py`
   - Notas: el step `When importo los módulos de carga de documentos y de text splitting` importa `ingestion.loader` e `ingestion.chunker` con `importlib.import_module`. Para que pase: añadir las 4 dependencias a `requirements.txt`, instalar, y que `loader.py`/`chunker.py` solo tengan los imports de cabecera + stubs (sin lógica real todavía).

2. **Variable de entorno de ruta de datos crudos con valor por defecto** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e06_t01.py`
   - Implementación en: `ingestion/config.py`
   - Notas: `ingestion/config.py` expone `load_ingestion_config()`. Con `monkeypatch.delenv("KB_RAW_DATA_PATH", raising=False)`, `config["KB_RAW_DATA_PATH"]` debe ser `"data/raw"`.

3. **Variable de entorno de ruta de datos crudos personalizada**
   - Step definitions en: `tests/step_defs/test_e06_t01.py`
   - Implementación en: `ingestion/config.py` (mismo fichero, sin cambios si el paso anterior ya usa `os.getenv("KB_RAW_DATA_PATH", "data/raw")`)
   - Notas: `monkeypatch.setenv("KB_RAW_DATA_PATH", "/ruta/personalizada")` → `config["KB_RAW_DATA_PATH"] == "/ruta/personalizada"`.

4. **Estructura de módulo ingestion/ presente**
   - Step definitions en: `tests/step_defs/test_e06_t01.py`
   - Implementación en: todos los ficheros `ingestion/`
   - Notas: verifica con `pathlib.Path` que existen los 5 ficheros: `__init__.py`, `config.py`, `loader.py`, `chunker.py`, `indexer.py`. Último escenario porque depende de que todos existan.

## Restricciones a respetar

- **Agnóstico de proveedor de IA (D-010):** ninguna dependencia de esta tarea acopla a un proveedor de LLM concreto — son librerías de carga/chunking, no de inferencia.
- **Convenciones del repo:** variables de configuración en `.env`/`.env.example`, nunca hardcodeadas (`AGENTS.md`).
- Los stubs de `loader.py`, `chunker.py`, `indexer.py` no implementan lógica real — solo imports + `NotImplementedError`. La lógica llega en T-02, T-03 y T-04 respectivamente.

## Lo que queda fuera de esta tarea

- Implementación real de carga de documentos (PDF/HTML) — T-02.
- Estrategia de chunking multiidioma — T-03.
- Indexación real en ChromaDB — T-04.
- Creación de `data/raw/manifest.json` — decidido explícitamente fuera de T-01, se aborda en T-02.
- Organización o commit de los ficheros crudos de `data/raw/` — viven fuera del repo (Drive/local).
