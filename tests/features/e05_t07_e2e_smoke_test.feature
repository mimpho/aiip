# E-05 T-07 — Smoke test manual E2E de la interfaz conversacional (antes T-06)
# Tipo: Configuración manual — verificación sin tests automatizados (D-030)
# Ampliado (D-031/D-032) para cubrir signup y login con Google, no solo el chat.
# Ampliado de nuevo (task-start, 10 jul 2026) para cubrir recuperación de
# contraseña y confirmación de email por correo (D-040, puntos 2-5), construidas
# en T-06 y nunca verificadas en navegador real — riesgo abierto señalado en D-031.
# Precondición confirmada por Marcos: "Confirm email" activado y las plantillas
# de email ("Confirm signup", "Reset password") reescritas en el dashboard de
# Supabase apuntando a /auth/confirm (D-040, pasos manuales).
# Mismo patrón que E-06 T-07: cierre de épica con verificación real, no mocks.
# Ajustado en vivo durante la propia ejecución del smoke test (10 jul 2026, D-041):
# el paso intermedio de "Documentos consultados" se retiró de la UI (redundante
# con el listado de fuentes de D-026) y se sustituyó por un log server-side
# (logger.info en _answer(), chainlit/main_family.py) — útil para debugging,
# sin valor para el usuario familiar. El Scenario 1 deja de pedir verificación
# visual de "pasos intermedios" y pide en su lugar comprobar el log del servidor.

Feature: Smoke test manual E2E de la interfaz conversacional

  Como responsable del proyecto AIIP
  Quiero verificar manualmente que la interfaz completa funciona con el pipeline real y datos reales de la KB,
  incluyendo signup con confirmación por email, login con Google y recuperación de contraseña
  Para validar que E-05 cumple sus criterios antes de cerrarla

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: Preguntas representativas del perfil familiar funcionan end-to-end
    Given la app familiar corriendo localmente con la KB real indexada
    When pruebo las preguntas representativas CU-01, CU-02, CU-03, CU-05 y CU-06 del PRD (CU-04 fuera de alcance, backlog multimodal)
    Then el streaming, las fuentes citadas y el tono se comportan según lo esperado
    And el log del servidor muestra la línea "Retrieval para..." con los documentos recuperados y su score para cada pregunta (D-041)

  Scenario: Signup con un email nuevo termina en cuenta confirmada y accesible
    Given la app familiar corriendo localmente y un email nuevo sin cuenta previa en Supabase
    When me registro con ese email y contraseña en el formulario de login (password_auth_callback dispara signup())
    Then recibo el correo "Confirm signup" con un enlace a /auth/confirm?type=signup
    And al abrir el enlace veo la confirmación de cuenta con enlace a /login, sin autenticar automáticamente
    And un login posterior con esas credenciales autentica correctamente
    And en ese primer login se me pide el nombre por chat (_ensure_full_name, D-040 punto 7)
    And al responder, el nombre se persiste y aparece en el saludo de una sesión de chat posterior

  Scenario: Login con Google funciona de extremo a extremo en el navegador
    Given la app familiar corriendo localmente
    When inicio sesión con una cuenta de Google real desde el botón de login
    Then @cl.oauth_callback completa el intercambio con Google y sincroniza el usuario en Supabase
    And termino en una sesión de chat activa con el perfil correcto (role de la app)

  Scenario: Recuperación de contraseña funciona de extremo a extremo en el navegador
    Given una cuenta ya confirmada y el enlace "¿Olvidaste tu contraseña?" descubrible desde la pantalla de login (custom_js, D-040)
    When solicito la recuperación desde /auth/forgot-password con ese email
    Then recibo el correo "Reset password" con un enlace a /auth/confirm?type=recovery
    And al abrir el enlace puedo fijar una nueva contraseña
    And un login posterior con la nueva contraseña autentica correctamente, y la antigua ya no funciona

  Scenario: Verificación en móvil y escritorio
    Given la app familiar corriendo localmente
    When la abro en escritorio y en un viewport móvil, incluyendo login, signup, /auth/forgot-password y /auth/confirm
    Then la interfaz es usable y coherente con el theming en ambos casos en todas esas pantallas

  Scenario: El resultado queda documentado para revisión
    Given las preguntas y comprobaciones de los escenarios anteriores
    When completo la verificación
    Then dejo constancia en tests/results/e05_t07_smoke_test_results.md
    And confirmo si E-05 está lista para cerrarse
