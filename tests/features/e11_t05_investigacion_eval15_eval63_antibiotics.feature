# E-11 T-05 — Investigación dirigida: eval_15, confirmación de eval_63, documento
# sospechoso guia_antibiotics_esp_0.pdf
# Depende de T-01/T-02 (corpus ampliado y retriever ajustado — puede resolver casos
# como efecto colateral, igual que le pasó a eval_63 con el fix de hallazgo D en E-09).
#
# Contexto (revisado en task-start contra los datos ya medidos por T-01/T-02, 20 jul
# 2026 — ver e09_t02_ragas_full_scores_pre_e11_t02.json → ..._e11_t02_baseline.json →
# ..._e11_t02_ragas_full_scores.json, pre-E11 → tras T-01 (KB) → tras T-02 (BM25)):
# - eval_63 (backlog/ideas.md #5): Faithfulness 0.0/Answer Relevancy 0.29 pre-T05 de
#   E-09, ya en 0.877/0.794 post-T05. Se confirma que se mantiene con el nuevo corpus
#   y mejora con el peso adaptativo (Context Precision 0.639 → 0.804).
# - eval_15: el motivo original por el que se marcó como prioritario ("único caso con
#   Faithfulness bajo, 0.38, además de 0.0 en las otras tres métricas") ya no se
#   reproduce: Faithfulness sube a 0.9 tras T-01 y se mantiene en 0.875 en la medición
#   final; Answer Relevancy pasa de 0.0 a 0.839 (el patrón "evasivo" del Plan B de E-09,
#   `tests/eval/results/e09_t05_plan_b_investigacion.md`, tampoco se reproduce ya) —
#   resuelto como efecto colateral de la ampliación de KB (T-01), se documenta con una
#   línea de cierre, no se re-investiga desde cero. Pero aparecen dos datos nuevos no
#   anticipados en el criterio original de la épica: Context Precision se mantiene
#   exactamente en 0.0 en las tres mediciones pese a que T-01 añadió dos fuentes que
#   cubren justo este tema (SEICAP "50 preguntas clave" y la FAQ de IPOPI sobre viajes,
#   `docs/kb-sources.md` líneas 43/45); y Context Recall retrocede de 1.0 (tras T-01) a
#   0.0 (tras T-02, peso adaptativo de BM25) — una regresión, no una mejora. El foco de
#   la investigación pasa de "por qué falla la generación" a "por qué el retrieval no
#   encuentra/prioriza bien las fuentes nuevas, y por qué el ajuste de BM25 empeoró el
#   recall aquí" (decisión de Marcos en `task-start`, 20 jul 2026).
# - guia_antibiotics_esp_0.pdf: 4 apariciones espurias documentadas
#   (backlog/ideas.md, "Hallazgos del RAG" punto 1, actualizaciones 10/17/18 jul) en
#   preguntas de temática muy distinta (urgencias, día a día, umbral de fiebre). No hay
#   datos post-T-01/T-02 sobre si se sigue reproduciendo — reproducción manual guiada
#   en Cowork (Chainlit), Marcos ejecuta con Claude guiando paso a paso.

Feature: Investigación dirigida — eval_15, eval_63 y documento sospechoso

  Como responsable del proyecto AIIP
  Quiero confirmar el cierre de eval_63 y del problema original de eval_15, investigar
  por qué su Context Precision/Recall siguen fallando pese al corpus ampliado, y
  entender por qué guia_antibiotics_esp_0.pdf aparece de forma recurrente en preguntas
  no relacionadas
  Para cerrar o acotar con evidencia los hallazgos de calidad más específicos que
  quedaron abiertos tras E-09

  # --- Confirmación de eval_63 ---

  Scenario: eval_63 sigue resuelto con el corpus y retriever ya ajustados
    Given eval_63 ("What is a primary immunodeficiency?") con Faithfulness 0.877 post-T05
      de E-09
    Then su Faithfulness se mantiene en línea con sus vecinos del subconjunto otro_idioma
      tras T-01/T-02 (no vuelve a caer a 0.0) y su Context Precision mejora de 0.639 a
      0.804 con el peso adaptativo de BM25
    And se documenta el cierre sin necesidad de investigación adicional

  # --- eval_15: problema original cerrado, nuevo hallazgo a investigar ---

  Scenario: Problema original de eval_15 cerrado como efecto colateral de T-01
    Given eval_15 ("¿Podemos viajar en avión llevando la medicación de inmunoglobulinas?")
      con Faithfulness 0.38 y 0.0 en Answer Relevancy/Context Precision/Context Recall
      antes de esta épica
    Then tras T-01 (KB ampliada) Faithfulness sube a 0.9 y Answer Relevancy a 0.84,
      confirmado en la medición final (0.875 y 0.839) — la hipótesis de "respuesta
      evasiva" del Plan B de E-09 ya no aplica
    And se documenta el cierre de este punto con una línea, sin re-investigar la causa

  Scenario: Context Precision de eval_15 permanece en 0.0 pese a fuentes relevantes ya indexadas
    Given las fuentes SEICAP "50 preguntas clave" e IPOPI "Can PID patients travel and
      live abroad?" ya indexadas desde T-01 y relevantes para la pregunta
    When se reproduce la consulta contra el pipeline real (guiado en Cowork o vía
      Antigravity, según decida Marcos) y se inspeccionan los chunks recuperados
    Then se identifica si las fuentes nuevas se recuperan pero no se solapan con
      "expected_answer" (problema de precisión de contenido del chunk) o si no se
      recuperan en absoluto (problema de ranking/retriever)

  Scenario: Context Recall de eval_15 retrocede de 1.0 a 0.0 tras el peso adaptativo de BM25
    Given Context Recall en 1.0 tras T-01 (corpus ampliado, peso uniforme) y en 0.0 tras
      T-02 (peso adaptativo)
    When se compara el top-k recuperado en ambas configuraciones para esta consulta
    Then se identifica qué chunk relevante entraba en el top-k con peso uniforme y quedó
      fuera con el peso adaptativo, y si el patrón es específico de este caso o indica un
      problema más general del mecanismo de D-061

  Scenario: Decisión explícita sobre el hallazgo nuevo de eval_15
    Given la causa raíz identificada para Context Precision/Recall
    When se evalúa el coste de un fix acotado frente a documentarlo como backlog abierto
    Then se decide explícitamente entre aplicar el fix o dejarlo documentado para T-07,
      sin dejarlo ambiguo

  # --- Documento sospechoso ---
  # Reproducción guiada en Cowork (Marcos ejecuta en Chainlit, Claude guía paso a paso) —
  # se intenta cerrar en esta misma sesión si el resultado es rápido de interpretar.

  Scenario: Reproducción de las 3 preguntas ya documentadas contra el corpus/BM25 actuales
    Given las 3 preguntas de "Hallazgos del RAG" (backlog/ideas.md, actualizaciones 10/18
      jul) que citaron guia_antibiotics_esp_0.pdf de forma espuria: "¿A quién llamo si es
      fin de semana?", "¿Cómo puedo cuidar el día a día de mi familiar?", "¿A partir de
      cuánta fiebre tengo que acudir al médico?"
    When Marcos las reproduce en Chainlit (perfil familiar) con el corpus ampliado y el
      peso adaptativo de BM25 ya activos
    Then se registra si guia_antibiotics_esp_0.pdf sigue apareciendo entre las fuentes
      citadas en cada una, y se compara contra el comportamiento documentado (10/18 jul)

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
