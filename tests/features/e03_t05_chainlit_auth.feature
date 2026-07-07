# E-03 T-05 — Integración de autenticación en Chainlit
# Criterio: password_auth_callback retorna cl.User con role cuando las
# credenciales son válidas, y None cuando son inválidas.
# Google OAuth queda fuera: el flujo es 100% browser→Supabase, sin hook Python
# en Chainlit (ver D-014). T-04 ya cubre sign_in_with_oauth().

Feature: Integración de autenticación en Chainlit

  Como usuario de AIIP
  Quiero que Chainlit reconozca mi sesión y mi rol al iniciar sesión
  Para que el pipeline futuro (E-04) sepa qué KB y tono aplicar

  Background:
    Given la variable APP_ROLE es "family"

  Scenario: Login con credenciales válidas devuelve cl.User con role
    Given login() devuelve una sesión válida con role "family"
    When llamo a password_auth_callback con email "user@example.com" y contraseña correcta
    Then la función devuelve un cl.User con identifier "user@example.com"
    And el metadata del cl.User contiene role "family"

  Scenario: Login con credenciales inválidas devuelve None
    Given login() eleva AuthApiError por credenciales inválidas
    When llamo a password_auth_callback con email "user@example.com" y contraseña incorrecta
    Then la función devuelve None
