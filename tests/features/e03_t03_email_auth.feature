# E-03 T-03 — Registro y login con email/password, rol fijo por app
# Criterio: signup crea usuario + perfil con rol correcto; login devuelve sesión
# y rol; errores se propagan limpiamente. Tests contra Supabase real con cleanup.

Feature: Registro y login con email y contraseña

  Como usuario (family o professional)
  Quiero registrarme e iniciar sesión con email y contraseña
  Para acceder a AIIP con credenciales propias

  Background:
    Given las variables de entorno SUPABASE_URL, SUPABASE_ANON_KEY y SUPABASE_SERVICE_KEY están configuradas
    And existe un email de prueba único generado para esta ejecución
    And al finalizar el test el usuario de prueba es eliminado de Supabase Auth

  Scenario: Registro desde la app family crea perfil con rol family
    Given APP_ROLE es "family"
    When llamo a signup con el email de prueba y contraseña válida
    Then el usuario existe en Supabase Auth
    And existe un perfil en la tabla profiles con role "family"

  Scenario: Registro desde la app professional crea perfil con rol professional
    Given APP_ROLE es "professional"
    When llamo a signup con el email de prueba y contraseña válida
    Then el usuario existe en Supabase Auth
    And existe un perfil en la tabla profiles con role "professional"

  Scenario: Registro con email ya existente eleva un error claro
    Given un usuario ya registrado con el email de prueba
    When llamo a signup con el mismo email
    Then se eleva una excepción con mensaje que indica email duplicado
    And no se crea un perfil duplicado en profiles

  Scenario: Login con credenciales correctas devuelve sesión y rol
    Given un usuario registrado con el email de prueba y role "family"
    When llamo a login con el email de prueba y contraseña correcta
    Then la función devuelve una sesión Supabase válida
    And la función devuelve el rol "family"

  Scenario: Login con credenciales incorrectas eleva un error claro
    When llamo a login con el email de prueba y contraseña incorrecta
    Then se eleva una excepción con mensaje que indica credenciales inválidas
    And no se devuelve sesión
