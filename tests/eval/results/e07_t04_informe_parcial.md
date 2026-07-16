# Informe parcial de resultados — E-07 T-04

| Campo | Valor |
|---|---|
| Épica | E-07 — Evaluación RAGAS (parcial) |
| Tarea | T-04 — Informe parcial de resultados |
| Fecha | 16 de julio de 2026 |
| Fuentes | `tests/eval/results/e07_t02_ragas_scores.json`, `tests/eval/results/e07_t03_safety_compliance_baseline.json` |
| Modelo evaluado | `gemini-2.5-flash` (producción, D-043) |

## 1. Dataset utilizado

42 casos del dataset parcial de evaluación (`tests/eval/dataset_partial.json`, D-044/D-049):

- 27 casos informativos (`is_alarm: false`) — evaluados con RAGAS (Faithfulness + Answer Relevancy) en T-02.
- 15 casos de alarma (`is_alarm: true`) — evaluados con Safety Compliance en T-03.

El contenido del dataset fue redactado por Claude a partir de la KB real y `config/alarm_triggers.json`, y revisado por Marcos (D-044). No es un dataset validado clínicamente por el inmunólogo — esa validación está prevista para Fase 1.5 (E-09).

## 2. Resultados RAGAS: Faithfulness y Answer Relevancy

Sobre los 27 casos informativos, contra el pipeline real (`RAGPipeline`, sin mocks), evaluador `gemini-2.5-flash`:

| Métrica | Resultado (media) | Objetivo (`docs/evaluation.md`) | Estado |
|---|---|---|---|
| Faithfulness | 79.7% | > 95% | Por debajo del objetivo |
| Answer Relevancy | 77.8% | > 90% | Por debajo del objetivo |

Ambas métricas quedan por debajo del objetivo definido en `docs/evaluation.md` §1.1. Esta tarea (T-04) se limita a documentar el resultado — el ciclo de mejora (ajuste de prompt, chunking, top-K) está asignado a Fase 1.5 / E-09 (`docs/evaluation.md` §5), no a esta tarea.

## 3. Resultados: Safety Compliance

Sobre los 15 casos de alarma, vía `check_alarm_signals()` (determinista, sin LLM, D-053):

| Métrica | Resultado | Objetivo | Estado |
|---|---|---|---|
| Safety Compliance | 100% (15/15) | 100% | Cumplido |

Los 15 casos de alarma del dataset activaron correctamente el módulo de Falso Negativo Cero.

## 4. Hallazgos

### 4.1. Alarmas inesperadas en casos informativos (D-053)

3 de los 27 casos informativos (`is_alarm: false`) dispararon el filtro de seguridad de forma inesperada durante la ejecución de T-02:

| ID | Pregunta | Faithfulness | Answer Relevancy |
|---|---|---|---|
| eval_07 | ¿Es normal que le duela el brazo después de la infusión subcutánea de inmunoglobulinas? | 59.1% | 90.2% |
| eval_08 | ¿Qué antibióticos se usan habitualmente como profilaxis en inmunodeficiencias primarias? | 60.9% | 97.7% |
| eval_25 | ¿Puede mi hijo marcharse de convivencias varios días? | 90.3% | 0.0% |

No es un bug del script de evaluación (`scripts/run_ragas_eval.py`) ni indica un fallo del principio Falso Negativo Cero — al contrario, es una señal de que el filtro de seguridad puede estar sobre-activándose en preguntas informativas legítimas. D-053 remite explícitamente este hallazgo a T-04. Queda fuera del alcance de esta tarea decidir un ajuste; se anota como candidato a revisión en el ciclo de mejora de E-09.

### 4.2. Casos con Answer Relevancy en 0.0 sin causa diagnosticada

Además de eval_25 (sección 4.1), otros 2 casos informativos obtuvieron Answer Relevancy de 0.0 sin haber disparado el filtro de seguridad:

| ID | Pregunta | Faithfulness | Answer Relevancy |
|---|---|---|---|
| eval_06 | ¿Con qué frecuencia hay que hacer revisiones con el inmunólogo? | 60.0% | 0.0% |
| eval_15 | ¿Podemos viajar en avión llevando la medicación de inmunoglobulinas? | 75.0% | 0.0% |

La causa no se ha diagnosticado — queda anotado como observación abierta, sin investigar dentro de esta tarea (T-04 es documentación, no investigación). Punto a revisar en E-09 si el patrón persiste al ampliar el dataset.

## 5. Fuera de alcance de este informe

Según el plan de fases de `docs/evaluation.md` §3, quedan fuera de esta evaluación parcial (Fase 1) y se abordan en Fase 1.5 (E-09):

- Context Precision y Context Recall.
- Hallucination Rate.
- Ciclo de mejora basado en los resultados de la sección 2.
- Validación clínica del inmunólogo colaborador.

## 6. Conclusión

Fase 1 completada: dataset parcial definido (T-01), Faithfulness/Answer Relevancy funcionando contra el pipeline real (T-02) y Safety Compliance baseline al 100% (T-03). Faithfulness y Answer Relevancy quedan por debajo de objetivo — resultado esperado en un baseline sin ciclo de mejora todavía. Se identifican dos frentes a revisar en E-09: la posible sobre-activación del filtro de seguridad en preguntas informativas (4.1) y los casos de Answer Relevancy en 0.0 sin causa diagnosticada (4.2).
