# Cierre — E-11 T-05: Investigación dirigida (`eval_15`, `eval_63`, `guia_antibiotics_esp_0.pdf`)

| Campo | Valor |
|---|---|
| Épica | E-11 — Mejora de calidad post-E-09 |
| Tarea | T-05 — Investigación dirigida: `eval_15`, confirmación `eval_63`, documento sospechoso `guia_antibiotics_esp_0.pdf` |
| Fecha | 20 de julio de 2026 |
| Fuentes | `tests/eval/results/e11_t05_eval15_investigacion.json` (diagnóstico de retrieval, Antigravity), reproducción manual en Chainlit (Cowork), `docs/kb-sources.md` líneas 43/45 |
| Decisiones de referencia | D-057/D-059 (E-09/creación de E-11), D-060/D-061 (T-01/T-02), D-068 (este cierre) |
| `.feature` | `tests/features/e11_t05_investigacion_eval15_eval63_antibiotics.feature` |

## 1. `eval_63` — confirmado, sin investigación adicional

Faithfulness estable (~0.88) desde el fix de hallazgo D en E-09; Context Precision mejora de
0.639 a 0.804 con el peso adaptativo de BM25 (T-02). Cierra el hallazgo #5 de
`backlog/ideas.md`. Ver D-068 §1.

## 2. `eval_15` — problema original cerrado, hallazgo nuevo investigado y documentado

**Problema original** (Faithfulness 0.38, 0.0 en las otras tres métricas, "hallazgo B" del
Plan B de E-09): cerrado como efecto colateral de T-01 (KB ampliada). Faithfulness sube a 0.9
(baseline)/0.875 (final); Answer Relevancy pasa de 0.0 a 0.84/0.839. La hipótesis de
"respuesta evasiva" ya no se reproduce. Ver D-068 §2.

**Hallazgo nuevo, no anticipado en el criterio original de la épica:** Context Precision se
mantiene en 0.0 en 5 mediciones independientes (3 históricas + 2 ejecuciones frescas del
diagnóstico) pese a que T-01 añadió dos fuentes para este tema. Context Recall fluctúa entre
1.0 y 0.0 con retrieval idéntico entre mediciones.

Diagnóstico ejecutado en Antigravity (`scripts/run_e11_t05_eval15_investigation.py`,
`tasks/E11-T05-plan.md`), verificado en Cowork:

- **Retrieval confirmado sin cambios entre T-01 y T-02 para esta consulta**: señal léxica
  `True` ⇒ peso adaptativo = peso uniforme (0.4/0.6). Forzar el peso `NO_SIGNAL` (0.05/0.95)
  tampoco cambia el top-10 (contraste informativo, no aplica en producción para esta
  consulta).
- **Ninguna de las dos fuentes nuevas de T-01** (SEICAP cap. 6 "viajes", FAQ de IPOPI) aparece
  en el top-10, con ningún peso probado.
- **Contraste frase a frase contra `expected_answer`**: el top-10 cubre el mensaje general
  ("se puede viajar, hay que planificarlo, carta del inmunólogo") vía un único chunk
  (`aedip/mantenerse-saludable.pdf`, sección "Viajes"), mezclado con contenido irrelevante
  para esta pregunta (antibióticos IV en casa, efectos secundarios de inmunoglobulina). No
  cubre dos afirmaciones concretas: condiciones de conservación en frío, y consultar la
  farmacia hospitalaria para el transporte.
- **Verificación adicional en Cowork, más allá del diagnóstico de Antigravity**: búsqueda
  directa (no solo por score) de "nevera"/"refrigeración"/"cadena de frío" (y equivalentes en
  inglés) en el texto completo de los 41 PDFs + HTMLs de `data/raw/`. **Cero resultados.**
  Revisado también el capítulo de viajes del SEICAP (cap. 6, páginas 41-42): trata comida,
  agua, vacunas y zonas de riesgo — no menciona transporte ni conservación de medicación. La
  FAQ de IPOPI tampoco. **Conclusión: la afirmación sobre conservación en frío no existe en
  ningún documento de la KB — no es un problema de ranking de retrieval, es un hueco de
  contenido genuino** que ninguna mejora de BM25/chunking puede resolver por sí sola.
- **Estabilidad del juez LLM**: dos ejecuciones frescas sobre el mismo `retrieved_contexts`
  dieron Context Recall 1.0 las dos veces — coincide con el valor archivado de T-01 (peso
  uniforme), no con el 0.0 archivado de T-02 (mismo retrieval en ambos). Evidencia directa de
  no-determinismo del juez LLM (`evaluator_llm`, `temperature=0.1`,
  `scripts/run_ragas_eval.py`) para esta métrica en este caso, no de una regresión de
  retrieval real.

**Decisión (Marcos, 20 jul 2026):**

1. **Context Recall**: documentado como ruido de medición conocido del juez LLM, sin fix —
   mismo criterio de D-050/D-051 (no exigir determinismo a un evaluador LLM). No se persigue
   más.
2. **Context Precision**: el hueco de contenido (conservación en frío de inmunoglobulinas en
   viaje) no se rellena con conocimiento general del LLM — descartado explícitamente,
   corolario de D-059 en `AGENTS.md`: el manejo de un fármaco inyectable sin fuente vetada por
   Jacques es más arriesgado que dejar el hueco documentado, y no es un caso "no clínico"
   comparable al hallazgo C (T-03) donde sí se investigó y descartó abrir el LLM.
3. **No se añade una fuente nueva ahora.** Se documenta como el primer hueco de una lista
   viva nueva en `backlog/ideas.md` ("Huecos de KB — temas coloquiales pendientes de
   ampliar", entrada #1) para agrupar y resolver junto con futuros huecos similares en una
   próxima ampliación de KB — mismo patrón que ya funcionó en T-01 (6 huecos resueltos de una
   vez, D-060), en vez de un ciclo de vetado por cada hueco puntual que aparezca.

## 3. `guia_antibiotics_esp_0.pdf` — cerrado

Reproducción manual guiada en Chainlit (perfil familiar, corpus/BM25 actuales) de las 3
preguntas documentadas en `backlog/ideas.md` (actualizaciones 10/18 jul): el patrón se repite
en 2 de 3. Causa raíz identificada: el documento (guía de la unidad UPIIP, Hospital Vall
d'Hebron) incluye una sección "Datos de contacto" con el teléfono de Urgencias Pediátricas de
ese hospital concreto — contenido correcto pero específico de un centro, presentado sin esa
salvedad. Cerrado generalizando la restricción ya existente de `[RESTRICCIONES ABSOLUTAS]`
sobre protocolos de tratamiento a cualquier información operativa de un centro concreto
(protocolo, dato de contacto, nombre de servicio/unidad). Aplicado directamente en
`prompts/system_prompt_family.txt`. Detalle completo en D-068 §4.

## 4. Confirmación

Confirmado por Marcos (20 jul 2026): las tres investigaciones quedan cerradas tal como están
documentadas en este informe y en D-068 — `eval_63` confirmado, `eval_15` cerrado (problema
original) con hallazgo nuevo documentado (no resuelto, backlog agrupado), y
`guia_antibiotics_esp_0.pdf` cerrado con el ajuste de prompt aplicado. T-05 pasa a
✅ Completada en `backlog/epics.md`.
