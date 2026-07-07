# E-06 T-05 — Pipeline de ingesta end-to-end
# Criterio: loader → chunker → indexer se ejecutan de principio a fin de forma reproducible

Feature: Pipeline de ingesta end-to-end

  Como desarrollador
  Quiero un pipeline que ejecute loader → chunker → indexer sobre todas las fuentes de data/raw/
  Para poder reindexar la KB completa de forma reproducible cuando cambien las fuentes

  Background:
    Given data/raw/ contiene fuentes de fixture organizadas por carpeta

  Scenario: Ejecución completa puebla la colección family
    When se ejecuta el pipeline de ingesta completo
    Then la colección "family_test" queda poblada con chunks
    And cada chunk es trazable a su fichero de origen y a su idioma

  Scenario: Ejecución repetida no duplica chunks
    Given el pipeline de ingesta ya se ejecutó una vez sobre las fuentes de fixture
    When se ejecuta el pipeline de ingesta una segunda vez sobre las mismas fuentes
    Then el número total de chunks indexados no aumenta

  Scenario: Un documento que cambia de número de chunks no deja huérfanos
    Given un documento ya indexado con un número de chunks determinado
    When el documento cambia de contenido y genera menos chunks tras el chunking
    And se ejecuta el pipeline de ingesta de nuevo
    Then el número de chunks de ese documento en la colección coincide con el nuevo número
    And no quedan chunks huérfanos de la versión anterior del documento

  Scenario: Fallo en una fuente no detiene el procesamiento de las demás
    Given una de las fuentes de fixture está corrupta o no se puede leer
    When se ejecuta el pipeline de ingesta completo
    Then las fuentes restantes se procesan e indexan igualmente
    And el fallo de la fuente corrupta queda registrado en el resumen final de la ejecución
