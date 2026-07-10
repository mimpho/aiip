# E-05 T-03 — Visualización de pasos intermedios del RAG
# Criterio: el pipeline expone los documentos recuperados como paso intermedio reutilizando
# la misma llamada de retrieval que usa la citación final (sin doble consulta, D-035).
# main_family.py NO los renderiza como cl.Step: sería redundante con el listado de fuentes
# al final de la respuesta (D-026), según revisión de Marcos en el smoke test de T-07 (D-041).

Feature: Visualización de los pasos intermedios del pipeline RAG

  Como familiar, o revisor del proyecto
  Quiero que el sistema reutilice el retrieval ya hecho para no duplicar consultas
  Para que la respuesta y su listado de fuentes sean consistentes entre sí

  Scenario: El pipeline expone los documentos recuperados antes de la respuesta final
    Given una pregunta con resultados de retrieval en la colección "family"
    When se ejecuta el paso de recuperación del pipeline
    Then se devuelve la lista de documentos recuperados con su fuente y score
    And esa lista está disponible antes de que la generación del LLM haya terminado

  Scenario: Sin resultados de retrieval no se expone un paso vacío
    Given una pregunta sin resultados de retrieval en la colección, coherente con D-020
    When se ejecuta el paso de recuperación del pipeline
    Then la lista de documentos recuperados expuesta está vacía
    And no se lanza ninguna excepción por la ausencia de resultados

  Scenario: Los metadatos expuestos coinciden con los usados en la citación final
    Given una pregunta con resultados de retrieval
    When se comparan los documentos expuestos como paso intermedio con los usados en _build_sources_section
    Then ambos provienen de la misma llamada a similarity_search_with_score, sin una segunda consulta al vectorstore

  Scenario: El chat no muestra un paso de recuperación redundante con el listado final de fuentes
    Given una pregunta de un usuario autenticado
    When se procesa el mensaje en main_family.on_message
    Then no se abre ningún paso (cl.Step) de documentos consultados
    And el pipeline reutiliza los mismos resultados de retrieval para el streaming de la respuesta, sin una segunda consulta al vectorstore
