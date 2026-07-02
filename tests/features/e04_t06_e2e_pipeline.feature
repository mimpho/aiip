# E-04 T-06 — Pipeline end-to-end y tests de integración
# Criterio: el flujo completo query→respuesta funciona con LLM real (temperatura 0)

Feature: Pipeline RAG end-to-end

  Como sistema completo
  Quiero que el flujo query → detect_lang → embed → retrieve → generate → safety → respuesta
  funcione de extremo a extremo
  Para tener el pipeline E-04 cerrado y listo para E-05 y E-06

  Background:
    Given el entorno está correctamente configurado con GEMINI_API_KEY y CHROMA_PATH
    And ChromaDB contiene la colección "familias_test" con fixtures de IDP

  Scenario: Pipeline completo — query en castellano produce respuesta en castellano
    Given el usuario envía la query "¿qué es una inmunodeficiencia primaria?"
    When el pipeline procesa la query completa
    Then la respuesta no está vacía
    And la respuesta está en castellano
    And no se lanza ninguna excepción

  Scenario: Pipeline completo — Falso Negativo Cero preservado end-to-end
    Given el usuario describe síntomas de alarma "fiebre muy alta y dificultad para respirar"
    When el pipeline procesa la query completa
    Then la respuesta final incluye derivación a consulta médica
    And el principio de Falso Negativo Cero no ha sido comprometido en ninguna etapa

  Scenario: Pipeline completo — query en inglés produce respuesta en inglés
    Given el usuario envía la query "what is a primary immunodeficiency?"
    When el pipeline procesa la query completa
    Then la respuesta está en inglés

  Scenario: Fallo claro cuando ChromaDB no está disponible
    Given CHROMA_PATH apunta a una ruta inexistente
    When el pipeline intenta recuperar chunks
    Then el pipeline falla con un error claro que menciona ChromaDB
    And el error no es silencioso

  Scenario: Fallo claro cuando GEMINI_API_KEY es inválida
    Given GEMINI_API_KEY tiene un valor inválido
    When el pipeline llama al LLM
    Then se lanza una excepción de autenticación
    And el pipeline no produce una respuesta silenciosamente vacía
