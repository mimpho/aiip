# E-03 T-06 — Separación de URLs por perfil (familiar real + profesional stub)
# Criterio: dos entrypoints Chainlit independientes; el stub profesional
#            muestra el formulario deshabilitado con banner "En construcción"

Feature: Separación de URLs por perfil

  Como usuario familiar
  Quiero que la app familiar no mencione ni enlace ninguna versión profesional
  Para no generar confusión sobre el alcance del producto

  Como desarrollador
  Quiero un segundo entrypoint Chainlit con el formulario deshabilitado
  Para tener la separación de URLs lista para F-01 sin desarrollar lógica de auth

  Scenario: la app familiar no expone referencias al perfil profesional
    Given la app familiar está arrancada en el puerto 8000
    When cargo la página de login de la app familiar
    Then no hay ningún texto ni enlace que mencione "profesional" ni "F-01"

  Scenario: la app profesional muestra el formulario deshabilitado
    Given la app profesional está arrancada en el puerto 8001
    When cargo la página de la app profesional
    Then veo un banner "En construcción" con texto explicativo encima del formulario
    And todos los inputs del formulario están deshabilitados
    And el botón de submit está deshabilitado

  Scenario: las dos apps arrancan en puertos distintos sin conflicto
    Given el entorno tiene PORT_FAMILIAR=8000 y PORT_PROFESIONAL=8001 en .env
    When arranco la app familiar y la app profesional simultáneamente
    Then cada una responde en su puerto sin error de binding

  Scenario: la app profesional no instancia nada del módulo auth
    Given la app profesional arranca
    When se inicializa el proceso de Chainlit
    Then no se importa ni instancia supabase_client ni ningún callback de auth
