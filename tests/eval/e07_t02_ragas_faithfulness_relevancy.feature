# E-07 T-02 — RAGAS: Faithfulness + Answer Relevancy contra el pipeline real
# Tipo: Script documentado — verificación sin tests automatizados (D-050, revisita D-015,
# mismo patrón que tests/features/e06_t07_rag_smoke_test.feature)
# Alcance y diseño técnico: D-051

Feature: RAGAS Faithfulness + Answer Relevancy contra el pipeline real

  Como responsable del proyecto AIIP
  Quiero calcular Faithfulness y Answer Relevancy con RAGAS contra RAGPipeline real
  (sin mocks) sobre los 27 casos informativos del dataset parcial
  Para obtener el primer dato propio de calidad del pipeline con gemini-2.5-flash (D-043)
  antes del informe parcial de T-04

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: Las dependencias de RAGAS están instaladas
    Given "requirements.txt"
    When reviso sus dependencias
    Then incluye "ragas" y "datasets" como dependencias intencionales del proyecto

  Scenario: El script existe y usa RAGPipeline real, sin mocks
    Given el fichero "scripts/run_ragas_eval.py"
    When reviso su implementación
    Then instancia "RAGPipeline" con la configuración real de "rag.config.load_rag_config()"
    And no parchea ni mockea "ChatGoogleGenerativeAI", el vectorstore de Chroma ni el embedder
    And usa "LLM_MODEL" (mismo modelo de producción) como evaluador de RAGAS, sin variable de entorno nueva
    And reutiliza "rag.embeddings.get_embeddings()" (BAAI/bge-m3) para Answer Relevancy

  Scenario: El script evalúa solo el subconjunto informativo del dataset
    Given el dataset "tests/eval/dataset_partial.json" cargado con "evaluation.dataset.load_dataset"
    When el script selecciona los casos a evaluar
    Then solo se incluyen los 27 casos con "is_alarm" en false
    And los 15 casos de alarma quedan excluidos (reservados para T-03, Safety Compliance)

  Scenario: La respuesta evaluada no incluye el bloque de fuentes
    Given una respuesta generada por "RAGPipeline" para un caso del dataset
    When el script la prepara para RAGAS
    Then el bloque de fuentes concatenado (D-026/D-041) queda separado antes de calcular Faithfulness y Answer Relevancy
    And RAGAS recibe solo el texto de la respuesta clínica

  Scenario: La ejecución es incremental y reanudable
    Given una ejecución previa del script interrumpida a mitad del dataset
    When se relanza "scripts/run_ragas_eval.py"
    Then detecta qué ids del dataset ya tienen score guardado en "tests/eval/results/e07_t02_ragas_scores.json"
    And continúa solo con los casos pendientes, sin repetir llamadas ya hechas

  Scenario: Los resultados quedan documentados para revisión manual
    Given la ejecución completa del script sobre los 27 casos informativos
    When reviso "tests/eval/results/e07_t02_ragas_scores.json"
    Then cada caso incluye id, pregunta, score de Faithfulness y score de Answer Relevancy
    And el fichero incluye también los agregados (media) de ambas métricas
    And Marcos revisa el fichero y confirma si los resultados están listos para el informe parcial de T-04
