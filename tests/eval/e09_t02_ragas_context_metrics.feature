# E-09 T-02 — RAGAS: Context Precision + Context Recall contra el pipeline real
# Tipo: Script documentado — verificación sin tests automatizados (mismo patrón que
# E07-T02, D-050/D-051). Extiende scripts/run_ragas_eval.py, no lo sustituye.

Feature: RAGAS Context Precision + Context Recall contra el pipeline real

  Como responsable del proyecto AIIP
  Quiero calcular Context Precision y Context Recall con RAGAS contra RAGPipeline real
  sobre los casos informativos del dataset completo (T-01)
  Para completar las 4 métricas RAGAS exigidas por el criterio de aceptación de E-09

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: El script reutiliza la infraestructura ya validada en E-07 T-02
    Given scripts/run_ragas_eval.py
    When se extiende con las nuevas métricas
    Then sigue usando RAGPipeline real sin mocks, el mismo LLM evaluador (LLM_MODEL) y
      el mismo embedder (BAAI/bge-m3) que Faithfulness/Answer Relevancy
    And reutiliza los workarounds ya documentados (D-052: stub de ChatVertexAI,
      _EVALUATOR_MAX_TOKENS)

  Scenario: Se evalúan los casos informativos del dataset completo
    Given el dataset de evaluación completo (T-01, 72 casos)
    When el script selecciona los casos a evaluar para Context Precision/Recall
    Then se incluyen los casos informativos (is_alarm en false)
    And se documenta explícitamente si se amplía o no el subconjunto evaluado respecto
      a los 27 casos originales de E-07

  Scenario: Los resultados quedan documentados junto a los de Faithfulness/Answer Relevancy
    Given la ejecución completa del script sobre el subconjunto informativo
    When reviso tests/eval/results/e09_t02_ragas_full_scores.json
    Then cada caso incluye Context Precision y Context Recall, además de Faithfulness y
      Answer Relevancy re-evaluados sobre el dataset completo
    And el fichero incluye los agregados (media) de las 4 métricas

  Scenario: La ejecución es incremental y reanudable
    Given una ejecución previa del script interrumpida a mitad del dataset
    When se relanza scripts/run_ragas_eval.py
    Then detecta qué ids ya tienen score guardado y continúa solo con los pendientes

  Scenario: Marcos revisa y confirma los resultados
    Given tests/eval/results/e09_t02_ragas_full_scores.json completo
    When Marcos lo revisa
    Then confirma si Context Precision/Recall están listos para el informe final (T-06)
    And anota si algún resultado por debajo de objetivo (>85%) apunta al hallazgo D
      (ruido en dense search, backlog/ideas.md) como causa probable
