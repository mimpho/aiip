# E-09 T-05 — Ciclo de mejora (hallazgos A, B, D, F)
# Alcance ampliado y reordenado (D-056, 17 jul 2026): T-05 se ejecuta antes de T-03/T-04.
# De los 6 hallazgos remitidos a E-09 (informe E-07 T-04 §4.1/§4.2 + backlog/ideas.md),
# este ciclo cubre:
#   A. Sobre-activación del filtro de seguridad en eval_07/eval_08/eval_25 (D-053 §4.1)
#   B. Answer Relevancy en 0.0 sin causa diagnosticada: eval_06, eval_15 (D-053 §4.2) —
#      tratado como Plan B, no scope comprometido (D-057)
#   D. Ruido en dense search / hybrid search (backlog/ideas.md #2), reincorporado por
#      D-056 al tener su impacto cuantificado (Context Precision 53.8%, T-02)
#   F. langdetect falla en frases cortas de síntomas en español (backlog/ideas.md #4)
# C (grounding vs. conocimiento de mundo) y E (registro lingüístico) quedan en
# backlog/ideas.md como backlog abierto, fuera de este ciclo.
#
# Decisiones técnicas por hallazgo, ver D-057:
#   A -> stoplist + contexto en config/alarm_triggers.json (datos, no código)
#   D -> EnsembleRetriever de LangChain (BM25 + vectorial, RRF) — el Search() nativo de
#        Chroma es exclusivo de Chroma Cloud, descartado para Chroma local
#   F -> sustituir langdetect por lingua-py, restringido a es/en/ca
#
# A, D y F son ajustes deterministas/verificables sin LLM evaluador salvo por la
# re-medición final (que sí usa RAGAS). B es investigativo: el resultado puede ser un fix
# o quedar documentado como no resuelto -- ver bloque de Plan B.
#
# Criterio de cierre (D-056): no basta con arreglar el código — hay que re-ejecutar
# scripts/run_ragas_eval.py sobre el pipeline ya arreglado y documentar el antes/después
# real de las 4 métricas de T-02 (Faithfulness 79.2%, Answer Relevancy 75.9%, Context
# Precision 53.8%, Context Recall 70.3%).

Feature: Ciclo de mejora — hallazgos A, B, D y F

  Como responsable del proyecto AIIP
  Quiero aplicar ajustes sobre los hallazgos A, D y F, evaluar B como Plan B si hay
  margen, y verificar que ningún ajuste rompe comportamiento ya validado
  Para cumplir el criterio "al menos un ciclo de mejora basado en los resultados"

  # --- Hallazgo A: sobre-activación del filtro de seguridad ---

  Scenario: eval_07, eval_08 y eval_25 dejan de activar el filtro de seguridad
    Given las preguntas de eval_07 ("¿Es normal que le duela el brazo después de la
      infusión subcutánea de inmunoglobulinas?"), eval_08 ("¿Qué antibióticos se usan
      habitualmente como profilaxis en inmunodeficiencias primarias?") y eval_25
      ("¿Puede mi hijo marcharse de convivencias varios días?")
    When se evalúan con check_alarm_signals tras aplicar la stoplist ("después", "varios",
      "infusión") de config/alarm_triggers.json
    Then ninguna de las tres activa la alarma

  Scenario: "antibióticos" solo dispara la alarma con contexto de duración o frecuencia
    Given la pregunta de eval_08 ("¿Qué antibióticos se usan habitualmente como profilaxis
      en inmunodeficiencias primarias?"), sin término de duración/frecuencia
    And la pregunta de eval_62 ("Este año lleva ya dos tandas de antibióticos por
      infecciones de oído, no sé si eso ya es motivo de preocupación..."), con término de
      duración ("año")
    When se evalúan con check_alarm_signals tras el ajuste de requires_context
    Then eval_08 no activa la alarma
    And eval_62 sigue activando la alarma

  Scenario: Ningún caso de alarma o caso límite real deja de activarse (regresión T-03)
    Given los 27 casos de alarma y casos límite del dataset (tests/eval/dataset_partial.json)
    When se evalúan con check_alarm_signals tras el ajuste
    Then todos siguen activando la alarma igual que antes del ajuste
    # Comprobación no negociable: el ajuste de A no puede comprometer Falso Negativo Cero.
    # Si un solo caso real deja de activarse, el ajuste se descarta o se refina.

  # --- Hallazgo D: ruido en dense search / hybrid search ---

  Scenario: Preguntas con nombres propios geográficos recuperan chunks con coincidencia léxica exacta
    Given la pregunta "¿Qué hospitales con servicio de inmunología hay en Barcelona?"
    When se recupera con el retriever híbrido (EnsembleRetriever: BM25 + vectorial) tras
      el ajuste
    Then los chunks recuperados incluyen contenido que menciona "Barcelona" explícitamente
    And no se limita a hospitales de otras ciudades recuperados solo por similitud semántica

  Scenario: El directorio de hospitales (aedip) aparece para preguntas de contacto genéricas
    Given la pregunta "¿A quién llamo si es fin de semana?" (caso real documentado en
      tests/results/e05_t07_smoke_test_results.md, CU-05)
    When se recupera con el retriever híbrido tras el ajuste
    Then el chunk de data/raw/aedip/Hospitales-con-Servicios-de-Inmunologia.html aparece
      entre los resultados recuperados

  Scenario: Los casos ya bien recuperados en T-02 no empeoran (regresión)
    Given los casos informativos con Context Precision > 0.99 en T-02 (eval_09, eval_10,
      eval_19, eval_24, entre otros)
    When se recuperan con el retriever híbrido tras el ajuste
    Then el contenido recuperado sigue siendo relevante para la pregunta

  # --- Hallazgo F: langdetect / lingua-py en frases cortas de síntomas ---

  Scenario Outline: Frases declarativas cortas de síntomas en español se detectan como español
    Given la frase "<frase>"
    When se evalúa con detect_language tras sustituir langdetect por lingua-py
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
    Then todas siguen detectando el idioma correcto (es, en o ca según corresponda)
    # Regresión: el fix de F no puede introducir falsos negativos nuevos en frases que
    # ya funcionaban (D-017, D-019).

  # --- Hallazgo B: Plan B, no scope comprometido (D-057) ---

  Scenario: B se investiga solo si sobra margen tras A, D y F
    Given los ajustes de A, D y F ya aplicados y verificados
    When queda margen de tiempo dentro de T-05
    Then se investiga la causa de Answer Relevancy 0.0 en eval_06 y eval_15 (respuesta
      generada, parseo de RAGAS, formato de la pregunta)
    And si hay causa raíz identificada, se aplica un ajuste y se re-evalúan ambos casos
    And si no queda margen, B se documenta como "abierto" en el cierre del ciclo, sin
      tratarse como fallo oculto

  # --- Cierre del ciclo: re-medición obligatoria (D-056) ---

  Scenario: Backup de resultados previos antes de re-medir
    Given tests/eval/results/e09_t02_ragas_full_scores.json con los 32 casos de T-02 ya
      evaluados (checkpointing por id)
    When se prepara la re-ejecución de scripts/run_ragas_eval.py tras aplicar los ajustes
      de A, D y F (y de B si se abordó)
    Then el fichero existente se respalda (p. ej. e09_t02_ragas_full_scores_pre_t05.json)
      o _RESULTS_PATH apunta a un fichero nuevo
    And ningún caso se salta por el checkpointing del fichero anterior

  Scenario: Re-medición completa de las 4 métricas RAGAS
    Given el pipeline con los ajustes de A, D y F aplicados (y de B si se abordó)
    When se re-ejecuta scripts/run_ragas_eval.py sobre los 32 casos de T-02
    Then se obtienen Faithfulness, Answer Relevancy, Context Precision y Context Recall
      actualizados
    And se documenta el antes/después frente a los valores de T-02 (79.2% / 75.9% /
      53.8% / 70.3%)

  Scenario: Los hallazgos quedan documentados con su resultado final
    Given los ajustes aplicados (o descartados) para A, D y F, y el estado final de B
    When se prepara el informe final (T-06)
    Then cada hallazgo indica su estado: resuelto, mitigado o abierto
    And los hallazgos C y E quedan referenciados como backlog abierto, no como parte de
      este ciclo

  Scenario: Marcos revisa y confirma el cierre del ciclo de mejora
    Given los resultados de los escenarios anteriores, incluida la re-medición
    When Marcos los revisa
    Then confirma si el ciclo de mejora está listo para el informe final (T-06)
