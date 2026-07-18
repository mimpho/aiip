# E-11 T-03 — Hallazgo C: regla acotada de grounding para conectores no clínicos
#
# Contexto (backlog/ideas.md, "Hallazgos del RAG" punto 1; D-059 punto 5): el LLM está
# instruido para usar "exclusivamente" el contexto. Ante "¿hay un hospital cerca de
# Vic?" con un chunk que dice "Barcelona", el modelo se niega a conectar ambos
# conceptos aunque sea geografía básica, y se escuda en Falso Negativo Cero para dar
# una respuesta genérica. D-059 descarta relajar el grounding general o subir
# temperatura — la vía aprobada es una regla concreta y limitada (qué tipo de conector
# no-clínico se permite), nunca una relajación general. GATE explícito: Marcos aprueba
# la redacción exacta antes de que toque prompts/system_prompt_family.txt en
# producción.

Feature: Hallazgo C — regla acotada de grounding para conectores no clínicos

  Como responsable del proyecto AIIP
  Quiero permitir que el LLM conecte conceptos no clínicos (ej. geografía básica) con
  una regla concreta y limitada, sin relajar el grounding para datos clínicos
  Para reducir respuestas evasivas ante preguntas informativas que solo requieren
  sentido común no clínico, sin comprometer Falso Negativo Cero

  # --- Investigación offline (D-059 punto 5): método, no comportamiento de producción ---

  Scenario: Contraste offline entre respuesta laxa y estricta
    Given una pregunta con conector no-clínico (ej. "¿hay algún hospital con inmunología
      cerca de Vic?", con un chunk que menciona "Barcelona")
    When se genera una respuesta con grounding más laxo y se contrasta con la respuesta
      estricta actual, ambas pasadas por los mecanismos de seguridad existentes
      (check_alarm_signals, apply_safety_filter)
    Then el contraste se usa solo como método de investigación para acotar la regla, no se
      despliega ninguna de las dos versiones directamente a producción

  # --- Regla propuesta y gate de aprobación ---

  Scenario: Regla propuesta con alcance concreto y limitado
    Given el resultado de la investigación offline
    When se redacta la regla para "prompts/system_prompt_family.txt"
    Then el alcance queda limitado explícitamente a conectores no-clínicos de sentido común
      (ej. geografía básica, distancias, relaciones temporales obvias)
    And excluye explícitamente cualquier inferencia sobre datos clínicos no presentes en el
      contexto

  Scenario: Marcos aprueba la redacción exacta antes de producción
    Given la regla redactada
    When Marcos la revisa
    Then confirma la redacción exacta o pide ajustes antes de que se aplique a
      "prompts/system_prompt_family.txt"

  # --- Aplicación y verificación ---

  Scenario: El conector no-clínico se resuelve tras el ajuste
    Given la regla ya aprobada y aplicada al system prompt
    When se pregunta por el caso de Vic/Barcelona (o equivalente)
    Then el modelo conecta el concepto no-clínico usando el contexto disponible, sin
      inventar datos clínicos

  Scenario: El grounding clínico se mantiene estricto (regresión Falso Negativo Cero)
    Given un caso con un hecho clínico no presente en el contexto recuperado
    When se pregunta
    Then el modelo no extrapola el dato clínico ausente
    And sigue derivando a consulta médica como antes del ajuste

  Scenario: Los casos ya evaluados en E-09 no empeoran
    Given los 32 casos informativo/otro_idioma ya medidos en T-01/T-02
    When se re-evalúan tras el ajuste de hallazgo C
    Then su Faithfulness no empeora frente a la línea base previa a este ajuste

  Scenario: Marcos revisa y confirma el cierre del hallazgo C
    Given los resultados de los escenarios anteriores
    When Marcos los revisa
    Then confirma si el hallazgo C queda acotado y cerrado, o si la regla necesita más
      ajuste
