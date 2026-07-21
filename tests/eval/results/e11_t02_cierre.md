# Cierre — E-11 T-02: re-medición RAGAS + peso adaptativo de BM25

| Campo | Valor |
|---|---|
| Épica | E-11 — Mejora de calidad post-E-09 |
| Tarea | T-02 — Re-medición RAGAS + peso adaptativo de BM25 |
| Fecha | 19 de julio de 2026 |
| Fuentes | `tests/eval/results/e09_t02_ragas_full_scores_pre_e11_t02.json` (E-09 T-05), `tests/eval/results/e09_t02_ragas_full_scores_e11_t02_baseline.json` (línea base post-ampliación), `tests/eval/results/e09_t02_ragas_full_scores.json` (final, peso adaptativo) |
| Modelo evaluado | `gemini-2.5-flash` (producción, D-043) |
| Decisiones de referencia | D-060 (T-01), D-061 (mecanismo del peso adaptativo) |

## 1. Triple antes/después (32 casos, `informativo` + `otro_idioma`)

| Métrica | E-09 T-05 (corpus sin ampliar, peso uniforme) | Línea base (corpus ampliado, peso uniforme) | Final (corpus ampliado, peso adaptativo) |
|---|---|---|---|
| Faithfulness | 83.7% | 85.5% | 84.6% |
| Answer Relevancy | 79.5% | 78.6% | 79.9% |
| Context Precision | 52.1% | 62.6% | 63.2% |
| Context Recall | 75.5% | 83.9% | 86.5% |

**Lectura:** la ampliación de la KB (T-01) es la que produce el salto real — Context
Precision +10.5pp y Context Recall +8.4pp solo por tener más/mejor cobertura documental,
antes de tocar BM25. El peso adaptativo, sobre ese nuevo baseline, aporta una mejora
adicional pero pequeña: Context Precision +0.6pp, Context Recall +2.6pp, Answer Relevancy
+1.3pp; Faithfulness retrocede levemente (−0.9pp, dentro del ruido esperable del LLM
evaluador — no hay una relación directa de causalidad plausible entre el peso de BM25 y
Faithfulness, que depende del texto generado, no del ranking de recuperación). Ningún caso
de los 32 dispara `unexpected_alarm`.

## 2. Regresión / mejora de los 10 casos identificados en la retrospectiva de E-09 T-05 (D-061)

Comparación contra la **línea base post-ampliación** (no contra E-09 T-05), que es el
punto de partida correcto para aislar el efecto del ajuste de BM25 del efecto de la KB.

| Caso | Señal léxica (`has_lexical_signal`) | Context Precision línea base | Context Precision final | Delta |
|---|---|---|---|---|
| eval_64 (empeoró en E-09 T-05) | sin señal | 1.000 | 1.000 | +0.000 |
| eval_17 (empeoró en E-09 T-05) | **con señal** | 0.975 | 0.975 | +0.000 |
| eval_16 (empeoró en E-09 T-05) | sin señal | 0.500 | 0.500 | +0.000 |
| eval_19 (empeoró en E-09 T-05) | sin señal | 0.500 | 0.500 | +0.000 |
| eval_02 (empeoró en E-09 T-05) | sin señal | 0.933 | 0.933 | +0.000 |
| eval_04 (empeoró en E-09 T-05) | sin señal | 0.556 | 0.556 | +0.000 |
| eval_07 (mejoró en E-09 T-05) | con señal | 0.710 | 0.710 | +0.000 |
| eval_11 (mejoró en E-09 T-05) | sin señal | 0.111 | 0.111 | +0.000 |
| eval_01 (mejoró en E-09 T-05) | sin señal | 1.000 | 1.000 | +0.000 |
| eval_21 (mejoró en E-09 T-05) | con señal | 0.812 | 0.812 | +0.000 |

Los 6 casos que empeoraron no empeoran más (criterio cumplido) y los 4 que mejoraron se
mantienen igual (criterio cumplido, "igual o mejor"). En los 32 casos completos solo 2
(`eval_08`, `eval_63`) cambian de Context Precision entre línea base y final
(+0.05 y +0.136 respectivamente) — el resto del corpus ampliado ya es lo bastante bueno
por sí mismo para que el peso de BM25 no altere el ranking final en la mayoría de
preguntas, con o sin señal léxica.

**Nota sobre `eval_17`:** clasificado como "con señal léxica" por el criterio ampliado de
D-061 (una palabra del corpus real de producción supera el `average_idf`, no detectable
con el corpus de prueba de 5 frases usado en `tests/step_defs/test_e11_t02.py`). Al tener
señal, su peso no cambia respecto al uniforme (0.4/0.6) — su resultado idéntico entre línea
base y final es consistente con eso, no una falla del criterio.

## 3. Fallback (no necesario)

El peso adaptativo (D-061) cerró dentro del margen de la tarea sin necesidad de recurrir al
fallback de peso fijo recalibrado (0.2/0.8) descrito en el `.feature`. No se documenta activación
de fallback porque no se activó.

## 4. Regresiones de la suite de tests

Suite completa (`PYTHONPATH=. pytest tests/ -v`): 147 passed, 14 skipped, 1 xfailed, sin
regresiones. Los 3 escenarios de código de T-02 (detección de señal léxica, recálculo del
peso por consulta, ponderación mayor con señal) llevan asserts pytest-bdd normales en
`tests/step_defs/test_e11_t02.py`; los 8 escenarios restantes (backup/reset/re-medición/
confirmación) están marcados `pytest.skip()` con motivo documentado, mismo patrón que
`tests/step_defs/test_e09_t05.py` — ya no dependen de una ejecución futura (la ejecución
real ya se hizo para este cierre), pero se mantienen como skip porque siguen sin ser
deterministas/automatizables (dependen del LLM evaluador real) y por consistencia con el
criterio de D-050/D-051 de no poner asserts sobre resultados de un LLM no determinista.

## 5. Confirmación

Revisado y confirmado por Marcos (19 jul 2026): el ajuste de BM25 queda cerrado tal como
está documentado en este informe, sin necesidad de iterar antes de pasar a T-03. Último
escenario del `.feature` ("Marcos revisa y confirma el ajuste de BM25") satisfecho.
