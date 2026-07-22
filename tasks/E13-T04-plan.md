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

10. **Confirmación de cierre** (Marcos): revisar `tests/eval/results/e13_t04_cierre.md`,
    `docs/kb-sources.md` y `docs/evaluation.md`, y decidir si E-13 queda lista para
    `epic-close` (siguiente parada: E-10).

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
