# E-11 T-07 — Cierre: informe final en docs/evaluation.md
# Tipo: Documentación — sin TDD, mismo patrón que E09-T06 — con un bloque previo de
# regresión sin asserts (D-070), ampliado con estabilidad de juez + investigación de
# causa raíz (D-071), mismo patrón script+revisión manual que D-050/D-051.
#
# Criterio de aceptación de la épica: resultados documentados en docs/evaluation.md
# como actualización post-E-09, con re-medición antes/después dirigida a los casos
# afectados (mismo criterio de transparencia que E-09 T-05/T-06 — CHART/TRIPOD-LLM,
# sin suavizar).

Feature: Cierre de E-11 — informe final en docs/evaluation.md

  Como responsable del proyecto AIIP
  Quiero verificar que los cambios de prompt de T-04/T-05 no han degradado nada y
  documentar en docs/evaluation.md los resultados de todo el ciclo de mejora de E-11
  Para cerrar la épica con el mismo rigor de transparencia aplicado en E-09, antes de
  pasar a E-10

  # Bloque 0 — Regresión de T-04/T-05 antes de escribir el informe (D-070, ejecutado en Antigravity)

  Scenario: La suite de tests no tiene regresiones tras los cambios de prompt
    Given "prompts/system_prompt_family.txt" modificado en T-04 (D-067) y T-05 (D-068)
    When se ejecuta "PYTHONPATH=. pytest tests/ -v"
    Then no hay regresiones respecto al último resultado conocido (147 passed, 14 skipped, 1 xfailed, T-02)

  Scenario: La glosa de tono de T-04 se confirma tras el cambio, no solo antes
    Given las 7 preguntas de "scripts/run_e11_t04_linguistic_review.py"
    When se re-ejecutan contra el pipeline con el ajuste de "[TONO — PERFIL FAMILIAR]" ya aplicado
    Then "ling_02", "ling_04" y "ling_07" glosan fármacos/acrónimos/síndromes de forma consistente
    And ninguna respuesta diluye el cierre obligatorio de derivación médica (D-002)

  Scenario: La restricción de información de centro de T-05 se confirma tras el cambio
    Given las 3 preguntas de reproducción manual de "tests/eval/results/e11_t05_cierre.md" §3
    When se repiten contra el pipeline con la restricción de "[RESTRICCIONES ABSOLUTAS]" ya generalizada
    Then la cita de "guia_antibiotics_esp_0.pdf" incluye la salvedad de información específica de un centro

  Scenario: RAGAS acotado a los casos con relación temática a los cambios de prompt
    Given "eval_08" (antibióticos, afectado por T-05) y "eval_03"/"eval_04"/"eval_13" (infusiones, afectado por T-04)
    When se comparan sus 4 métricas RAGAS contra el valor registrado en T-02
    Then no hay una caída significativa en ninguna métrica para estos 4 casos
    And cualquier cambio se documenta con el valor exacto, sin suavizar

  # Bloque 0b — Segunda ronda: estabilidad de juez + citación duplicada (D-071)

  Scenario: Estabilidad del juez de Context Precision en los casos con caída significativa
    Given "eval_08" (Δ−0.300) y "eval_13" (Δ−0.143) del escenario de RAGAS acotado
    When se invoca el juez de Context Precision dos veces sobre el mismo "SingleTurnSample"
      (sin repetir retrieval ni generación), mismo patrón que D-069 para "eval_06"
    Then se documenta si la varianza está en el juez (dos scores distintos) o en la
      generación (dos scores iguales entre sí pero distintos del valor de T-02)

  Scenario: Consistencia de la citación duplicada para una misma pregunta
    Given "ling_07", que duplicó "Fuentes consultadas:" en las dos transcripciones ya
      disponibles (pre-fix y post-fix de T-04)
    When se repite 3 veces contra el generador de producción
    Then se documenta si duplica las 3 veces (sesgo por pregunta) o de forma intermitente
      (ruido de muestreo)

  Scenario: Variante de instrucción reforzada contra la citación duplicada
    Given un "RAGGenerator" alternativo con "[FUENTES]" reescrito de forma más explícita,
      mutado solo en memoria (nunca escrito a "prompts/system_prompt_family.txt")
    When se ejecutan las mismas 10 preguntas del Bloque 0 (7 "ling_XX" + 3 "t05_regr_XX")
    Then se compara la tasa de duplicación de esta variante contra la tasa ya observada en
      producción (11/17)
    And si la variante reduce la duplicación de forma clara, se propone la redacción
      concreta a Marcos en Cowork antes de aplicarla

  # Bloque 1 — Documentación del informe final (Cowork, tras el Bloque 0)

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

  Scenario: El resultado de la regresión de T-04/T-05 queda documentado (Bloque 0 + 0b)
    Given el resultado de los 4 escenarios del Bloque 0 y los 3 del Bloque 0b
    When se documenta el informe final
    Then se indica explícitamente que el prompt final (post-T-04/T-05) fue verificado antes
      del cierre, con el resultado de pytest, la relectura cualitativa, el RAGAS acotado, la
      estabilidad de juez de eval_08/eval_13 y el resultado de la investigación de citación
      duplicada (hallazgo nuevo, con su estado: resuelto, mitigado o trasladado a backlog)

  Scenario: Documentado sin suavizar (CHART/TRIPOD-LLM)
    Given todos los resultados de E-11, incluidos los que no mejoran o siguen por debajo de
      objetivo
    When se documenta el informe final
    Then no se omite ni se minimiza ningún resultado negativo, mismo criterio que E-09 T-06

  Scenario: Marcos revisa y confirma el cierre de la épica
    Given "docs/evaluation.md" actualizado con todos los resultados de E-11
    When Marcos lo revisa
    Then confirma si está listo para el cierre de la épica (epic-close) y el paso a E-10
