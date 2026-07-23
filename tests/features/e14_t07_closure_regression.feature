# E-14 T-07 — Cierre: regresión y smoke test end-to-end
# Tipo: cierre de épica — checklist manual + regresión acotada, mismo patrón que E-09 T-06/
# E-11 T-07/E-13 T-04. Verifica el flujo completo integrado, no solo cada tarea por separado.
#
# Contexto: T-06 tocó prompts/system_prompt_family.txt en producción — esta tarea incluye la
# regresión que ese cambio requiere (precedente E-11 T-07, D-070/D-071: no dejarlo para
# "ampliación de alcance a mitad de la tarea de cierre").
#
# D-009 queda parcialmente implementada tras esta épica (gate de consentimiento, T-02) — el
# cierre actualiza docs/security.md para que deje de describirse como "sin implementar".

Feature: Cierre de E-14 — regresión y smoke test end-to-end

  Como responsable del proyecto AIIP
  Quiero verificar el flujo completo de memoria de perfil de principio a fin, y medir el
  impacto del cambio de prompt sobre los casos afectados
  Para cerrar la épica con evidencia, no solo con las tareas individuales en verde

  Scenario: Flujo completo end-to-end sin fallos
    Given un usuario nuevo sin cuenta
    When completa signup, ve el gate de consentimiento de datos de salud (T-02), completa el
      onboarding por chat (T-03, incluyendo la distinción entre quien chatea y de quién son
      los datos), edita un dato desde el panel de ajustes (T-05), y hace una pregunta al chat
    Then cada paso se comporta según lo descrito en su tarea
    And la respuesta final refleja el contexto de perfil (T-06) sin errores

  Scenario: Regresión acotada a los casos afectados por el cambio de prompt
    Given el placeholder profile_context añadido a _PROMPT_TEMPLATE (T-06) y el cambio en
      prompts/system_prompt_family.txt
    When se re-ejecutan los casos de evaluación relevantes (los que tocan tono/tuteo/registro
      familiar, no la suite RAGAS completa)
    Then no hay regresión frente a los resultados de cierre de E-13 en Faithfulness/Answer
      Relevancy para esos casos
    And cualquier cambio se documenta sin suavizar (mismo criterio de transparencia que E-09
      T-05/E-11 T-07)

  Scenario: Usuario sin perfil sigue funcionando igual que antes de E-14
    Given un usuario que rechazó el consentimiento de datos de salud (T-02)
    When usa el chat con normalidad
    Then el comportamiento es indistinguible del pipeline anterior a E-14

  Scenario: docs/security.md refleja que el gate de D-009 ya está implementado
    Given docs/security.md con la sección de protección de datos que documentaba el gate de
      D-009 como "sin implementar"
    When se actualiza tras el cierre de T-02
    Then la sección refleja que el gate está implementado, con referencia a D-009 y a esta
      épica

  Scenario: Marcos confirma el cierre de la épica
    Given todos los escenarios anteriores completados
    When Marcos los revisa
    Then confirma el cierre de E-14 o señala qué falta antes de darla por completada
