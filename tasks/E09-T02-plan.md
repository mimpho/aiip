# Plan — E-09 T-02 RAGAS completo: Context Precision + Context Recall

## Contexto técnico

**Decisiones ya tomadas (Cowork, `task-start`):** ver D-055 — alcance 32 casos
(`category in ("informativo", "otro_idioma")`), `reference=case.expected_answer`,
extensión de `scripts/run_ragas_eval.py` en el mismo fichero (no un script nuevo),
resultados en un fichero nuevo `tests/eval/results/e09_t02_ragas_full_scores.json` (las 4
métricas juntas), sin tocar `tests/eval/results/e07_t02_ragas_scores.json` (queda como
histórico). Reutiliza los workarounds ya documentados en D-052 (stub de `ChatVertexAI`,
`_EVALUATOR_MAX_TOKENS=8192`) y el patrón de script-sin-TDD de D-050/D-051, confirmado
como aplicable aquí (no la corrección de D-053, que es para chequeos deterministas).

**Research previo — confirmado por código instalado (`ragas==0.4.3`,
`.venv/lib/python3.12/site-packages/ragas/metrics/`):**

- `ragas.metrics._context_precision.LLMContextPrecisionWithReference` (exportada como
  `ragas.metrics.ContextPrecision`) y `ragas.metrics._context_recall.LLMContextRecall`
  (exportada como `ragas.metrics.ContextRecall`) — ambas con
  `_required_columns = {"user_input", "retrieved_contexts", "reference"}` en
  `MetricType.SINGLE_TURN`. Ninguna de las dos necesita embeddings — a diferencia de
  `ResponseRelevancy`, que sí los requiere y ya está en uso en el script.
- Import recomendado por paralelismo con el resto del script (que ya importa
  `Faithfulness, ResponseRelevancy` desde `ragas.metrics`):
  `from ragas.metrics import ContextPrecision, ContextRecall` (nombres estables, alias
  de las clases `LLMContext...WithReference`/`LLMContextRecall`). Antigravity debe
  confirmar el import exacto al implementar — si `ContextPrecision`/`ContextRecall` no
  resuelven, usar directamente `LLMContextPrecisionWithReference`/`LLMContextRecall`.
- Ambas metrics se instancian igual que `Faithfulness`: `ContextPrecision(llm=evaluator_llm)`,
  `ContextRecall(llm=evaluator_llm)` — mismo `evaluator_llm` (`LangchainLLMWrapper`) ya
  construido en el script para Faithfulness/Answer Relevancy.
- `SingleTurnSample` ya se construye en el script con `user_input`, `response`,
  `retrieved_contexts`. Solo hace falta añadir `reference=case.expected_answer` al
  construirlo — campo ya disponible en `EvalCase` sin cambios de schema.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `scripts/run_ragas_eval.py` | modificar | Añadir `ContextPrecision`/`ContextRecall`, cambiar el filtro de selección de casos, añadir `reference` al `SingleTurnSample`, escribir en el fichero de resultados nuevo |
| `tests/eval/results/e09_t02_ragas_full_scores.json` | crear (generado por el script) | Resultados de las 4 métricas sobre los 32 casos |
| `tests/eval/e09_t02_ragas_context_metrics.feature` | ya existe | Checklist de verificación manual (formalizado en `task-start`) |

## Orden de implementación (sin TDD — D-050/D-055)

No hay ciclo rojo→verde con pytest-bdd. Antigravity modifica el script existente y
verifica manualmente cada escenario del `.feature` en orden:

1. **Imports y construcción de métricas nuevas** — añadir `ContextPrecision`,
   `ContextRecall` al import ya existente de `ragas.metrics` (junto a `Faithfulness`,
   `ResponseRelevancy`). Instanciar ambas con el `evaluator_llm` ya construido en `main()`
   (mismo objeto que usan `faithfulness_metric`/`relevancy_metric`, sin recrearlo).

2. **Cambiar el filtro de selección de casos** — sustituir
   `informative_cases = [c for c in all_cases if not c.is_alarm]` (línea actual del
   script) por un filtro sobre `category`:
   ```python
   target_categories = {"informativo", "otro_idioma"}
   target_cases = [c for c in all_cases if c.category in target_categories]
   ```
   Verificar que da exactamente 32 casos (27 + 5) antes de seguir — si no coincide,
   parar y revisar el dataset, no ajustar el filtro para forzar el número.

3. **Cambiar la ruta de resultados** — `_RESULTS_PATH` pasa a apuntar a
   `tests/eval/results/e09_t02_ragas_full_scores.json` (fichero nuevo, no reutilizar
   `_load_existing_results()` sobre el fichero de E-07 T-02 — el checkpointing de esta
   tarea es independiente, empieza de cero).

4. **Añadir `reference` al `SingleTurnSample`** — construirlo con
   `reference=case.expected_answer` además de `user_input`, `response`,
   `retrieved_contexts` ya presentes.

5. **Scoring por caso + checkpointing** — para cada caso pendiente (id no presente aún en
   `e09_t02_ragas_full_scores.json`):
   - Calcular las 4 métricas sobre el mismo `sample`: `faithfulness_metric`,
     `relevancy_metric` (ya existentes) + `ContextPrecision`/`ContextRecall` nuevas.
   - Añadir el resultado (`id`, `question`, `faithfulness`, `answer_relevancy`,
     `context_precision`, `context_recall`) a la estructura en memoria y volcar el
     fichero completo a disco tras cada caso (mismo patrón ya existente de
     `_write_output()`).
   - Mantener la lógica de `unexpected_alarm` ya existente (`check_alarm_signals`) — sigue
     siendo una señal relevante aunque ahora el subconjunto incluya `otro_idioma`.
   - Al final, `_aggregate()` debe incluir la media de las 4 métricas, no solo 2.

6. **Verificación manual** — ejecutar el script completo, revisar
   `tests/eval/results/e09_t02_ragas_full_scores.json` contra el checklist del `.feature`
   (32 ids, 4 métricas por caso, agregados). Confirmar que
   `tests/eval/results/e07_t02_ragas_scores.json` no se ha tocado. Marcos revisa el
   resultado y anota si algún resultado por debajo de 85% apunta al hallazgo D
   (`backlog/ideas.md`).

## Restricciones a respetar

- **Agnosticismo de proveedor (D-010):** las métricas nuevas se construyen sobre el mismo
  `evaluator_llm` (`ChatGoogleGenerativeAI` vía `LangchainLLMWrapper`) ya en uso — no
  introducir SDK nuevo.
- **Falso Negativo Cero:** no aplica directamente (script de evaluación, no genera
  respuestas de producción nuevas) — mantener el registro de `unexpected_alarm` ya
  existente, ahora también sobre los 5 casos de `otro_idioma`.
- **Privacy by design:** no aplica contenido nuevo — reutiliza el dataset ya validado en
  T-01 (D-054).

## Lo que queda fuera de esta tarea

- Re-evaluar `diagnostico`, `limite`, `prompt_injection` y `alarma` con estas métricas —
  descartado explícitamente en D-055 (sus `expected_answer` no son contenido clínico
  grounded).
- Hallucination Rate (E-09 T-04) y Safety Compliance ampliado (E-09 T-03) — tareas
  separadas de la épica.
- Ciclo de mejora sobre los resultados — es T-05, acotado a los hallazgos A/B/F
  (`backlog/epics.md`), no incluye ajustes derivados de Context Precision/Recall salvo que
  Marcos decida ampliarlo al cerrar esta tarea.
- El informe final con las 4 métricas consolidadas y el checklist CHART — es T-06.
