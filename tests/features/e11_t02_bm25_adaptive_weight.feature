# E-11 T-02 — Re-medición tras ampliación de KB + peso adaptativo de BM25
# Depende de T-01 (corpus ya ampliado).
#
# Contexto (D-057, E-09 T-05): peso uniforme 0.4/0.6 (BM25/vectorial) en
# rag/retriever.py::get_hybrid_retriever. Retrospectiva post-cierre de E-09
# (backlog/ideas.md, "Hallazgos del RAG" punto 1): de 32 casos, 23 no cambian con
# BM25, y de los 9 que sí, 6 empeoran (preguntas conceptuales sin señal léxica: "Are
# primary immunodeficiencies hereditary?", "¿Existen grupos de apoyo...?", "¿Qué es la
# IDVC?", "¿Qué especialista debe hacer el seguimiento?") y solo 3 mejoran (preguntas
# con nombre propio/geográfico, ej. "Barcelona"). Decisión de epic-start (18 jul 2026):
# prioridad en el peso adaptativo (activar/ponderar BM25 solo ante señal léxica
# fuerte), con la recalibración simple del peso fijo (ej. 0.2/0.8) como fallback
# barato si el adaptativo no cierra a tiempo.

Feature: Re-medición post-ampliación de KB y peso adaptativo de BM25

  Como responsable del proyecto AIIP
  Quiero re-medir RAGAS sobre el corpus ampliado (T-01) y ajustar el peso de BM25 para
  que solo contribuya cuando la consulta tiene señal léxica fuerte
  Para que Context Precision mejore en preguntas con nombre propio/geográfico sin
  penalizar las preguntas conceptuales que ya recuperaban bien solo con vectorial

  # --- Backup y línea base ---

  Scenario: Backup de resultados antes de tocar BM25
    Given la línea base post-ampliación obtenida en T-01
    When se prepara el ajuste de peso de BM25
    Then el fichero de resultados se respalda (mismo cuidado que D-056 punto 3) antes de
      cualquier nueva ejecución de "scripts/run_ragas_eval.py"

  # --- Peso adaptativo (prioridad) ---

  Scenario: Señal léxica fuerte se define de forma concreta
    Given una consulta de usuario
    When se evalúa si tiene señal léxica fuerte (nombre propio con mayúscula inicial no al
      comienzo de frase, término de baja frecuencia en el corpus, o patrón de entidad
      geográfica)
    Then la consulta se clasifica como "con señal" o "sin señal" de forma determinista, sin
      LLM de por medio

  Scenario: BM25 se pondera solo ante señal léxica fuerte
    Given "get_hybrid_retriever" en "rag/retriever.py" ya ajustado
    When se recupera contexto para una consulta "con señal" (ej. "¿Qué hospitales con
      servicio de inmunología hay en Barcelona?")
    Then el peso de BM25 aplicado es mayor que el de una consulta "sin señal" en la misma
      ejecución

  Scenario: Las preguntas conceptuales sin señal no empeoran (regresión)
    Given los 6 casos que empeoraron en la retrospectiva de E-09 T-05 (preguntas
      conceptuales sin nombre propio ni término geográfico)
    When se recuperan con el retriever ajustado
    Then su Context Precision no empeora frente a la búsqueda puramente vectorial (peso
      BM25 ~0 en estos casos)

  Scenario: Las preguntas con nombre propio/geográfico mejoran
    Given los 3 casos que mejoraron en la retrospectiva de E-09 T-05
    When se recuperan con el retriever ajustado
    Then su Context Precision se mantiene igual o mejor que con el peso uniforme 0.4/0.6

  # --- Fallback: recalibración simple (solo si no da tiempo al adaptativo) ---

  Scenario: Fallback a peso fijo recalibrado si el adaptativo no cierra a tiempo
    Given que el peso adaptativo no llega a completarse dentro del margen de la tarea
    When se aplica la vía barata (bajar el peso fijo de BM25, ej. a 0.2/0.8)
    Then se documenta explícitamente que se optó por el fallback y por qué
    And se re-mide igual que si fuera la solución adaptativa

  # --- Cierre: re-medición y documentación ---

  Scenario: Re-medición completa tras el ajuste de BM25
    Given el retriever ya ajustado (adaptativo o fallback)
    When se re-ejecuta "scripts/run_ragas_eval.py" sobre los 32 casos
    Then se obtiene Context Precision y Context Recall actualizados
    And se documenta el antes/después frente a la línea base de T-01 y frente a los
      resultados de E-09 (peso uniforme)

  Scenario: Marcos revisa y confirma el ajuste de BM25
    Given los resultados de la re-medición
    When Marcos los revisa
    Then confirma si el ajuste queda cerrado (adaptativo o fallback) o si hace falta
      iterar antes de pasar a las siguientes tareas de la épica
