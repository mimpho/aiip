# E-03 T-02 — Esquema Supabase: tabla profiles + RLS
# Criterio: valida que la migración crea el esquema correcto, que RLS funciona
# y que get_or_create_profile opera sin duplicar perfiles.

Feature: Tabla profiles con RLS y get_or_create_profile

  Como desarrollador del proyecto AIIP
  Quiero una tabla profiles con políticas RLS y la función get_or_create_profile
  Para almacenar el rol (familiar/profesional) ligado a auth.users de forma segura

  Background:
    Given la migración de profiles está aplicada en Supabase

  Scenario: La tabla profiles tiene el esquema correcto
    When consulto la estructura de la tabla profiles
    Then existe la columna id como FK a auth.users
    And existe la columna role con CHECK que solo admite "familiar" o "profesional"
    And existe la columna created_at
    And existe la columna updated_at

  Scenario: updated_at se actualiza automáticamente al modificar el perfil
    Given un perfil existente con un updated_at conocido
    When actualizo cualquier campo del perfil
    Then updated_at tiene un valor más reciente que el anterior

  Scenario: RLS bloquea la lectura del perfil de otro usuario
    Given dos usuarios autenticados A y B con perfiles distintos
    When el usuario A intenta leer el perfil del usuario B
    Then la operación es rechazada por RLS

  Scenario: RLS bloquea la escritura en el perfil de otro usuario
    Given dos usuarios autenticados A y B con perfiles distintos
    When el usuario A intenta escribir en el perfil del usuario B
    Then la operación es rechazada por RLS

  Scenario: RLS permite leer y escribir el propio perfil
    Given un usuario autenticado con perfil propio
    When lee su propio perfil
    Then obtiene los datos correctamente
    When actualiza su propio perfil
    Then la actualización se aplica correctamente

  Scenario: get_or_create_profile crea un perfil nuevo si no existe
    Given un user_id válido sin perfil en la tabla profiles
    When llamo a get_or_create_profile con ese user_id y role "familiar"
    Then se crea un perfil con role "familiar"
    And la función devuelve el perfil creado

  Scenario: get_or_create_profile devuelve el perfil existente sin duplicar
    Given un user_id válido con perfil existente y role "familiar"
    When llamo a get_or_create_profile con ese user_id y role "familiar"
    Then no se crea un perfil duplicado
    And la función devuelve el perfil existente
