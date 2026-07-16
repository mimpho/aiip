# E-07 T-04 — Informe parcial de resultados
# Tipo: Documentación — verificación sin tests automatizados (mismo patrón que T-02, D-050)

Feature: Informe parcial de resultados de evaluación RAGAS y Safety Compliance

  Como responsable del proyecto AIIP
  Quiero un informe que documente los resultados de Faithfulness, Answer Relevancy
  y Safety Compliance obtenidos en T-01/T-02/T-03, junto con los problemas
  identificados
  Para dejar constancia de la Fase 1 antes del ciclo de mejora de E-09 (Fase 1.5)

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: El informe existe en la ubicación acordada
    Given los resultados de "tests/eval/results/e07_t02_ragas_scores.json" y
      "tests/eval/results/e07_t03_safety_compliance_baseline.json"
    When se redacta el informe parcial
    Then el fichero "tests/eval/results/e07_t04_informe_parcial.md" existe

  Scenario: El informe documenta el dataset usado
    Given el dataset parcial de 42 casos (27 informativos + 15 alarma, D-049)
    When reviso el informe
    Then indica la composición del dataset y su procedencia

  Scenario: El informe documenta Faithfulness y Answer Relevancy
    Given los agregados de "e07_t02_ragas_scores.json" (Faithfulness 79.7%,
      Answer Relevancy 77.8%)
    When reviso el informe
    Then muestra ambos valores agregados
    And los compara con los objetivos de docs/evaluation.md (>95% / >90%)
    And aclara que no se aplica ciclo de mejora en esta tarea (Fase 1.5, E-09)

  Scenario: El informe documenta el baseline de Safety Compliance
    Given el agregado de "e07_t03_safety_compliance_baseline.json" (100%, 15/15)
    When reviso el informe
    Then muestra el resultado y el tamaño de la muestra

  Scenario: El informe documenta el hallazgo de alarmas inesperadas (D-053)
    Given los 3 casos informativos marcados "unexpected_alarm" en
      "e07_t02_ragas_scores.json" (eval_07, eval_08, eval_25)
    When reviso el informe
    Then los menciona explícitamente como hallazgo, enlazando D-053

  Scenario: El informe documenta los casos de Answer Relevancy en 0.0 sin causa diagnosticada
    Given los casos eval_06 y eval_15 con "answer_relevancy" en 0.0 sin "unexpected_alarm"
    When reviso el informe
    Then los anota como observación abierta, sin diagnosticar la causa (fuera de
      alcance de esta tarea)

  Scenario: El informe delimita el alcance frente a Fase 1.5
    When reviso el informe
    Then indica explícitamente que Context Precision, Context Recall y
      Hallucination Rate quedan fuera de esta tarea (E-09)

  Scenario: Marcos revisa y confirma el informe
    Given el informe completo
    When Marcos lo revisa
    Then confirma si está listo para cerrar T-04
