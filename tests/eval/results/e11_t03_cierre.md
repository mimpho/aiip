# Cierre — E-11 T-03: Hallazgo C, regla acotada de grounding para conectores no clínicos

| Campo | Valor |
|---|---|
| Épica | E-11 — Mejora de calidad post-E-09 |
| Tarea | T-03 — Hallazgo C: regla acotada de grounding para conectores no clínicos |
| Fecha | 19 de julio de 2026 |
| Fuentes | `tests/eval/results/e11_t03_investigacion_offline.json` (investigación offline), `scripts/run_e11_t03_grounding_investigation.py` |
| Modelo evaluado | `gemini-2.5-flash` (producción, D-043) |
| Decisiones de referencia | D-059 punto 5 (investigación offline como método), D-065 (tipo de tarea sin TDD, exclusiones de alcance) |

## 1. Resultado de la investigación offline

Caso sintético construido y verificado contra el KB real post-ampliación (T-01): la pregunta
"¿hay algún hospital con inmunología cerca de Vic?" recupera el chunk de
`data/raw/aedip/Hospitales-con-Servicios-de-Inmunologia.html`, que etiqueta los hospitales
Sant Joan de Déu y Vall d'Hebron como "Barcelona" — ningún chunk recuperado menciona "Vic".
El caso reproduce fielmente la estructura del hallazgo original (`backlog/ideas.md`,
"Hallazgos del RAG" punto 1, ilustración de Marcos durante E-05 T-03).

| Variante | Mecanismo | Resultado |
|---|---|---|
| Estricta | `RAGPipeline.query()`, prompt de producción sin cambios | Conecta el concepto no clínico sin evasivas: *"no hay hospitales listados específicamente en Vic. Sin embargo, en Barcelona, que no está muy lejos, hay varios hospitales..."* |
| Laxa | `RAGGenerator` alternativo con permiso experimental añadido en memoria (nunca escrito a `prompts/system_prompt_family.txt`) | Contenido y tono prácticamente idénticos a la estricta — sin diferencia de comportamiento relevante |

**Lectura:** el comportamiento evasivo descrito en el hallazgo C original **no se reproduce**
con el prompt de producción actual. Es plausible que la evasividad observada por Marcos
durante la validación de E-05 T-03 correspondiera a una versión anterior de
`prompts/system_prompt_family.txt` — el prompt ha recibido varias revisiones desde entonces
(D-026, D-040, restricciones añadidas en E-09 T-04) que pueden haber cambiado este
comportamiento como efecto colateral, sin que ninguna de ellas se dirigiera específicamente a
este hallazgo.

## 2. Decisión de cierre

Confirmado por Marcos (19 jul 2026): **se cierra el hallazgo C sin modificar
`prompts/system_prompt_family.txt`.** No se redacta ni se aplica ninguna regla de grounding —
el comportamiento deseado (conectar conceptos no clínicos de sentido común sin comprometer el
grounding clínico) ya se produce con el prompt actual, y añadir una regla explícita sin
necesidad demostrada iría contra el principio de no aflojar el grounding sin justificación
real (D-002, D-059 punto 3).

Consecuencia directa: los escenarios del `.feature`
(`tests/eval/e11_t03_grounding_conectores.feature`) que dependían de la redacción y aplicación
de una regla (Bloque 2: "Regla propuesta...", "Marcos aprueba la redacción exacta"; Bloque 3:
"El conector no-clínico se resuelve tras el ajuste", "Los 32 casos ya medidos en T-02 no
empeoran") **no aplican** — no hay ajuste que verificar ni regresión que medir, porque no hay
cambio de código ni de prompt. El escenario de "Contraste offline" (Bloque 1) queda satisfecho
con la investigación ya documentada arriba. El escenario de "grounding clínico se mantiene
estricto" también queda satisfecho por construcción (no se tocó nada del comportamiento
clínico).

## 3. Regresiones de la suite de tests

No aplica — no se modificó ningún fichero de código ni `prompts/system_prompt_family.txt`.
No hace falta re-ejecutar `pytest tests/` ni RAGAS para esta tarea.

## 4. Confirmación

Revisado y confirmado por Marcos (19 jul 2026): el hallazgo C queda cerrado tal como está
documentado en este informe, sin cambios de producción, dado que el comportamiento del
prompt actual ya satisface el objetivo original del hallazgo.
