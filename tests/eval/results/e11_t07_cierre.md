# Cierre — E-11 T-07: informe final en docs/evaluation.md

| Campo | Valor |
|---|---|
| Épica | E-11 — Mejora de calidad post-E-09 |
| Tarea | T-07 — Cierre: informe final en `docs/evaluation.md` |
| Fecha | 21 de julio de 2026 |
| Fuentes | `tests/eval/results/e11_t02_cierre.md`, `e11_t03_cierre.md`, `e11_t04_cierre.md`, `e11_t05_cierre.md`, `e11_t06_cierre.md`, `e11_t07_ragas_regression_check.json`, `e11_t07_t05_regression_check.json`, `e11_t07_context_precision_stability.json`, `e11_t07_citation_duplication_investigation.json` |
| Decisiones de referencia | D-070 (Bloque 0: regresión de T-04/T-05), D-071 (Bloque 0b: estabilidad de juez + causa raíz de citación duplicada), D-072 (cierre de ambos puntos + fix de `[FUENTES]`) |
| `.feature` | `tests/eval/e11_t07_informe_final.feature` |

## 1. Alcance ejecutado

T-07 se amplió dos veces sobre el borrador de `epic-start` (documentación pura). La
primera ampliación (D-070) añadió un bloque de verificación de regresión de los cambios
de prompt de T-04/T-05 antes de escribir el informe final, al detectar que ninguno de los
dos se había re-verificado con RAGAS ni con la suite de tests tras aplicarse. La segunda
(D-071) surgió de dos hallazgos del primer bloque que no se cerraron por analogía con
precedentes: dos caídas de Context Precision más allá del umbral orientativo, y un
hallazgo nuevo no buscado (citación duplicada de fuentes).

## 2. Regresión de T-04/T-05 (Bloque 0, D-070)

- **Suite de tests:** `PYTHONPATH=. pytest tests/ -v` — 147 passed, 14 skipped, 1
  xfailed, idéntico al baseline de T-02. Sin regresión funcional.
- **T-04 (tono):** las 7 preguntas de `scripts/run_e11_t04_linguistic_review.py`
  re-ejecutadas confirman que la glosa de fármacos/acrónimos/síndromes aparece de forma
  consistente en los casos con hallazgo (`ling_04`, `ling_07`), sin diluir el cierre
  obligatorio de derivación médica.
- **T-05 (restricción de centro):** de las 3 preguntas de reproducción manual, la que
  antes citaba `guia_antibiotics_esp_0.pdf` sin salvedad ahora incluye explícitamente la
  salvedad de información específica de un centro.
- **RAGAS acotado (`eval_03`, `eval_04`, `eval_08`, `eval_13`):** Faithfulness, Answer
  Relevancy y Context Recall dentro de ruido o mejor. Context Precision cae más allá del
  umbral en `eval_08` (Δ−0.300) y `eval_13` (Δ−0.143) — investigado en el Bloque 0b.

## 3. Estabilidad de Context Precision y causa raíz de la citación duplicada (Bloque 0b, D-071)

- **`eval_08`/`eval_13`:** dos invocaciones del juez sobre el mismo `SingleTurnSample`
  (sin repetir retrieval/generación). `eval_13` reproduce dentro de una sola ejecución los
  dos valores históricos ya registrados en la épica (0.0 y 0.143). `eval_08` da 0.5 en
  ambas invocaciones, coincidiendo con el valor oficial de T-02. Contexto recuperado
  revisado manualmente en los dos casos: directamente relevante a la pregunta. **Cerrado
  como ruido documentado del evaluador LLM** (D-072), mismo patrón que `eval_06`/`eval_15`
  (D-068/D-069) — no se re-mide más, no se toca `rag/retriever.py`.
- **Citación duplicada:** `ling_07` repetido 3 veces en producción duplica 1 de 3 (ruido
  de muestreo, no propiedad fija de la pregunta). Una variante de `[FUENTES]` con
  prohibición explícita y contraejemplo, probada en memoria sobre las 10 preguntas del
  Bloque 0, elimina la duplicación (0/10 frente al 11/17 ya observado en producción), sin
  regresión de seguridad en ninguna de las 10 respuestas.

## 4. Fix aplicado a producción (D-072)

`prompts/system_prompt_family.txt`, sección `[FUENTES]`, reescrita en Cowork (sin
Antigravity, mismo patrón que D-068) con la prohibición explícita de generar un bloque de
fuentes propio y un contraejemplo concreto. No se re-ejecuta RAGAS ni la suite de tests
para este cambio — ajuste de formato/generación, no de retrieval (D-018 ya confirma que
ningún test depende de la redacción exacta del prompt).

## 5. Informe final

`docs/evaluation.md` actualizado:
- §5.1: tabla de hallazgos con estado final de B (parcial), C (cerrado) y E (cerrado).
- §5.4 (nueva): resultados consolidados de E-11 (triple antes/después de T-02, ampliación
  de KB trazada, hallazgos, investigación T-05, desglose de T-06, y verificación de
  regresión de este cierre).
- §7: tabla de métricas de éxito con columna de resultado post-E-11 y delta — **Context
  Recall cruza el objetivo de >85% por primera vez en el proyecto** (86.5%); Context
  Precision mejora +11.1pp sin llegar a objetivo; Faithfulness/Answer Relevancy casi sin
  cambio; Hallucination Rate binario sin cambio, matizado por el desglose de T-06.

Documentado sin suavizar (CHART/TRIPOD-LLM): 3 de 6 métricas siguen por debajo de
objetivo, y se indica explícitamente.

## 6. Limitación de transparencia declarada

El fix de `[FUENTES]` (D-072) se aplicó al final de esta tarea y no se ha vuelto a medir
RAGAS después — es un ajuste de formato de la respuesta, no de retrieval, mismo criterio
que D-067/D-068. Documentado así en `docs/evaluation.md` §5.4, no oculto.

## 7. Confirmación

Pendiente de revisión y confirmación de Marcos — último escenario del `.feature`
("Marcos revisa y confirma el cierre de la épica"). Si confirma, T-07 pasa a ✅ Completada
en `backlog/epics.md` y la épica queda lista para `epic-close`.
