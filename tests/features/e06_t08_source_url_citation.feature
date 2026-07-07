# E-06 T-08 — Enlazar fuentes citadas a su URL original
# Criterio: manifest → metadata de chunk → citación con enlace markdown (D-029)

Feature: Citación de fuentes con URL original

  Como usuario del asistente
  Quiero que las fuentes citadas enlacen a su URL original cuando esté documentada
  Para poder verificar la información en la fuente primaria

  Scenario: El loader añade la URL del manifest al metadata del documento
    Given un documento cargado desde una fuente con "url" documentada en el manifest
    When se ejecuta el loader
    Then el metadato "url" del documento coincide con el valor del manifest

  Scenario: El loader deja la URL a None si el manifest no la documenta
    Given un documento cargado desde una fuente sin "url" documentada en el manifest
    When se ejecuta el loader
    Then el metadato "url" del documento es None

  Scenario: El chunker propaga la URL del documento a cada chunk
    Given un documento cargado con el metadato "url" ya asignado
    When se aplica el chunker
    Then cada chunk resultante conserva el metadato "url" del documento

  Scenario: La sección de fuentes muestra un enlace markdown cuando el chunk tiene URL
    Given chunks recuperados cuyo metadata incluye "url"
    When se construye la sección de fuentes
    Then la sección de fuentes incluye un enlace markdown a esa URL

  Scenario: La sección de fuentes cae al nombre de fichero si el chunk no tiene URL
    Given chunks recuperados cuyo metadata no incluye "url"
    When se construye la sección de fuentes
    Then la sección de fuentes muestra "source/filename" sin enlace
