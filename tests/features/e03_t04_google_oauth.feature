# E-03 T-04 — Login con Google OAuth, rol fijo por app
# Criterio: sign_in_with_oauth genera una URL válida hacia Google (provider
# configurado en T-01); get_or_create_profile asigna APP_ROLE al primer login
# y no duplica el perfil en logins subsiguientes.
# Nota: el browser redirect y el callback de Supabase son responsabilidad de
# Supabase Auth — no se testean aquí (requieren e2e con Playwright).

Feature: Login con Google OAuth mediado por Supabase

  Como usuario (familiar o profesional)
  Quiero iniciar sesión con mi cuenta de Google
  Para acceder a AIIP sin crear una contraseña nueva

  Background:
    Given las variables de entorno SUPABASE_URL y SUPABASE_ANON_KEY están configuradas
    And Google OAuth está habilitado en Supabase Auth

  Scenario: sign_in_with_oauth devuelve una URL de redirección hacia Google
    When llamo a sign_in_with_oauth con provider "google"
    Then la respuesta contiene una URL
    And la URL empieza por "https://accounts.google.com"

  Scenario: Primer login OAuth crea perfil con el rol de la app
    Given APP_ROLE es "familiar"
    And un user_id de prueba sin perfil en la tabla profiles
    When llamo a get_or_create_profile con ese user_id y APP_ROLE "familiar"
    Then se crea un perfil en la tabla profiles con role "familiar"
    And la función devuelve el perfil creado

  Scenario: Login OAuth repetido no duplica ni sobreescribe el perfil
    Given APP_ROLE es "familiar"
    And un user_id de prueba con perfil existente y role "familiar"
    When llamo a get_or_create_profile con ese user_id y APP_ROLE "familiar"
    Then no se crea un perfil duplicado
    And la función devuelve el perfil existente con role "familiar"

  Scenario: Login OAuth desde la app profesional crea perfil con rol profesional
    Given APP_ROLE es "profesional"
    And un user_id de prueba sin perfil en la tabla profiles
    When llamo a get_or_create_profile con ese user_id y APP_ROLE "profesional"
    Then se crea un perfil en la tabla profiles con role "profesional"
    And la función devuelve el perfil creado
