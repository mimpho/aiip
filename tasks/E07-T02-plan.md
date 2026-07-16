# Plan — E-07 T-02 RAGAS: Faithfulness + Answer Relevancy contra el pipeline real

## Contexto técnico

**Decisiones ya tomadas (Cowork, `task-start`):** ver D-050 (script documentado sin TDD,
precedente E06-T07) y D-051 (alcance 27 casos informativos, evaluador = `LLM_MODEL`,
embeddings = `rag.embeddings.get_embeddings()`, extracción de contexto sin bloque de
fuentes, resultados en `tests/eval/results/e07_t02_ragas_scores.json`, checkpointing por
fichero).

**Research previo — API de `ragas` (librería no usada todavía en el proyecto):**

- `docs/evaluation.md` (sección 4) muestra un ejemplo con `ragas.evaluate()` +
  `datasets.Dataset` + `ChatGoogleGenerativeAI(model="gemini-1.5-flash")` — API antigua
  (ragas ≤0.2) y modelo ya no vigente (D-043). No usar ese ejemplo tal cual.
- La documentación actual de ragas (docs.ragas.io, dic. 2025) distingue dos APIs:
  1. **API "collections" (moderna, recomendada para proyectos nuevos):**
     `ragas.metrics.collections.Faithfulness`/`AnswerRelevancy`, requiere un LLM/embeddings
     creados con `ragas.llms.llm_factory("modelo", provider="google", client=genai.Client(...))`
     usando el SDK nativo `google-genai` (no LangChain) — internamente usa Instructor +
     LiteLLM. Adoptarla implicaría una dependencia nueva (`google-genai`) y una segunda vía
     de acceso a Gemini en el proyecto, en paralelo a `langchain-google-genai` ya usado en
     `rag/generator.py` — no coherente con D-010 (siempre vía abstracción LangChain).
  2. **API "legacy" (`ragas.metrics.Faithfulness`, `ragas.metrics.ResponseRelevancy`,
     marcada "deprecated en 0.4, se elimina en 1.0"):** acepta directamente un LLM de
     LangChain envuelto en `ragas.llms.LangchainLLMWrapper(llm)` y embeddings de LangChain
     envueltos en `ragas.embeddings.LangchainEmbeddingsWrapper(embeddings)` — confirmado en
     la guía oficial de integración con LangChain (docs.ragas.io/howtos/integrations/langchain).
     Permite puntuar caso a caso con `scorer.single_turn_score(sample)` /
     `await scorer.single_turn_ascore(sample)` sobre un `ragas.dataset_schema.SingleTurnSample`
     — sin necesidad de construir un `datasets.Dataset` ni llamar al `evaluate()` por lotes.
- **Decisión de implementación (dentro de lo ya aprobado en D-051, no reabre el punto):**
  usar la API "legacy" (`LangchainLLMWrapper` + `LangchainEmbeddingsWrapper` +
  `SingleTurnSample` + `single_turn_score` por caso). Razones: (a) reutiliza
  `ChatGoogleGenerativeAI` (ya en `rag/generator.py`) y `rag.embeddings.get_embeddings()` sin
  SDK nuevo, coherente con D-010 y con el punto 2/3 de D-051; (b) el scoring caso a caso
  encaja de forma natural con el checkpointing (punto 6 de D-051) — no hace falta simular
  checkpointing sobre una evaluación por lotes. Contrapartida asumida: la API legacy se
  elimina en ragas 1.0 — mitigarlo pinneando una versión de `ragas` conocida (< 1.0) en
  `requirements.txt`, igual que se hace con `pydantic` y el resto de dependencias del
  proyecto. Si en el futuro (E-09) ragas 1.0 ya es la única opción, revisitar esta decisión
  (la migración a la API collections quedaría documentada aquí como referencia).
- Dependencia nueva: solo `ragas` (no hace falta `datasets` con este enfoque, al no usar
  `evaluate()`/`Dataset.from_list`).
- No se ha podido confirmar en la documentación pública el nombre exacto de la clase de
  embeddings LangChain-compatible más allá de `LangchainEmbeddingsWrapper` (nombre inferido
  por paralelismo con `LangchainLLMWrapper`, ambos documentados en `ragas.llms`/`ragas.embeddings`
  respectivamente en la guía de integración). Antigravity debe verificar el import exacto
  (`from ragas.embeddings import LangchainEmbeddingsWrapper`) al implementar, y ajustar si el
  nombre real difiere en la versión instalada.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `requirements.txt` | modificar | Añadir `ragas` (versión pinneada, <1.0 para mantener la API legacy usada aquí) |
| `scripts/run_ragas_eval.py` | crear | Script que instancia `RAGPipeline` real, evalúa los 27 casos informativos con Faithfulness + Answer Relevancy, con checkpointing |
| `tests/eval/results/` | crear | Carpeta nueva para resultados de evaluación (paralela a `tests/eval/dataset_partial.json`) |
| `tests/eval/e07_t02_ragas_faithfulness_relevancy.feature` | ya existe | Checklist de verificación manual (creado en `task-start`) |

## Orden de implementación (sin TDD — D-050)

No hay ciclo rojo→verde con pytest-bdd. En su lugar, Antigravity implementa el script y
verifica manualmente cada escenario del `.feature` en orden:

1. **Dependencias instaladas** — añadir `ragas` a `requirements.txt` (pinnear versión
   instalada tras `pip install ragas`, comprobando que `ragas.metrics.Faithfulness`,
   `ragas.metrics.ResponseRelevancy`, `ragas.llms.LangchainLLMWrapper` y
   `ragas.dataset_schema.SingleTurnSample` son importables con esa versión).

2. **Script usa RAGPipeline real, sin mocks** — `scripts/run_ragas_eval.py`:
   - Carga config con `rag.config.load_rag_config()`, instancia `RAGPipeline(config)`.
   - Evaluador: `LangchainLLMWrapper(ChatGoogleGenerativeAI(model=config["LLM_MODEL"], ...))`
     — reutilizar la misma construcción de `ChatGoogleGenerativeAI` que
     `rag/generator.py::RAGGenerator` (mismos parámetros de inferencia, D-010: nunca
     hardcodeados). Embeddings: `LangchainEmbeddingsWrapper(get_embeddings())`.

3. **Selección del subconjunto informativo** — usar
   `evaluation.dataset.load_dataset("tests/eval/dataset_partial.json")` +
   `evaluation.dataset.validate_dataset(...)`, filtrar `is_alarm is False` (27 casos).

4. **Extracción de contexto sin bloque de fuentes** — para cada caso, obtener los chunks
   recuperados vía `pipeline.retrieve(question)` (ya público, D-035) y la respuesta vía
   `pipeline.query(question)`. Como `query()` devuelve la respuesta con el bloque de fuentes
   ya concatenado (D-026/D-041), extraer solo la parte de respuesta clínica antes de
   construir el `SingleTurnSample`. Opciones para Antigravity a resolver en implementación:
   (a) separar por el marcador textual que usa `_build_sources_section` en `rag/pipeline.py`
   (revisar su formato exacto), o (b) llamar directamente a `pipeline._generator.generate(...)`
   con el contexto de `retrieve()` para obtener la respuesta pura sin pasar por `query()` —
   preferible (a) si el marcador es estable, ya que evita tocar el método "privado" del
   generador desde fuera de la clase.

5. **Scoring por caso + checkpointing** — por cada caso pendiente (id no presente aún en
   `tests/eval/results/e07_t02_ragas_scores.json`):
   - Construir `SingleTurnSample(user_input=question, response=respuesta_limpia,
     retrieved_contexts=[chunk.page_content for chunk, _ in retrieved])`.
   - `faithfulness_score = Faithfulness(llm=evaluator_llm).single_turn_score(sample)`
   - `relevancy_score = ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings).single_turn_score(sample)`
   - Añadir el resultado (`id`, `question`, `faithfulness`, `answer_relevancy`) a la
     estructura en memoria y volcar el fichero completo a disco tras cada caso (no solo al
     final) — así una interrupción a mitad de ejecución no pierde el progreso ya hecho.
   - Al final, añadir un bloque `aggregate` con la media de cada métrica sobre los 27 casos.

6. **Verificación manual** — ejecutar el script completo, revisar
   `tests/eval/results/e07_t02_ragas_scores.json` contra el checklist del `.feature`
   (schema por caso, agregados, cobertura de los 27 ids). Marcos revisa el resultado.

## Restricciones a respetar

- **Falso Negativo Cero:** no aplica directamente (este script no genera respuestas nuevas
  de producción, solo evalúa las ya generadas por `RAGPipeline.query()` real), pero si
  algún caso informativo dispara el filtro de seguridad de forma inesperada (falso
  positivo de `check_alarm_signals`), anotarlo — es una señal relevante para el informe de
  T-04, no un bug de este script.
- **Agnosticismo de proveedor (D-010):** el evaluador de RAGAS debe construirse sobre
  `ChatGoogleGenerativeAI`/`get_embeddings()` ya existentes en el proyecto, vía
  `LangchainLLMWrapper`/`LangchainEmbeddingsWrapper` — no introducir el SDK nativo
  `google-genai` (ver Contexto técnico).
- **Privacy by design:** no aplica contenido nuevo — reutiliza el dataset ya revisado por
  Marcos en T-01.

## Lo que queda fuera de esta tarea

- Los 15 casos de alarma del dataset (evaluados en T-03, Safety Compliance, no con
  Faithfulness/Answer Relevancy).
- Context Precision y Context Recall (E-09, requieren `relevant_chunks`, D-044 punto 2).
- Ciclo de mejora sobre los resultados (E-09) — T-02 solo produce el primer dato, no actúa
  sobre él.
- Medición de latencia (mencionada en `docs/evaluation.md` sección 7 pero no asignada
  explícitamente a T-02 en `backlog/epics.md`) — si Antigravity quiere registrarla como
  dato adicional sin coste extra (ej. cronometrar cada llamada a `pipeline.query()`), es
  bienvenido pero no es un criterio de aceptación de esta tarea.
- El informe narrativo de resultados — es T-04.
