# E-11 T-06 — Hallucination Rate: desglose por bandas de severidad
# Tipo: Reporting/documentación — sin TDD, mismo patrón que E09-T04/T06.
#
# Contexto (D-058, epic-start E-11 18 jul 2026): Hallucination Rate se define como %
# de casos con faithfulness < 1.0 (conteo binario, D-058) — 93.75% (30/32 casos)
# post-E-09. No es un fallo de medición: RAGAS Faithfulness calcula bien el soporte
# por afirmación, pero el binario no distingue severidad. De los 30 casos "alucinados",
# 29 están entre 0.69 y 0.96 (matiz/parafraseo, no dato inventado) y solo eval_15 es
# grave (0.38). Bandas aprobadas por Marcos:
#   Grave        (< 0.5)
#   Moderada     (0.5–0.85)
#   Leve         (0.85–<1.0)
#   Sin desviación (1.0)
# El binario 93.75% se mantiene en el informe por continuidad con E-09, acompañado de
# este desglose.

Feature: Hallucination Rate — desglose por bandas de severidad

  Como responsable del proyecto AIIP
  Quiero complementar el Hallucination Rate binario con un desglose por bandas de
  severidad de Faithfulness
  Para que el informe final distinga alucinación real (contenido inventado) de matices
  de redacción que no representan un riesgo clínico

  Scenario: Las bandas de severidad quedan definidas y documentadas
    Given las bandas Grave (< 0.5), Moderada (0.5–0.85), Leve (0.85–<1.0) y Sin desviación
      (1.0)
    When se documentan en "docs/evaluation.md"
    Then queda explícito que las bandas se derivan del score de Faithfulness por caso, no de
      una nueva llamada a la API (mismo principio de D-058: reutilizar datos ya calculados)

  Scenario: El desglose se calcula sobre los scores ya existentes tras esta épica
    Given los scores de Faithfulness de los 32 casos informativo/otro_idioma, ya
      actualizados tras T-01/T-02/T-03 de esta épica
    When se clasifica cada caso en su banda
    Then se obtiene el conteo y porcentaje de casos por banda

  Scenario: eval_15 queda identificado como el caso grave, si sigue siéndolo
    Given el resultado de T-05 sobre eval_15 (fix aplicado o documentado como coste
      aceptado)
    When se calcula el desglose por severidad
    Then se indica explícitamente si eval_15 sigue en la banda Grave o si pasó a una banda
      menos severa tras el trabajo de T-05

  Scenario: El binario y el desglose conviven en el informe
    Given el Hallucination Rate binario (% de casos con faithfulness < 1.0)
    When se documenta en "docs/evaluation.md"
    Then el binario se mantiene tal cual, sin suavizarlo
    And el desglose por bandas aparece como métrica complementaria en la misma sección,
      no sustituyendo al binario

  Scenario: Marcos confirma las bandas y el resultado final
    Given el desglose calculado sobre los datos reales de esta épica
    When Marcos lo revisa
    Then confirma si las bandas propuestas siguen siendo adecuadas o si prefiere ajustar
      algún corte antes del informe final (T-07)
