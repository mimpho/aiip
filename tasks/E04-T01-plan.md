# Plan — E-04 T-01 Setup de dependencias y estructura del módulo RAG

## Contexto técnico

**Dependencias nuevas a añadir a `requirements.txt`** (no presentes actualmente):

| Paquete | Versión | Rol |
|---|---|---|
| `langchain` | 1.3.11 | Orquestación del pipeline RAG (D-004, D-010) |
| `langchain-google-genai` | 4.2.6 | Integración LangChain ↔ Gemini Flash |
| `langchain-chroma` | 1.1.0 | Integración LangChain ↔ ChromaDB |
| `chromadb` | 1.5.9 | Vector DB con persistencia local (D-004) |
| `langdetect` | 1.0.9 | Detección automática de idioma (D-011) |

`sentence-transformers` ya está en `requirements.txt` (bge-m3, D-004).
`google-generativeai` ya está en `requirements.txt` (necesario para `langchain-google-genai`).
`python-dotenv` ya está en `requirements.txt`.

**Variable de entorno nueva:** `CHROMA_PATH` — ruta al directorio de persistencia de ChromaDB.
Nombre canónico de la API key de Gemini: `GOOGLE_API_KEY` (establecido en E-01, confirmado en D-014).

**Stubs del módulo `rag/`:** clases/funciones con firma definida y `raise NotImplementedError`.
Esto evita `AttributeError` en imports de T-02 a T-06 y hace los tests fallar con el error correcto (rojo limpio).

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `requirements.txt` | modificar | Añadir langchain, langchain-google-genai, langchain-chroma, chromadb, langdetect |
| `.env.example` | modificar | Añadir `CHROMA_PATH` |
| `rag/__init__.py` | crear | Marca el directorio como módulo Python |
| `rag/config.py` | crear | Carga y valida variables de entorno del pipeline RAG |
| `rag/pipeline.py` | crear | Stub de la clase `RAGPipeline` (orquestador end-to-end) |
| `rag/embeddings.py` | crear | Stub de la función `get_embeddings()` (bge-m3 via sentence-transformers) |
| `rag/retriever.py` | crear | Stub de la función `get_retriever()` (ChromaDB via langchain-chroma) |
| `rag/generator.py` | crear | Stub de la clase `RAGGenerator` (Gemini Flash via langchain-google-genai) |
| `rag/safety.py` | crear | Stub de la función `apply_safety_filter()` (Falso Negativo Cero) |
| `tests/step_defs/test_e04_t01.py` | crear | Step definitions pytest-bdd para e04_t01_rag_setup.feature |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = ciclo rojo → verde antes de pasar al siguiente.

### 1. Scenario: Importación correcta de módulos RAG

- **Step definitions en:** `tests/step_defs/test_e04_t01.py`
- **Implementación en:** `requirements.txt` + los ficheros `rag/`
- **Notas:**
  - El step `Given el entorno virtual tiene las dependencias instaladas` es una precondición — en el test se verifica con `importlib.import_module`.
  - El step `When importo los módulos langchain, chromadb y sentence_transformers` hace los imports reales.
  - El step `Then ningún módulo lanza ImportError` simplemente pasa si los imports anteriores no lanzaron excepción.
  - Para que este scenario pase: añadir las 5 dependencias a `requirements.txt` y ejecutar `pip install -r requirements.txt`.

### 2. Scenario: Variables de entorno requeridas presentes

- **Step definitions en:** `tests/step_defs/test_e04_t01.py`
- **Implementación en:** `rag/config.py`
- **Notas:**
  - `rag/config.py` expone una función `load_rag_config()` que lee `GOOGLE_API_KEY`, `HF_TOKEN` y `CHROMA_PATH` con `python-dotenv` y lanza `EnvironmentError` si alguna falta.
  - El fixture del test usa `monkeypatch.setenv` para simular el `.env` — no depende del `.env` real.
  - Variables mínimas requeridas: `GOOGLE_API_KEY`, `HF_TOKEN`, `CHROMA_PATH`.

### 3. Scenario: Variable de entorno requerida ausente

- **Step definitions en:** `tests/step_defs/test_e04_t01.py`
- **Implementación en:** `rag/config.py` (mismo fichero, sin cambios si el scenario anterior pasó)
- **Notas:**
  - El test usa `monkeypatch.delenv("GOOGLE_API_KEY", raising=False)` para simular la ausencia.
  - El mensaje del `EnvironmentError` debe mencionar literalmente `"GOOGLE_API_KEY"`.
  - Este scenario reutiliza la misma `load_rag_config()` — si el anterior pasó, este debería ser rojo por el mensaje; ajusta el mensaje en `config.py` hasta verde.

### 4. Scenario: Estructura de módulo rag/ presente

- **Step definitions en:** `tests/step_defs/test_e04_t01.py`
- **Implementación en:** todos los ficheros `rag/`
- **Notas:**
  - El test verifica con `pathlib.Path` que existen los 6 ficheros: `__init__.py`, `pipeline.py`, `embeddings.py`, `retriever.py`, `generator.py`, `safety.py`.
  - Crear cada fichero con stub mínimo (ver estructura abajo).
  - Este scenario es el último porque depende de que todos los ficheros existan.

## Estructura de stubs (opción B)

```python
# rag/__init__.py
# Módulo RAG — pipeline de Retrieval-Augmented Generation para AIIP
```

```python
# rag/config.py
import os
from dotenv import load_dotenv

REQUIRED_VARS = ["GOOGLE_API_KEY", "HF_TOKEN", "CHROMA_PATH"]

def load_rag_config() -> dict:
    """Carga y valida las variables de entorno del pipeline RAG."""
    load_dotenv()
    config = {}
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value:
            raise EnvironmentError(f"Variable de entorno requerida no definida: {var}")
        config[var] = value
    return config
```

```python
# rag/pipeline.py
class RAGPipeline:
    """Orquestador del pipeline RAG end-to-end."""

    def __init__(self, config: dict):
        raise NotImplementedError

    def query(self, question: str) -> str:
        """Recibe una pregunta y devuelve la respuesta generada."""
        raise NotImplementedError
```

```python
# rag/embeddings.py
def get_embeddings():
    """Devuelve el modelo de embeddings bge-m3 via sentence-transformers."""
    raise NotImplementedError
```

```python
# rag/retriever.py
def get_retriever(embeddings, chroma_path: str, collection_name: str):
    """Devuelve un retriever LangChain sobre la colección ChromaDB indicada."""
    raise NotImplementedError
```

```python
# rag/generator.py
class RAGGenerator:
    """Genera respuestas via Gemini Flash usando LangChain."""

    def __init__(self, config: dict):
        raise NotImplementedError

    def generate(self, question: str, context: str, language: str) -> str:
        raise NotImplementedError
```

```python
# rag/safety.py
def apply_safety_filter(response: str) -> str:
    """Aplica el filtro de Falso Negativo Cero sobre la respuesta generada."""
    raise NotImplementedError
```

## Restricciones a respetar

- **D-010 (Agnósticismo de proveedor):** nunca importar el SDK nativo de Google directamente — solo via `langchain-google-genai`. Los stubs no deben importar nada que cree dependencia de proveedor.
- **D-002 (Falso Negativo Cero):** `safety.py` existe como módulo separado desde T-01 — su implementación real es T-05, pero su presencia como stub independiente garantiza que el principio tiene entidad propia en la arquitectura.
- **Configuración:** modelo LLM y parámetros de inferencia van en variables de entorno, nunca hardcodeados (ver `AGENTS.md`).

## Lo que queda fuera de esta tarea

- Implementación real de ningún stub — eso es T-02 a T-06.
- Descarga del modelo bge-m3 — ocurre en T-02 al instanciar el embedder.
- Creación de la colección ChromaDB — ocurre en E-06 (Ingesta KB).
- System prompt del agente — ocurre en T-04/T-05.
- `langdetect` se instala aquí pero se integra en T-03.
