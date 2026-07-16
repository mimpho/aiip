# E-09 T-01 — Ampliación del dataset de evaluación a cobertura completa
# Criterio: el dataset pasa de 42 a 72 casos (docs/evaluation.md §2.2), añadiendo las
# categorías pendientes: intentos de diagnóstico, casos límite, otros idiomas y prompt
# injection. Schema ampliado en D-054 (campo `category` explícito, `is_alarm` mantenido
# por compatibilidad, `language` a Literal["es","en","ca"], campos de prompt injection
# opcionales). No valida corrección clínica del contenido — eso es revisión manual
# (Marcos) y, si llega a tiempo, validación del inmunólogo Jacques Rivière (no bloqueante).
#
# TDD normal (D-006): validación de EvalCase, sin llamadas a red ni al pipeline real.
# Precedente: E07-T01 (tests/eval/e07_t01_partial_eval_dataset.feature).

Feature: Dataset de evaluación completo (72 casos)

  Como responsable del proyecto AIIP
  Quiero ampliar tests/eval/dataset_partial.json con los 30 casos restantes (10 intentos
  de diagnóstico + 10 casos límite + 5 otros idiomas + 5 prompt injection), cada uno con
  un campo category explícito (D-054)
  Para poder seleccionar subconjuntos de forma fiable en T-02/T-03/T-04/T-05

  Background:
    Given el dataset de evaluación completo cargado desde tests/eval/dataset_partial.json

  Scenario: Conteo total y por categoría del dataset ampliado
    When se valida su estructura
    Then contiene exactamente 72 entradas
    And 27 entradas tienen category "informativo"
    And 15 entradas tienen category "alarma"
    And 10 entradas tienen category "diagnostico"
    And 10 entradas tienen category "limite"
    And 5 entradas tienen category "otro_idioma"
    And 5 entradas tienen category "prompt_injection"

  Scenario: is_alarm es coherente con category en todo el dataset
    When se valida su estructura
    Then todas las entradas con category "alarma" tienen is_alarm en true
    And todas las entradas con category "informativo" tienen is_alarm en false

  Scenario: Los casos de prompt injection incluyen los campos de ataque obligatorios
    Given una entrada con category "prompt_injection"
    When se valida contra el schema
    Then incluye attack_type, expected_behavior y expected_safety_trigger
    And ninguno de los tres campos es null

  Scenario: Los casos de otros idiomas están en inglés o catalán, no en castellano
    Given una entrada con category "otro_idioma"
    When se valida contra el schema
    Then su campo language es "en" o "ca"
    And no es "es"

  Scenario: El validador rechaza una entrada de prompt injection sin attack_type
    Given una entrada con category "prompt_injection" sin el campo attack_type
    When se valida contra el schema
    Then la validación falla indicando el campo obligatorio ausente

  Scenario: El validador rechaza una entrada con category y is_alarm incoherentes
    Given una entrada con category "alarma" e is_alarm en false
    When se valida contra el schema
    Then la validación falla indicando la incoherencia

  Scenario: No hay preguntas ni identificadores duplicados en el dataset ampliado
    When se valida su estructura
    Then no hay dos entradas con el mismo texto de question
    And no hay dos entradas con el mismo id
    And los ids de los 30 casos nuevos son secuenciales y no colisionan con los 42 ya existentes

  Scenario: El subconjunto de seguridad completo queda identificable por category
    When se selecciona el subconjunto de seguridad (category en alarma, diagnostico,
      limite o prompt_injection)
    Then contiene exactamente 40 casos (15 + 10 + 10 + 5)
    # docs/evaluation.md §2.3 dice "30 casos" para este subconjunto -- la suma real de
    # sus propias categorías (§2.2) da 40, no 30. Inconsistencia previa a D-049, a
    # corregir en T-06 junto con el 65 vs 72 de §3.

  Scenario: Marcos revisa y aprueba el contenido de los 30 casos nuevos
    Given los 30 casos nuevos redactados a partir de la KB real y config/alarm_triggers.json
    When Marcos los revisa
    Then confirma si están listos para T-02/T-03/T-04, dejando constancia de que la
      validación clínica del inmunólogo queda pendiente y no es bloqueante
