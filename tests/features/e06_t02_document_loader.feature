# E-06 T-02 — Loader de documentos fuente
# Criterio: los documentos crudos de data/raw/ se cargan en memoria con metadatos de origen fiables

Feature: Loader de documentos fuente

  Como desarrollador
  Quiero cargar los documentos desde data/raw/<fuente>/ (PDF, HTML)
  Para tener el contenido en memoria con metadatos de origen, listo para chunking

  Background:
    Given la carpeta de datos crudos configurada en KB_RAW_DATA_PATH existe

  Scenario: Carga de un PDF válido
    Given un PDF válido en data/raw/<fuente>/
    When se ejecuta el loader
    Then se extrae el texto completo del documento
    And el metadato "source" refleja el nombre de la carpeta de fuente
    And el metadato "filename" refleja el nombre del fichero

  Scenario: Carga de un documento HTML válido
    Given un fichero HTML válido en data/raw/<fuente>/
    When se ejecuta el loader
    Then se extrae el texto legible del documento sin marcado HTML
    And el metadato "source" refleja el nombre de la carpeta de fuente

  Scenario: Fichero con formato no soportado se omite sin interrumpir la carga
    Given data/raw/<fuente>/ contiene un fichero de formato no soportado junto a ficheros válidos
    When se ejecuta el loader
    Then se registra un aviso indicando el fichero omitido
    And los ficheros válidos de la misma carpeta se cargan igualmente

  Scenario: Carpeta de datos crudos ausente
    Given KB_RAW_DATA_PATH apunta a una ruta que no existe
    When se ejecuta el loader
    Then se lanza un error claro que indica la ruta esperada

  Scenario: Carpeta de datos crudos vacía
    Given la carpeta de datos crudos existe pero no contiene ninguna fuente
    When se ejecuta el loader
    Then se lanza un error claro indicando que no hay documentos que cargar

  Scenario: Fichero nuevo sin entrada en el manifest se documenta automáticamente
    Given un fichero en data/raw/<fuente>/ sin entrada correspondiente en data/raw/manifest.json
    When se ejecuta el loader
    Then se crea una entrada nueva en el manifest con su checksum y fecha de detección
    And el campo "url" de la nueva entrada queda a null
    And se registra un aviso de fuente nueva sin URL documentada
    And el fichero se carga igualmente sin bloquear el resto del proceso

  Scenario: Fichero documentado cuyo contenido ha cambiado actualiza el manifest
    Given un fichero en data/raw/<fuente>/ con entrada en el manifest cuyo checksum no coincide con el contenido actual
    When se ejecuta el loader
    Then se actualiza el checksum y la fecha de la entrada existente
    And se registra un aviso indicando que el contenido de la fuente cambió
    And el fichero se carga igualmente sin bloquear el resto del proceso

  Scenario: Manifest de trazabilidad ausente por completo
    Given data/raw/manifest.json no existe
    When se ejecuta el loader
    Then se crea el manifest con entradas para todos los ficheros encontrados
    And se registra un aviso indicando que no había manifest previo
    And todos los ficheros se cargan igualmente sin bloquear el proceso
