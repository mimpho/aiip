# E-05 T-06 — UI de autenticación en Chainlit: signup + login Google + fusión de auth/style.css
# Criterio: D-031 (toda la auth vive dentro de Chainlit, sin superficie separada) +
# D-032 (login con Google vía @cl.oauth_callback nativo de Chainlit, sincronizado
# server-side con Supabase; reabre D-014)
# TDD parcial (D-030): la lógica de wiring y sincronización es testeable sin browser;
# el intercambio real de tokens con Google en el navegador se verifica manualmente en T-07.

Feature: UI de autenticación en Chainlit — signup y login con Google

  Como familiar sin cuenta todavía, o que prefiere entrar con Google
  Quiero poder registrarme y quiero poder iniciar sesión con mi cuenta de Google desde el chat
  Para acceder a AIIP sin depender solo de usuario y contraseña

  Background:
    Given la app Chainlit del perfil familiar está inicializada

  Scenario: Signup desde el chat crea el usuario y su perfil
    Given un email y contraseña válidos, sin cuenta previa
    When se invoca la acción de signup desde la UI de Chainlit
    Then se llama a signup() con ese email, contraseña y el role de la app
    And el usuario queda autenticado tras el registro, sin necesidad de un segundo login manual

  Scenario: Signup con email ya registrado muestra un error legible
    Given un email que ya tiene cuenta en Supabase Auth
    When se invoca la acción de signup desde la UI de Chainlit con ese email
    Then se captura la excepción de email duplicado
    And se muestra un mensaje de error legible en español, sin romper la sesión de chat

  Scenario: Login con Google via oauth_callback nativo de Chainlit
    Given el usuario completa el flujo de Google gestionado por Chainlit (@cl.oauth_callback)
    When Chainlit recibe el perfil de Google ya verificado (raw_user_data)
    Then se busca o crea el usuario correspondiente en auth.users de Supabase por email (Admin API)
    And se obtiene o crea su perfil con el role de la app
    And se devuelve un cl.User válido para la sesión de Chainlit

  Scenario: Segundo login con Google del mismo usuario no duplica el perfil
    Given un usuario que ya inició sesión con Google anteriormente
    When vuelve a autenticarse con Google
    Then no se crea un nuevo usuario en auth.users ni un perfil duplicado
    And se reutiliza el perfil y role existentes

  # Checklist manual — no automatizable sin navegador real
  Scenario: El botón de login con Google es visible y accesible en el chat
    Given abro la app familiar
    When busco la opción de login con Google
    Then el botón o enlace es visible y usa el theming de la app

  Scenario: auth/style.css queda resuelto, sin fichero huérfano
    Given design/auth/style.css existía sin ningún consumidor (D-031)
    When se revisa el repositorio tras esta tarea
    Then su contenido relevante está fusionado en design/public/style.css, o el fichero ha sido retirado
