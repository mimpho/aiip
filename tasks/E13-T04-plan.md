# Plan — E-13 T-04 Remedición RAGAS + cierre

> Tarea de configuración, sin TDD (D-050/D-051, mismo patrón que E-07 T-02/E-09 T-02/
> E-11 T-02). Este plan existe como excepción a la regla habitual de "Paso 4 no aplica a
> tareas de configuración" (D-080, precedente E-13 T-03) — Antigravity arranca esta tarea
> en una conversación nueva, sin memoria de las decisiones tomadas en Cowork sobre nombres
> de fichero, alcance de D-084 o el `.feature` corregido. Este fichero traduce el
> `.feature` y las decisiones relevantes en una secuencia de comandos ejecutable sin tener
> que reconstruir contexto.

## Contexto técnico

- Rama activa: `task/E13-T04-ragas-remeasure-closure` (ya creada sobre
  `epic/E13-medlineplus` actualizada, incluye T-01/T-02/T-03 mergeadas — 40 fichas de
  MedlinePlus Genetics ya en `data/raw/medlineplus_genetics/`).
- `.feature` de referencia: `tests/eval/e13_t04_ragas_remedicion_cierre.feature` — checklist
  script-sin-TDD, corregido en Cowork (nombres de fichero reales, 39→40 fichas, escenario
  nuevo de D-084).
- Script (sin cambios, reutilizado tal cual desde E-07/E-09/E-11): `scripts/run_ragas_eval.py`.
  Escribe siempre en `tests/eval/results/e09_t02_ragas_full_scores.json`
  (`_RESULTS_PATH`, hardcoded) — el nombre del fichero no cambia entre épicas, solo se
  respalda/snapshotea con sufijos distintos por convención (ver paso 1).
- Baseline pre-E-13 (post-cierre de E-11, ya en el fichero vigente antes de tocar nada):
  Faithfulness 84.6%, Answer Relevancy 79.9%, Context Precision 63.2%, Context Recall
  86.5% (32 casos, `informativo` + `otro_idioma`) — coincide con `docs/evaluation.md`
  §5.4/§7.
- Dataset: `tests/eval/dataset_partial.json`, mismo subconjunto de 32 casos que E-09/E-11
  (`category in ("informativo", "otro_idioma")`), sin cambios en esta tarea.
- El caso XIAP/IPEX original (D-063) **no está en el dataset RAGAS** — se verifica aparte,
  con una consulta directa al pipeline (mismo patrón que D-073/D-077), no como parte de la
  remedición de las 4 métricas.
- Casos de contexto pobre a revisar en la verificación dirigida: `eval_06` (Context
  Precision cuestionado, banda Grave, D-069 — "¿Con qué frecuencia hay que hacer
  revisiones con el inmunólogo?") y `eval_15` (Context Precision 0.0 histórico, hueco de
  KB documentado en `backlog/ideas.md`, D-068 — "¿Podemos viajar en avión llevando la
  medicación de inmunoglobulinas?").
- D-084 (limitación de listado/BM25, ya cerrada — no requiere código): solo hace falta
  documentarla en `docs/evaluation.md` como modo de fallo conocido, sin volver a investigar
  ni tocar `RAG_TOP_K`/`rag/retriever.py`.

## Secuencia de comandos (orden exacto)

1. **Respaldar el resultado vigente antes de resetear**:
   ```bash
   cp tests/eval/results/e09_t02_ragas_full_scores.json \
      tests/eval/results/e09_t02_ragas_full_scores_pre_e13_t04.json
   ```
   Confirmar que el backup tiene 32 casos y `aggregate` coincide con los valores de
   "Baseline pre-E-13" de arriba antes de continuar.

2. **Resetear el fichero vigente** (necesario porque la ejecución es incremental/checkpointed
   — sin resetear, el script vería los 32 casos como ya evaluados y no llamaría a Gemini):
   ```bash
   echo '{"cases": []}' > tests/eval/results/e09_t02_ragas_full_scores.json
   ```

3. **Ejecutar la remedición** (llamadas reales a Gemini + bge-m3, no determinista, puede
   tardar y reintentar solo):
   ```bash
   PYTHONPATH=. python scripts/run_ragas_eval.py
   ```
   Si se corta a mitad (p. ej. 429 de cuota), relanzar el mismo comando — el checkpointing
   retoma donde quedó, sin repetir casos ya escritos.

4. **Snapshot de cierre** una vez completados los 32 casos:
   ```bash
   cp tests/eval/results/e09_t02_ragas_full_scores.json \
      tests/eval/results/e09_t02_ragas_full_scores_e13_t04_baseline.json
   ```

5. **Verificación dirigida XIAP/IPEX** (fuera del dataset RAGAS, consulta directa al
   pipeline real, mismo patrón que D-073/D-077):
   ```python
   from rag.config import load_rag_config
   from rag.pipeline import RAGPipeline

   pipeline = RAGPipeline(load_rag_config())
   for q in ["xiap", "ipex"]:
       print("---", q, "---")
       print(pipeline.query(q))
   ```
   Confirmar que ambas respuestas siguen atribuyendo la relación gen→síndrome al chunk
   indexado (no a conocimiento general del LLM) y que "xiap" no reproduce el bug de D-078.

6. **Verificación dirigida eval_06 / eval_15**: extraer del fichero final (paso 4) los
   scores de `eval_06` y `eval_15` y compararlos contra el histórico (0.38 y 0.0
   respectivamente en `docs/evaluation.md` §5.3/§5.4). Documentar si mejoran, se mantienen
   o no cambian, con el valor exacto — sin suavizar si siguen igual de mal.

7. **Redactar el informe de cierre** en `tests/eval/results/e13_t04_cierre.md`, mismo
   formato que `tests/eval/results/e11_t02_cierre.md` (tabla de campos, tabla de métricas
   con delta explícito de las 4, hallazgos de verificación dirigida, confirmación final).
   Incluir explícitamente el delta contra el baseline pre-E-13 (paso 1), sin omitir ni
   suavizar ninguna métrica que empeore o se quede por debajo de objetivo (`AGENTS.md`,
   principio de transparencia ya aplicado en D-058/D-072).

8. **Actualizar `docs/kb-sources.md`**: fila de MedlinePlus Genetics, estado
   `Propuesta` → `Validada`, referenciando las 40 fichas nuevas (D-076) ya indexadas y
   remedidas.

9. **Actualizar `docs/evaluation.md`**:
   - Nueva subsección `5.5` (o la que corresponda tras `5.4`) con la tabla de 4 métricas
     post-E-13 vs. post-E-11, siguiendo el mismo estilo que §5.4.
   - Añadir columna/fila "post-E-13" a la tabla de §7 (Métricas de éxito consolidadas),
     igual que ya existe la columna "post-E-11, T-02 final".
   - Documentar D-084 como modo de fallo conocido (preguntas de listado amplio en
     español), con la salvedad de que no afecta al caso de uso principal — no se cuenta
     como "por debajo de objetivo" en la tabla de métricas porque no hay caso de listado en
     el dataset (D-084 ya lo deja anotado así), es una limitación aparte, no una métrica.
   - No tocar `prompts/system_prompt_family.txt` — ninguna tarea de E-13 lo modifica
     (último escenario de código del `.feature`, ya sin acción pendiente).

10. ~~**Confirmación de cierre** (Marcos)~~ — **en pausa de nuevo** (22 jul 2026): tras
    revisar el resultado del paso 11, Marcos pidió investigar también la causa de la caída
    agregada de Context Precision (−3.7pp) antes de confirmar — ver paso 13.

11. **Investigación dirigida de `eval_25`** (añadido 22 jul 2026, decisión de Marcos —
    mismo patrón que D-069/eval_06 y D-072/eval_08-eval_13):

    **Contexto clave ya identificado en Cowork:** Context Precision, Context Recall y
    Answer Relevancy de `eval_25` son **idénticos** pre/post E-13 (0.0, 1.0, 0.0 sin
    cambio) — solo Faithfulness cambia (0.857→0.32). Como el retrieval no cambió, la
    hipótesis de partida es que la caída es variación de generación/juez, no un efecto
    real de las 40 fichas nuevas — pero hay que confirmarlo, no darlo por hecho.

    ```python
    from rag.config import load_rag_config
    from rag.pipeline import RAGPipeline

    pipeline = RAGPipeline(load_rag_config())
    question = "¿Puede mi hijo marcharse de convivencias varios días?"
    raw_results = pipeline.retrieve(question)
    print(pipeline.query(question))
    print([doc.metadata.get("source") for doc, _ in raw_results])
    ```

    a. Leer la respuesta completa generada y compararla contra `expected_answer` de
       `eval_25` en `tests/eval/dataset_partial.json` y contra los chunks recuperados —
       ¿la respuesta afirma algo no soportado por el contexto? ¿o es matiz/parafraseo
       (mismo patrón que 29/30 de los casos "alucinados" según D-058)?
    b. **Estabilidad del juez** (mismo patrón que D-069/D-072): invocar
       `Faithfulness.single_turn_score()` dos veces sobre el mismo `SingleTurnSample`
       (respuesta/contexto ya fijos del paso anterior) para ver si el score es estable o
       varía entre invocaciones — si varía, es ruido del evaluador LLM, no del contenido.
    c. Documentar la conclusión en una sección nueva de
       `tests/eval/results/e13_t04_cierre.md` y, si aplica, marcar el caso como
       "cuestionado" en `docs/evaluation.md` §5.3/§5.5 (mismo criterio que D-069/D-072),
       o como regresión real si el contenido confirma un problema genuino.
    d. **No reabrir el alcance de retrieval/BM25** (D-084 sigue fuera de alcance) — esto
       es investigación puntual de un caso de generación/juez, no motivo para tocar
       `rag/retriever.py` ni `RAG_TOP_K`. Excepción: si aparece algo que comprometa el
       principio de Falso Negativo Cero, volver a Cowork antes de tocar producción.

    **Completado (22 jul 2026, `scripts/run_e13_t04_eval25_investigation.py`,
    `tests/eval/results/e13_t04_eval25_investigacion.json`):** confirmado ruido del juez
    (0.52/0.32 sobre el mismo `SingleTurnSample`, sin cambio en las otras 3 métricas,
    contenido bien fundamentado). `eval_25` marcado como cuestionado (D-085), mismo
    criterio que `eval_06`. Detalle completo en sección 3ter de
    `tests/eval/results/e13_t04_cierre.md`.

12. ~~**Confirmación de cierre** (Marcos)~~ — **reactivado**: paso 13 completado, ver paso 14.

13. **Investigación de la causa de la caída de Context Precision** (añadido 22 jul 2026,
    decisión de Marcos, D-086):

    **Ya resuelto en Cowork, sin necesidad de pipeline (D-086):** de los 32 casos, 26 no
    cambian, 1 mejora y solo 5 empeoran — la caída agregada está concentrada, no dispersa
    (refuta dilución generalizada del corpus). `eval_08` (0.5→0.2) reproduce exactamente su
    patrón histórico bimodal ya cerrado como ruido del juez en D-072 (T-02: 0.5, Ronda 1:
    0.2) — no requiere nueva investigación. `eval_20` (delta −0.025) es demasiado pequeño
    para priorizar (un orden de magnitud menor que el ruido ya observado).

    **Pendiente con pipeline real (Antigravity) — los 3 casos sin explicar:**

    ```python
    from rag.config import load_rag_config
    from rag.pipeline import RAGPipeline

    pipeline = RAGPipeline(load_rag_config())
    preguntas = {
        "eval_22": "¿Tendríamos que informar al inmunólogo de referencia si salimos del país de vacaciones?",
        "eval_10": "¿Es seguro que mi hijo vaya al colegio con una inmunodeficiencia primaria?",
        "eval_63": "What is a primary immunodeficiency?",
    }
    for case_id, question in preguntas.items():
        raw_results = pipeline.retrieve(question)
        print(case_id, [doc.metadata.get("source") for doc, _ in raw_results])
    ```

    a. **Comprobación de dilución:** para cada uno de los 3 casos, ¿aparece algún chunk de
       `medlineplus_genetics` en el contexto recuperado post-E-13 que no estuviera antes?
       Si sí, ¿desplaza a un chunk que antes rankeaba mejor y era más relevante para la
       pregunta (revisión manual del contenido, no solo el nombre de la fuente)? Nota:
       `eval_63` es el único caso en inglés (`otro_idioma`) — es el candidato más plausible
       a dilución real, porque las 40 fichas nuevas SÍ comparten idioma con esta pregunta
       (a diferencia del resto del dataset, mayoritariamente en español) y podrían competir
       de verdad por el ranking, no solo estar presentes sin afectar (D-084).
    b. **Estabilidad del juez** (mismo patrón D-069/D-072/D-085): invocar
       `ContextPrecision.single_turn_score()` dos veces sobre el mismo `SingleTurnSample`
       (contexto ya fijado en el paso anterior) para cada uno de los 3 casos.
    c. Documentar la conclusión de cada caso (dilución real vs. ruido del juez vs. mezcla)
       en una sección nueva de `tests/eval/results/e13_t04_cierre.md`, y actualizar
       `docs/evaluation.md` §5.5 con la lectura final de la caída de Context Precision —
       ya no como "sin causa raíz confirmada" sino con el desglose real.
    d. **No reabrir el alcance de retrieval/BM25** salvo que la evidencia de dilución sea
       clara y consistente en los 3 casos — en ese caso, documentar como hallazgo abierto
       para una épica futura (no tocar `rag/retriever.py` dentro de T-04), mismo criterio
       que D-084.

    **Completado (22 jul 2026, `scripts/run_e13_t04_context_precision_investigation.py`,
    `tests/eval/results/e13_t04_context_precision_investigacion.json`):** `eval_22` y
    `eval_10` no recuperan ningún chunk de `medlineplus_genetics` (la ampliación de KB no
    puede ser la causa) y muestran inestabilidad directa del juez sobre el mismo
    `SingleTurnSample` (0.500/0.917 y 0.700/1.000) — ruido del juez confirmado con
    evidencia limpia. `eval_63` sí recupera un chunk nuevo, pero en la última posición del
    ranking; el juez es estable en esta sesión (0.804) pero reproduce el valor histórico
    pre-E-13, no el post-E-13 oficial (0.650) — indicio hacia ruido de sesión, sin la misma
    contundencia que los otros dos. No se reabre el alcance de retrieval/BM25: no hay
    evidencia clara y consistente de dilución en los 3 casos. Detalle completo en sección
    3quater de `tests/eval/results/e13_t04_cierre.md`; `docs/evaluation.md` §5.5/§7
    actualizados con la lectura final.

14. ~~**Confirmación de cierre** (Marcos)~~ — **confirmado (22 jul 2026):** T-04 cerrada
    con el resultado completo (ganancias reales en Context Recall/Answer Relevancy/
    Hallucination Rate binario; las dos regresiones, Context Precision y Faithfulness,
    explicadas mayoritariamente como ruido del evaluador, no como coste real de las 40
    fichas nuevas; D-084 documentado sin plan de arreglo). E-13 lista para `epic-close`.

## Restricciones a respetar

- No modificar `scripts/run_ragas_eval.py` (mismo script reutilizado sin cambios desde
  E-07 T-02).
- No tocar `RAG_TOP_K`, `rag/retriever.py` ni el peso adaptativo de BM25 (D-061) — D-084
  ya cerró esa investigación sin cambio de código.
- No añadir un caso nuevo de tipo "listado" a `tests/eval/dataset_partial.json` en esta
  tarea (D-084 lo deja explícitamente para una revisión futura del dataset, fuera de
  alcance del TFM).
- No aplicar ningún ajuste de prompt derivado de la revisión de registro lingüístico de
  T-01/T-02/T-03, si quedó alguno pendiente — se documenta como hallazgo abierto para una
  épica futura (mismo criterio que D-065).

## Lo que queda fuera de esta tarea

- Traducir o duplicar las fichas de MedlinePlus al español (candidata a backlog post-TFM,
  D-084).
- Cualquier cambio de código en el retriever o en la lógica de peso adaptativo de BM25.
- El cierre formal de la épica (PR epic→main, retro) — eso es `epic-close`, no esta tarea.
