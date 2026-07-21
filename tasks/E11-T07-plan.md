# Plan — E-11 T-07 Cierre: informe final en docs/evaluation.md (Bloque 0 — regresión)

## Contexto técnico

Tarea de tipo documentación (mismo patrón que E09-T06), pero con un bloque previo de
ejecución real sin TDD (D-070, mismo patrón script+revisión manual que D-050/D-051). No
hay ciclo rojo→verde: son scripts de instrumentación sin asserts que vuelcan resultados a
fichero para revisión manual de Marcos en Cowork.

**Por qué existe este bloque:** D-067 (T-04, ajuste de tono en
`[TONO — PERFIL FAMILIAR]`) y D-068 (T-05, generalización de la restricción de
información de centro en `[RESTRICCIONES ABSOLUTAS]`) modificaron
`prompts/system_prompt_family.txt` en producción sin re-ejecutar después ni la suite de
tests ni RAGAS. D-070 decide verificarlo antes de escribir el informe final, en vez de
documentar la omisión sin más.

**Qué NO hace esta tarea:** no aplica ningún fix. Si algún paso revela una regresión real,
el script la documenta con el valor exacto (sin suavizar) y la decisión de si bloquea el
cierre de la épica se toma en Cowork, no en Antigravity.

**Fuera de este plan:** la actualización de `docs/evaluation.md` (Bloque 1 del `.feature`,
todos los escenarios de documentación) se hace en Cowork, después de traer los resultados
de este bloque. No la generes en Antigravity.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `tests/eval/results/e11_t04_transcripcion_pre_fix.json` | crear (copia) | Backup del contenido actual de `e11_t04_transcripcion.json` (transcripción **previa** al ajuste de tono, evidencia que sostiene D-067) antes de sobrescribirlo |
| `tests/eval/results/e11_t04_transcripcion.json` | regenerar (script existente) | Se sobrescribe al re-ejecutar `scripts/run_e11_t04_linguistic_review.py` — ahora contiene la transcripción **post-fix** |
| `scripts/run_e11_t07_t05_regression_check.py` | crear | Reproduce las 3 preguntas de `backlog/ideas.md` (10/18 jul, hallazgo #1) contra `RAGPipeline.query()` real, vuelca respuesta completa + fuentes citadas |
| `tests/eval/results/e11_t07_t05_regression_check.json` | generado por el script anterior | Transcripción de las 3 respuestas post-fix, para lectura manual de si aparece la salvedad de "información de un centro concreto" |
| `scripts/run_e11_t07_ragas_regression_check.py` | crear | Calcula las 4 métricas RAGAS (Faithfulness, Answer Relevancy, Context Precision, Context Recall) solo para `eval_03`, `eval_04`, `eval_08`, `eval_13` contra el pipeline actual |
| `tests/eval/results/e11_t07_ragas_regression_check.json` | generado por el script anterior | Scores nuevos de los 4 casos, sin tocar `e09_t02_ragas_full_scores.json` (el registro oficial de T-02 no se sobrescribe — mismo criterio que D-058/D-069 de no sustituir el número oficial) |

**No se modifica** `tests/eval/results/e09_t02_ragas_full_scores.json` en ningún paso —
es el registro oficial de T-02 que T-06 ya usa para las bandas de severidad; alterarlo
aquí invalidaría ese trabajo ya cerrado.

## Orden de ejecución (sin TDD — scripts de instrumentación, D-050)

1. **Suite pytest completa.**
   ```
   PYTHONPATH=. pytest tests/ -v
   ```
   Compara el resultado contra el último conocido (147 passed, 14 skipped, 1 xfailed,
   `tests/eval/results/e11_t02_cierre.md` §4). Si el número de passed/skipped/xfailed
   cambia, documenta exactamente qué test y por qué antes de seguir — no ignores un
   cambio aunque parezca menor.

2. **Backup de la transcripción pre-fix de T-04.** Copia
   `tests/eval/results/e11_t04_transcripcion.json` a
   `tests/eval/results/e11_t04_transcripcion_pre_fix.json` (el fichero actual es la
   evidencia que sostiene D-067 — no se pierde, solo se renombra la copia).

3. **Re-ejecuta T-04 tal cual.**
   ```
   python scripts/run_e11_t04_linguistic_review.py
   ```
   No modifiques el script — usa las mismas 7 preguntas (`ling_01`–`ling_07`). Sobrescribe
   `e11_t04_transcripcion.json` con la transcripción post-fix. Lee las respuestas de
   `ling_02`, `ling_04` y `ling_07` (los tres casos con hallazgo en
   `tests/eval/results/e11_t04_cierre.md` §2) y compara contra la versión pre-fix: ¿ahora
   aparece la glosa breve para fármacos/acrónimos/síndromes? ¿Se mantiene el cierre
   obligatorio de derivación médica en las 7 respuestas? No hace falta volver a escribir
   el análisis completo de `e11_t04_cierre.md` — una nota corta por caso basta, el informe
   final se redacta en Cowork.

4. **Crea `scripts/run_e11_t07_t05_regression_check.py`** siguiendo el mismo patrón que
   `scripts/run_e11_t04_linguistic_review.py` (import de `RAGPipeline`, `sys.path.insert`
   para la raíz del repo, sin mocks). Preguntas exactas (`backlog/ideas.md`, "Hallazgos
   del RAG" punto 1):
   - `"¿A quién llamo si es fin de semana?"` (10 jul, smoke test E-05 T-07 CU-05)
   - `"¿Cómo puedo cuidar el día a día de mi familiar?"` (18 jul)
   - `"¿A partir de cuánta fiebre tengo que acudir al médico?"` (18 jul)

   Vuelca a `tests/eval/results/e11_t07_t05_regression_check.json`: pregunta, respuesta
   completa, y si `guia_antibiotics_esp_0.pdf` aparece entre las fuentes citadas. Lee las
   3 respuestas: para las dos que antes citaban el documento sin salvedad
   (`e11_t05_cierre.md` §3 — "a quién llamo" y "cuánta fiebre"), confirma si ahora aparece
   la salvedad de información específica de un centro. Para la tercera ("día a día") no se
   espera cambio — la cita ya era correcta antes del fix.

5. **Crea `scripts/run_e11_t07_ragas_regression_check.py`** reutilizando el patrón de
   `scripts/run_ragas_eval.py` (stub de `ChatVertexAI`, mismo `evaluator_llm`, mismas
   métricas `Faithfulness`/`ResponseRelevancy`/`ContextPrecision`/`ContextRecall`), pero
   filtrado a `["eval_03", "eval_04", "eval_08", "eval_13"]` únicamente — no proceses el
   resto del dataset. Escribe a `tests/eval/results/e11_t07_ragas_regression_check.json`
   (fichero nuevo, no toques `e09_t02_ragas_full_scores.json`). Compara contra los valores
   oficiales de T-02 ya registrados:

   | Caso | Faithfulness (T-02) | Answer Relevancy (T-02) | Context Precision (T-02) | Context Recall (T-02) |
   |---|---|---|---|---|
   | eval_03 | 0.865 | 0.745 | 1.000 | 1.000 |
   | eval_04 | 0.959 | 0.857 | 0.556 | 1.000 |
   | eval_08 | 0.848 | 0.836 | 0.500 | 1.000 |
   | eval_13 | 0.850 | 0.892 | 0.143 | 0.500 |

   Considera "caída significativa" cualquier delta negativo mayor de ~0.10 en una métrica
   para un mismo caso (umbral orientativo, no exacto — el ruido normal del juez LLM ya
   documentado en D-058/D-069/T-05 está en ese rango; una caída mayor merece lectura
   detallada antes de descartarla como ruido).

6. **Parada explícita.** No apliques ningún fix ni toques `prompts/system_prompt_family.txt`,
   `rag/retriever.py` ni `config/alarm_triggers.json` en esta tarea. Vuelve a Cowork con
   los 3 ficheros de resultados (`e11_t04_transcripcion.json` regenerado,
   `e11_t07_t05_regression_check.json`, `e11_t07_ragas_regression_check.json`) y el
   resultado de la suite pytest, listos para que Marcos y el agente decidan si hay alguna
   regresión que documentar antes de escribir `docs/evaluation.md`.

## Restricciones a respetar

- Falso Negativo Cero (AGENTS.md): si alguna de las respuestas re-generadas (T-04 o T-05)
  compromete el cierre de seguridad o inventa una cifra/protocolo, es un hallazgo aparte a
  documentar explícitamente, no algo a pasar por alto aunque no sea el foco de esta tarea.
- No modificar código de producción ni prompts en este bloque — es verificación pura.
- No repetir llamadas innecesarias al evaluador LLM más allá de las estrictamente
  necesarias para los 4 casos del paso 5 (coste de cuota de Gemini, D-027).
- No relanzar los 32 casos completos de RAGAS — el alcance acotado es una decisión
  explícita de D-070, no una limitación técnica.

## Lo que queda fuera de esta tarea (Ronda 1)

- Aplicar cualquier fix si el Bloque 0 revela una regresión — se decide en Cowork si entra
  en el alcance de T-07 o se traslada a `backlog/ideas.md`, mismo criterio que T-05/T-06.
- Actualizar `docs/evaluation.md` (Bloque 1 completo del `.feature`) — se hace en Cowork
  tras traer estos resultados.
- Recalcular RAGAS para los 28 casos restantes del dataset — el desglose de bandas de T-06
  y el resto de §7 siguen usando `e09_t02_ragas_full_scores.json` tal cual (D-069).

---

## Ronda 2 (D-071) — estabilidad de juez de Context Precision + causa raíz de citación duplicada

**Por qué existe esta ronda:** la Ronda 1 reveló dos cosas que Marcos quiere verificar más
a fondo antes de cerrar la épica en vez de cerrarlas por analogía con precedentes: (1) dos
caídas de Context Precision más allá del umbral (`eval_08` Δ−0.300, `eval_13` Δ−0.143) en
`tests/eval/results/e11_t07_ragas_regression_check.json`; (2) un hallazgo nuevo no buscado
— el modelo genera intermitentemente su propio bloque "Fuentes consultadas:" en texto
plano, duplicando el bloque determinista real e incumpliendo `[FUENTES]` (D-026). Detectado
en 11 de 17 transcripciones completas ya revisadas
(`tests/eval/results/e11_t04_transcripcion_pre_fix.json`,
`tests/eval/results/e11_t04_transcripcion.json`,
`tests/eval/results/e11_t07_t05_regression_check.json`). Confirmado que no lo causó
T-04/T-05 (ya aparecía pre-fix).

**Qué NO hace esta ronda:** sigue sin aplicar ningún fix a producción. Si la variante de
instrucción reforzada (paso 2) reduce claramente la duplicación, se propone la redacción
concreta a Marcos en Cowork — no se escribe a `prompts/system_prompt_family.txt` desde
Antigravity.

### Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `scripts/run_e11_t07_context_precision_stability.py` | crear | Una reproducción real (retrieval + generación) de `eval_08` y `eval_13` cada uno, luego invoca `ContextPrecision.single_turn_score()` dos veces sobre el mismo `SingleTurnSample` (sin repetir retrieval/generación) |
| `tests/eval/results/e11_t07_context_precision_stability.json` | generado por el script anterior | Los dos scores por caso + el contexto/respuesta usados, para que Marcos y el agente decidan en Cowork si la varianza es del juez o de la generación |
| `scripts/run_e11_t07_citation_duplication_investigation.py` | crear | Paso 1: repite `ling_07` 3 veces contra el generador de producción. Paso 2: genera las mismas 10 preguntas del Bloque 0 (7 `ling_XX` + 3 `t05_regr_XX`) con un `RAGGenerator` alternativo (`[FUENTES]` reforzado, mutado solo en memoria, mismo patrón que `scripts/run_e11_t03_grounding_investigation.py::_build_lax_generator`) |
| `tests/eval/results/e11_t07_citation_duplication_investigation.json` | generado por el script anterior | Resultado de los dos pasos: tasa de duplicación de `ling_07` repetido (0-3/3), y tasa de duplicación de la variante reforzada sobre las 10 preguntas, con las respuestas completas |

### Orden de ejecución (sin TDD — scripts de instrumentación, D-050)

**A. Estabilidad de Context Precision (`eval_08`/`eval_13`)**

1. Para cada caso, una sola reproducción real: `pipeline.retrieve(question)` +
   `_clean_response()` (mismo patrón que `scripts/run_ragas_eval.py`), construir un único
   `SingleTurnSample` (mismos `retrieved_contexts`/`response`/`reference` que se usarían
   para puntuar una sola vez).
2. Instanciar `ContextPrecision(llm=evaluator_llm)` e invocar `single_turn_score()` dos
   veces sobre ese MISMO `SingleTurnSample` — no repetir `retrieve()` ni `query()` entre
   las dos invocaciones (mismo patrón exacto que el paso 6 de `run_e11_t06_eval06_investigation.py`
   para Faithfulness).
3. Volcar a `tests/eval/results/e11_t07_context_precision_stability.json`: pregunta,
   contexto recuperado, respuesta, los dos scores del juez, y un campo
   `interpretacion: null` para rellenar en Cowork — el script no concluye, solo aporta
   evidencia:
   - Si los dos scores del juez coinciden entre sí pero no con el valor de T-02 → la
     varianza está en la generación (la respuesta de hoy es distinta a la de T-02), no en
     el juez.
   - Si los dos scores del juez difieren entre sí → la varianza está en el juez, mismo
     patrón que D-069.

**B. Citación duplicada — consistencia por pregunta**

4. Repetir `ling_07` (`"¿Cómo se clasifican los distintos tipos de inmunodeficiencias
   primarias?"`) 3 veces contra `RAGPipeline.query()` real de producción, sin cambiar nada.
   Contar cuántas de las 3 respuestas contienen un bloque "Fuentes consultadas:" adicional
   en texto plano antes del bloque determinista (mismo criterio de detección que el
   análisis de Cowork: `response.count("Fuentes consultadas") >= 2`).

**C. Citación duplicada — variante de instrucción reforzada**

5. Construye un `RAGGenerator` alternativo (mismo patrón que
   `scripts/run_e11_t03_grounding_investigation.py::_build_lax_generator`, mutación en
   memoria de `_system_prompt`, nunca escrita a fichero) que **reemplaza** el párrafo
   `[FUENTES]` actual por una versión más explícita, con contraejemplo concreto:

   ```
   [FUENTES]
   Basa todas tus respuestas exclusivamente en los documentos proporcionados como contexto.
   No generes NUNCA un encabezado ni una lista con nombres de fichero dentro de tu
   respuesta — ni "Fuentes consultadas:", ni "Fuentes:", ni ningún equivalente. El sistema
   añade automáticamente ese listado después de tu respuesta; si tú también lo generas,
   aparecerá duplicado. Incorrecto (NO hagas esto):
   "...consulta con tu equipo médico.\n\nFuentes consultadas:\n- documento.pdf"
   Correcto: termina tu respuesta en el párrafo de cierre, sin ningún bloque de fuentes
   propio.
   Si la información no está en el contexto, indícalo explícitamente.
   ```

6. Ejecuta esta variante sobre las mismas 10 preguntas ya usadas en el Bloque 0
   (`ling_01`–`ling_07`, `t05_regr_01`–`t05_regr_03`), reutilizando el texto de las
   preguntas ya documentado en `tasks/E11-T07-plan.md` (Ronda 1, paso 4) y
   `scripts/run_e11_t04_linguistic_review.py`. Cuenta la tasa de duplicación de esta
   variante.

7. Vuelca a `tests/eval/results/e11_t07_citation_duplication_investigation.json`:
   resultado del paso 4 (`ling_07` × 3, cuántas duplican), resultado de los pasos 5-6
   (tasa de duplicación de la variante reforzada sobre las 10 preguntas, con las 10
   respuestas completas), y comparación explícita contra la tasa ya observada en
   producción (11/17, Ronda 1).

8. **Parada explícita.** No apliques la instrucción reforzada a
   `prompts/system_prompt_family.txt`. Vuelve a Cowork con los dos ficheros de resultados
   de esta ronda para que Marcos decida: si la variante reduce claramente la duplicación,
   se redacta el ajuste definitivo en Cowork (Bloque 2, mismo patrón que D-067); si no
   reduce la tasa de forma clara, se documenta como limitación conocida sin fix aplicable
   por prompt.

### Restricciones a respetar (Ronda 2)

- No modificar `prompts/system_prompt_family.txt` en esta ronda — la variante reforzada
  vive solo en memoria, igual que T-03.
- No repetir llamadas innecesarias al evaluador LLM — el paso A son 2 invocaciones del
  juez por caso (4 total), no más.
- Falso Negativo Cero: si alguna de las 13 respuestas generadas en esta ronda (3 de
  `ling_07` + 10 de la variante reforzada) compromete el cierre de seguridad, documentarlo
  como hallazgo aparte inmediatamente, aunque no sea el foco de esta ronda.

### Lo que queda fuera de esta ronda

- Aplicar la instrucción reforzada a producción — se decide y redacta en Cowork tras leer
  el resultado.
- Investigar la causa raíz última de por qué el LLM decide citar inline en unos casos y no
  en otros (más allá de la consistencia por pregunta de `ling_07` y el contraste con la
  variante reforzada) — si ninguno de los dos experimentos es concluyente, se documenta
  como comportamiento no determinista del LLM sin causa raíz confirmada, mismo criterio de
  honestidad que D-069 aplicó a `eval_06`, y se decide en Cowork si basta para cerrar E-11
  o si necesita una tercera ronda.
- Recalcular RAGAS de `eval_08`/`eval_13` sobre el dataset oficial — el registro de T-02
  (`e09_t02_ragas_full_scores.json`) no se toca en esta ronda tampoco.
