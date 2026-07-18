# E-11 T-07 — Cierre: informe final en docs/evaluation.md
# Tipo: Documentación — sin TDD, mismo patrón que E09-T06.
#
# Criterio de aceptación de la épica: resultados documentados en docs/evaluation.md
# como actualización post-E-09, con re-medición antes/después dirigida a los casos
# afectados (mismo criterio de transparencia que E-09 T-05/T-06 — CHART/TRIPOD-LLM,
# sin suavizar).

Feature: Cierre de E-11 — informe final en docs/evaluation.md

  Como responsable del proyecto AIIP
  Quiero documentar en docs/evaluation.md los resultados de todo el ciclo de mejora de
  E-11 como actualización post-E-09
  Para cerrar la épica con el mismo rigor de transparencia aplicado en E-09, antes de
  pasar a E-10

  # Checklist de verificación manual

  Scenario: La tabla de métricas de éxito se actualiza con los resultados de E-11
    Given los resultados de T-01 (línea base post-ampliación), T-02 (post-BM25 adaptativo),
      T-03 (post-hallazgo C) y T-06 (desglose de Hallucination Rate)
    When se actualiza la tabla de "docs/evaluation.md" §7
    Then cada métrica muestra el valor de E-09 y el valor post-E-11, con el delta explícito
    And se indica cuáles siguen por debajo de objetivo tras esta épica

  Scenario: Cada hallazgo de E-11 queda documentado con su estado final
    Given los hallazgos C, E, eval_15, eval_63 y guia_antibiotics_esp_0.pdf trabajados en
      T-03/T-04/T-05
    When se documenta el ciclo de mejora de E-11
    Then cada hallazgo indica su estado: resuelto, mitigado o abierto, con la misma
      granularidad que el cierre de E-09 T-05

  Scenario: El peso de BM25 queda documentado con su justificación
    Given el resultado de T-02 (peso adaptativo o fallback de recalibración simple)
    When se documenta en "docs/evaluation.md"
    Then se indica cuál de las dos vías se aplicó y por qué, con el antes/después de Context
      Precision/Recall

  Scenario: El desglose de Hallucination Rate por severidad queda incluido
    Given el resultado de T-06 (bandas Grave/Moderada/Leve/Sin desviación)
    When se documenta el informe final
    Then el binario 93.75%-derivado-de-E-09 y el nuevo desglose por severidad aparecen
      juntos, con el valor post-E-11 si cambió

  Scenario: La ampliación de la KB queda trazada
    Given las fuentes nuevas añadidas en T-01
    When se documenta el informe
    Then se referencian las fuentes nuevas en "docs/kb-sources.md" y su impacto en los
      casos de contexto pobre de E-09

  Scenario: Documentado sin suavizar (CHART/TRIPOD-LLM)
    Given todos los resultados de E-11, incluidos los que no mejoran o siguen por debajo de
      objetivo
    When se documenta el informe final
    Then no se omite ni se minimiza ningún resultado negativo, mismo criterio que E-09 T-06

  Scenario: Marcos revisa y confirma el cierre de la épica
    Given "docs/evaluation.md" actualizado con todos los resultados de E-11
    When Marcos lo revisa
    Then confirma si está listo para el cierre de la épica (epic-close) y el paso a E-10
