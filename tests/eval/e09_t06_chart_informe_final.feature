# E-09 T-06 — Checklist CHART + informe final en docs/evaluation.md
# Tipo: Documentación — verificación sin tests automatizados (mismo patrón que
# E07-T04, D-050). A diferencia de E07-T04 (informe en tests/eval/results/*.md), el
# criterio de aceptación de E-09 pide los resultados documentados en docs/evaluation.md
# directamente (backlog/epics.md).
#
# Revisado en task-start (18 jul 2026): el borrador original (creado en epic-start,
# commit f39ed46, antes de T-02..T-05) tenía el Scenario "ciclo de mejora" desfasado
# respecto al reordenamiento mid-sprint D-056/D-057 (alcance real de T-05: A, B, D, F,
# no A, B, F; D no quedó en backlog, quedó mitigado parcialmente). Corregido aquí. Se
# añade además un escenario nuevo para los hallazgos puntuales post-T-05 (eval_63,
# eval_71) que no tenían hueco explícito en el borrador original.

Feature: Checklist CHART e informe final de evaluación en docs/evaluation.md

  Como responsable del proyecto AIIP
  Quiero completar el checklist CHART/TRIPOD-LLM y documentar en docs/evaluation.md los
  resultados completos de RAGAS, Safety Compliance, Hallucination Rate y el ciclo de
  mejora
  Para cerrar los tres criterios de aceptación documentales de E-09

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: La tabla de métricas de éxito refleja resultados reales
    Given los resultados de T-02/T-05 (Faithfulness, Answer Relevancy, Context Precision,
      Context Recall — 32 casos informativo+otro_idioma, post-T-05), T-03 (Safety
      Compliance, 25 casos alarma+límite) y T-04 (comportamiento diagnóstico/prompt
      injection, 15 casos, y Hallucination Rate derivado de Faithfulness)
    When se actualiza la tabla de docs/evaluation.md §7
    Then cada métrica tiene un valor real documentado, no solo el objetivo
    And se indica explícitamente cuáles quedan por debajo de objetivo
    And se aclara cómo se compone la fila de Safety Compliance (25 casos deterministas
      de T-03 + 15 casos de comportamiento de T-04, ambos subconjuntos al 100%)

  Scenario: Se corrigen las inconsistencias numéricas detectadas en epic-start
    Given docs/evaluation.md §3 dice "65 casos" y §2.2 desglosa 72
    And docs/evaluation.md §2.3 dice "30 casos" en el subconjunto de seguridad cuando la
      suma de sus propias categorías da 40
    When se actualiza el documento
    Then ambas cifras quedan corregidas a 72 y 40 respectivamente, coherentes con el
      desglose de §2.2

  Scenario: El ciclo de mejora queda documentado con comparativa pre/post
    Given los resultados de T-05 (hallazgos A, B, D, F — D-056, D-057)
    When se documenta el ciclo de mejora en docs/evaluation.md §5
    Then se muestra el resultado antes y después del ajuste para cada hallazgo
    And A y F quedan marcados como resueltos, D como mitigado parcialmente (con su
      lectura caso a caso de Context Precision: 23/32 sin cambio, 6/9 de los que cambian
      empeoran en preguntas conceptuales sin señal léxica), y B como abierto (Plan B
      investigado, sin fix aplicado)
    And se referencian C y E como backlog abierto no cubierto en este ciclo
      (backlog/ideas.md)

  Scenario: El checklist CHART queda completado con datos reales
    Given la tabla CHART de docs/evaluation.md §6
    When se completa cada ítem
    Then los ítems con placeholder ("A documentar durante...") tienen fecha, entorno y
      dato real
    And la tabla TRIPOD-LLM complementaria queda completada igual

  Scenario: Hallazgos puntuales post-T-05 quedan trazados en el informe
    Given el hallazgo eval_63 (backlog/ideas.md #5, outlier del subconjunto otro_idioma)
      y el ajuste de eval_71 (decisions.md D-058, addendum — prompt injection)
    When se documenta el informe final
    Then se indica que eval_63 ya no es outlier post-T-05 (Faithfulness 0.877 / Answer
      Relevancy 0.794, en rango de sus vecinos 0.77-1.0 / 0.70-0.98) con la lectura más
      plausible (efecto colateral del fix del hallazgo F sobre detección de idioma) y la
      salvedad de que no hay texto de respuesta guardado para confirmarlo con certeza
    And se indica que eval_71 (prompt injection) se corrigió dentro de T-04 mediante un
      ajuste al system prompt, y que Hallucination Rate (93.75%) corresponde al pipeline
      anterior a ese ajuste puntual, sin relación causal con él

  Scenario: El estado de la validación clínica de Jacques queda reflejado sin bloquear el cierre
    Given el estado real de la revisión de Jacques Rivière en la fecha de cierre de E-09
    When se documenta en docs/evaluation.md
    Then se indica si llegó feedback a tiempo o si queda como seguimiento post-TFM
    And en ningún caso su ausencia impide marcar E-09 como completada

  Scenario: Marcos revisa y confirma el informe final
    Given docs/evaluation.md actualizado
    When Marcos lo revisa
    Then confirma si está listo para el cierre de la épica (epic-close)
