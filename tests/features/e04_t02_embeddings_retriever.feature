# E-04 T-02 — Embeddings y retriever con ChromaDB
# Criterio: bge-m3 genera embeddings correctos y ChromaDB recupera chunks relevantes

Feature: Embeddings y retriever ChromaDB

  Como sistema RAG
  Quiero embeber una query con bge-m3 y recuperar los chunks más relevantes de ChromaDB
  Para tener el retriever funcional antes de construir el pipeline completo

  Background:
    Given ChromaDB está inicializado con la colección "family_test"

  Scenario: Dimensión correcta del embedding bge-m3
    Given el modelo bge-m3 está cargado
    When genero el embedding del texto "¿Qué es una inmunodeficiencia primaria?"
    Then el vector resultante tiene dimensión 1024

  Scenario: Retrieval con documentos indexados devuelve resultados
    Given la colección "family_test" contiene 10 chunks sobre IDP
    When ejecuto el retriever con la query "síntomas de inmunodeficiencia"
    Then devuelve entre 1 y 5 chunks
    And cada chunk tiene un score de similitud mayor que 0.0

  Scenario: Retrieval cross-lingual castellano sobre chunks en inglés
    Given la colección "family_test" contiene chunks en inglés sobre primary immunodeficiency
    When ejecuto el retriever con la query en castellano "¿cuáles son los síntomas?"
    Then devuelve al menos 1 chunk relevante

  Scenario: Retrieval con colección vacía devuelve lista vacía sin excepción
    Given la colección "family_test" está vacía
    When ejecuto el retriever con cualquier query
    Then devuelve una lista vacía
    And no se lanza ninguna excepción
