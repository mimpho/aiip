# Plan — E-11 T-03 Hallazgo C: regla acotada de grounding para conectores no clínicos

## Contexto técnico

Decisiones ya tomadas (Cowork, `task-start`, D-059 punto 5, D-065):

- **Tipo de tarea:** sin TDD (checklist manual, D-050/D-051), no pytest-bdd con asserts —
  no hay ningún código determinista nuevo. `.feature`:
  `tests/eval/e11_t03_grounding_conectores.feature`.
- **Caso sintético de referencia:** "¿hay algún hospital con inmunología cerca de Vic?" no es
  un caso real del dataset (`tests/eval/dataset_partial.json`) ni del smoke test E-05 T-07
  CU-05 — es una ilustración hipotética de Marcos (E-05 T-03). Verificado contra el KB real:
  `data/raw/aedip/Hospitales-con-Servicios-de-Inmunologia.html` sí contiene hospitales
  etiquetados "Barcelona" (Sant Joan de Déu, Vall d'Hebron) — ninguno menciona "Vic" — así que
  la pregunta debería recuperar ese chunk vía retrieval híbrido (BM25+vectorial) y es un caso
  reproducible de verdad, no un experimento a ciegas.
- **Mecanismo de contraste (D-059 punto 5):** `RAGGenerator` (`rag/generator.py`) carga
  `_system_prompt` una vez en `__init__` desde `prompts/system_prompt_family.txt`. Para
  generar la respuesta "laxa" sin tocar el fichero de producción, se instancia un segundo
  `RAGGenerator` (o se muta `_system_prompt` de una instancia ya construida antes de llamar a
  `generate()`) con una variante del prompt que añade permiso explícito para conectar
  conceptos no clínicos de sentido común — nunca se escribe esa variante en
  `prompts/system_prompt_family.txt` hasta que Marcos apruebe la redacción final (Bloque 2
  del `.feature`). Ambas respuestas (laxa y estricta) deben pasar por
  `check_alarm_signals`/`apply_safety_filter` (`rag/safety.py`) igual que en producción —
  `RAGPipeline.query()` ya hace esto para la estricta; para la laxa hay que aplicar el filtro
  manualmente sobre el texto generado.
- **Regresión de los 32 casos, alcance acotado a Faithfulness:** el ajuste de hallazgo C solo
  toca el system prompt (generación), no el retriever — Context Precision/Recall dependen de
  qué se recupera, no de qué se genera, así que no deberían cambiar y no hace falta
  recalcularlos (ahorra llamadas a la API). Solo se re-mide Faithfulness contra la línea base
  de `tests/eval/results/e09_t02_ragas_full_scores.json` (resultado final de T-02, peso
  adaptativo BM25 — confirmado en `tests/eval/results/e11_t02_cierre.md`).
- **Exclusiones de alcance ya fijadas (D-065), no se redescubren en la investigación:**
  fármacos/dosis, protocolos de tratamiento, inferencias sobre el estado clínico del usuario,
  fuentes externas no indexadas. La regla redactada en el Bloque 2 debe declarar estas
  exclusiones explícitamente, no solo el permiso positivo.

**Sin hallazgos adicionales de research** más allá de lo ya confirmado en `task-start`:
`check_alarm_signals`/`apply_safety_filter` existen tal cual en `rag/safety.py`, sin cambios
de firma necesarios.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `scripts/run_e11_t03_grounding_investigation.py` | crear | Genera y contrasta respuesta laxa vs. estricta sobre el caso sintético Vic/Barcelona (y cualquier caso adicional que surja), ambas pasadas por los mecanismos de seguridad. No se despliega ninguna a producción — solo transcribe para revisión. |
| `tests/eval/results/e11_t03_investigacion_offline.json` | generar (por el script) | Transcripción completa de ambas respuestas + metadatos (pregunta, contexto recuperado, chunk fuente) para que Marcos y el agente redacten la regla en Cowork |
| `prompts/system_prompt_family.txt` | modificar (tras aprobación explícita de Marcos, Bloque 2/3 del `.feature`) | Añade la regla acotada de grounding (alcance positivo + exclusiones) a la sección `[FUENTES]` |
| `scripts/run_e11_t03_regression_eval.py` | crear | Re-mide Faithfulness (no las otras 3 métricas — ver Contexto técnico) sobre los 32 casos `informativo`+`otro_idioma`, calcado del patrón de `scripts/run_ragas_eval.py` pero apuntando a un fichero de resultados nuevo |
| `tests/eval/results/e11_t03_ragas_faithfulness_post_grounding.json` | generar (por el script) | Faithfulness post-ajuste, comparado explícitamente contra `e09_t02_ragas_full_scores.json` |
| `tests/eval/e11_t03_grounding_conectores.feature` | ya existe, ya aprobado | Sin más cambios |

## Orden de implementación (sin TDD — D-050/D-065)

No hay ciclo rojo→verde con pytest-bdd. Esta tarea tiene **dos gates de aprobación de Marcos
en medio** (redacción de la regla, y cierre final) — Antigravity ejecuta hasta el primer gate,
se detiene, y retoma tras la aprobación. No aplica producción directa sin ese paso intermedio.

### Bloque 1 — Investigación offline (hasta el primer gate)

1. **Setup del script `run_e11_t03_grounding_investigation.py`** — mismo patrón de `main()`
   que `scripts/run_e09_t04_eval.py`: `load_rag_config()`, `RAGPipeline(rag_config)`. No
   requiere el stub de `ChatVertexAI` (no importa `ragas`).

2. **Caso sintético Vic/Barcelona** — `pipeline.retrieve("¿hay algún hospital con inmunología
   cerca de Vic?")`, confirmar que el chunk recuperado menciona "Barcelona" (Sant Joan de Déu
   o Vall d'Hebron) sin mencionar "Vic". Si el retrieval no trae ese chunk (posible tras la
   ampliación de KB de T-01/T-02), documentarlo y ajustar la pregunta de prueba hasta
   encontrar un caso real donde el patrón se reproduzca — no forzar el caso si ya no aplica.

3. **Respuesta estricta** — `pipeline.query(pregunta)` (ya pasa por `apply_safety_filter`
   internamente).

4. **Respuesta laxa** — construir un `RAGGenerator` alternativo (misma config, pero con
   `_system_prompt` sustituido por una variante que añade, sin quitar nada de lo existente,
   permiso para conectar conceptos no clínicos de sentido común usando el contexto
   disponible). Generar con `.generate(question, context, language)` sobre el mismo contexto
   recuperado en el paso 2 (no volver a recuperar). Aplicar manualmente
   `check_alarm_signals(pregunta)` + `apply_safety_filter(respuesta, has_alarm)` sobre el
   resultado — la variante laxa nunca pasa por `RAGPipeline.query()` tal cual, así que no
   hereda el filtro automáticamente.

5. **Volcado** — escribir ambas transcripciones completas (no solo un resumen) a
   `tests/eval/results/e11_t03_investigacion_offline.json`: pregunta, chunk(s) recuperado(s),
   respuesta estricta, respuesta laxa, y si cada una activó `has_alarm`.

6. **Parada explícita.** El script no toca `prompts/system_prompt_family.txt`. Antigravity
   reporta que el Bloque 1 está listo y que el Bloque 2 (redacción + aprobación) requiere
   volver a Cowork — no continúa solo.

### Bloque 2 — Redacción y aprobación (en Cowork, no en Antigravity)

7. El agente (en Cowork) lee `e11_t03_investigacion_offline.json`, propone la redacción
   exacta de la regla para `[FUENTES]` de `prompts/system_prompt_family.txt`, incluyendo:
   - Alcance positivo (geografía básica, distancias, relaciones temporales obvias)
   - Exclusiones explícitas (fármacos/dosis, protocolos de tratamiento, estado clínico del
     usuario, fuentes externas no indexadas) — ya fijadas en D-065, no opcionales
   Marcos aprueba la redacción exacta o pide ajustes (gate — no se continúa sin esto).

8. Tras la aprobación: aplicar el texto aprobado a `prompts/system_prompt_family.txt`
   (edición directa de texto — puede hacerse en Cowork, no requiere el entorno de
   Antigravity).

### Bloque 3 — Verificación y cierre (vuelta a Antigravity)

9. **Re-ejecutar el caso Vic/Barcelona con la regla ya aplicada** — `pipeline.query()` (ahora
   con el prompt de producción ya actualizado) sobre la misma pregunta del paso 2. Verificar
   que la respuesta conecta el concepto no clínico sin inventar datos clínicos.

10. **Caso de regresión clínica** — elegir un caso existente del dataset con un hecho clínico
    no presente en el contexto recuperado (ej. algún caso `limite` de
    `tests/eval/dataset_partial.json`), verificar que el modelo sigue sin extrapolar y sigue
    derivando a consulta médica. Confirmar que `check_alarm_signals`/`apply_safety_filter` no
    cambian de comportamiento.

11. **Setup y ejecución de `run_e11_t03_regression_eval.py`** — calcar `run_ragas_eval.py`
    pero: (a) solo instanciar `Faithfulness` (no `ResponseRelevancy`/`ContextPrecision`/
    `ContextRecall`), (b) `_RESULTS_PATH` apunta a
    `tests/eval/results/e11_t03_ragas_faithfulness_post_grounding.json` (fichero nuevo, no
    sobrescribe `e09_t02_ragas_full_scores.json`), (c) ejecución incremental igual que el
    original (checkpointing por `id`).

12. **Comparación explícita** — por cada uno de los 32 casos, comparar
    `faithfulness` nuevo contra el valor en `e09_t02_ragas_full_scores.json`. Documentar
    cualquier caso que empeore (no debería haber ninguno, dado que el ajuste solo añade
    permiso para conectores no clínicos, no afecta a los 32 casos que no los contienen) — si
    aparece alguno, anotarlo explícitamente en vez de descartarlo.

13. **Verificación manual final** — revisar
    `tests/eval/results/e11_t03_investigacion_offline.json` +
    `e11_t03_ragas_faithfulness_post_grounding.json` contra el checklist completo del
    `.feature`. Marcos revisa y confirma si el hallazgo C queda cerrado.

## Restricciones a respetar

- **Falso Negativo Cero (D-002):** la respuesta laxa del Bloque 1 es solo para investigación
  — nunca se expone a un usuario real ni se despliega. Las exclusiones de D-065 (fármacos,
  protocolos, estado clínico, fuentes externas) son no negociables en la redacción final.
- **Dos gates de aprobación, no uno:** a diferencia de E-09 T-04 (un solo gate al final), esta
  tarea exige la aprobación de Marcos **antes** de tocar `prompts/system_prompt_family.txt`
  en producción (D-059 punto 5) — Antigravity no debe aplicar el texto por su cuenta aunque
  la investigación del Bloque 1 termine sin incidentes.
- **Agnosticismo de proveedor (D-010):** el `RAGGenerator` alternativo del Bloque 1 se
  construye igual que el de producción, sobre `ChatGoogleGenerativeAI` vía `rag_config`, no
  un SDK nuevo.
- `PYTHONPATH=.` no aplica — son scripts, no pytest.

## Lo que queda fuera de esta tarea

- Recalcular Context Precision/Recall/Answer Relevancy — no deberían cambiar (el ajuste no
  toca retrieval) y no se re-miden para ahorrar llamadas a la API; si en la revisión manual
  aparece indicio de que sí cambian, se documenta como hallazgo nuevo, no se resuelve aquí.
  Hallazgo E (registro lingüístico) y `eval_15`/`eval_63`/`guia_antibiotics_esp_0.pdf` — T-04
  y T-05 de esta épica.
- El informe final consolidado — es T-07.
