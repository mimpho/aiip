# E-09 T-05 — Plan B: investigación de Answer Relevancy 0.0 (eval_06, eval_15, eval_25)

**Estado: abierto** (D-057). Investigado dentro del margen disponible tras A, D y F;
no se aplica ningún ajuste de código a partir de este hallazgo — ver justificación abajo.

**Actualización tras la re-medición completa (32/32 casos, cierre de T-05):** el fichero
de resultados original (T-02) ya incluía un tercer caso con el mismo patrón —
**eval_25** — que no estaba nombrado en el informe parcial de T-04 §4.2 porque se había
documentado bajo el hallazgo A (§4.1: disparaba la alarma de seguridad de forma
indebida). Tras el ajuste de A, eval_25 ya no dispara la alarma (`unexpected_alarm`
desaparece de su entrada), pero su `answer_relevancy`/`context_precision`/
`context_recall` siguen en 0.0 exactamente igual que antes — confirma que es un problema
independiente del de A, no resuelto por su ajuste. El patrón cubre 3 casos, no 2.

## Contexto

En T-02 (`tests/eval/results/e09_t02_ragas_full_scores_pre_t05.json`, respaldo de este
ciclo), tres de los 32 casos informativos anotan simultáneamente `answer_relevancy = 0.0`,
`context_precision = 0.0` y `context_recall = 0.0`, mientras que `faithfulness` es normal:

| id | question | faithfulness | answer_relevancy | context_precision | context_recall |
|---|---|---|---|---|---|
| eval_06 | ¿Con qué frecuencia hay que hacer revisiones con el inmunólogo? | 0.600 | 0.0 | 0.0 | 0.0 |
| eval_15 | ¿Podemos viajar en avión llevando la medicación de inmunoglobulinas? | 0.737 | 0.0 | 0.0 | 0.0 |
| eval_25 | ¿Puede mi hijo marcharse de convivencias varios días? | 0.853 | 0.0 | 0.0 | 0.0 |

Los tres casos tienen resultado completo en el fichero (las 4 métricas presentes), lo que
descarta que el bloque `try/except` de `scripts/run_ragas_eval.py` esté tragándose una
excepción silenciosamente — RAGAS calculó `0.0` de forma legítima, no hubo fallo de
llamada. Tras la re-medición post-T-05, los tres casos **siguen en 0.0** sin cambios —
los ajustes de A, D y F no lo tocan (esperable: A es un caso distinto ya identificado por
separado, D y F no deberían afectar a preguntas ya bien detectadas en idioma y sin señal
de alarma).

## Investigación realizada

1. **Reproducción con el pipeline actual** (ya con los ajustes A/D/F de este ciclo
   aplicados): se ejecutó `RAGPipeline.query()` sobre las dos preguntas reales.
   Retrieval y generación completan sin error en ambos casos.

2. **Hallazgo concreto — fuga de citas inline (contradice D-026):** el prompt de
   sistema (`prompts/system_prompt_family.txt`, sección `[FUENTES]`) instruye
   explícitamente: *"No cites el nombre del documento ni de la sección dentro de la
   respuesta [...] El sistema añade automáticamente el listado de fuentes consultadas
   al final."* Sin embargo, en la reproducción de **eval_06** y **eval_15** el LLM
   generó una lista de fuentes citada inline dentro de la propia respuesta (p. ej.
   *"Manual de IDF para pacientes y familias (páginas 191, 201, 226)"*), duplicada
   por la sección `Fuentes consultadas:` que añade `_build_sources_section()` de
   forma determinista — dos bloques de fuentes con formato distinto en el mismo texto.
   Se comprobó como contraste el caso **eval_09** (deporte y IDP, Context Precision
   > 0.99 en T-02, no está entre los casos con score 0.0): su respuesta reproducida
   **no** presenta esa fuga — solo aparece la sección determinista, tal y como exige
   el prompt.
   - Esto es un incumplimiento intermitente del LLM sobre una instrucción del
     system prompt, no un bug determinista del código del pipeline.
   - Es una causa plausible para `answer_relevancy = 0.0`: `ResponseRelevancy` de
     RAGAS genera preguntas sintéticas a partir del texto de `response` vía LLM y
     compara su embedding con la pregunta real; un bloque de citas duplicado y con
     formato inconsistente al final de la respuesta es un candidato razonable para
     degradar esa generación.

3. **Descartada divergencia de retrieval entre llamadas:** `scripts/run_ragas_eval.py`
   llama a `pipeline.retrieve()` una vez para construir `retrieved_contexts` y
   luego, dentro de `_clean_response()`, a `pipeline.query()` — que internamente
   vuelve a invocar el retriever. Se verificó que `pipeline.retrieve()` devuelve
   exactamente el mismo resultado (mismo contenido, mismo orden) en llamadas
   repetidas sobre las mismas preguntas — descarta que `retrieved_contexts` (lo que
   ve RAGAS) y el contexto realmente usado para generar la respuesta diverjan.

4. **Hallazgo más fuerte tras añadir eval_25 — patrón de respuesta evasiva
   ("noncommittal"), no la fuga de citas.** Se reprodujo también eval_25 y su
   respuesta **no** presenta la fuga de citas inline del punto 2 — descarta esa
   fuga como causa común a los 3 casos. Lo que sí comparten los tres es el *tono*
   de la respuesta: en los tres, el modelo evita dar una respuesta directa y
   remite de forma explícita y repetida a "consulta con tu equipo médico"/"cada
   caso es único"/"depende de muchos factores individuales" antes de aportar
   cualquier información concreta. `ResponseRelevancy` de RAGAS tiene un
   comportamiento documentado para esto: si el LLM juez clasifica la respuesta
   como "noncommittal" (evasiva, no comprometida con una respuesta concreta),
   asigna `0.0` directamente, sin pasar por el cálculo de similitud de
   preguntas generadas. Esto encaja con un rasgo estructural del producto, no
   con un bug: el prompt de sistema (`prompts/system_prompt_family.txt`,
   `[RESTRICCIONES ABSOLUTAS]` + `[CIERRE OBLIGATORIO]`) exige exactamente ese
   tono — nunca confirmar seguridad, remitir siempre a consulta médica — como
   aplicación directa de Falso Negativo Cero (`AGENTS.md`). Es plausible que
   estas 3 preguntas concretas (frecuencia de revisiones, viajar en avión,
   irse de convivencias) inviten a una respuesta especialmente condicionada
   ("depende de tu caso") que el juez de RAGAS penaliza con más severidad que
   en otras preguntas informativas donde la respuesta, aun remitiendo también
   al equipo médico al final, sí aporta contenido concreto antes.

5. **Sin confirmar del todo: por qué `context_precision`/`context_recall` son
   exactamente 0.0 en los tres.** Estas dos métricas no dependen del texto de
   `response` (solo de `retrieved_contexts` y `reference`), así que el patrón de
   respuesta evasiva del punto 4 no las explica directamente. Los 3
   `expected_answer` del dataset para estos casos sí contienen contenido
   específico (no son ellos mismos evasivos), así que la hipótesis de "referencia
   genérica sin contenido verificable" tampoco encaja limpiamente. Queda sin
   diagnosticar con un análisis frase a frase del contexto recuperado frente a la
   referencia para estos 3 casos concretos.

## Decisión

No se aplica ningún ajuste de código para B en este ciclo: la causa de
`answer_relevancy = 0.0` tiene ahora un candidato más sólido (respuesta evasiva
penalizada por el diseño de `ResponseRelevancy`, coherente con la exigencia de tono
del prompt de sistema) pero no está confirmada de forma concluyente frase a frase, y
la causa de `context_precision`/`context_recall = 0.0` sigue sin diagnosticar. Ajustar
el prompt para reducir el tono evasivo entra en tensión directa con Falso Negativo
Cero (principio no negociable, `AGENTS.md`) — cualquier cambio en esa dirección
necesita más que esta investigación de margen para justificarse.

**Estado para el informe final (T-06): abierto.** Confirmado con la re-medición
completa de este ciclo (32/32 casos): eval_06, eval_15 y eval_25 siguen en 0.0 tras
los ajustes de A, D y F — ninguno de los tres los toca, como se esperaba. No aparecen
casos nuevos con el mismo patrón entre los 32. Candidato de causa razonablemente
sólido (tono evasivo penalizado por RAGAS) pero en tensión con un principio de
producto no negociable — se traslada a T-06 para decidir si amerita una tarea
dedicada, con la salvedad explícita de que "arreglarlo" podría significar aceptar el
0.0 como coste del diseño de seguridad, no necesariamente cambiar el prompt.
