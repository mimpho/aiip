# E-07 T-01 — Dataset de evaluación parcial
# Criterio: valida la estructura del dataset (conteos, schema, unicidad).
# No valida corrección clínica del contenido — eso es revisión manual (Marcos) y,
# en Fase 1.5, validación del inmunólogo (E-09).

Feature: Dataset de evaluación parcial

  Como responsable del proyecto
  Quiero un dataset estructurado de 35 casos de prueba (20 informativos + 15 de alarma)
  Para poder ejecutar Faithfulness y Answer Relevancy (T-02) y el baseline de Safety Compliance (T-03) contra el pipeline real

  Background:
    Given el fichero tests/eval/dataset_partial.json existe

  Scenario: Conteo total y por categoría del dataset
    Given el dataset parcial de evaluación cargado desde tests/eval/dataset_partial.json
    When se valida su estructura
    Then contiene exactamente 35 entradas
    And 20 entradas corresponden a consultas informativas
    And 15 entradas tienen is_alarm en true

  Scenario: Todas las entradas cumplen el schema obligatorio
    Given el dataset parcial de evaluación cargado desde tests/eval/dataset_partial.json
    When se valida su estructura
    Then cada entrada incluye id, question, expected_answer, is_alarm, profile y language
    And ninguna entrada incluye el campo relevant_chunks
    And profile es "familiar" y language es "es" en todas las entradas

  Scenario: No hay preguntas ni identificadores duplicados en el dataset
    Given el dataset parcial de evaluación cargado desde tests/eval/dataset_partial.json
    When se valida su estructura
    Then no hay dos entradas con el mismo texto de question
    And no hay dos entradas con el mismo id

  Scenario: El validador rechaza una entrada con un campo obligatorio ausente
    Given una entrada de dataset sin el campo expected_answer
    When se valida su estructura
    Then la validación falla indicando qué campo obligatorio falta
