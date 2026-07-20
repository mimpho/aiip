# Cierre — E-11 T-06: Hallucination Rate, desglose por bandas de severidad

| Campo | Valor |
|---|---|
| Épica | E-11 — Mejora de calidad post-E-09 |
| Tarea | T-06 — Hallucination Rate: desglose por bandas de severidad |
| Fecha | 20 de julio de 2026 |
| Fuentes | `tests/eval/results/e09_t02_ragas_full_scores.json` (32 casos, sin re-medición), `tests/eval/results/e11_t06_eval06_investigacion.json` (investigación dirigida, Antigravity) |
| Decisiones de referencia | D-058 (bandas propuestas, epic-start E-11), D-069 (task-start T-06: frontera 0.85, eval_06 sustituye a eval_15, alcance de la investigación) |

## 1. Bandas de severidad sobre los 32 casos

Fuente: `tests/eval/results/e09_t02_ragas_full_scores.json` (post-T-02, sin re-medición desde entonces — D-066/D-067 no tocan retrieval ni requieren nueva RAGAS).

| Banda | Rango | Casos | % |
|---|---|---|---|
| Grave | < 0.5 | 1 | 3.1% |
| Moderada | 0.5–0.85 | 13 | 40.6% |
| Leve | 0.85–<1.0 (límite incluido, D-069) | 13 | 40.6% |
| Sin desviación | 1.0 | 5 | 15.6% |

**Detalle por caso:**

| Banda | Casos |
|---|---|
| Grave | eval_06 |
| Moderada | eval_02, eval_05, eval_07, eval_08, eval_12, eval_19, eval_20, eval_22, eval_23, eval_26, eval_27, eval_64, eval_67 |
| Leve | eval_01, eval_03, eval_04, eval_09, eval_10, eval_13, eval_14, eval_15, eval_17, eval_18, eval_25, eval_63, eval_65 |
| Sin desviación | eval_11, eval_16, eval_21, eval_24, eval_66 |

De los 30 casos que cuentan como "alucinados" en el binario (D-058), 29 quedan en
Moderada o Leve — matiz de redacción/parafraseo sobre contenido real de la KB, no dato
inventado. Solo `eval_06` cae en Grave, y esa clasificación queda cuestionada (§2).

## 2. Investigación dirigida de `eval_06`

`eval_06` ("¿Con qué frecuencia hay que hacer revisiones con el inmunólogo?") ya figuraba
en hallazgo B (Answer Relevancy 0.0 en eval_06/eval_15/eval_25, `docs/evaluation.md` §5.1,
🔴 Abierto) y presentaba una caída de Faithfulness sin explicar a lo largo de la épica:

| Momento | Faithfulness |
|---|---|
| Pre-E-11 (E-09 T-05) | 0.722 |
| Tras T-01 (KB ampliada) | 0.615 |
| Tras T-02 (peso adaptativo BM25) — **score oficial usado en el desglose** | 0.385 |
| Reproducción de hoy (T-06, mismo pipeline) | 0.7308 |

Ejecutado en Antigravity (`scripts/run_e11_t06_eval06_investigation.py`,
`tests/eval/results/e11_t06_eval06_investigacion.json`), sin aplicar ningún fix
(investigación pura, D-065/D-069):

1. **Hipótesis de hallazgo B (cita inline de documento/páginas)** — no se reproduce
   (`finding_b_contrast.present: false`). No explica el score bajo en esta ejecución.
2. **Estabilidad del juez** — `Faithfulness` da 0.7308 en dos invocaciones sobre el mismo
   `SingleTurnSample` (misma respuesta, mismo contexto). El juez es estable; el ruido no
   está en la evaluación.
3. **Reproducción íntegra del caso** (retrieval + generación reales, pipeline actual) da
   0.7308, no 0.385 — y coincide más con el valor pre-épica (0.722) que con el registrado.
   La respuesta generada hoy está bien fundamentada en los chunks recuperados (seguimiento
   en embarazo, pruebas de laboratorio de rutina, derivación a inmunólogo — todo verificable
   literalmente en el contexto recuperado), sin cita duplicada, sin alarma de seguridad
   inesperada (`unexpected_alarm: false`), con tono cauteloso apropiado (remite a consulta
   médica sin inventar una cifra de frecuencia).
4. **Causa más probable: no determinismo del LLM generador**, no una regresión sistemática
   de T-01/T-02. Cada medición histórica es una muestra de un texto generado distinto; con
   temperatura > 0 en el generador, el score de Faithfulness varía de ejecución en
   ejecución para la misma pregunta y el mismo pipeline. No hay evidencia de causa
   estructural (retrieval degradado, cita duplicada, alarma).

**Decisión:** el score oficial (0.385) se mantiene sin modificar en el dataset y en el
conteo de bandas — no se sustituye por la re-medición más favorable (mismo criterio de
D-058 de no "suavizar" el número eligiendo la lectura que hace quedar mejor al sistema).
Pero se marca explícitamente como **cuestionado** en `docs/evaluation.md` §5.3, en vez de
presentarse como una alucinación grave confirmada y estable.

## 3. Documentación

- `docs/evaluation.md` §5.3 (nueva): bandas de severidad + nota de transparencia sobre
  `eval_06`.
- `docs/evaluation.md` §7: fila de Hallucination Rate actualizada con referencia a §5.3.
- Binario (93.75%) sin cambios — `eval_06` sigue contando como "alucinado" con cualquiera
  de los dos valores (ambos < 1.0).

## 4. Regresiones de la suite de tests

No aplica: T-06 es documentación/investigación sin TDD (D-050/D-065), sin código de
producción modificado. No se ha tocado `rag/retriever.py`, `prompts/` ni
`config/alarm_triggers.json`.

## 5. Confirmación

Bandas y frontera 0.85→Leve confirmadas por Marcos (20 jul 2026). Alcance ampliado con
investigación dirigida de `eval_06` aprobado por Marcos tras cuestionar el aplazamiento
inicial propuesto (misma sesión). Tratamiento final de `eval_06` (mantener score oficial,
marcarlo cuestionado en vez de sustituirlo) confirmado por Marcos. Último escenario del
`.feature` ("Marcos confirma las bandas y el resultado final") satisfecho.
