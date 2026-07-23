# E-14 T-03 — Flujo de onboarding por chat
# Criterio: tras el consentimiento de T-02, se completa el perfil de paciente que E-14 usa en
# T-06 para contextualizar respuestas. Mismo patrón que _ensure_full_name (D-040): se pregunta
# por chat lo que falte, no se repite una vez respondido.
#
# Decisión de epic-start (23 jul 2026): distinguir "quién chatea" (user_name) de "de quién son
# los datos clínicos" (patient_name) evita asumir que quien escribe es el paciente — ya
# advertido en prompts/system_prompt_family.txt (líneas 41-46), pero hasta ahora nunca
# preguntado explícitamente. Referirse al paciente por su nombre real en vez de "el paciente"
# es una decisión deliberada de tono (momento delicado para la familia), no solo estética.
#
# Revisión de task-start (24 jul 2026, D-089): "user_name" para el caso "sobre mí" se lee de
# cl.context.session.user.metadata["full_name"] (ya resuelto por _ensure_full_name, D-040),
# no de la columna profiles.user_name — esa la puebla T-04, todavía pendiente. La pregunta
# "¿sobre quién son los datos?" usa cl.AskActionMessage con dos botones, mismo patrón fiable
# que el gate de consentimiento de T-02, en vez de texto libre a interpretar. La validación de
# patient_age (D-088, asignada a esta tarea) se resuelve con una repregunta única.
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
    And un usuario autenticado con "health_data_consent_at" y "full_name" ya informados (T-02, D-040)

  Scenario: Se pregunta primero si los datos son sobre el propio usuario o sobre otra persona
    Given un usuario con "patient_name" en NULL
    When se dispara on_chat_start
    Then se pregunta con cl.AskActionMessage, con botones "Sobre mí" y "Sobre otra persona",
      si los datos son sobre sí mismo o sobre otra persona (ej. su hijo/a)

  Scenario: Si los datos son sobre el propio usuario, no se pregunta un nombre aparte
    Given el usuario pulsa el botón "Sobre mí"
    When se guarda la respuesta
    Then "patient_name" se rellena con el valor de "full_name" en la sesión en curso
      (cl.context.session.user.metadata, D-089), sin preguntar de nuevo

  Scenario: Si los datos son sobre otra persona, se pregunta su nombre
    Given el usuario pulsa el botón "Sobre otra persona"
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

  Scenario: Edad no numérica o fuera de rango se repregunta una vez (D-088, D-089)
    Given "patient_name" ya resuelto
    When se pregunta "patient_age" y la primera respuesta no es un entero válido entre 0 y 120
    Then se informa del error y se repregunta una única vez
    And si la segunda respuesta tampoco es válida, se sigue sin guardar "patient_age"
      (no bloquea el resto del onboarding ni se repregunta hasta el próximo chat)

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
