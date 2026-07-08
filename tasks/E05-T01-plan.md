# Plan — E-05 T-01 Integración del pipeline RAG en el chat familiar

## Contexto técnico

**`cl.make_async()`** — utilidad de Chainlit para envolver una función síncrona y ejecutarla en un thread separado sin bloquear el event loop. Patrón confirmado (docs.chainlit.io/api-reference/make-async):

```python
answer = await cl.make_async(sync_func)(arg1, arg2)
```

Se usa así para `RAGPipeline.query()`, que es síncrono (D-033).

**Instanciación lazy del singleton** — D-033 fija que el `RAGPipeline` se instancia una sola vez y se reutiliza entre sesiones, pero instanciarlo de forma *eager* a nivel de módulo (en el import de `main_family.py`) rompería los tests: `RAGPipeline.__init__` carga `bge-m3` real y `load_rag_config()` lanza `EnvironmentError` si faltan variables de entorno (no configuradas en el entorno de test). Solución: singleton *lazy* — variable de módulo `_pipeline = None` + función `_get_pipeline()` que la instancia en el primer uso y la cachea. Los tests hacen `monkeypatch` de `_get_pipeline` directamente, sin disparar nunca la construcción real. Sigue siendo "una instancia para toda la app" (no por sesión), solo cambia el momento de creación de "import" a "primera invocación".

**Indicador de "escribiendo" (Escenario 2)** — Chainlit no requiere código especial para el spinner por defecto, pero para que el escenario sea verificable con pytest-bdd (sin browser) se usa un patrón explícito y testeable: crear un `cl.Message(content="")` y enviarlo *antes* de invocar el pipeline, luego actualizar su contenido con `.update()` al recibir la respuesta. Esto da un punto de aserción concreto (un mensaje se envía antes de que se resuelva la llamada al pipeline) en vez de depender de comportamiento no determinista del frontend.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `chainlit/main_family.py` | modificar | Añade `_get_pipeline()` (singleton lazy) y el handler `on_message` que invoca `RAGPipeline.query()` vía `cl.make_async()` |
| `tests/step_defs/test_e05_t01.py` | crear | Step definitions pytest-bdd para los 4 escenarios, usando el patrón de fake `chainlit` module ya establecido en `test_e03_t05.py` |

No se toca `rag/pipeline.py` ni `rag/config.py` — ya exponen todo lo necesario (`RAGPipeline.query()`, `load_rag_config()`).

## Orden de implementación TDD

Sigue el orden de los escenarios en el `.feature`. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Pregunta del usuario devuelve la respuesta del pipeline** — `tests/features/e05_t01_chat_pipeline_integration.feature`
   - Step definitions en: `tests/step_defs/test_e05_t01.py`
   - Implementación en: `chainlit/main_family.py`
   - Notas: mockear `_get_pipeline()` para devolver un `MagicMock` con `.query.return_value = "respuesta fake"`. Verificar que `on_message` llama a `query()` con el texto exacto del mensaje y que se envía un `cl.Message` con ese contenido.

2. **Indicador de "escribiendo" mientras se genera la respuesta**
   - Notas: verificar que se envía un `cl.Message(content="")` (o equivalente) *antes* de que se resuelva `cl.make_async(pipeline.query)(...)`. Con `cl.Message`/`user_session` mockeados (`MagicMock`), se puede verificar el orden de llamadas con `mock.mock_calls` o contadores.

3. **Error del pipeline no rompe la sesión de chat**
   - Notas: mockear `_get_pipeline().query` para que lance una excepción genérica (`Exception("LLM no disponible")`). Verificar que `on_message` no propaga la excepción, que se actualiza el mensaje con un texto de error en español, y que una llamada posterior a `on_message` (segunda pregunta) sigue funcionando con normalidad — no hay estado corrupto compartido.

4. **Mensajes vacíos no invocan el pipeline**
   - Notas: probar con contenido `""` y `"   "` (solo espacios). Verificar que `_get_pipeline().query` no se llama (usar `assert not mock.query.called`).

## Restricciones a respetar

- **Agnóstico de proveedor:** esta tarea no toca la capa de generación (`rag/generator.py`); no se introduce ninguna llamada directa a SDK de proveedor.
- **Falso Negativo Cero:** `RAGPipeline.query()` ya aplica `apply_safety_filter`/`check_alarm_signals` internamente (E-04, D-019/D-020) — T-01 no modifica esa lógica, solo la invoca. No añadir lógica de seguridad duplicada en `main_family.py`.
- **Reparto git:** implementación en rama `task/E05-T01-rag-pipeline-chat-integration` ya creada; el agente en Antigravity no hace `push`/`merge`.

## Lo que queda fuera de esta tarea

- Streaming de tokens (T-02) — la respuesta se muestra completa al recibirla, no token a token.
- Visualización de pasos intermedios / documentos recuperados (T-03) — no se expone el retrieval en la UI todavía.
- Perfil profesional (`main_professional.py`) — fuera de alcance, sigue bloqueado (stub).
- Cualquier cambio en `rag/pipeline.py`, `rag/generator.py` o `rag/safety.py`.
