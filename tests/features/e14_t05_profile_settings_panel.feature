# E-14 T-05 — Edición de perfil desde ajustes
# Criterio: falta un sitio para corregir/completar el perfil sin depender del flujo de chat de
# T-03 (ej. si se saltó una pregunta, o cambia el diagnóstico). Primer uso de cl.ChatSettings/
# @cl.on_settings_update en el proyecto (no hay precedente en main_family.py).
#
# Decisión de epic-start (23 jul 2026): se descartó meter la opción dentro del desplegable
# nativo de usuario — investigado y confirmado que es un portal de Radix UI sin id fijo, que se
# desmonta en document.body en cada apertura/cierre; el único ítem ("Logout") no tiene id ni
# data-testid. Cualquier inserción ahí necesitaría un MutationObserver reinsertándola en cada
# apertura, frágil ante cualquier cambio de Chainlit. En su lugar: cl.ChatSettings (mecanismo
# nativo, soporta valores prellenados) + reposicionar su icono con custom_css (config oficial
# de Chainlit, chainlit/config.py — el icono tiene id estable "chat-settings-open-modal", no
# una clase hasheada). La investigación de integrarlo en el desplegable nativo queda como nota
# no bloqueante, con tiempo acotado — ver último escenario.

Feature: Edición de perfil desde el panel de ajustes

  Como usuario con perfil guardado (completo o no)
  Quiero ver y modificar mis datos desde un panel de ajustes
  Para corregir o completar mi información sin depender de que el chat me lo vuelva a preguntar

  Background:
    Given la app Chainlit del perfil familiar está inicializada
    And un usuario autenticado

  Scenario: El panel de ajustes muestra los datos actuales prellenados
    Given un usuario con user_name, patient_name, patient_diagnosis, patient_age y
      patient_context ya guardados en profiles
    When abre el panel de ajustes (cl.ChatSettings)
    Then ve un campo por cada dato, con su valor actual como "initial"/"initial_value"

  Scenario: Guardar cambios en el panel los persiste en profiles
    Given el panel de ajustes abierto con datos prellenados
    When el usuario modifica uno o más campos y guarda
    Then se dispara @cl.on_settings_update con el dict completo de valores
    And profiles se actualiza con los nuevos valores para ese usuario

  Scenario: El panel también sirve para completar un onboarding no terminado
    Given un usuario con "health_data_consent_at" informado pero con patient_diagnosis,
      patient_age o patient_context en NULL (saltó preguntas de T-03)
    When abre el panel de ajustes
    Then puede rellenar ahí los campos que faltan, con el mismo backend que usa T-03
    And guardar desde el panel evita que el chat le vuelva a preguntar esos mismos datos

  Scenario: Un usuario sin consentimiento de datos de salud no ve los campos clínicos en el panel
    Given un usuario con "health_data_consent_at" en NULL
    When abre el panel de ajustes
    Then solo ve el campo de user_name (cuenta), no patient_name/patient_diagnosis/
      patient_age/patient_context
    And no se le fuerza a dar el consentimiento desde este panel (el gate sigue siendo
      responsabilidad de T-02 en on_chat_start)

  # Checklist manual — visual/CSS, no automatizable con pytest-bdd

  Scenario: El icono de ajustes queda reposicionado junto al avatar de usuario
    Given custom_css definido en .chainlit/config.toml apuntando a un fichero en public/
    When se abre la app en el navegador
    Then el icono con id "chat-settings-open-modal" aparece visualmente más cerca del avatar
      de usuario (arriba a la derecha), sin romper su comportamiento nativo de abrir el panel
    And no se han tocado ficheros del bundle de Chainlit (solo config.toml + CSS propio)

  Scenario: Investigación no bloqueante — integrar el acceso dentro del desplegable nativo
    Given el riesgo ya documentado (portal de Radix, sin id fijo, se remonta en cada apertura)
    When se dedica un tiempo acotado a intentar un MutationObserver que reinserte un enlace a
      "Editar perfil" dentro del desplegable nativo
    Then si el resultado es estable y no rompe el comportamiento de "Logout", se documenta y se
      añade
    And si no sale limpio en ese tiempo, T-05 se cierra igualmente con el panel de ajustes +
      icono reposicionado como criterio principal — este escenario no bloquea el cierre
