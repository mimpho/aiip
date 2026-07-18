# E-09 T-02 — RAGAS: Context Precision + Context Recall contra el pipeline real
# Tipo: Script documentado — verificación sin tests automatizados (mismo patrón que
# E07-T02, D-050/D-051/D-053). Extiende scripts/run_ragas_eval.py, no lo sustituye.
# Alcance y decisiones técnicas: D-055.

Feature: RAGAS Context Precision + Context Recall contra el pipeline real

  Como responsable del proyecto AIIP
  Quiero calcular Context Precision y Context Recall con RAGAS contra RAGPipeline real
  sobre el subconjunto informativo + otro_idioma del dataset completo (T-01)
  Para completar las 4 métricas RAGAS exigidas por el criterio de aceptación de E-09

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: El script reutiliza la infraestructura ya validada en E-07 T-02
    Given scripts/run_ragas_eval.py
    When se extiende con LLMContextPrecisionWithReference y LLMContextRecall
    Then sigue usando RAGPipeline real sin mocks, el mismo LLM evaluador (LLM_MODEL) y
      el mismo embedder (BAAI/bge-m3) que Faithfulness/Answer Relevancy
    And reutiliza los workarounds ya documentados (D-052: stub de ChatVertexAI,
      _EVALUATOR_MAX_TOKENS=8192)

  Scenario: Se evalúan los 32 casos de categoría informativo + otro_idioma
    Given el dataset de evaluación completo (T-01, 72 casos)
    When el script selecciona los casos por category in ("informativo", "otro_idioma")
    Then se evalúan exactamente 27 casos informativo + 5 casos otro_idioma (32 en total)
    And quedan excluidos diagnostico, limite, prompt_injection y alarma (D-055: sus
      expected_answer no son contenido clínico grounded en los chunks recuperados)
    And cada SingleTurnSample incluye reference=case.expected_answer, requerido por
      LLMContextPrecisionWithReference/LLMContextRecall

  Scenario: Los resultados quedan documentados junto a los de Faithfulness/Answer Relevancy
    Given la ejecución completa del script sobre los 32 casos
    When reviso tests/eval/results/e09_t02_ragas_full_scores.json
    Then cada caso incluye Context Precision, Context Recall, Faithfulness y Answer
      Relevancy, recalculados juntos sobre este subconjunto
    And el fichero incluye los agregados (media) de las 4 métricas
    And tests/eval/results/e07_t02_ragas_scores.json no se modifica (queda como registro
      histórico del baseline de 27 casos)

  Scenario: La ejecución es incremental y reanudable
    Given una ejecución previa del script interrumpida a mitad del subconjunto
    When se relanza scripts/run_ragas_eval.py
    Then detecta qué ids ya tienen score guardado en e09_t02_ragas_full_scores.json y
      continúa solo con los pendientes

  Scenario: Marcos revisa y confirma los resultados
    Given tests/eval/results/e09_t02_ragas_full_scores.json completo
    When Marcos lo revisa
    Then confirma si Context Precision/Recall están listos para el informe final (T-06)
    And anota si algún resultado por debajo de objetivo (>85%) apunta al hallazgo D
      (ruido en dense search, backlog/ideas.md) como causa probable
