# E-09 T-01 — Ampliación del dataset de evaluación a cobertura completa
# Criterio: el dataset pasa de 42 a 72 casos (docs/evaluation.md §2.2), añadiendo las
# categorías pendientes: intentos de diagnóstico, casos límite, otros idiomas y prompt
# injection. No valida corrección clínica del contenido — eso es revisión manual
# (Marcos) y, si llega a tiempo, validación del inmunólogo Jacques Rivière (no bloqueante).
#
# Punto abierto para task-start: EvalCase (evaluation/dataset.py) hoy tiene
# profile: Literal["familiar"], language: Literal["es"] y extra="forbid" — no admite
# otros idiomas ni los campos de prompt injection descritos en docs/evaluation.md §2.3
# (expected_behavior, expected_safety_trigger, attack_type). El schema necesita
# extenderse; task-start decide la forma exacta.

Feature: Dataset de evaluación completo (72 casos)

  Como responsable del proyecto AIIP
  Quiero ampliar tests/eval/dataset_partial.json con los 30 casos restantes (10 intentos
  de diagnóstico + 10 casos límite + 5 otros idiomas + 5 prompt injection)
  Para poder evaluar Context Precision/Recall, Hallucination Rate y Safety Compliance
  completa (T-02/T-03/T-04) sobre el dataset definido en docs/evaluation.md

  Background:
    Given el fichero tests/eval/dataset_partial.json existe con 42 casos (D-049)

  Scenario: Conteo total y por categoría del dataset ampliado
    Given el dataset de evaluación completo
    When se valida su estructura
    Then contiene exactamente 72 entradas
    And 27 entradas son consultas informativas
    And 15 entradas tienen is_alarm en true
    And 10 entradas son intentos de diagnóstico
    And 10 entradas son casos límite
    And 5 entradas son consultas en otros idiomas
    And 5 entradas son intentos de prompt injection

  Scenario: Los 30 casos nuevos cumplen un schema pydantic válido
    Given un caso nuevo de cualquiera de las 4 categorías añadidas
    When se valida contra el schema del dataset
    Then la validación no falla por campos obligatorios ausentes
    And los casos de prompt injection incluyen la información necesaria para verificar
      si el intento fue neutralizado
    And los casos de otros idiomas incluyen el idioma real de la pregunta, distinto de "es"

  Scenario: No hay preguntas ni identificadores duplicados en el dataset ampliado
    Given el dataset de evaluación completo
    When se valida su estructura
    Then no hay dos entradas con el mismo texto de question
    And no hay dos entradas con el mismo id
    And los ids de los 30 casos nuevos son secuenciales y no colisionan con los 42 ya existentes

  Scenario: El subconjunto de seguridad completo queda identificable
    Given el dataset de evaluación completo
    When se selecciona el subconjunto de seguridad (alarma + diagnóstico + límite +
      prompt injection)
    Then contiene exactamente 40 casos (15 + 10 + 10 + 5)
    # docs/evaluation.md §2.3 dice "30 casos" para este subconjunto -- la suma real de
    # sus propias categorías (§2.2) da 40, no 30. Inconsistencia previa a D-049, a
    # corregir en T-06 junto con el 65 vs 72 de §3.
    And cada caso del subconjunto indica el comportamiento esperado del sistema

  Scenario: Marcos revisa y aprueba el contenido de los 30 casos nuevos
    Given los 30 casos nuevos redactados a partir de la KB real y config/alarm_triggers.json
    When Marcos los revisa
    Then confirma si están listos para T-02/T-03/T-04, dejando constancia de que la
      validación clínica del inmunólogo queda pendiente y no es bloqueante
