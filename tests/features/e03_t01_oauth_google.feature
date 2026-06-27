# E-03 T-01 — Configurar OAuth de Google en Supabase Auth
# Tarea de configuración (estilo E-01) — sin rama, sin PR.
# Supabase es el único broker de identidad OAuth — ver D-014 en decisions.md.
# Los escenarios manuales se verifican a mano. El último escenario se verifica
# con un script (no requiere step definitions completas de pytest-bdd).

Feature: T-01 OAuth de Google operativo en Supabase Auth

  Como desarrollador del proyecto AIIP
  Quiero tener Google configurado como proveedor OAuth en Supabase Auth
  Para ofrecer login con Google a familiares y profesionales sin duplicar
  mecanismos de identidad

  Scenario: Pantalla de consentimiento de Google configurada
    Given que accedo a Google Cloud Console con mi cuenta
    When configuro el OAuth consent screen con scopes "email", "profile", "openid"
    Then la app queda en modo "Testing"
    And mi cuenta y las cuentas de prueba necesarias están añadidas como test users

  Scenario: Client ID y Secret creados con la redirect URI correcta
    Given que el consent screen está configurado
    When creo un OAuth Client ID de tipo "Web application"
    And registro la redirect URI "https://<project-ref>.supabase.co/auth/v1/callback"
    Then obtengo un Client ID y un Client Secret válidos

  Scenario: Provider de Google activado en Supabase
    Given que tengo el Client ID y Secret de Google
    When los configuro en Supabase Authentication > Providers > Google
    Then el provider queda en estado "Enabled"
    And ninguna credencial OAuth se añade a .env ni a .env.example

  Scenario: Redirect URLs de ambas apps registradas en Supabase
    Given que el provider de Google está activo
    When accedo a Supabase Auth > URL Configuration > Redirect URLs
    Then añado la URL de la app familiar
    And añado la URL de la app profesional
    And ambas quedan en la allowlist de redirección

  Scenario: Verificación automatizada de la URL de autorización
    Given que el provider está activo y las redirect URLs están configuradas
    When ejecuto el script de verificación de OAuth con la URL de la app familiar
    Then recibo una URL de autorización válida con host de Google y los parámetros client_id y redirect_uri presentes
    And el mismo resultado se obtiene al ejecutar el script con la URL de la app profesional
