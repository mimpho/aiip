# E-14 T-05 — Edición de perfil desde ajustes
# Criterio: falta un sitio para corregir/completar el perfil sin depender del flujo de chat de
# T-03 (ej. si se saltó una pregunta, o cambia el diagnóstico). Primer uso de cl.ChatSettings/
# @cl.on_settings_update en el proyecto (no hay precedente en main_family.py).
#
# Actualizado en task-start (25 jul 2026, D-092) sobre el draft de epic-start (23 jul 2026):
# - Icono de ajustes: no custom_css (el id "chat-settings-open-modal" solo existe en la ubicación
#   por defecto, junto al chat input) — chat_settings_location = "sidebar" en config.toml lo
#   coloca de forma nativa junto al avatar, con id propio "chat-settings-header-button".
# - Desplegable de usuario: deja de ser "investigación no bloqueante" y pasa a criterio real.
#   El componente nativo solo pinta una línea (display_name o, si no hay, identifier/email) —
#   nunca las dos. Se inyecta un bloque de dos líneas (nombre en --font-display/Merriweather 500
#   + email) leyendo de GET /user (endpoint nativo de Chainlit), con MutationObserver para
#   detectar la apertura del portal — mismo patrón que el theme-toggle en custom.js.
#
# Limitación aceptada (25 jul 2026, QA manual, ampliación de D-092): display_name viaja embebido en
# el JWT de sesión, emitido solo en el login — un cambio de nombre (onboarding o panel de T-05) no
# se refleja en avatar/desplegable hasta el siguiente login real (sesión de hasta 15 días,
# user_session_timeout). Se descarta construir un endpoint de refresco de sesión; se acepta la
# espera al siguiente login como comportamiento esperado, no un bug.

Feature: Edición de perfil desde el panel de ajustes

  Como usuario con perfil guardado (completo o no)
  Quiero ver y modificar mis datos desde un panel de ajustes
  Para corregir o completar mi información sin depender de que el chat me lo vuelva a preguntar

  Background:
    Given la app Chainlit del perfil familiar está inicializada
    And un usuario autenticado

  Scenario: El panel de ajustes muestra los datos actuales prellenados
    Given un usuario con user_name, patient_name, patient_diagnosis, patient_age y patient_context ya guardados en profiles
    When abre el panel de ajustes (cl.ChatSettings)
    Then ve un campo por cada dato, con su valor actual como "initial"

  Scenario: Guardar cambios en el panel los persiste en profiles
    Given el panel de ajustes abierto con datos prellenados
    When el usuario modifica uno o más campos y guarda
    Then se dispara @cl.on_settings_update con el dict completo de valores
    And profiles se actualiza con los nuevos valores para ese usuario
    And el usuario ve un mensaje de confirmación de que el perfil se ha actualizado

  Scenario: patient_age fuera de rango no se persiste, el resto de campos sí
    Given el panel de ajustes abierto con datos prellenados
    When el usuario guarda con patient_age fuera de 0-120
    Then ese campo no se persiste en profiles (se mantiene el valor anterior)
    And el resto de campos modificados sí se guardan
    And el usuario ve un mensaje de error específico sobre patient_age

  Scenario: El panel también sirve para completar un onboarding no terminado
    Given un usuario con "health_data_consent_at" informado pero con patient_diagnosis, patient_age o patient_context en NULL (saltó preguntas de T-03)
    When abre el panel de ajustes
    Then puede rellenar ahí los campos que faltan, con el mismo backend que usa T-03
    And guardar desde el panel evita que el chat le vuelva a preguntar esos mismos datos

  Scenario: Un usuario sin consentimiento de datos de salud no ve los campos clínicos en el panel
    Given un usuario con "health_data_consent_at" en NULL
    When abre el panel de ajustes
    Then solo ve el campo de user_name (cuenta), no patient_name/patient_diagnosis/patient_age/patient_context
    And no se le fuerza a dar el consentimiento desde este panel (el gate sigue siendo responsabilidad de T-02 en on_chat_start)

  # Checklist manual — visual/CSS/JS, no automatizable con pytest-bdd

  Scenario: El icono de ajustes queda visible junto al avatar de usuario
    Given "chat_settings_location = sidebar" en chainlit/family/.chainlit/config.toml
    When se abre la app en el navegador
    Then el botón con id "chat-settings-header-button" aparece en la fila del header, inmediatamente antes del botón de usuario ("user-nav-button")
    And no se ha tocado ningún fichero del bundle de Chainlit ni CSS/JS propio — solo config.toml

  Scenario: El desplegable de usuario muestra nombre (serifa) y email a la vez
    Given un usuario cuyo display_name se resuelve correctamente (profiles.user_name o user_metadata.full_name informados)
    When abre el desplegable de usuario (clic en el avatar)
    Then ve el nombre en la tipografía --font-display (Merriweather, peso 500) en la línea superior, y el email debajo, sin depender de qué pinte Chainlit de forma nativa
    And el comportamiento de "Cerrar sesión" no se ve afectado

  Scenario: El desplegable de usuario degrada con solo el email si no hay nombre resuelto
    Given un usuario sin display_name resuelto (profiles.user_name y user_metadata.full_name ambos vacíos)
    When abre el desplegable de usuario
    Then ve solo el email, sin una línea de nombre vacía o rota
