# E-14 T-06 — Memoria de perfil en el pipeline de generación
# Criterio: el perfil capturado en T-01/T-03/T-05 debe usarse para contextualizar respuestas
# (criterio de aceptación de alto nivel de E-14, epics.md). No toca retrieval — el mismo
# principio que ya bloquea la capa 1 conversacional de E-08 (D-059: mezclar contexto adicional
# con un pipeline cuya calidad no está resuelta dificulta el diagnóstico de fallos) aplica
# aquí en su forma más conservadora posible: solo se inyecta en la llamada de generación
# (RAGGenerator), nunca en la consulta que dispara la búsqueda en ChromaDB/BM25.
#
# Decisión de epic-start (23 jul 2026): el contexto inyectado usa el nombre real del paciente
# (patient_name), nunca la palabra "paciente" — refuerza la instrucción ya existente en
# prompts/system_prompt_family.txt (líneas 41-46) de no asumir que quien escribe es el
# paciente, en vez de contradecirla.
#
# Actualizado en task-start (25 jul 2026, D-093) sobre el draft de epic-start: el draft solo
# cubría rag/generator.py/rag/pipeline.py — se añade el wiring en chainlit/main_family.py
# (de dónde sale el perfil que llega a pipeline.query()/aquery_stream()) y se elimina la
# ambigüedad del escenario de perfil vacío ("vacío o ausente" → se omite el bloque entero).
#
# Nota de proceso: esta tarea toca prompts/system_prompt_family.txt en producción antes del
# cierre de la épica — el cierre (T-07) incluye regresión (tests + RAGAS acotado a los casos
# afectados), no solo al final (precedente E-11 T-07, D-070/D-071).

Feature: Memoria de perfil inyectada en el prompt de generación

  Como usuario con perfil de paciente
  Quiero que el agente use mi diagnóstico/edad/contexto al responder
  Para recibir respuestas más ajustadas a mi situación, sin que eso cambie qué documentos
  se recuperan de la base de conocimiento

  Background:
    Given RAGGenerator con su _PROMPT_TEMPLATE actual (system_prompt, context, question, language_instruction)

  Scenario: Perfil completo se formatea como bloque de contexto en el prompt
    Given un usuario con patient_name, patient_diagnosis, patient_age y patient_context todos informados
    When pipeline.aquery_stream()/query() construye la llamada a generate()/agenerate_stream()
    Then se añade un nuevo placeholder (profile_context) al _PROMPT_TEMPLATE con esos cuatro datos, usando el nombre real del paciente, nunca la palabra "paciente"
    And el placeholder existente "context" (los chunks recuperados) no cambia de contenido

  Scenario: El contexto de perfil no participa en la consulta de retrieval
    Given un usuario con perfil completo y una pregunta cualquiera
    When se ejecuta pipeline.retrieve()
    Then la consulta enviada al EnsembleRetriever (BM25 + vectorial) es la pregunta original, sin el contexto de perfil añadido ni como texto ni como filtro de metadata

  Scenario: Perfil parcial se inyecta solo con los campos disponibles
    Given un usuario con patient_name y patient_diagnosis informados, pero patient_age y patient_context en NULL
    When se construye profile_context
    Then el bloque incluye solo los datos disponibles, sin mencionar los campos vacíos ni inventar valores para ellos

  Scenario: Usuario sin perfil (rechazó el consentimiento de T-02) no cambia el comportamiento actual
    Given un usuario con patient_name en NULL (sin onboarding completado)
    When se genera una respuesta
    Then el bloque [PERFIL DEL PACIENTE] se omite por completo del _PROMPT_TEMPLATE (D-093) — ni cabecera ni contenido
    And el pipeline se comporta exactamente igual que antes de E-14

  Scenario: system_prompt_family.txt se actualiza para explicar cómo usar profile_context
    Given el placeholder profile_context ya soportado por _PROMPT_TEMPLATE
    When se revisa prompts/system_prompt_family.txt
    Then incluye una instrucción explícita sobre cómo usar esos datos (ej. no repetir el diagnóstico como si fuera nuevo, ajustar el registro si la edad es relevante) sin contradecir la instrucción ya existente de no asumir que quien escribe es el paciente

  Scenario: El perfil se cachea en sesión y se usa en cada mensaje sin releer Supabase (D-093)
    Given la app Chainlit del perfil familiar está inicializada
    And on_chat_start ya leyó profile vía _ensure_patient_profile()
    When se guarda ese profile en cl.user_session y se envía un mensaje de chat (on_message)
    Then _answer() lee el perfil desde cl.user_session, sin volver a llamar a get_profile()
    And pipeline.query()/aquery_stream() recibe ese perfil como argumento opcional (default None, retrocompatible con las llamadas existentes de test_e04_t06.py y smoke_test_rag.py)

  Scenario: Editar el perfil desde ajustes actualiza la copia en sesión (D-093)
    Given un usuario con perfil ya cacheado en cl.user_session
    When on_settings_update (T-05) persiste un cambio en profiles
    Then la copia de profile en cl.user_session se actualiza con los mismos campos
    And el siguiente mensaje de ese chat ya usa los datos nuevos, sin esperar a un nuevo on_chat_start
