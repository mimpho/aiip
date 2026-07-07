# E-03 T-06 — Separación de URLs por perfil (family real + professional stub)
# Criterio: dos entrypoints Chainlit independientes; el stub professional
#            muestra el formulario deshabilitado con banner "En construcción"

Feature: Separación de URLs por perfil

  Como usuario family
  Quiero que la app family no mencione ni enlace ninguna versión professional
  Para no generar confusión sobre el alcance del producto

  Como desarrollador
  Quiero un segundo entrypoint Chainlit con el formulario deshabilitado
  Para tener la separación de URLs lista para F-01 sin desarrollar lógica de auth

  Scenario: la app family no expone referencias al perfil professional
    Given la app family está arrancada en el puerto 8000
    When cargo la página de login de la app family
    Then no hay ningún texto ni enlace que mencione "professional" ni "F-01"

  Scenario: la app professional muestra el formulario deshabilitado
    Given la app professional está arrancada en el puerto 8001
    When cargo la página de la app professional
    Then veo un banner "En construcción" con texto explicativo encima del formulario
    And todos los inputs del formulario están deshabilitados
    And el botón de submit está deshabilitado

  Scenario: las dos apps arrancan en puertos distintos sin conflicto
    Given el entorno tiene PORT_FAMILY=8000 y PORT_PROFESSIONAL=8001 en .env
    When arranco la app family y la app professional simultáneamente
    Then cada una responde en su puerto sin error de binding

  Scenario: la app professional no instancia nada del módulo auth
    Given la app professional arranca
    When se inicializa el proceso de Chainlit
    Then no se importa ni instancia supabase_client ni ningún callback de auth
