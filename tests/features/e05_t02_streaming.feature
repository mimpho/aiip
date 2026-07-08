# E-05 T-02 — Streaming nativo de tokens
# Criterio: la respuesta se emite progresivamente; el filtro de seguridad (D-019) se
# aplica sobre el texto completo ensamblado y se añade como fragmento final, nunca
# reescribe ni intercala contenido en medio del streaming (D-030).

Feature: Streaming nativo de tokens en la respuesta del chat

  Como familiar
  Quiero ver la respuesta aparecer progresivamente mientras se genera
  Para tener una experiencia de chat natural, sin esperar un bloque de texto

  Background:
    Given RAGPipeline expone un modo de generación en streaming

  Scenario: Los tokens de la respuesta se emiten progresivamente
    Given una pregunta sin señales de alarma
    When se invoca la generación en streaming
    Then se reciben varios fragmentos de texto en orden, no un único bloque final
    And la concatenación de los fragmentos reconstruye la respuesta completa del LLM

  Scenario: El recordatorio de seguridad se añade tras completar el streaming
    Given una pregunta con una señal de alarma detectada por check_alarm_signals
    When el streaming del cuerpo de la respuesta termina
    Then se añade el recordatorio de consulta médica de apply_safety_filter como fragmento final
    And ese recordatorio no aparece intercalado en medio del streaming del cuerpo

  Scenario: Afirmación tranquilizadora detectada solo tras completar el streaming
    Given una pregunta sin señales de alarma en la query
    And el LLM genera en streaming una respuesta que contiene la frase "no es grave"
    When el streaming termina y se ensambla el texto completo
    Then apply_safety_filter añade el recordatorio de consulta médica al final

  Scenario: Streaming sin necesidad de filtro no añade texto adicional
    Given una pregunta informativa sin alarma y sin frases tranquilizadoras en la respuesta
    When el streaming termina
    Then no se añade ningún recordatorio adicional al final de la respuesta

  Scenario: Error durante el streaming no rompe la sesión de chat
    Given una pregunta sin señales de alarma
    When el streaming lanza una excepción antes de completarse, por ejemplo porque el LLM no está disponible
    Then el chat muestra un mensaje de error legible en español
    And la sesión de chat sigue activa para la siguiente pregunta

  Scenario: El listado de fuentes se añade tras el streaming, después del recordatorio de seguridad si aplica
    Given una pregunta cuyos documentos recuperados tienen metadatos de fuente
    When el streaming termina y se aplica apply_safety_filter
    Then se añade el listado de fuentes como fragmento final
    And si hay recordatorio de seguridad, el listado de fuentes aparece después de él
