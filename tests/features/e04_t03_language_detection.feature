# E-04 T-03 — Detección de idioma e integración en pipeline
# Criterio: el idioma del usuario se detecta correctamente y se propaga al prompt

Feature: Detección de idioma

  Como sistema RAG
  Quiero detectar el idioma del usuario automáticamente
  Para generar la respuesta en el idioma correcto

  Scenario: Detección de castellano
    Given el módulo de detección de idioma está inicializado
    When analizo el texto "¿Qué tratamientos existen para las inmunodeficiencias primarias?"
    Then el idioma detectado es "es"

  Scenario: Detección de inglés
    Given el módulo de detección de idioma está inicializado
    When analizo el texto "What treatments exist for primary immunodeficiencies?"
    Then el idioma detectado es "en"

  Scenario: Detección de catalán
    Given el módulo de detección de idioma está inicializado
    When analizo el texto "Quins tractaments existeixen per a les immunodeficiències primàries?"
    Then el idioma detectado es "ca"

  Scenario: Fallback a castellano cuando la detección falla
    Given el módulo de detección de idioma está inicializado
    When analizo un texto demasiado corto para detectar idioma como "ok"
    Then el idioma resultante es "es"
    And no se lanza ninguna excepción

  Scenario: Instrucción de idioma incluida en el prompt
    Given el idioma detectado es "es"
    When construyo el prompt final para el LLM
    Then el prompt contiene la instrucción de responder en castellano
