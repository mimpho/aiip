# E-05 T-01 — Integración del pipeline RAG en el chat familiar
# Criterio: el chat invoca RAGPipeline y muestra su respuesta, sin romperse ante errores

Feature: Integración del pipeline RAG en el chat familiar

  Como familiar autenticado
  Quiero escribir una pregunta en el chat y recibir la respuesta generada por el pipeline RAG
  Para poder consultar información sobre IDP sin salir de la interfaz

  Background:
    Given la app Chainlit del perfil familiar está inicializada
    And existe una instancia de RAGPipeline disponible para la sesión

  Scenario: Pregunta del usuario devuelve la respuesta del pipeline
    Given un usuario autenticado con perfil "family"
    When el usuario envía el mensaje "¿qué es una inmunodeficiencia primaria?"
    Then se invoca RAGPipeline.query() con esa pregunta
    And el chat muestra la respuesta devuelta por el pipeline

  Scenario: Indicador de "escribiendo" mientras se genera la respuesta
    Given un usuario autenticado envía una pregunta
    When el pipeline todavía no ha devuelto la respuesta
    Then el chat muestra un indicador de que el asistente está generando la respuesta

  Scenario: Error del pipeline no rompe la sesión de chat
    Given un usuario autenticado envía una pregunta
    When RAGPipeline.query() lanza una excepción, por ejemplo porque el LLM no está disponible
    Then el chat muestra un mensaje de error legible en español
    And la sesión de chat sigue activa para la siguiente pregunta

  Scenario: Mensajes vacíos no invocan el pipeline
    Given un usuario autenticado
    When envía un mensaje vacío o compuesto solo por espacios
    Then no se invoca RAGPipeline.query()
