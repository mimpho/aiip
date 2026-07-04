# E-04 T-05 — Módulo de seguridad: Falso Negativo Cero
# Criterio: el agente nunca confirma seguridad y siempre deriva a médico ante alarma
# ⚠️ Gate clínico — la lista de triggers en config/alarm_triggers.json es un placeholder
# (ver D-019 en decisions.md). Validar contenido con Jacques Rivière antes de producción;
# no bloquea el cierre de esta tarea, que valida el mecanismo, no el contenido clínico.

Feature: Módulo de seguridad Falso Negativo Cero

  Como sistema de seguridad clínica
  Quiero que el agente nunca confirme que una situación es segura
  Para proteger a las familias de falsos negativos con consecuencias graves

  Background:
    Given el módulo de seguridad está inicializado
    And los triggers de alarma están cargados desde "config/alarm_triggers.json"

  Scenario: Detección de señal de alarma en la query — fiebre alta
    Given el usuario describe "mi hijo tiene 40 grados de fiebre desde hace dos días"
    When se evalúa la query con check_alarm_signals
    Then se detecta una señal de alarma

  Scenario: Detección de señal de alarma en la query — dificultad respiratoria
    Given el usuario describe "tiene dificultad para respirar y los labios azulados"
    When se evalúa la query con check_alarm_signals
    Then se detecta una señal de alarma

  Scenario: Query sin señal de alarma — pregunta informativa
    Given el usuario pregunta "¿qué es la agammaglobulinemia de Bruton?"
    When se evalúa la query con check_alarm_signals
    Then no se detecta ninguna señal de alarma

  Scenario: Refuerzo de derivación médica cuando hay alarma detectada en la query
    Given se ha detectado una señal de alarma en la query
    And el LLM ha generado la respuesta "Puede tratarse de un episodio febril. Descansa e hidrátate bien."
    When se aplica el filtro de seguridad a la respuesta
    Then la respuesta final incluye una derivación explícita a consulta médica

  Scenario: Intercepción de afirmación tranquilizadora absoluta aunque no haya alarma en la query
    Given no se ha detectado señal de alarma en la query
    And el LLM ha generado una respuesta que contiene "no es grave, no te preocupes"
    When se aplica el filtro de seguridad a la respuesta
    Then la respuesta final sustituye o matiza la afirmación tranquilizadora
    And la respuesta final incluye una derivación explícita a consulta médica

  Scenario: Respuesta informativa sin alarma no añade alarmismo innecesario
    Given no se ha detectado señal de alarma en la query
    And el LLM ha generado una respuesta informativa sobre "la agammaglobulinemia de Bruton"
    When se aplica el filtro de seguridad a la respuesta
    Then la respuesta final se mantiene informativa
    And no se añade alarmismo innecesario

  Scenario: Triggers de alarma cargados desde fichero de configuración
    Given existe el fichero "config/alarm_triggers.json"
    When se inicializa el módulo de seguridad
    Then los triggers se cargan desde el fichero JSON, no están hardcodeados en el código
