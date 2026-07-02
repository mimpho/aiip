# Plan — E-04 T-04 Generador: LLM Gemini Flash via LangChain

## Contexto técnico

Research hecho contra el código fuente instalado de `langchain-google-genai==4.2.6`
(`.venv/lib/python3.12/site-packages/langchain_google_genai/chat_models.py`),
no documentado de forma obvia en el README del paquete:

- **Nombres de parámetros del constructor `ChatGoogleGenerativeAI`:** `model`,
  `temperature`, `top_p`, `max_output_tokens` (no `max_tokens`) y
  `google_api_key`. Mapeo directo desde `LLM_MODEL` / `LLM_TEMPERATURE` /
  `LLM_TOP_P` / `LLM_MAX_TOKENS` / `GOOGLE_API_KEY`.
- **`GOOGLE_API_KEY` ya es el nombre correcto y preferente:** el propio SDK
  comprueba primero `GOOGLE_API_KEY` y solo como fallback `GEMINI_API_KEY`
  ("`GOOGLE_API_KEY` is checked first for backwards compatibility"). Confirma
  D-018 — no hace falta introducir `GEMINI_API_KEY` en ningún sitio.
- **Excepción real ante fallo de autenticación / clave inválida:** las
  llamadas al modelo (`generate_content` vía `google.genai`) lanzan
  `google.genai.errors.ClientError`, que `chat_models._handle_client_error`
  captura y re-lanza como `langchain_google_genai.ChatGoogleGenerativeAIError`
  (salvo el caso específico de contexto excedido, que usa
  `GoogleContextOverflowError`, no aplica aquí). El step def del escenario
  "Error de autenticación con clave inválida" debe mockear `.invoke()` para
  que lance `ChatGoogleGenerativeAIError`, no una excepción genérica inventada.
- **Rango válido de `temperature`:** la librería valida `0 <= temperature <= 2.0`
  y lanza `ValueError` fuera de rango — el default `0.1` de D-018 es válido.
- **Rango válido de `top_p`:** `0 <= top_p <= 1` — el default `0.1` es válido.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `prompts/system_prompt_familiar.txt` | crear | System prompt real (estructura completa de `tech-spec.md` sección 5: rol, restricciones Falso Negativo Cero, idioma, fuentes, tono familiar, cierre obligatorio) |
| `rag/config.py` | modificar | Añadir `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_MAX_TOKENS` como opcionales con default, mismo patrón que `RAG_TOP_K` (D-016) |
| `rag/generator.py` | modificar | Implementar `RAGGenerator.__init__` y `.generate()` (sustituye los `NotImplementedError` del stub de T-01) |
| `.env.example` | modificar | Añadir `LLM_TEMPERATURE=0.1`, `LLM_TOP_P=0.1`, `LLM_MAX_TOKENS=300` (`LLM_MODEL` ya existe) |
| `tests/step_defs/test_e04_t04.py` | crear | Step definitions pytest-bdd para `e04_t04_llm_generator.feature` |

## Orden de implementación TDD

1. **Error claro cuando GOOGLE_API_KEY no está definida** — `tests/features/e04_t04_llm_generator.feature`
   - Step definitions en: `tests/step_defs/test_e04_t04.py`
   - Implementación en: `rag/generator.py` (`RAGGenerator.__init__` valida `config["GOOGLE_API_KEY"]` directamente — no depende de `load_rag_config()`, igual que `get_retriever()` en T-02 se instancia sin pasar por `config.py`)
   - Notas: mensaje de error debe mencionar literalmente `GOOGLE_API_KEY`, igual que el patrón ya usado en `rag/config.py`.

2. **Parámetros de inferencia leídos de entorno**
   - Implementación en: `rag/generator.py` + `rag/config.py`
   - Notas: `RAGGenerator` lee `LLM_MODEL`/`LLM_TEMPERATURE`/`LLM_TOP_P`/`LLM_MAX_TOKENS` del dict `config` recibido (con defaults si faltan), nunca hardcodeados. El test verifica que al mockear `ChatGoogleGenerativeAI`, se invoca con los valores exactos pasados en `config`, no con los defaults.

3. **System prompt leído de fichero, no embebido en código**
   - Implementación en: `rag/generator.py` (`_load_system_prompt()`) + `prompts/system_prompt_familiar.txt`
   - Notas: ruta resuelta relativa a la raíz del repo (`Path(__file__).resolve().parent.parent / "prompts" / "system_prompt_familiar.txt"`), no relativa al cwd del proceso que lo ejecute (Chainlit, pytest, etc. pueden tener cwd distinto).

4. **Generación de respuesta con contexto válido**
   - Implementación en: `rag/generator.py` (`generate()`)
   - Notas: mockear `rag.generator.ChatGoogleGenerativeAI` con `unittest.mock.patch`; el mock de `.invoke()` devuelve un objeto con `.content` (formato `AIMessage` real). Verificar que el prompt final incluye system prompt + contexto + query + idioma.

5. **Error de autenticación con clave inválida**
   - Implementación en: `rag/generator.py` (no requiere código nuevo si `generate()` no atrapa excepciones — deben propagarse)
   - Notas: mockear `.invoke()` con `side_effect=ChatGoogleGenerativeAIError(...)` (ver Contexto técnico). Confirmar que `RAGGenerator.generate()` no atrapa ni convierte esta excepción — debe propagarse tal cual (Falso Negativo Cero también aplica a errores: nunca fallar en silencio).

6. **`@integration` — Llamada real a la API de Gemini (smoke test)**
   - Implementación: ninguna en `rag/generator.py` — solo el step def
   - Notas: en `test_e04_t04.py`, hacer `pytest.skip(...)` al inicio del step `When` si `os.getenv("RUN_LLM_INTEGRATION_TESTS") != "1"` o si `GOOGLE_API_KEY` no está definida — no debe ejecutarse por defecto en CI. Documentar en el docstring del step cómo activarlo manualmente.

## Restricciones a respetar

- Agnóstico de proveedor (D-010): nunca importar el SDK nativo de Google
  (`google.generativeai`) directamente — solo vía `langchain_google_genai`.
- System prompt en fichero separado bajo `prompts/`, nunca embebido en
  `rag/generator.py` (principio no negociable de `AGENTS.md`).
- Modelo y parámetros de inferencia en `.env`, nunca hardcodeados.
- Las excepciones deben propagarse sin silenciarse — coherente con Falso
  Negativo Cero aplicado también a fallos técnicos, no solo a contenido.

## Lo que queda fuera de esta tarea

- Integración del generador en `rag/pipeline.py` — es T-06.
- Lógica de validación Falso Negativo Cero sobre la respuesta generada
  (`rag/safety.py`, `apply_safety_filter`) — es T-05. El system prompt de
  esta tarea ya incluye las restricciones textuales, pero la verificación
  en tiempo de ejecución (post-generación) no es responsabilidad de T-04.
- System prompt del perfil profesional (`prompts/system_prompt_profesional.txt`)
  — Fase 2, fuera de alcance de E-04.
