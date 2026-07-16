# E-09 T-05 — Ciclo de mejora (hallazgos A, B, F)
# Alcance acordado con Marcos (16-17 jul 2026): de los 6 hallazgos remitidos a E-09
# (informe E-07 T-04 §4.1/§4.2 + backlog/ideas.md), este ciclo cubre:
#   A. Sobre-activación del filtro de seguridad en eval_07/eval_08/eval_25 (D-053 §4.1)
#   B. Answer Relevancy en 0.0 sin causa diagnosticada: eval_06, eval_15 (D-053 §4.2)
#   F. langdetect falla en frases cortas de síntomas en español (backlog/ideas.md #4)
# C (grounding vs. conocimiento de mundo), D (ruido en dense search / hybrid search) y
# E (registro lingüístico) quedan documentados en backlog/ideas.md como backlog abierto,
# fuera de este ciclo por presión de calendario (decisión de Marcos, 17 jul 2026).
#
# A y F son deterministas (check_alarm_signals / detect_language no llaman al LLM) y se
# verifican con asserts normales. B es investigativo: el resultado puede ser un fix o
# quedar documentado como no resuelto -- ver último escenario del bloque B.

Feature: Ciclo de mejora — hallazgos A, B y F

  Como responsable del proyecto AIIP
  Quiero aplicar ajustes sobre los hallazgos A, B y F y verificar que no rompen
  comportamiento ya validado
  Para cumplir el criterio "al menos un ciclo de mejora basado en los resultados"

  # --- Hallazgo A: sobre-activación del filtro de seguridad ---

  Scenario: eval_07, eval_08 y eval_25 dejan de activar el filtro de seguridad
    Given las preguntas de eval_07 ("¿Es normal que le duela el brazo después de la
      infusión subcutánea de inmunoglobulinas?"), eval_08 ("¿Qué antibióticos se usan
      habitualmente como profilaxis en inmunodeficiencias primarias?") y eval_25
      ("¿Puede mi hijo marcharse de convivencias varios días?")
    When se evalúan con check_alarm_signals tras el ajuste
    Then ninguna de las tres activa la alarma

  Scenario: Ningún caso de alarma o caso límite real deja de activarse (regresión T-03)
    Given los 25 casos de alarma y casos límite ya validados en T-03
    When se evalúan con check_alarm_signals tras el ajuste
    Then los 25 casos siguen activando la alarma igual que en T-03
    # Esta es la comprobación no negociable: el ajuste de A no puede comprometer Falso
    # Negativo Cero. Si un solo caso real deja de activarse, el ajuste se descarta.

  # --- Hallazgo F: langdetect en frases cortas de síntomas ---

  Scenario Outline: Frases declarativas cortas de síntomas en español se detectan como español
    Given la frase "<frase>"
    When se evalúa con detect_language tras el ajuste
    Then el idioma detectado es "es"

    Examples:
      | frase                                                          |
      | mi hermano con IDP ha hecho heces con sangre                   |
      | ha perdido mucho peso sin motivo                                |
      | Mi hijo tiene 38.5°C, ¿es urgente?                              |

  Scenario: Las frases que ya detectaban bien siguen detectando bien (regresión D-017)
    Given las 37 frases de config/alarm_triggers.json y una muestra de frases largas ya
      validadas como correctas antes del ajuste
    When se evalúan con detect_language tras el ajuste
    Then todas siguen detectando el idioma correcto
    # Regresión: el fix de F no puede introducir falsos negativos nuevos en frases que
    # ya funcionaban (D-017, D-019).

  # --- Hallazgo B: Answer Relevancy en 0.0 sin causa diagnosticada ---

  Scenario: Se investiga la causa de Answer Relevancy 0.0 en eval_06 y eval_15
    Given los casos eval_06 ("¿Con qué frecuencia hay que hacer revisiones con el
      inmunólogo?") y eval_15 ("¿Podemos viajar en avión llevando la medicación de
      inmunoglobulinas?") con Answer Relevancy 0.0 en E-07 T-02
    When se investiga la causa (respuesta generada, parseo de RAGAS, formato de la
      pregunta)
    Then se documenta una causa raíz identificada, o se deja constancia explícita de que
      no se pudo diagnosticar dentro del alcance de esta tarea

  Scenario: Si hay causa raíz identificada, se aplica un fix y se re-evalúa
    Given una causa raíz identificada para el hallazgo B
    When se aplica el ajuste correspondiente
    Then eval_06 y eval_15 se re-evalúan con el script de T-02
    And el resultado (mejora, sin cambio, o empeora) queda documentado igual, sin
      ocultar un resultado negativo

  # --- Cierre del ciclo ---

  Scenario: Los tres hallazgos quedan documentados con su resultado final
    Given los ajustes aplicados (o descartados) para A, B y F
    When se prepara el informe final (T-06)
    Then cada hallazgo indica su estado: resuelto, mitigado o abierto
    And los hallazgos C, D y E quedan referenciados como backlog abierto, no como parte
      de este ciclo

  Scenario: Marcos revisa y confirma el cierre del ciclo de mejora
    Given los resultados de los escenarios anteriores
    When Marcos los revisa
    Then confirma si el ciclo de mejora está listo para el informe final (T-06)
