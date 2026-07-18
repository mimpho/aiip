# E-11 T-05 — Investigación dirigida: eval_15, confirmación de eval_63, documento
# sospechoso guia_antibiotics_esp_0.pdf
# Depende de T-01/T-02 (corpus ampliado y retriever ajustado — puede resolver casos
# como efecto colateral, igual que le pasó a eval_63 con el fix de hallazgo D en E-09).
#
# Contexto:
# - eval_63 (backlog/ideas.md #5): Faithfulness 0.0/Answer Relevancy 0.29 pre-T05 de
#   E-09, ya en 0.877/0.794 post-T05 (efecto colateral del fix de hallazgo D/F) — se
#   confirma que se mantiene con el nuevo corpus, no se re-investiga desde cero.
# - eval_15 (tests/eval/results/e09_t05_plan_b_investigacion.md): el más grave del
#   "hallazgo B" — único con Faithfulness bajo (0.38) además de 0.0 en Answer
#   Relevancy/Context Precision/Context Recall. Candidato de causa: respuesta evasiva
#   penalizada por ResponseRelevancy de RAGAS ("noncommittal"), pero sin confirmar
#   frase a frase, y en tensión con Falso Negativo Cero si el fix fuera suavizar el
#   tono.
# - guia_antibiotics_esp_0.pdf: 4 apariciones espurias documentadas
#   (backlog/ideas.md, "Hallazgos del RAG" punto 1, actualizaciones 10/17/18 jul) en
#   preguntas de temática muy distinta (urgencias, día a día, umbral de fiebre).

Feature: Investigación dirigida — eval_15, eval_63 y documento sospechoso

  Como responsable del proyecto AIIP
  Quiero confirmar el cierre de eval_63, investigar en profundidad eval_15 y entender
  por qué guia_antibiotics_esp_0.pdf aparece de forma recurrente en preguntas no
  relacionadas
  Para cerrar o acotar con evidencia los hallazgos de calidad más específicos que
  quedaron abiertos tras E-09

  # --- Confirmación de eval_63 ---

  Scenario: eval_63 sigue resuelto con el corpus y retriever ya ajustados
    Given eval_63 ("What is a primary immunodeficiency?") con Faithfulness 0.877 post-T05
      de E-09
    When se re-mide tras T-01/T-02 de esta épica
    Then su Faithfulness se mantiene en línea con sus vecinos del subconjunto otro_idioma
      (no vuelve a caer a 0.0)

  # --- eval_15: investigación prioritaria ---

  Scenario: Comparación frase a frase de contexto recuperado frente a referencia
    Given eval_15 ("¿Podemos viajar en avión llevando la medicación de inmunoglobulinas?")
      con Faithfulness 0.38 y 0.0 en las otras tres métricas
    When se compara cada afirmación de la respuesta generada contra el contexto recuperado y
      contra "expected_answer" del dataset
    Then se identifica qué afirmaciones concretas no están respaldadas por el contexto

  Scenario: Se distingue causa de generación de causa de retrieval
    Given el análisis frase a frase
    When se determina si el problema está en qué se recuperó (Context Precision/Recall) o en
      cómo se generó la respuesta (tono evasivo, síntesis incorrecta)
    Then queda documentada una causa raíz concreta, no solo la hipótesis de "respuesta
      evasiva" ya registrada en el Plan B de E-09

  Scenario: Decisión explícita sobre eval_15
    Given la causa raíz identificada
    When se evalúa si el fix entra en tensión con Falso Negativo Cero (AGENTS.md, principio
      no negociable)
    Then se decide explícitamente entre aplicar un fix acotado o documentar el 0.38 como
      coste aceptado del diseño de seguridad, sin dejarlo ambiguo

  # --- Documento sospechoso ---

  Scenario: Estructura de guia_antibiotics_esp_0.pdf revisada
    Given las 4 apariciones espurias documentadas (backlog/ideas.md) en preguntas de
      urgencias, día a día y umbral de fiebre
    When se revisa el chunking del documento (tamaño de chunk, límites de sección, densidad
      de términos genéricos como "fiebre"/"urgencias")
    Then se documenta una hipótesis concreta de por qué su alcance semántico es
      desproporcionado frente a otros documentos monográficos

  Scenario: Decisión sobre mejora de chunking dirigida
    Given la hipótesis documentada
    When se evalúa el coste de una mejora de chunking específica para este documento (ej.
      separar la tabla de proceso de reacciones a infusión del resto del contenido)
    Then se decide explícitamente entre aplicar la mejora dirigida o documentar el patrón
      como backlog abierto

  Scenario: Marcos revisa y confirma las tres investigaciones
    Given los resultados de eval_63, eval_15 y el documento sospechoso
    When Marcos los revisa
    Then confirma el cierre de cada uno (resuelto, mitigado o documentado como abierto) antes
      de pasar al informe final (T-07)
