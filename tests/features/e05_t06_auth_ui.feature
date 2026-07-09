# E-05 T-06 — UI de autenticación en Chainlit: login, signup, recuperación de
# contraseña y login con Google
# Criterio: D-031 (toda la auth vive dentro de Chainlit, sin superficie separada) +
# D-032 (login con Google vía @cl.oauth_callback nativo de Chainlit, sincronizado
# server-side con Supabase; reabre D-014) + D-040 (signup mergeado en
# password_auth_callback con "Confirm email" activado, rutas /auth/forgot-password
# y /auth/confirm compartidas registradas sobre la misma app de Chainlit, custom_js
# para la descubribilidad del enlace de recuperación, y nombre pedido en el chat
# tras el primer login en vez de en el formulario de signup)
# TDD parcial (D-030): la lógica de wiring, sincronización y las rutas propias son
# testeables sin browser; el intercambio real de tokens con Google y los correos de
# confirmación/recuperación se verifican manualmente en T-07.

Feature: Autenticación en Chainlit — login, signup, recuperación de contraseña y Google

  Como familiar sin cuenta todavía, con cuenta pero contraseña olvidada, o que
  prefiere entrar con Google
  Quiero poder registrarme, recuperar el acceso a mi cuenta, y poder iniciar
  sesión con mi cuenta de Google
  Para acceder a AIIP sin depender solo de recordar usuario y contraseña

  Background:
    Given la app Chainlit del perfil familiar está inicializada

  # ── Login y signup mergeados (password_auth_callback) ──────────────────

  Scenario: Login con credenciales correctas de una cuenta existente autentica
    Given un usuario ya registrado y confirmado, con email y contraseña válidos
    When envía esas credenciales en el formulario de login
    Then login() devuelve sesión y role
    And se autentica sin llegar a intentar signup()

  Scenario: Credenciales de un email sin cuenta previa disparan signup automático
    Given un email y contraseña sin cuenta previa en Supabase Auth
    When se envían en el mismo formulario de login
    Then login() falla y se intenta signup() con las mismas credenciales
    And signup() crea el usuario y su perfil con el role de la app

  Scenario: Signup con "Confirm email" activado no autentica hasta confirmar
    Given un signup recién creado cuya cuenta todavía no ha sido confirmada por email
    When signup() se completa sin sesión activa (email de confirmación pendiente)
    Then password_auth_callback devuelve None
    And no se crea un perfil duplicado en intentos posteriores con las mismas credenciales antes de confirmar

  Scenario: Email ya registrado con contraseña incorrecta no duplica el perfil
    Given un email que ya tiene cuenta en Supabase Auth
    When se envían esas credenciales con una contraseña incorrecta
    Then login() falla y el signup() de respaldo también falla por email duplicado
    And no se crea un perfil duplicado
    And password_auth_callback devuelve None sin romper la app

  # ── Recuperación de contraseña (/auth/forgot-password, /auth/confirm) ──

  Scenario: Solicitar recuperación con un email registrado dispara el envío del correo
    Given un email con cuenta existente en Supabase Auth
    When se envía por POST a /auth/forgot-password
    Then se llama a reset_password_for_email(email)
    And la respuesta no revela si el email tiene cuenta o no (evita enumeración)

  Scenario: Solicitar recuperación con un email no registrado responde igual que con uno registrado
    Given un email sin cuenta en Supabase Auth
    When se envía por POST a /auth/forgot-password
    Then la respuesta es indistinguible de la del escenario anterior

  Scenario: Confirmar un token de recuperación válido permite fijar una nueva contraseña
    Given un token_hash de tipo "recovery" válido y no usado
    When se accede a /auth/confirm con ese token_hash y type=recovery
    Then verify_otp() devuelve una sesión válida
    And se muestra el formulario para establecer la nueva contraseña

  Scenario: Enviar la nueva contraseña tras verificar el token la actualiza
    Given una sesión válida obtenida tras verify_otp() de tipo "recovery"
    When se envía la nueva contraseña por POST a /auth/confirm
    Then update_user() actualiza la contraseña de ese usuario
    And un login posterior con la nueva contraseña autentica correctamente

  Scenario: Confirmar un token de signup válido activa la cuenta
    Given un token_hash de tipo "signup" válido y no usado
    When se accede a /auth/confirm con ese token_hash y type=signup
    Then verify_otp() confirma la cuenta
    And se muestra la confirmación con enlace a /login, sin autenticar automáticamente en Chainlit

  Scenario: Token de confirmación inválido o caducado no autentica
    Given un token_hash caducado, ya usado, o inexistente
    When se accede a /auth/confirm con ese token_hash
    Then verify_otp() falla
    And se muestra un error claro sin exponer detalles internos de Supabase

  # ── Login con Google (@cl.oauth_callback) ───────────────────────────────

  Scenario: Login con Google vía oauth_callback nativo de Chainlit
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

  Scenario: Primer login con Google guarda el nombre sin preguntarlo nunca
    Given un usuario nuevo que se autentica con Google, con nombre disponible en raw_user_data
    When se crea su usuario y perfil
    Then su nombre se guarda en user_metadata.full_name
    And on_chat_start no le pide el nombre por chat

  # ── Nombre para personalización (pedido en el chat, no en el formulario) ─

  Scenario: Primer login sin nombre guardado lo pide en el chat
    Given un usuario recién autenticado (login, signup confirmado, u OAuth) sin full_name en user_metadata
    When se dispara on_chat_start
    Then se pide el nombre con cl.AskUserMessage antes del saludo y la bienvenida
    And la respuesta se guarda en user_metadata.full_name vía update_user_by_id()

  Scenario: Login posterior con nombre ya guardado no vuelve a preguntar
    Given un usuario con full_name ya presente en user_metadata
    When se dispara on_chat_start
    Then no se pide el nombre
    And el saludo usa full_name

  Scenario: Saludo sin nombre guardado se muestra sin nombre, no con el email
    Given un usuario sin full_name en user_metadata (no respondió a cl.AskUserMessage a tiempo)
    When se genera el saludo
    Then se muestra el saludo genérico sin nombre
    And no se usa identifier (email) como sustituto

  # ── Checklist manual — no automatizable sin navegador ni correo real ────

  Scenario: El botón de login con Google es visible y accesible en la pantalla de login
    Given abro la app familiar
    When busco la opción de login con Google
    Then el botón o enlace es visible y usa el theming de la app

  Scenario: El enlace "¿Olvidaste tu contraseña?" es visible y navega al formulario
    Given abro la pantalla de login de la app familiar
    When busco la opción de recuperar contraseña, inyectada vía custom_js
    Then el enlace es visible y lleva a /auth/forgot-password

  Scenario: El correo de confirmación de signup llega y su enlace confirma la cuenta
    Given me registro con un email real
    When reviso mi bandeja de entrada
    Then recibo el correo de confirmación con el enlace generado desde la plantilla de Supabase
    And al pulsarlo mi cuenta queda confirmada y puedo iniciar sesión

  Scenario: El correo de recuperación llega y su enlace lleva al formulario de nueva contraseña
    Given solicito recuperar mi contraseña con un email real
    When reviso mi bandeja de entrada
    Then recibo el correo de recuperación con el enlace generado desde la plantilla de Supabase
    And al pulsarlo veo el formulario de nueva contraseña, no un error

  Scenario: Cancelar el consentimiento de Google devuelve al login sin romper la app
    Given inicio el flujo de login con Google
    When cancelo el consentimiento en la pantalla de Google
    Then vuelvo a la pantalla de login de Chainlit
    And no se crea ningún usuario ni perfil

  Scenario: auth/style.css retirado, sin fichero huérfano
    Given design/auth/style.css apuntaba a clases de Supabase Auth UI sin consumidor real
    When se revisa el repositorio tras esta tarea
    Then el fichero ha sido retirado

  Scenario: Las tres pantallas propias comparten look&feel coherente y sin estilos en línea
    Given /auth/forgot-password, /auth/confirm (signup) y /auth/confirm (recovery)
    When se revisa su HTML y CSS
    Then las tres reutilizan la misma plantilla base (tarjeta, campo de formulario, botón) y los tokens de design/public/tokens.css
    And ninguna usa estilos en línea
    And son visualmente coherentes entre sí y con la pantalla de login nativa de Chainlit
