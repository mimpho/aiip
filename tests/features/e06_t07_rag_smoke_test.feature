# E-06 T-07 — Smoke test manual del pipeline RAG con datos reales de la KB
# Tipo: Configuración manual — verificación sin tests automatizados

Feature: Smoke test manual del pipeline RAG con datos reales de la KB

  Como responsable del proyecto AIIP
  Quiero ejecutar RAGPipeline real (sin mocks) contra preguntas representativas del perfil familias,
  usando la KB real ya indexada en la colección "family"
  Para verificar manualmente que retrieval y generación funcionan sobre contenido real,
  antes de arrancar E-05 y sin construir la UI sobre un backend sin verificar

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: La KB real está indexada en ChromaDB antes de correr el smoke test
    Given la carpeta local "data/raw/" con las fuentes reales (UPIIP, IPOPI, IDF, AFPA/HAS)
    When compruebo si la colección "family" en "data/chroma/" ya contiene esas fuentes indexadas
    Then si no está poblada, ejecuto "run_ingestion_pipeline()" (ingestion/pipeline.py, T-05) contra "data/raw/" real
    And confirmo que la colección "family" tiene chunks reales antes de continuar con los siguientes escenarios

  Scenario: El script del smoke test existe y usa RAGPipeline real, no mocks
    Given el fichero "scripts/smoke_test_rag.py"
    When reviso su implementación
    Then instancia "RAGPipeline" de "rag/pipeline.py" con la configuración real de "rag.config.load_rag_config()"
    And no parchea ni mockea "ChatGoogleGenerativeAI" ni el vectorstore de Chroma

  Scenario: Pregunta general sobre IDP
    Given una pregunta general y amplia sobre inmunodeficiencias primarias (ej. "¿qué es una inmunodeficiencia primaria?")
    When ejecuto el script contra "RAGPipeline.query()"
    Then la respuesta es coherente con el contenido real de la KB
    And los chunks recuperados y su fuente quedan registrados en "tests/results/e06_t07_smoke_test_results.md"

  Scenario: Pregunta sobre una fuente específica de la KB
    Given una pregunta cuya respuesta debería provenir de una fuente concreta indexada (upiip, IPOPI o IDF)
    When ejecuto el script contra "RAGPipeline.query()"
    Then los chunks recuperados corresponden efectivamente a esa fuente
    And la respuesta generada refleja el contenido de esos chunks

  Scenario: Pregunta en inglés para verificar cross-lingual retrieval real
    Given la misma pregunta general del Scenario 3 formulada en inglés
    When ejecuto el script contra "RAGPipeline.query()"
    Then el idioma detectado es inglés y la respuesta se genera en inglés (D-011/D-022)
    And los chunks recuperados son relevantes aunque estén en un idioma distinto al de la pregunta

  Scenario: Pregunta con señal de alarma verifica Falso Negativo Cero con datos reales
    Given una pregunta que contiene una frase presente en "config/alarm_triggers.json"
    When ejecuto el script contra "RAGPipeline.query()"
    Then "check_alarm_signals()" detecta la señal de alarma
    And la respuesta final incluye la derivación a consulta médica reforzada por "apply_safety_filter()"

  Scenario: Pregunta fuera de contexto de IDPs
    Given una pregunta sin relación con inmunodeficiencias primarias (ej. "¿cómo hago una tortilla de patatas?")
    When ejecuto el script contra "RAGPipeline.query()"
    Then la respuesta no fuerza una conexión artificial con contenido irrelevante recuperado de la KB
    And queda registrado en "tests/results/e06_t07_smoke_test_results.md" cómo se comporta el pipeline ante contenido fuera de dominio

  Scenario: El resultado queda documentado para revisión manual
    Given las 5 preguntas ejecutadas en los escenarios anteriores
    When reviso "tests/results/e06_t07_smoke_test_results.md"
    Then cada entrada incluye pregunta, idioma detectado, chunks recuperados (fuente + score), respuesta generada y si disparó alarma
    And Marcos revisa el fichero y confirma si el pipeline está listo para que E-05 construya la UI sobre él
