# E-11 T-02 — Re-medición tras ampliación de KB + peso adaptativo de BM25
# Depende de T-01 (corpus ya ampliado y reingestado, sin RAGAS — D-060).
#
# Contexto (D-057, E-09 T-05): peso uniforme 0.4/0.6 (BM25/vectorial) en
# rag/retriever.py::get_hybrid_retriever. Retrospectiva post-cierre de E-09
# (backlog/ideas.md, "Hallazgos del RAG" punto 1): de 32 casos, 22 no cambian con
# BM25, y de los 10 que sí, 6 empeoran (eval_64, eval_17, eval_16, eval_19, eval_02,
# eval_04 — preguntas conceptuales sin nombre propio ni término geográfico) y 4
# mejoran (eval_07, eval_11, eval_01, eval_21). Corrección de task-start (D-061):
# ninguno de los 4 que mejoran tiene nombre propio/geográfico — el ejemplo
# "hospitales en Barcelona" no pertenece a estos 32 casos (viene de un smoke test
# manual distinto, E-05 T-07 CU-05). El criterio de "señal léxica fuerte" se amplía
# en consecuencia (ver D-061): mayúscula no inicial de frase, o palabra de baja
# frecuencia en el corpus (IDF de rank_bm25) — no solo nombre propio/geográfico.

Feature: Re-medición post-ampliación de KB y peso adaptativo de BM25

  Como responsable del proyecto AIIP
  Quiero re-medir RAGAS sobre el corpus ampliado (T-01) y ajustar el peso de BM25 para que solo contribuya cuando la consulta tiene señal léxica fuerte
  Para que Context Precision mejore en preguntas con señal léxica sin penalizar las preguntas conceptuales que ya recuperaban bien solo con vectorial

  # --- Línea base: efecto de la ampliación de KB, aislado del ajuste de BM25 ---
  # Tipo: script sin TDD (D-050/D-051) — instrumentación + revisión manual, no asserts.

  Scenario: Reset y respaldo antes de la línea base post-ampliación
    Given el fichero de resultados de E-09 T-05 (corpus sin ampliar, peso uniforme 0.4/0.6) en tests/eval/results/e09_t02_ragas_full_scores.json
    When se prepara la primera ejecución de scripts/run_ragas_eval.py de esta tarea
    Then el fichero se respalda como referencia de E-09 (peso uniforme, corpus sin ampliar) y se resetea a vacío
    And se documenta explícitamente que el reset es necesario porque la ejecución es incremental y sin resetear no mediría nada nuevo sobre el corpus ampliado

  Scenario: Medición de línea base sobre el corpus ampliado, sin tocar BM25 todavía
    Given el fichero de resultados reseteado y el retriever con el peso uniforme 0.4/0.6 aún sin modificar
    When se ejecuta scripts/run_ragas_eval.py sobre los 32 casos (informativo + otro_idioma)
    Then se obtiene Context Precision y Context Recall de línea base post-ampliación
    And el resultado se respalda antes de tocar el peso de BM25

  # --- Peso adaptativo (prioridad, D-061) ---
  # Tipo: código con TDD — funciones deterministas, sin LLM, asserts pytest-bdd.

  Scenario: Señal léxica fuerte se define de forma concreta y determinista
    Given una consulta de usuario
    When se evalúa si tiene señal léxica fuerte con has_lexical_signal
    Then la consulta se clasifica como "con señal" o "sin señal" de forma determinista, sin LLM de por medio

  Scenario: El peso de BM25 se recalcula en cada consulta, no una sola vez al construir el pipeline
    Given RAGPipeline con el retriever híbrido ya construido y cacheado
    When se invoca retrieve()/query() para una consulta concreta
    Then el peso de EnsembleRetriever (weights) se actualiza para esa consulta antes de invocar el retriever, sin reconstruir el índice BM25 desde cero

  Scenario: BM25 se pondera solo ante señal léxica fuerte
    Given get_hybrid_retriever en rag/retriever.py ya ajustado para aceptar un peso actualizable
    When se recupera contexto para una consulta "con señal"
    Then el peso de BM25 aplicado es mayor que el de una consulta "sin señal" en la misma ejecución

  Scenario: Las preguntas que empeoraron con peso uniforme no empeoran más con el ajuste (regresión)
    Given los 6 casos que empeoraron en la retrospectiva de E-09 T-05 (eval_64, eval_17, eval_16, eval_19, eval_02, eval_04 — conceptuales, sin señal léxica fuerte)
    When se recuperan con el retriever ajustado
    Then su Context Precision no empeora frente a la línea base post-ampliación (peso BM25 ~0 en estos casos, al no tener señal léxica)

  Scenario: Las preguntas que mejoraron con peso uniforme se mantienen o mejoran
    Given los 4 casos que mejoraron en la retrospectiva de E-09 T-05 (eval_07, eval_11, eval_01, eval_21)
    When se recuperan con el retriever ajustado
    Then su Context Precision se mantiene igual o mejor que con la línea base post-ampliación
    # Nota (D-061): estos 4 casos no tienen nombre propio/geográfico — si el criterio
    # de señal léxica ampliado (mayúscula + rareza en corpus) no los detecta como "con
    # señal", este escenario documenta el resultado igualmente (mejora puede venir de
    # la ampliación de KB, no del ajuste de BM25) en vez de asumir causalidad.

  # --- Fallback: recalibración simple (solo si el adaptativo no cierra a tiempo) ---

  Scenario: Fallback a peso fijo recalibrado si el adaptativo no cierra a tiempo
    Given que el peso adaptativo no llega a completarse dentro del margen de la tarea
    When se aplica la vía barata de bajar el peso fijo de BM25 para todas las consultas por igual
    Then se documenta explícitamente que se optó por el fallback y por qué
    And se re-mide igual que si fuera la solución adaptativa

  # --- Cierre: re-medición final y documentación ---
  # Tipo: script sin TDD (D-050/D-051) — instrumentación + revisión manual, no asserts.

  Scenario: Reset y respaldo antes de la medición final tras el ajuste de BM25
    Given el fichero de resultados con la línea base post-ampliación ya respaldado
    When se prepara la segunda ejecución de scripts/run_ragas_eval.py de esta tarea
    Then el fichero se resetea a vacío antes de medir con el peso ya ajustado (adaptativo o fallback)

  Scenario: Re-medición final tras el ajuste de BM25
    Given el retriever ya ajustado (adaptativo o fallback) y el fichero de resultados reseteado
    When se re-ejecuta scripts/run_ragas_eval.py sobre los 32 casos
    Then se obtiene Context Precision y Context Recall final
    And se documenta el triple antes/después separando el efecto de la KB del efecto del ajuste de BM25

  Scenario: Marcos revisa y confirma el ajuste de BM25
    Given los resultados de la re-medición final
    When Marcos los revisa
    Then confirma si el ajuste queda cerrado (adaptativo o fallback) o si hace falta iterar antes de pasar a las siguientes tareas de la épica
