# E-11 T-04 — Hallazgo E: revisión cualitativa del registro lingüístico
# Tipo: Revisión cualitativa dirigida — sin TDD (no automatizable con pytest, mismo
# patrón que E07-T04). Independiente del corpus (T-01/T-02), puede arrancar en
# paralelo desde el inicio de la épica.
#
# Contexto (backlog/ideas.md, hallazgo #3, 8 jul 2026): detectado en QA manual de E-05
# T-04 — respuestas sobre procesos como el trasplante de médula usan vocabulario
# clínico ("acondicionamiento", "recuperación del sistema inmunitario") potencialmente
# no accesible para un familiar sin formación médica, pese a que
# "prompts/system_prompt_family.txt" ya pide "lenguaje accesible... sin tecnicismos
# innecesarios". Quedó fuera del ciclo de mejora de E-09 (D-056).

Feature: Hallazgo E — revisión cualitativa del registro lingüístico

  Como responsable del proyecto AIIP
  Quiero revisar si el registro lingüístico real generado por el LLM es consistente con
  la instrucción de tono accesible del system prompt
  Para el perfil familiar, en temas con vocabulario clínico denso

  # Checklist de verificación manual

  Scenario: Selección de preguntas con vocabulario clínico denso
    Given temas con vocabulario clínico denso identificados en QA previo (ej. trasplante de
      médula, acondicionamiento, tratamiento con inmunoglobulinas)
    When se seleccionan preguntas representativas del dataset o se formulan preguntas
      dirigidas nuevas
    Then queda una muestra dirigida suficiente para la lectura cualitativa (no todo el
      dataset — revisión dirigida, no exhaustiva)

  Scenario: Respuestas revisadas contra la instrucción de tono
    Given la muestra dirigida de preguntas
    When se ejecutan contra "RAGPipeline.query()" real y se revisan las respuestas
    Then se marca cada término técnico no explicado en lenguaje accesible
    And se contrasta contra la sección "[TONO — PERFIL FAMILIAR]" de
      "prompts/system_prompt_family.txt"

  Scenario: Hallazgos documentados con ejemplos concretos
    Given las respuestas revisadas
    When se documentan los hallazgos
    Then cada término técnico problemático queda citado junto a la respuesta completa donde
      aparece, no solo el veredicto agregado

  Scenario: Decisión sobre si el hallazgo requiere ajuste
    Given los hallazgos documentados
    When se evalúa su alcance
    Then se decide explícitamente entre: ajustar la instrucción de tono del system prompt,
      dejarlo como backlog abierto (si el registro es puntual y no sistemático), o no
      requiere cambio

  Scenario: Marcos revisa y confirma el hallazgo E
    Given el informe de la revisión cualitativa
    When Marcos lo revisa
    Then confirma si el hallazgo E queda cerrado con la decisión tomada, o si hace falta
      profundizar más
