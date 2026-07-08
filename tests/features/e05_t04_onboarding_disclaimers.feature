# E-05 T-04 — Onboarding y disclaimers de seguridad en el chat familiar
# Tipo: Configuración manual — verificación sin tests automatizados (D-030)

Feature: Onboarding y disclaimers de seguridad en el chat familiar

  Como familiar
  Quiero ver un mensaje de bienvenida y un recordatorio claro de que AIIP no diagnostica
  Para entender los límites de la herramienta desde el primer momento (PRD 6.1)

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: Mensaje de bienvenida al iniciar sesión por primera vez
    Given inicio sesión por primera vez en la app familiar
    When se abre el chat
    Then veo un mensaje de bienvenida con tono cercano, propio del perfil familiar
    And el mensaje incluye el recordatorio "AIIP acompaña e informa, nunca diagnostica"

  Scenario: El tono del recordatorio no es alarmista
    Given leo el mensaje de bienvenida
    When reviso su redacción
    Then el tono es claro y cercano en la forma, sin restar seriedad al mensaje de fondo
