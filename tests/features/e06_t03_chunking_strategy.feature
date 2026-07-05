# E-06 T-03 — Estrategia de chunking multiidioma
# Criterio: los documentos se dividen en chunks trazables, en el idioma original de cada fuente (amplía D-011)

Feature: Chunking multiidioma

  Como desarrollador
  Quiero dividir los documentos cargados en chunks de ~512 tokens con solapamiento del 10-20%,
  preservando el idioma original de cada fuente
  Para optimizar la precisión de retrieval sin perder contexto ni forzar traducción

  Scenario: Chunking de un documento largo
    Given un documento cargado con más de 512 tokens de texto
    When se aplica el chunker
    Then cada chunk generado tiene un tamaño aproximado de 512 tokens
    And el solapamiento entre chunks consecutivos está entre el 10% y el 20%

  Scenario: Metadatos de trazabilidad conservados en el chunk
    Given un documento cargado con metadatos de origen
    When se aplica el chunker
    Then cada chunk conserva los metadatos "source", "language", "date_indexed" y "profile"

  Scenario: Documento más corto que el tamaño de chunk
    Given un documento cargado con menos de 512 tokens de texto
    When se aplica el chunker
    Then se genera un único chunk con el contenido completo del documento

  Scenario: El idioma del chunk respeta el idioma original de la fuente
    Given un documento en español cargado desde una fuente no inglesa
    When se aplica el chunker
    Then el metadato "language" de cada chunk refleja el español
    And el texto del chunk no se traduce al inglés
