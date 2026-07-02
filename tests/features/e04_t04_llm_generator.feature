# E-04 T-04 — Generador: LLM Gemini Flash via LangChain
# Criterio: el generador produce respuestas coherentes y lee configuración de entorno
# Ver D-018 — nombres de variables agnósticos + estrategia mock/@integration

Feature: Generador LLM Gemini Flash

  Como sistema RAG
  Quiero construir la respuesta final usando Gemini Flash con los chunks recuperados
  Para tener el generador funcional como componente independiente

  Background:
    Given GOOGLE_API_KEY está definida en el entorno

  Scenario: Generación de respuesta con contexto válido
    Given tengo 3 chunks de contexto sobre inmunodeficiencias primarias
    And tengo la query "¿Qué es la agammaglobulinemia de Bruton?"
    When llamo al generador
    Then la respuesta no está vacía
    And no se lanza ninguna excepción

  Scenario: Parámetros de inferencia leídos de entorno
    Given LLM_MODEL, LLM_TEMPERATURE, LLM_TOP_P y LLM_MAX_TOKENS están definidos en el entorno
    When inicializo el LLM
    Then el modelo usa los valores del entorno, no valores hardcodeados

  Scenario: System prompt leído de fichero, no embebido en código
    Given existe el fichero prompts/system_prompt_familiar.txt
    When inicializo el generador
    Then el system prompt se carga desde el fichero

  Scenario: Error claro cuando GOOGLE_API_KEY no está definida
    Given GOOGLE_API_KEY no está definida en el entorno
    When inicializo el generador
    Then se lanza EnvironmentError con mensaje que menciona GOOGLE_API_KEY

  Scenario: Error de autenticación con clave inválida
    Given GOOGLE_API_KEY está definida con un valor inválido
    When llamo al generador con cualquier query
    Then se lanza una excepción de autenticación
    And el error no es silencioso ni un timeout

  @integration
  Scenario: Llamada real a la API de Gemini (smoke test, skippable sin red/clave válida)
    Given GOOGLE_API_KEY es una clave válida y hay conexión a red
    When llamo al generador real con la query "¿Qué es una inmunodeficiencia primaria?"
    Then la respuesta no está vacía
    And no se lanza ninguna excepción
