# E-09 T-06 — Checklist CHART + informe final en docs/evaluation.md
# Tipo: Documentación — verificación sin tests automatizados (mismo patrón que
# E07-T04, D-050). A diferencia de E07-T04 (informe en tests/eval/results/*.md), el
# criterio de aceptación de E-09 pide los resultados documentados en docs/evaluation.md
# directamente (backlog/epics.md).

Feature: Checklist CHART e informe final de evaluación en docs/evaluation.md

  Como responsable del proyecto AIIP
  Quiero completar el checklist CHART/TRIPOD-LLM y documentar en docs/evaluation.md los
  resultados completos de RAGAS, Safety Compliance, Hallucination Rate y el ciclo de
  mejora
  Para cerrar los tres criterios de aceptación documentales de E-09

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: La tabla de métricas de éxito refleja resultados reales
    Given los resultados de T-02 (Faithfulness, Answer Relevancy, Context Precision,
      Context Recall), T-03/T-04 (Safety Compliance, comportamiento diagnóstico/prompt
      injection) y T-04 (Hallucination Rate)
    When se actualiza la tabla de docs/evaluation.md §7
    Then cada métrica tiene un valor real documentado, no solo el objetivo
    And se indica explícitamente cuáles quedan por debajo de objetivo

  Scenario: Se corrigen las inconsistencias numéricas detectadas en epic-start
    Given docs/evaluation.md §3 dice "65 casos" y §2.2 desglosa 72
    And docs/evaluation.md §2.3 dice "30 casos" en el subconjunto de seguridad cuando la
      suma de sus propias categorías da 40
    When se actualiza el documento
    Then ambas cifras quedan corregidas a 72 y 40 respectivamente, coherentes con el
      desglose de §2.2

  Scenario: El ciclo de mejora queda documentado con comparativa pre/post
    Given los resultados de T-05 (hallazgos A, B, F)
    When se documenta el ciclo de mejora en docs/evaluation.md §5
    Then se muestra el resultado antes y después del ajuste para cada hallazgo resuelto
      o mitigado
    And se referencian C, D y E como backlog abierto no cubierto en este ciclo
      (backlog/ideas.md)

  Scenario: El checklist CHART queda completado con datos reales
    Given la tabla CHART de docs/evaluation.md §6
    When se completa cada ítem
    Then los ítems con placeholder ("A documentar durante...") tienen fecha, entorno y
      dato real
    And la tabla TRIPOD-LLM complementaria queda completada igual

  Scenario: El estado de la validación clínica de Jacques queda reflejado sin bloquear el cierre
    Given el estado real de la revisión de Jacques Rivière en la fecha de cierre de E-09
    When se documenta en docs/evaluation.md
    Then se indica si llegó feedback a tiempo o si queda como seguimiento post-TFM
    And en ningún caso su ausencia impide marcar E-09 como completada

  Scenario: Marcos revisa y confirma el informe final
    Given docs/evaluation.md actualizado
    When Marcos lo revisa
    Then confirma si está listo para el cierre de la épica (epic-close)
