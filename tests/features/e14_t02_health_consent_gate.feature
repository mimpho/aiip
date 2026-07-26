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
#
# Decisiones de task-start (23 jul 2026): mecanismo `cl.AskActionMessage` (bloquea el chat
# hasta click o timeout), botones "Acepto" / "Ahora no", timeout 300s (más peso que los 120s
# de _ensure_full_name). Lectura/escritura de `health_data_consent_at` vía `get_profile`/
# `update_profile` nuevas en `auth/supabase_client.py` (service key, D-088). Los `Then` que en
# el draft de epic-start apuntaban al onboarding de T-03 se reescriben para apuntar al saludo
# actual — T-03 no existe todavía y no es alcance de esta tarea.
#
# Enmienda (E-14 T-08, D-090 Ronda 2, 24 jul 2026): el orden "gate antes del saludo" de más
# arriba se invierte — el saludo y la bienvenida pasan a enviarse siempre primero en
# on_chat_start, antes de este gate (mejora de UI: la primera impresión del chat ya no
# depende de si hay onboarding pendiente). El orden relativo respecto al resto de datos de
# salud (T-03) no cambia: este gate sigue yendo antes que cualquier pregunta de perfil.

Feature: Gate de consentimiento de datos de salud antes del onboarding

  Como usuario que abre el chat de AIIP
  Quiero que se me pida consentimiento explícito antes de que se me pidan datos de salud
  Para que el tratamiento de esa categoría especial de datos tenga base legal (D-009)

  Background:
    Given la app Chainlit del perfil familiar está inicializada
    And un usuario ya autenticado (login, signup confirmado, u OAuth)

  Scenario: Primer chat sin consentimiento registrado muestra el gate tras el saludo y la bienvenida
    Given un usuario con "health_data_consent_at" en NULL
    When se dispara on_chat_start
    Then el saludo y la bienvenida se muestran primero, y el texto de consentimiento de tratamiento de datos de salud se muestra a continuación (D-090 Ronda 2)
    And se requiere una acción afirmativa real (no basta con seguir escribiendo)

  Scenario: Aceptar el consentimiento lo registra una sola vez
    Given el gate de consentimiento visible
    When el usuario confirma con la acción afirmativa
    Then "health_data_consent_at" se actualiza con la marca de tiempo actual
    And el flujo continúa hacia el saludo (T-03 se enganchará aquí más adelante)

  Scenario: Chat posterior con consentimiento ya registrado no repite el gate
    Given un usuario con "health_data_consent_at" ya informado
    When se dispara on_chat_start
    Then no se muestra el gate de consentimiento
    And se pasa directamente al saludo (T-03 se enganchará aquí más adelante)

  Scenario: Rechazar el consentimiento no bloquea el chat
    Given el gate de consentimiento visible
    When el usuario lo rechaza o lo cierra sin confirmar
    Then "health_data_consent_at" permanece en NULL
    And el chat sigue funcionando con el comportamiento de hoy, sin pedir diagnóstico, edad ni contexto del paciente
    And en chats posteriores se le vuelve a mostrar el gate (no se asume rechazo permanente)

  # Documentación, sin step def dedicado (mismo precedente que los escenarios "checklist
  # manual" de test_e05_t06.py): el gate solo depende de user_id, no de la vía de
  # autenticación, y eso ya queda cubierto por los step defs de los escenarios anteriores.
  Scenario: El gate aplica igual sin importar la vía de autenticación
    Given un usuario que llegó por login con contraseña, por el signup mergeado, o por Google OAuth, sin "health_data_consent_at" informado
    When se dispara on_chat_start
    Then el comportamiento del gate es idéntico en los tres casos
