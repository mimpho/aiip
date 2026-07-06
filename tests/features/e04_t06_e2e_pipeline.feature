# E-04 T-06 — Pipeline end-to-end y tests de integración
# Criterio: el flujo completo query→respuesta funciona de extremo a extremo
# Estrategia: escenarios deterministas con LLM mockeado + 1 escenario @integration con LLM real (patrón D-018)

Feature: Pipeline RAG end-to-end

  Como sistema completo
  Quiero que el flujo query → detect_lang → embed → retrieve → generate → safety → respuesta
  funcione de extremo a extremo
  Para tener el pipeline E-04 cerrado y listo para E-05 y E-06

  Background:
    Given el entorno está correctamente configurado con GOOGLE_API_KEY y CHROMA_PATH
    And ChromaDB contiene la colección "family_test" con chunks de fixture sobre IDP

  Scenario: Pipeline completo — query en castellano produce respuesta en castellano
    Given el usuario envía la query "¿qué es una inmunodeficiencia primaria?"
    When el pipeline procesa la query completa (LLM mockeado)
    Then la respuesta no está vacía
    And la respuesta está en castellano
    And no se lanza ninguna excepción

  Scenario: Pipeline completo — Falso Negativo Cero preservado end-to-end
    Given el usuario describe síntomas de alarma "fiebre muy alta y dificultad para respirar"
    When el pipeline procesa la query completa (LLM mockeado con respuesta tranquilizadora)
    Then la respuesta final incluye derivación a consulta médica

  Scenario: Pipeline completo — query en inglés produce respuesta en inglés
    Given el usuario envía la query "what is a primary immunodeficiency?"
    When el pipeline procesa la query completa (LLM mockeado)
    Then la respuesta está en inglés

  Scenario: Retrieval sin resultados no bloquea la generación
    Given la colección "family_test" está vacía o CHROMA_PATH no existe
    When el pipeline procesa la query completa (LLM mockeado)
    Then el pipeline genera una respuesta igualmente, con contexto vacío
    And no se lanza ninguna excepción

  Scenario: Propagación de error de autenticación del LLM
    Given GOOGLE_API_KEY tiene un valor inválido
    When el pipeline procesa la query completa
    Then la excepción del generador se propaga sin ser atrapada silenciosamente

  @integration
  Scenario: Pipeline completo con LLM real
    Given GOOGLE_API_KEY es una clave válida y hay conexión a red
    When el pipeline procesa la query real "¿qué es una inmunodeficiencia primaria?"
    Then la respuesta no está vacía
    And no se lanza ninguna excepción
