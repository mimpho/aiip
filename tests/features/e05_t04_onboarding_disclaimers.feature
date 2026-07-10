# E-05 T-04 — Onboarding y disclaimers de seguridad en el chat familiar
# Tipo: Código, sin TDD — rama + PR propia, validación manual (D-030, mismo
# patrón que E06-T07). Implementación en on_chat_start (chainlit/main_family.py,
# ver D-036) — no en chainlit.md.

Feature: Onboarding y disclaimers de seguridad en el chat familiar

  Como familiar
  Quiero ver un mensaje de bienvenida y un recordatorio claro de que AIIP no diagnostica
  Para entender los límites de la herramienta desde el primer momento (PRD 6.1)

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: Mensaje de bienvenida al abrir el chat
    Given abro el chat de la app familiar
    When se inicia la sesión de chat (on_chat_start)
    Then veo un mensaje de bienvenida con tono cercano, propio del perfil familiar
    And el mensaje incluye el recordatorio "AIIP acompaña e informa, nunca diagnostica"
    And el mensaje se repite en cada apertura de chat, no solo la primera vez (D-036)

  Scenario: El tono del recordatorio no es alarmista
    Given leo el mensaje de bienvenida
    When reviso su redacción y su presentación visual
    Then el tono es claro y cercano en la forma, sin restar seriedad al mensaje de fondo
    And el mensaje no usa el color de warning/ámbar reservado a Falso Negativo Cero (D-036, tokens.css)

  Scenario: Preguntas sugeridas bajo el mensaje de bienvenida
    Given abro el chat de la app familiar
    When se inicia la sesión de chat (on_chat_start)
    Then veo una serie de preguntas sugeridas (starters) bajo el mensaje de bienvenida
    And al pulsar una pregunta sugerida, se envía como si la hubiera escrito yo
