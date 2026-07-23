# E-14 T-02 — Gate de consentimiento de datos de salud
# Criterio: D-009 (RGPD Art. 9, datos de salud como categoría especial) diseñó este gate en
# julio de 2026 y quedó documentado sin implementar — "se documenta aquí para que la próxima
# vez que se aborde (posiblemente junto con el resto de E-08, onboarding) no se parta de
# cero". E-14 es esa próxima vez.
#
# Decisión de epic-start (23 jul 2026): si el usuario rechaza el consentimiento, el chat sigue
# funcionando exactamente igual que hoy, sin onboarding de datos de salud — nunca se bloquea
# el acceso a información de seguridad por un consentimiento no dado (mismo espíritu que
# Falso Negativo Cero, D-002). El gate vive en on_chat_start, después de la autenticación y
# antes del saludo — igual que _ensure_full_name (D-040), pero antes que ella en el flujo,
# porque el nombre de cuenta no es un dato de salud y no necesita este gate.

Feature: Gate de consentimiento de datos de salud antes del onboarding

  Como usuario que abre el chat de AIIP
  Quiero que se me pida consentimiento explícito antes de que se me pidan datos de salud
  Para que el tratamiento de esa categoría especial de datos tenga base legal (D-009)

  Background:
    Given la app Chainlit del perfil familiar está inicializada
    And un usuario ya autenticado (login, signup confirmado, u OAuth)

  Scenario: Primer chat sin consentimiento registrado muestra el gate antes del saludo
    Given un usuario con "health_data_consent_at" en NULL
    When se dispara on_chat_start
    Then se muestra el texto de consentimiento de tratamiento de datos de salud antes de
      cualquier saludo o mensaje de bienvenida
    And se requiere una acción afirmativa real (no basta con seguir escribiendo)

  Scenario: Aceptar el consentimiento lo registra una sola vez
    Given el gate de consentimiento visible
    When el usuario confirma con la acción afirmativa
    Then "health_data_consent_at" se actualiza con la marca de tiempo actual
    And el flujo continúa hacia el onboarding de T-03

  Scenario: Chat posterior con consentimiento ya registrado no repite el gate
    Given un usuario con "health_data_consent_at" ya informado
    When se dispara on_chat_start
    Then no se muestra el gate de consentimiento
    And se pasa directamente a comprobar si falta algún dato de onboarding (T-03)

  Scenario: Rechazar el consentimiento no bloquea el chat
    Given el gate de consentimiento visible
    When el usuario lo rechaza o lo cierra sin confirmar
    Then "health_data_consent_at" permanece en NULL
    And el chat sigue funcionando con el comportamiento de hoy, sin pedir diagnóstico, edad
      ni contexto del paciente
    And en chats posteriores se le vuelve a mostrar el gate (no se asume rechazo permanente)

  Scenario: El gate aplica igual sin importar la vía de autenticación
    Given un usuario que llegó por login con contraseña, por el signup mergeado, o por Google
      OAuth, sin "health_data_consent_at" informado
    When se dispara on_chat_start
    Then el comportamiento del gate es idéntico en los tres casos
