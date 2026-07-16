# E-07 T-03 — Safety Compliance baseline (15 casos de alarma)
# Criterio: los 15 casos de alarma del dataset parcial (D-049) activan correctamente
# el módulo de seguridad (Falso Negativo Cero). Determinista, sin LLM (D-053).

Feature: Safety Compliance baseline sobre los casos de alarma del dataset

  Como responsable del proyecto AIIP
  Quiero verificar que los 15 casos de alarma del dataset de evaluación activan
  el módulo de seguridad (check_alarm_signals)
  Para obtener el primer baseline de Safety Compliance antes del informe parcial de T-04

  Background:
    Given el dataset parcial de evaluación cargado desde tests/eval/dataset_partial.json
    And los 15 casos con is_alarm en true seleccionados

  Scenario: Todos los casos de alarma activan el módulo de seguridad
    When se evalúa check_alarm_signals sobre cada uno de los 15 casos
    Then las 15 preguntas activan la alarma
    And el Safety Compliance baseline es del 100%

  Scenario: Un caso sin ninguna señal de alarma conocida no activa el módulo
    Given una pregunta sintética sin coincidencia con ningún trigger de config/alarm_triggers.json
    When se evalúa con check_alarm_signals
    Then no se detecta ninguna señal de alarma
    # Prueba que el assert del escenario anterior discrimina de verdad
    # (no pasaría igual si check_alarm_signals devolviese siempre True)

  Scenario: El resultado queda documentado para el informe parcial de T-04
    When se evalúa check_alarm_signals sobre cada uno de los 15 casos
    Then se escribe tests/eval/results/e07_t03_safety_compliance_baseline.json
    And cada entrada incluye id, question y si activó la alarma
    And el fichero incluye el agregado (% de Safety Compliance)
