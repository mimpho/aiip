# Plan — E-11 T-05 Investigación dirigida: `eval_15` (Context Precision/Recall)

## Contexto técnico

Decisiones ya tomadas y cerradas en Cowork (`task-start`, 20 jul 2026) — no se
re-investigan aquí:

- **`eval_63`**: confirmado resuelto (Faithfulness estable ~0.88, Context Precision
  0.639→0.804 con el peso adaptativo). Sin acción en Antigravity.
- **`guia_antibiotics_esp_0.pdf`**: investigado y cerrado en Cowork mediante reproducción
  manual guiada en Chainlit (3 preguntas de `backlog/ideas.md`, patrón confirmado en 2/3).
  Causa raíz: información operativa específica de un centro (UPIIP/Vall d'Hebron)
  presentada sin esa salvedad. Cerrado generalizando la restricción ya existente de
  `[RESTRICCIONES ABSOLUTAS]` sobre protocolos de tratamiento a cualquier información
  operativa de un centro concreto — aplicado directamente a
  `prompts/system_prompt_family.txt` en Cowork (no requiere Antigravity). Sin tests que
  dependan de la redacción exacta del bloque (verificado, `test_e04_t04.py` solo
  comprueba que el fichero existe).
- **`eval_15`, problema original** (Faithfulness 0.38, Answer Relevancy 0.0): cerrado como
  efecto colateral de T-01 (KB ampliada) — Faithfulness 0.9/0.875, Answer Relevancy
  0.84/0.839 en las mediciones post-T-01/T-02. No se re-investiga.

**Lo que sí requiere Antigravity** — hallazgo nuevo, no anticipado en el criterio original
de la épica: para `eval_15` ("¿Podemos viajar en avión llevando la medicación de
inmunoglobulinas?"), `context_precision` se mantiene exactamente en 0.0 en las tres
mediciones disponibles (`e09_t02_ragas_full_scores_pre_e11_t02.json` → pre-E11;
`..._e11_t02_baseline.json` → tras T-01, peso uniforme; `..._e11_t02_ragas_full_scores.json`
→ tras T-02, peso adaptativo) pese a que T-01 añadió dos fuentes que cubren justo este
tema (SEICAP "50 preguntas clave" — capítulo de viajes — e IPOPI "Can PID patients travel
and live abroad?" FAQ, `docs/kb-sources.md` líneas 43/45). Y `context_recall` retrocede de
1.0 (tras T-01) a 0.0 (tras T-02) — una regresión con el peso adaptativo, no una mejora.

Dos hipótesis a contrastar, no una sola dada por buena de antemano:

1. **Retrieval real**: las fuentes nuevas no se recuperan en el top-k, o se recuperan pero
   su contenido no se solapa con `expected_answer` del dataset.
2. **Ruido de medición del juez LLM de RAGAS**: `ContextPrecision`/`ContextRecall` usan
   `evaluator_llm` con `temperature=LLM_TEMPERATURE` (0.1, no determinista —
   `scripts/run_ragas_eval.py` líneas 129-133). Si `has_lexical_signal()` da `True` para
   esta pregunta ("inmunoglobulinas" es candidato a término de baja frecuencia/IDF alto),
   el peso adaptativo es idéntico al uniforme (`_SIGNAL_BM25_WEIGHT`/`_SIGNAL_VECTOR_WEIGHT`
   = mismos valores que `_BM25_WEIGHT`/`_VECTOR_WEIGHT`, `rag/retriever.py` líneas 10-20) —
   si el retrieval no cambió entre T-01 y T-02 para este caso concreto, el retroceso de
   Context Recall de 1.0 a 0.0 no puede deberse al ajuste de BM25, y apunta a variabilidad
   del juez LLM entre ejecuciones, no a un problema de retrieval real.

No se descarta ninguna de las dos sin comprobarlo empíricamente.

## Ficheros a crear

| Fichero | Acción | Propósito |
|---|---|---|
| `scripts/run_e11_t05_eval15_investigation.py` | crear | Diagnóstico de retrieval + estabilidad de RAGAS para `eval_15`. No modifica código de producción. |
| `tests/eval/results/e11_t05_eval15_investigacion.json` | generar (por el script) | Transcripción completa del diagnóstico: chunks recuperados, señal léxica, pesos aplicados, resultado de recalcular las métricas dos veces sobre el mismo contexto. |

## Orden de investigación (sin TDD — mismo patrón que T-03, D-065)

No hay ciclo rojo→verde con pytest-bdd. Un solo bloque, con vuelta a Cowork al final para
decidir causa raíz y next steps — no se aplica ningún fix en este script.

1. **Setup** — mismo patrón que `scripts/run_e11_t03_grounding_investigation.py`:
   `load_rag_config()`, `RAGPipeline(rag_config)`. No requiere el stub de `ChatVertexAI`.

2. **Señal léxica** — llamar a `has_lexical_signal(pregunta, bm25_retriever)` (importado de
   `rag/retriever.py`) sobre la pregunta exacta de `eval_15` (`tests/eval/dataset_partial.json`,
   id `eval_15`). Documentar el resultado (`True`/`False`) y qué pesos se aplican en
   consecuencia — esto determina si la hipótesis 2 (ruido de medición) es siquiera plausible.

3. **Retrieval de producción** — `pipeline.retrieve(pregunta)` con el peso adaptativo actual
   (el que aplica realmente hoy). Volcar el top-k completo: contenido de cada chunk
   (texto íntegro, no truncado), `source`/`filename` de metadata, score.

4. **¿Aparecen las fuentes nuevas?** — inspeccionar si algún chunk de
   `seicap/50-preguntas-inmunodeficiencias.pdf` o de la FAQ de IPOPI sobre viajes está en el
   top-k. Si no aparece ninguno, documentar qué documentos ocupan esas posiciones en su
   lugar. Si aparece, documentar si su contenido concreto (no solo el documento) se solapa
   con `expected_answer` de `eval_15`.

5. **Contraste manual contra la referencia** — comparar frase a frase el contenido de los
   chunks recuperados contra `expected_answer` de `eval_15` (`tests/eval/dataset_partial.json`
   línea 137: informe médico, condiciones de conservación, consultar con equipo médico/
   farmacia hospitalaria). Documentar qué afirmaciones de la referencia sí están cubiertas
   por algún chunk recuperado y cuáles no, con independencia de lo que diga RAGAS.

6. **Estabilidad del juez LLM** — sobre el MISMO `retrieved_contexts` obtenido en el paso 3
   (sin volver a llamar a `retrieve()`), invocar `ContextPrecision`/`ContextRecall` de RAGAS
   dos veces seguidas (mismo patrón de instanciación que `scripts/run_ragas_eval.py` líneas
   129-143). Si los dos resultados difieren entre sí para el mismo contexto de entrada, es
   evidencia directa de no-determinismo del juez, no de un problema de retrieval.

7. **Si el paso 2 dio señal léxica `True`** (peso adaptativo = peso uniforme, sin cambio real
   entre T-01 y T-02 para esta consulta): forzar también los pesos `_NO_SIGNAL_BM25_WEIGHT`/
   `_NO_SIGNAL_VECTOR_WEIGHT` (0.05/0.95) manualmente sobre el mismo `EnsembleRetriever` y
   volcar ese top-k también, solo para entender el mecanismo — no es el peso que se aplica
   en producción para esta consulta, se documenta como contraste informativo, no como
   resultado real.

8. **Volcado completo** — todo lo anterior a
   `tests/eval/results/e11_t05_eval15_investigacion.json`: pregunta, señal léxica, pesos
   aplicados, top-k completo con scores, contraste frase a frase, resultado de la prueba de
   estabilidad del juez (pasos 3-6).

9. **Parada explícita.** El script no aplica ningún fix ni toca `rag/retriever.py` ni
   prompts. Antigravity reporta que la investigación está lista y vuelve a Cowork para que
   Marcos y el agente decidan la causa raíz (retrieval real vs. ruido de medición) y si
   amerita un fix acotado o se documenta como backlog abierto (T-06/T-07).

## Restricciones a respetar

- **No modificar código de producción** (`rag/retriever.py`, prompts) en este script — es
  investigación pura, igual que el Bloque 1 de T-03 (D-065).
- **Agnosticismo de proveedor (D-010):** usar `ChatGoogleGenerativeAI` vía `rag_config`,
  igual que el resto de scripts del proyecto.
- No hace falta `PYTHONPATH=.` — es un script, no pytest.
- Ahorro de cuota: no re-ejecutar RAGAS sobre los 32 casos completos, solo `eval_15`
  (y los pasos 6-7 son recálculos puntuales sobre el mismo contexto, no nuevas llamadas de
  retrieval).

## Lo que queda fuera de esta tarea

- Aplicar cualquier fix de retrieval o de chunking — se decide en Cowork tras ver los
  resultados del diagnóstico, no en este script.
- Investigar `eval_06`/`eval_25` (mismo "hallazgo B" original de E-09, Plan B, sigue abierto
  y fuera del alcance acotado de T-05 — ver `backlog/epics.md`, criterios de E-11).
- El informe final consolidado de la épica — es T-07.
