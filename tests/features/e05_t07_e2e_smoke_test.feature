# E-05 T-07 — Smoke test manual E2E de la interfaz conversacional (antes T-06)
# Tipo: Configuración manual — verificación sin tests automatizados (D-030)
# Ampliado (D-031/D-032) para cubrir signup y login con Google, no solo el chat.
# Mismo patrón que E-06 T-07: cierre de épica con verificación real, no mocks.

Feature: Smoke test manual E2E de la interfaz conversacional

  Como responsable del proyecto AIIP
  Quiero verificar manualmente que la interfaz completa funciona con el pipeline real y datos reales de la KB,
  incluyendo signup y login con Google
  Para validar que E-05 cumple sus criterios antes de cerrarla

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: Preguntas representativas del perfil familiar funcionan end-to-end
    Given la app familiar corriendo localmente con la KB real indexada
    When pruebo las preguntas representativas CU-01 a CU-06 del PRD
    Then el streaming, los pasos intermedios, las fuentes citadas y el tono se comportan según lo esperado

  Scenario: Signup y login con Google funcionan de extremo a extremo en el navegador
    Given la app familiar corriendo localmente
    When me registro con un email nuevo y, por separado, inicio sesión con una cuenta de Google real
    Then ambos flujos terminan con una sesión de chat activa y el perfil correcto en Supabase

  Scenario: Verificación en móvil y escritorio
    Given la app familiar corriendo localmente
    When la abro en escritorio y en un viewport móvil
    Then la interfaz es usable y coherente con el theming en ambos casos, incluyendo login y signup

  Scenario: El resultado queda documentado para revisión
    Given las preguntas y comprobaciones de los escenarios anteriores
    When completo la verificación
    Then dejo constancia en tests/results/e05_t07_smoke_test_results.md
    And confirmo si E-05 está lista para cerrarse
