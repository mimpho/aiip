# E-06 T-04 — Indexer: indexación en ChromaDB
# Criterio: los chunks procesados quedan indexados en la colección "family" de producción, sin duplicados

Feature: Indexación en ChromaDB

  Como desarrollador
  Quiero indexar los chunks procesados en la colección "family" de ChromaDB
  Para que el retriever de E-04 los recupere en producción

  Background:
    Given ChromaDB está inicializado con la colección "family_test" y métrica coseno

  Scenario: Indexación de chunks con embeddings bge-m3
    Given un conjunto de chunks con su embedding bge-m3 ya calculado
    When se ejecuta el indexer
    Then los chunks quedan persistidos en la colección "family_test"
    And cada chunk indexado conserva sus metadatos de origen

  Scenario: Reindexación del mismo documento no duplica chunks
    Given un documento ya indexado previamente en la colección
    When se ejecuta el indexer de nuevo sobre el mismo documento
    Then el número total de chunks de ese documento en la colección no aumenta

  Scenario: Fallo de escritura en ChromaDB se propaga con contexto
    Given una escritura en ChromaDB que falla durante la indexación
    When se ejecuta el indexer
    Then el error se propaga indicando qué documento y qué chunk fallaron
