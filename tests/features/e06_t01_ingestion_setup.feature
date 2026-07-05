# E-06 T-01 — Setup de dependencias y estructura del módulo de ingesta
# Criterio: el entorno de ingesta arranca sin errores de importación ni de configuración

Feature: Setup del módulo de ingesta

  Como desarrollador
  Quiero tener instaladas y verificadas las dependencias del módulo de ingesta
  Para poder arrancar el TDD de loader, chunker e indexer sin problemas de entorno

  Scenario: Importación correcta de módulos de ingesta
    Given el entorno virtual tiene las dependencias instaladas
    When importo los módulos de carga de documentos y de text splitting
    Then ningún módulo lanza ImportError

  Scenario: Variable de entorno de ruta de datos crudos con valor por defecto
    Given el fichero .env no define KB_RAW_DATA_PATH
    When inicializo la configuración del módulo de ingesta
    Then KB_RAW_DATA_PATH toma el valor por defecto "data/raw"

  Scenario: Variable de entorno de ruta de datos crudos personalizada
    Given el fichero .env define KB_RAW_DATA_PATH con una ruta personalizada
    When inicializo la configuración del módulo de ingesta
    Then la configuración usa esa ruta personalizada

  Scenario: Estructura de módulo ingestion/ presente
    Given el repositorio está correctamente clonado
    When verifico la estructura de directorios
    Then existe el módulo ingestion/ con los ficheros __init__.py, loader.py, chunker.py e indexer.py
