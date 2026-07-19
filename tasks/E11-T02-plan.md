# Plan — E-11 T-02 Re-medición RAGAS + peso adaptativo de BM25

## Contexto técnico

Research hecho en `task-start` (19 jul 2026) instalando `rank_bm25==0.2.2` y descargando el
wheel de `langchain-classic==1.0.8` (versiones fijadas en `requirements.txt`) para inspeccionar
código fuente — no verificable antes desde el sandbox de Cowork (sin venv utilizable, D-057).

1. **`BM25Retriever.vectorizer` (langchain_community) es directamente el `BM25Okapi` de
   `rank_bm25`.** Expone `vectorizer.idf` (`dict[str, float]`, IDF por palabra) y
   `vectorizer.average_idf` (float, ya calculado). No hace falta calcular nada de esto a mano —
   se lee del objeto que `get_hybrid_retriever` ya construye.
2. **Aviso de tokenización:** `BM25Retriever.preprocess_func` por defecto es
   `text.split()` — split por espacios, sin bajar a minúsculas ni quitar puntuación. El lookup
   de IDF de una palabra de la pregunta debe tokenizar con ese mismo `preprocess_func` (accesible
   como atributo del `BM25Retriever`, `bm25_retriever.preprocess_func`) para que las claves
   coincidan con las indexadas. Es el mismo comportamiento que ya usa el BM25 real del proyecto,
   no una limitación nueva de esta tarea.
3. **`EnsembleRetriever.weights` (langchain_classic) se lee en cada llamada, no solo en la
   construcción.** `rank_fusion()` invoca `weighted_reciprocal_rank(doc_lists)`, que itera
   `zip(doc_lists, self.weights)` en cada `invoke()`/`ainvoke()`. Mutar
   `retriever.weights = [nuevo_bm25, nuevo_vector]` entre construcciones y antes de un
   `.invoke()` cambia el resultado de esa llamada sin reconstruir el índice BM25 (que es la
   parte cara — recorre todos los documentos). No hay `validate_assignment` en el modelo, así
   que la reasignación no dispara el validador de construcción (`_set_weights`, que solo corre
   en `model_validator(mode="before")` al crear la instancia).
4. **Precedente de estructura mixta TDD/no-TDD en un mismo `.feature`:**
   `tests/features/e09_t05_ciclo_mejora.feature` +
   `tests/step_defs/test_e09_t05.py` ya resolvieron exactamente este patrón (D-057). Los
   escenarios de código llevan asserts normales; los 4 escenarios de "Cierre del ciclo" (backup,
   re-medición real, documentación, confirmación de Marcos) tienen step defs que hacen
   `pytest.skip(reason)` con una constante de motivo compartida — nunca un `pass` que simule
   éxito. Este plan sigue el mismo patrón para T-02.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/retriever.py` | modificar | Añade `has_lexical_signal()` y `apply_adaptive_bm25_weight()`; constantes de peso para caso "con señal" / "sin señal" |
| `rag/pipeline.py` | modificar | `RAGPipeline.retrieve()` llama a `apply_adaptive_bm25_weight()` antes de invocar el retriever cacheado |
| `tests/step_defs/test_e11_t02.py` | crear | Step defs: asserts para los 3 escenarios de código, `pytest.skip()` documentado para los 8 escenarios de re-medición/backup/confirmación |
| `tests/eval/results/e09_t02_ragas_full_scores.json` | se regenera en ejecución | Ver "Procedimiento de las dos re-mediciones" abajo — no se edita a mano, lo escribe `scripts/run_ragas_eval.py` |
| `tests/eval/results/e09_t02_ragas_full_scores_pre_e11_t02.json` | crear (backup) | Copia de la medición de E-09 T-05 (corpus sin ampliar, peso uniforme) antes de la primera ejecución de esta tarea |
| `tests/eval/results/e09_t02_ragas_full_scores_e11_t02_baseline.json` | crear (backup) | Copia de la línea base post-ampliación (peso uniforme, corpus ya ampliado) antes de tocar BM25 |

`scripts/run_ragas_eval.py` no se modifica — ya soporta re-ejecución incremental sobre
`_RESULTS_PATH`; el reset se hace moviendo/borrando el fichero antes de cada ejecución, no
cambiando el script.

## Procedimiento de las dos re-mediciones (fuera de TDD, ejecución real)

```bash
# 1. Backup de la medición de E-09 T-05 (corpus sin ampliar) y reset
cp tests/eval/results/e09_t02_ragas_full_scores.json \
   tests/eval/results/e09_t02_ragas_full_scores_pre_e11_t02.json
rm tests/eval/results/e09_t02_ragas_full_scores.json

# 2. Línea base: corpus ampliado, peso BM25 todavía uniforme (0.4/0.6, sin tocar código)
PYTHONPATH=. python scripts/run_ragas_eval.py
cp tests/eval/results/e09_t02_ragas_full_scores.json \
   tests/eval/results/e09_t02_ragas_full_scores_e11_t02_baseline.json
rm tests/eval/results/e09_t02_ragas_full_scores.json

# 3. Implementar has_lexical_signal() / apply_adaptive_bm25_weight() (ciclo TDD, ver abajo)

# 4. Medición final: corpus ampliado, peso adaptativo ya aplicado
PYTHONPATH=. python scripts/run_ragas_eval.py
# tests/eval/results/e09_t02_ragas_full_scores.json queda como resultado final de la tarea
```

El triple archivo (`_pre_e11_t02` → `_e11_t02_baseline` → final) es lo que permite separar el
efecto de la KB ampliada del efecto del ajuste de BM25 al documentar el antes/después.

## Orden de implementación TDD

Solo los 3 primeros escenarios del `.feature` llevan asserts — son código determinista sin LLM.
Los demás (regresión/mejora contra los 6/4 casos reales, backup, re-medición, fallback,
confirmación de Marcos) dependen de ejecutar `scripts/run_ragas_eval.py` de verdad contra el LLM
evaluador — se marcan `pytest.skip()` con motivo documentado, mismo patrón que
`tests/step_defs/test_e09_t05.py` (sección "Cierre del ciclo").

1. **"Señal léxica fuerte se define de forma concreta y determinista"**
   — `tests/features/e11_t02_bm25_adaptive_weight.feature`
   - Step definitions en: `tests/step_defs/test_e11_t02.py`
   - Implementación en: `rag/retriever.py::has_lexical_signal(query, bm25_retriever)`
   - Notas: construir un `BM25Retriever` de prueba con `BM25Retriever.from_texts([...])` sobre
     un corpus pequeño y controlado (3-5 frases) para tener IDF conocido; casos de test: (a)
     palabra con mayúscula no inicial → señal; (b) palabra poco frecuente en el corpus de prueba
     (IDF > `average_idf`) → señal; (c) pregunta puramente conceptual sin mayúsculas fuera de
     inicio ni términos raros → sin señal.

2. **"El peso de BM25 se recalcula en cada consulta, no una sola vez al construir el pipeline"**
   - Step definitions en: `tests/step_defs/test_e11_t02.py`
   - Implementación en: `rag/retriever.py::apply_adaptive_bm25_weight(retriever, query)`
   - Notas: construir un `EnsembleRetriever` con `get_hybrid_retriever()` sobre un vectorstore de
     prueba (o mock), invocar `apply_adaptive_bm25_weight` con dos consultas distintas
     (con/sin señal) y comprobar que `retriever.weights` cambia entre llamadas sin reconstruir
     `retriever.retrievers[0]` (mismo objeto `BM25Retriever`, identidad por `id()`).

3. **"BM25 se pondera solo ante señal léxica fuerte"**
   - Step definitions en: `tests/step_defs/test_e11_t02.py`
   - Implementación: la misma función de (2); este escenario verifica el valor concreto
     (`weights[0]` mayor en el caso "con señal" que en "sin señal" para la misma instancia).
   - Notas: usar las constantes `_SIGNAL_BM25_WEIGHT = 0.4` / `_SIGNAL_VECTOR_WEIGHT = 0.6`
     (igual que el peso uniforme actual, D-057) para el caso "con señal", y
     `_NO_SIGNAL_BM25_WEIGHT = 0.05` / `_NO_SIGNAL_VECTOR_WEIGHT = 0.95` para "sin señal" —
     valores de partida a validar en la re-medición (mismo criterio que D-057 con 0.4/0.6),
     no cerrados.

4. **Wiring en `rag/pipeline.py`**
   - No es un escenario propio del `.feature`, pero es requisito de (2)/(3): `RAGPipeline.retrieve()`
     llama a `apply_adaptive_bm25_weight(self._retriever, question)` antes de
     `self._retriever.invoke(question)` (línea actual `rag/pipeline.py:72`).
   - Notas: si `self._retriever.retrievers` tiene un solo elemento (caso sin documentos, fallback
     de `get_hybrid_retriever` cuando `vectorstore.get()` devuelve vacío), `apply_adaptive_bm25_weight`
     no hace nada — no hay BM25 que ponderar.

**A partir de aquí, ejecución real (no TDD)** — seguir "Procedimiento de las dos re-mediciones"
y cerrar los escenarios restantes del `.feature` (línea base, regresión de los 6 casos, mejora
de los 4 casos, fallback si aplica, re-medición final, confirmación de Marcos) con los datos que
produzca `scripts/run_ragas_eval.py`, documentando el triple antes/después.

## Restricciones a respetar

- Modelo y parámetros de inferencia siguen viniendo de `rag/config.py`/`.env` — esta tarea no
  toca el LLM de producción, solo el retriever.
- `has_lexical_signal()`/`apply_adaptive_bm25_weight()` deterministas, sin LLM de por medio —
  parte central del criterio D-061, no negociable dentro de esta tarea.
- Ejecutar siempre `PYTHONPATH=. pytest tests/ -v` (convención del proyecto, `AGENTS.md`).
- No relajar el peso "sin señal" a 0.0 exacto sin verificarlo — `EnsembleRetriever` exige
  `any(w > 0 for w in weights)` en la validación de construcción; un peso muy bajo (0.05) es
  seguro, 0.0 podría fallar si en algún punto se reconstruye el objeto en vez de mutarlo.

## Lo que queda fuera de esta tarea

- Actualizar `docs/evaluation.md` con el resultado — es T-07 (cierre de la épica), que agrega el
  resultado de todas las tareas de E-11.
- Investigar `eval_15`, `eval_63` o `guia_antibiotics_esp_0.pdf` — es T-05.
- Cambiar la regla de grounding para conectores no clínicos (hallazgo C) — es T-03.
- Revisión del registro lingüístico (hallazgo E) — es T-04.
- Desglose de Hallucination Rate por severidad — es T-06.
