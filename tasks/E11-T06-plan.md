# Plan — E-11 T-06 Hallucination Rate: desglose por bandas de severidad

## Contexto técnico

Tarea de tipo reporting/documentación, sin TDD (mismo patrón que E09-T04/T06 y
`scripts/run_e11_t05_eval15_investigation.py`, D-050). No hay ciclo rojo→verde: es un
script de investigación sin asserts, que vuelca resultados a fichero para revisión manual
de Marcos en Cowork.

**Qué ya está decidido (no hay que redecidirlo aquí):**
- Bandas de severidad de Faithfulness (D-058, `epic-start` E-11): Grave (< 0.5), Moderada
  (0.5–0.85), Leve (0.85–<1.0, límite incluido — D-069), Sin desviación (1.0).
- Fuente de datos: `tests/eval/results/e09_t02_ragas_full_scores.json` (32 casos,
  post-T-02, sin re-medición desde entonces). El desglose se calcula sobre estos scores
  ya existentes — no se vuelve a llamar a RAGAS para los otros 31 casos.
- El caso Grave es `eval_06` (Faithfulness 0.385), no `eval_15` (D-069, ya cerrado en
  banda Leve por D-068).

**Lo que esta tarea sí necesita investigar:** por qué la Faithfulness de `eval_06`
("¿Con qué frecuencia hay que hacer revisiones con el inmunólogo?") cayó dos veces sin
explicación registrada:

| Momento | Faithfulness | Fichero |
|---|---|---|
| Pre-E-11 (E-09 T-05) | 0.722 | `tests/eval/results/e09_t02_ragas_full_scores_pre_e11_t02.json` |
| Tras T-01 (KB ampliada) | 0.615 | `tests/eval/results/e09_t02_ragas_full_scores_e11_t02_baseline.json` |
| Tras T-02 (peso adaptativo BM25) | 0.385 | `tests/eval/results/e09_t02_ragas_full_scores.json` |

**Hipótesis ya registrada (hallazgo B, `tests/eval/results/e09_t05_plan_b_investigacion.md`):**
en la reproducción de `eval_06` (y `eval_15`) el LLM generaba una lista de fuentes citada
inline dentro de la propia respuesta (nombre de documento + páginas), duplicando la
sección `Fuentes consultadas:` que añade `_build_sources_section()` — contra lo que indica
`prompts/system_prompt_family.txt` (sección `[FUENTES]`). Esa investigación se hizo con
Faithfulness en 0.60 (antes de T-01/T-02); no cubre las dos caídas posteriores.

**Limitación conocida:** no es posible re-ejecutar el pipeline contra el estado de la KB
o los pesos de BM25 anteriores a T-01/T-02 (la colección de ChromaDB ya está reindexada
sobre el corpus ampliado, y los pesos antiguos ya no están activos) — no hay forma de
reproducir exactamente los tres puntos de la tabla. La investigación se hace sobre el
**estado actual** (post-T-01/T-02) y contrasta contra la hipótesis ya registrada y contra
lo que se puede inferir del texto real generado ahora; no reconstruye retroactivamente por
qué cada paso concreto empeoró el número. Esto se documenta como limitación explícita en
el resultado, no se presenta como causa raíz confirmada si no lo es.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `scripts/run_e11_t06_eval06_investigation.py` | crear | Reproduce `eval_06` contra el pipeline real (retrieval + generación), captura respuesta y contexto recuperado, contrasta con la hipótesis de hallazgo B (cita inline duplicada) y comprueba estabilidad del juez de Faithfulness (dos invocaciones sobre el mismo `SingleTurnSample`, mismo patrón que `run_e11_t05_eval15_investigation.py` para Context Precision/Recall) |
| `tests/eval/results/e11_t06_eval06_investigacion.json` | generado por el script | Volcado completo: pregunta, respuesta real, chunks recuperados, presencia/ausencia de cita inline duplicada, tono de la respuesta, estabilidad del juez |

**Fuera de este plan (se hace en Cowork tras traer el resultado):** actualización de
`docs/evaluation.md` con el desglose de bandas + la explicación de `eval_06`, y
`tests/eval/results/e11_t06_cierre.md`. No los generes en Antigravity — vuelve a Cowork
con el JSON de investigación listo.

## Orden de ejecución (sin TDD — script de investigación, D-050)

Sigue este orden. Ningún paso lleva asserts; cada uno añade una clave al JSON de salida.

1. **Cargar el caso `eval_06`** de `tests/eval/dataset_partial.json` (mismo helper
   `_load_case` / `load_dataset` + `validate_dataset` que `run_e11_t05_eval15_investigation.py`).

2. **Retrieval real de producción** — `pipeline.retrieve(case.question)` sobre el
   `RAGPipeline` actual (KB ampliada + peso adaptativo, ya activos). Volcar chunks
   (`source`, `filename`, `score`, `content`) y los pesos BM25/vector realmente aplicados
   (`pipeline._retriever.weights`), igual que en el script de `eval_15`.

3. **Respuesta real generada** — usar el mismo patrón que `scripts/run_ragas_eval.py`
   (`_clean_response`: `pipeline.query()` menos el bloque de fuentes determinista) para
   obtener el texto de la respuesta sin reimplementar la generación.

4. **Contraste con la hipótesis de hallazgo B** — comprobar en el texto de la respuesta
   real si aparece una cita inline de documento/páginas (patrón ya visto: nombre de
   fichero o "páginas NNN" dentro del cuerpo de la respuesta, no solo en la sección de
   fuentes automática). Documentar presente/ausente con el fragmento literal si aparece.

5. **Tono de la respuesta** — nota manual (no automatizable con keywords fiables) sobre si
   la respuesta es evasiva/condicionada ("depende de tu caso", remite solo a consulta
   médica sin dar ninguna cifra orientativa) — mismo patrón de tono que motivó hallazgo B
   originalmente. Dejar el texto completo de la respuesta en el JSON para que Marcos lo
   lea directamente, no solo la conclusión del script.

6. **Estabilidad del juez de Faithfulness** — instanciar `Faithfulness(llm=evaluator_llm)`
   (mismo `evaluator_llm`/`_EVALUATOR_MAX_TOKENS` que `run_ragas_eval.py`) e invocar
   `single_turn_score` dos veces sobre el mismo `SingleTurnSample` (misma respuesta, mismo
   contexto recuperado, sin volver a llamar a `retrieve()` ni `query()`). Si los dos scores
   difieren de forma relevante, es evidencia de ruido del juez, no de un problema real de
   grounding.

7. **Volcado completo** a `tests/eval/results/e11_t06_eval06_investigacion.json`:
   pregunta, respuesta real completa, chunks recuperados, pesos aplicados, contraste de
   hallazgo B (presente/ausente + fragmento), nota de tono, estabilidad del juez (los dos
   scores), y un campo explícito `causa_raiz_confirmada: null` para que se rellene en
   Cowork tras la lectura manual — el script no concluye la causa, solo la evidencia.

8. **Parada explícita.** El script no aplica ningún fix ni toca `prompts/` ni
   `rag/retriever.py`. Vuelta a Cowork con el JSON listo para que Marcos y el agente
   decidan si la evidencia explica las dos caídas, y para redactar el desglose final de
   T-06 (`docs/evaluation.md`) y el cierre de la tarea.

## Restricciones a respetar

- Falso Negativo Cero (AGENTS.md): si la respuesta real de `eval_06` confirma o niega
  seguridad de forma inapropiada, es un hallazgo aparte a documentar, no algo a ignorar
  aunque no sea el foco de esta investigación.
- No modificar `rag/retriever.py`, `prompts/system_prompt_family.txt` ni
  `config/alarm_triggers.json` en esta tarea — es investigación pura (D-065/D-069), igual
  que T-05 con `eval_15`.
- No repetir llamadas innecesarias al evaluador LLM más allá de las dos del paso 6
  (coste de API).

## Lo que queda fuera de esta tarea

- Reconstruir el estado exacto de la KB/pesos anteriores a T-01/T-02 — no es posible sin
  revertir la reindexación de ChromaDB; se documenta como limitación, no se fuerza.
- Aplicar un fix sobre `eval_06` (cambio de prompt, ajuste de retrieval) — si la
  investigación revela una causa accionable, se decide en Cowork si entra en el alcance de
  T-06 o se traslada a backlog, igual que se hizo con Context Precision/Recall de
  `eval_15` en D-068.
- Recalcular Faithfulness de los otros 31 casos — el desglose de bandas usa los scores ya
  existentes de `e09_t02_ragas_full_scores.json` tal cual (D-069).
