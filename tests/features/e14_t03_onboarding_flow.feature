# E-14 T-03 — Flujo de onboarding por chat
# Criterio: tras el consentimiento de T-02, se completa el perfil de paciente que E-14 usa en
# T-06 para contextualizar respuestas. Mismo patrón que _ensure_full_name (D-040): se pregunta
# por chat lo que falte, no se repite una vez respondido.
#
# Decisión de epic-start (23 jul 2026): distinguir "quién chatea" (user_name, ya cubierto por
# D-040) de "de quién son los datos clínicos" (patient_name) evita asumir que quien escribe es
# el paciente — ya advertido en prompts/system_prompt_family.txt (líneas 41-46), pero hasta
# ahora nunca preguntado explícitamente. Referirse al paciente por su nombre real en vez de
# "el paciente" es una decisión deliberada de tono (momento delicado para la familia), no solo
# estética.
#
# El escenario "role=professional nunca se le pregunta" se descartó en epic-start: hoy
# chainlit/main_professional.py tiene el login bloqueado siempre (auth_callback devuelve None),
# así que no hay forma de llegar a on_chat_start con ese role — no hay nada que testear.

Feature: Onboarding de datos del paciente por chat

  Como usuario familiar con consentimiento de datos de salud ya dado
  Quiero que se me pregunte, por chat, sobre quién son los datos y su diagnóstico/edad/contexto
  Para que el agente pueda usar esa información al contextualizar sus respuestas (T-06)

  Background:
    Given la app Chainlit del perfil familiar está inicializada
    And un usuario autenticado con "health_data_consent_at" ya informado (T-02)

  Scenario: Se pregunta primero si los datos son sobre el propio usuario o sobre otra persona
    Given un usuario con "patient_name" en NULL
    When se dispara on_chat_start
    Then se pregunta con cl.AskUserMessage si el diagnóstico es sobre sí mismo o sobre otra
      persona (ej. su hijo/a)

  Scenario: Si los datos son sobre el propio usuario, no se pregunta un nombre aparte
    Given la pregunta de "¿sobre quién son los datos?" respondida como "sobre mí"
    When se guarda la respuesta
    Then "patient_name" se rellena con el mismo valor que "user_name", sin preguntar de nuevo

  Scenario: Si los datos son sobre otra persona, se pregunta su nombre
    Given la pregunta de "¿sobre quién son los datos?" respondida como "sobre otra persona"
    When se guarda la respuesta
    Then se pregunta el nombre de esa persona con cl.AskUserMessage
    And la respuesta se guarda en "patient_name"

  Scenario: Diagnóstico, edad y contexto se piden por el nombre del paciente, no como "el paciente"
    Given "patient_name" ya resuelto (propio usuario u otra persona)
    When se preguntan diagnóstico, edad y contexto pendientes
    Then las preguntas usan el nombre real (ej. "¿qué diagnóstico tiene Lucía?"), nunca la
      palabra "paciente"
    And las respuestas se guardan en "patient_diagnosis" (texto libre, sin validar contra
      ninguna lista cerrada), "patient_age" y "patient_context"

  Scenario: Solo se pregunta lo que falte
    Given un usuario con "patient_name" y "patient_diagnosis" ya guardados, pero
      "patient_age" y "patient_context" en NULL
    When se dispara on_chat_start
    Then solo se preguntan "patient_age" y "patient_context"
    And no se repiten las preguntas ya respondidas

  Scenario: Perfil completo no vuelve a preguntarse
    Given un usuario con "patient_name", "patient_diagnosis", "patient_age" y
      "patient_context" ya informados
    When se dispara on_chat_start
    Then no se pregunta nada de onboarding
    And se pasa directamente al saludo y la bienvenida
