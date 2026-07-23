# E-14 T-04 — Migración de full_name/user_name + nombre completo en el desplegable
# Criterio: D-040 guardó el nombre del usuario en user_metadata.full_name como solución
# provisional (el formulario de signup de Chainlit no admite un campo de nombre). E-08
# (nota de alcance, 9 jul 2026) ya señalaba migrarlo "a esa estructura propia [de perfil],
# no dejarlo repartido entre Auth y profiles" cuando esta épica se abordara — es lo que hace
# esta tarea.
#
# Hallazgo de epic-start (23 jul 2026): el desplegable nativo de usuario de Chainlit (arriba a
# la derecha) muestra el email en vez del nombre porque cl.User(...) nunca rellena
# display_name en los callbacks de login/signup/oauth de main_family.py — cae al fallback de
# identifier (el email). Chainlit sí soporta display_name (chainlit/user.py) y el propio
# componente del menú lo usa si está presente. No hay forma soportada de añadir opciones a
# ese menú (investigado en epic-start), pero sí de corregir qué texto muestra.

Feature: Migración de full_name a profiles y nombre completo en el desplegable

  Como usuario ya registrado antes de E-14
  Quiero que mi nombre se lea/escriba en profiles y se muestre completo en el menú de usuario
  Para dejar de tener el dato repartido entre Auth y profiles, y ver mi nombre real, no mi email

  Background:
    Given la app Chainlit del perfil familiar está inicializada

  Scenario: Usuario existente con full_name en user_metadata recibe backfill a profiles
    Given un usuario con "full_name" ya presente en user_metadata (D-040) y "user_name" en
      NULL en profiles
    When se dispara on_chat_start
    Then "user_name" se rellena en profiles con el valor de user_metadata.full_name
    And no se le vuelve a pedir el nombre por chat

  Scenario: Usuario nuevo sin nombre guardado lo pide y lo escribe directamente en profiles
    Given un usuario recién autenticado sin "user_name" en profiles ni "full_name" en
      user_metadata
    When se dispara on_chat_start
    Then se pide el nombre con cl.AskUserMessage (mismo mecanismo que D-040)
    And la respuesta se guarda en profiles.user_name, no en user_metadata

  Scenario: display_name se rellena en cada login con password
    Given un usuario que inicia sesión o se registra vía password_auth_callback, con
      "user_name" ya disponible en profiles
    When se construye el cl.User de la sesión
    Then cl.User(display_name=...) se rellena con el nombre
    And el desplegable de usuario muestra el nombre, no el email

  Scenario: display_name se rellena también en login con Google
    Given un usuario que inicia sesión vía oauth_callback (Google)
    When se construye el cl.User de la sesión
    Then display_name se rellena igual que en el login con password
    And el comportamiento del menú de usuario es idéntico entre las dos vías de autenticación

  Scenario: Usuario sin nombre aún disponible no muestra el email como sustituto
    Given un usuario autenticado sin "user_name" en profiles (aún no respondió al
      cl.AskUserMessage)
    When se construye el cl.User de esa sesión
    Then display_name queda sin informar y el menú cae a su fallback nativo (identifier)
    And no se fuerza ningún valor incorrecto en display_name
