# E-06 T-06 — Datasheet DAIMS de la KB
# Tipo: Configuración manual — verificación sin tests automatizados

Feature: Datasheet DAIMS de la Knowledge Base

  Como responsable del proyecto AIIP
  Quiero documentar el corpus de la KB siguiendo el framework DAIMS (arXiv 2501.14094)
  Para dejar trazabilidad de procedencia, composición y limitaciones del corpus usado en el RAG

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: Las 7 secciones de DAIMS están presentes y completas
    Given la plantilla DAIMS (Motivation, Composition, Collection process, Preprocessing/cleaning/labeling, Uses, Distribution, Maintenance)
    When reviso docs/kb-datasheet.md
    Then cada sección tiene todas sus preguntas respondidas, sin dejar ninguna en blanco
    And las preguntas no aplicables están marcadas "no relevante, porque..." en vez de omitidas

  Scenario: La sección Composition documenta el corpus real sin duplicar kb-sources.md
    Given las fuentes indexadas en la colección "familiar" tras T-05 (IPOPI, IDF, upiip, guías internas)
    When reviso la sección Composition
    Then describe tipos de instancia (documento), número de fuentes e idiomas, y referencia docs/kb-sources.md en vez de duplicar la tabla de fuentes

  Scenario: El checklist de 24 ítems de Preprocessing está adaptado a un corpus documental
    Given el checklist tabular de DAIMS (sección 4a, 24 ítems)
    When reviso cada ítem
    Then los ítems específicos de datos tabulares (ID de paciente, variable outcome, formato wide, splits train/test) están marcados "no relevante, corpus documental no tabular"
    And los ítems aplicables a documentos (idioma, duplicados, checksum/manifest, missing data) están respondidos con el estado real del pipeline de ingesta

  Scenario: La sección Collection process documenta el pipeline y la trazabilidad
    Given el pipeline loader → chunker → indexer (T-02 a T-05) y data/raw/manifest.json (D-021)
    When reviso la sección Collection process
    Then describe cómo se obtuvo cada fuente, qué mecanismo la procesó, y cómo se traza (checksum, URL, fecha) vía manifest.json

  Scenario: La sección Distribution refleja las restricciones de copyright de terceros
    Given que los documentos crudos son de terceros (IPOPI, IDF, upiip, etc.) y no se redistribuyen
    When reviso la sección Distribution
    Then queda explícito que el corpus no se distribuye fuera del uso interno del RAG del TFM, y que los ficheros crudos no viven en el repo por copyright

  Scenario: La sección Maintenance anota las fuentes propuestas como ampliación futura
    Given las fuentes "Propuesta"/"Por explorar" de docs/kb-sources.md (Acadip, AEDIP, etc.)
    When reviso la sección Maintenance
    Then quedan anotadas como ampliación futura no bloqueante, sin tratarlas como parte del corpus ya indexado

  Scenario: Correspondence y nombrado del fichero siguen la convención del repo
    Given la convención de nombrado propia de DAIMS (DAIMS_DatasetName_DDMMYYYY)
    When reviso el fichero final
    Then se documenta como docs/kb-datasheet.md (convención de docs/ del repo, no la de DAIMS) y la sección Correspondence identifica a Marcos como autor con fecha de cierre
