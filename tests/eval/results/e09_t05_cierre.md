# Cierre del ciclo de mejora — E-09 T-05

| Campo | Valor |
|---|---|
| Épica | E-09 — Evaluación RAGAS completa |
| Tarea | T-05 — Ciclo de mejora (hallazgos A, B, D, F) |
| Fecha | 17 de julio de 2026 |
| Fuentes | `tests/eval/results/e09_t02_ragas_full_scores_pre_t05.json` (antes), `tests/eval/results/e09_t02_ragas_full_scores.json` (después), `tests/eval/results/e09_t05_plan_b_investigacion.md` |
| Modelo evaluado | `gemini-2.5-flash` (producción, D-043) |
| Decisiones de referencia | D-056 (reordenamiento), D-057 (solución técnica por hallazgo) |

## 1. Re-medición RAGAS: antes / después (32 casos, `informativo` + `otro_idioma`)

| Métrica | T-02 (pre-T-05) | T-05 (post-ajustes) | Delta |
|---|---|---|---|
| Faithfulness | 79.2% | 83.7% | +4.5pp |
| Answer Relevancy | 75.9% | 79.5% | +3.6pp |
| Context Precision | 53.8% | 52.1% | −1.6pp |
| Context Recall | 70.3% | 75.5% | +5.2pp |

3 de las 4 métricas mejoran. Context Precision se mantiene prácticamente plana (ligero
retroceso de 1.6pp) — ver hallazgo D abajo para la lectura de por qué el retriever
híbrido no la mueve tanto como cabría esperar por ser la métrica peor del baseline.

Ningún caso de los 32 (`informativo`/`otro_idioma`) dispara la alarma de seguridad de
forma inesperada tras el ajuste de A (`unexpected_alarm` ausente en los 32 registros del
fichero post-T-05 — antes del ajuste, eval_07/eval_08/eval_25 sí la disparaban).

## 2. Estado por hallazgo

| Hallazgo | Estado | Resumen |
|---|---|---|
| **A** — sobre-activación del filtro de seguridad | ✅ Resuelto | Stoplist (`después`, `varios`, `infusión`) + `requires_context` para "antibióticos" en `config/alarm_triggers.json`. eval_07/08/25 dejan de disparar la alarma; los 27 casos reales de alarma/límite (Falso Negativo Cero) siguen activándose sin regresión. |
| **D** — ruido en dense/hybrid search | 🟡 Mitigado parcialmente | `EnsembleRetriever` (BM25 + vectorial, RRF) implementado en `rag/retriever.py`/`rag/pipeline.py`. Recupera correctamente coincidencias léxicas exactas (topónimos) y no empeora los casos ya bien recuperados en T-02. El caso CU-05 (directorio aedip para preguntas de contacto genéricas) **no se resuelve**: investigado contra la KB real, el chunk no comparte vocabulario con la pregunta — no es un problema de algoritmo de retrieval, necesitaría contenido nuevo en la KB o enrutamiento de intención (documentado como `xfail` en `tests/step_defs/test_e09_t05.py`). Context Precision agregada no mejora (ver tabla arriba). |
| **F** — `langdetect` falla en frases cortas de síntomas | ✅ Resuelto | Sustituido por `lingua-py`, restringido a es/en/ca. Las 3 frases cortas de síntomas que antes fallaban detectan correctamente "es"; las 37 frases de `alarm_triggers.json` + muestra ya validada (D-017) siguen detectando bien. |
| **B** — Answer Relevancy 0.0 (eval_06, eval_15, eval_25) | 🔴 Abierto | Investigado dentro del margen tras A/D/F (Plan B, D-057). Candidato de causa razonablemente sólido — respuesta evasiva ("noncommittal") penalizada por el diseño de `ResponseRelevancy` de RAGAS, en tensión directa con Falso Negativo Cero — pero no confirmado frase a frase, y `context_precision`/`context_recall = 0.0` en los mismos 3 casos sigue sin explicación completa. Detalle en `tests/eval/results/e09_t05_plan_b_investigacion.md`. Ningún ajuste de código aplicado — no es scope comprometido de T-05 (D-057). |
| **C, E** | Fuera de alcance | Quedan en `backlog/ideas.md`, no forman parte de este ciclo (D-056). |

## 3. Regresiones de la suite de tests

Suite completa (`PYTHONPATH=. pytest tests/ -v`): sin regresiones tras los ajustes. Se
actualizaron los mocks de `tests/step_defs/test_e05_t02.py` y `tests/step_defs/test_e05_t03.py`
(asumían la interfaz antigua de retrieval — `similarity_search_with_score` directo — que
el hallazgo D reemplaza por el retriever híbrido).

## 4. Pendiente de confirmación

Este documento resume el resultado técnico del ciclo. La confirmación de que el ciclo de
mejora está listo para el informe final (T-06) — último escenario del `.feature`,
"Marcos revisa y confirma el cierre del ciclo de mejora" — requiere revisión humana
explícita y no está marcada como completada aquí.
