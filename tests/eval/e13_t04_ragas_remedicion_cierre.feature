# E-13 T-04 — Remedición RAGAS + cierre
# Tipo: script sin TDD (D-050/D-051) — instrumentación + revisión manual, no asserts.
# Depende de T-01/T-02/T-03 (los 3 lotes ya indexados).
#
# Criterio de aceptación de la épica: KB ampliada y remedida contra RAGAS, con
# comparación explícita contra el cierre de E-11, sin suavizar (mismo criterio de
# transparencia que E-09/E-11).

Feature: Remedición RAGAS post-ampliación de KB (E-13) y cierre de la épica

  Como responsable del proyecto AIIP
  Quiero medir el impacto de las 40 fichas nuevas de MedlinePlus Genetics sobre las 4
  métricas RAGAS y cerrar la épica con el informe actualizado
  Para confirmar que la ampliación mejora Context Precision/Recall (u otras métricas) sin
  degradar el resto, antes de dar la KB por ampliada

  Scenario: Respaldo del resultado previo antes de la remedición
    Given el fichero de resultados vigente en
      "tests/eval/results/e09_t02_ragas_full_scores.json" (el que escribe
      "scripts/run_ragas_eval.py", con los números finales de cierre de E-11: Faithfulness
      84.6%, Answer Relevancy 79.9%, Context Precision 63.2%, Context Recall 86.5%)
    When se prepara la ejecución de "scripts/run_ragas_eval.py" de esta tarea
    Then el fichero se respalda como
      "tests/eval/results/e09_t02_ragas_full_scores_pre_e13_t04.json" (referencia pre-E-13,
      mismo patrón que "_pre_e11_t02.json") y el fichero vigente se resetea a vacío
    And se documenta explícitamente que el reset es necesario porque la ejecución es
      incremental (checkpointing) y sin resetear no mediría nada nuevo sobre el corpus
      ampliado con las fichas de MedlinePlus
    And al terminar la remedición, el resultado final se guarda también como
      "tests/eval/results/e09_t02_ragas_full_scores_e13_t04_baseline.json" (snapshot de
      cierre, mismo patrón que "_e11_t02_baseline.json")

  Scenario: Remedición de las 4 métricas RAGAS sobre el corpus ampliado
    Given los 3 lotes de MedlinePlus Genetics ya indexados (T-01/T-02/T-03) y el fichero de
      resultados reseteado
    When se ejecuta "scripts/run_ragas_eval.py" sobre los 32 casos (informativo +
      otro_idioma)
    Then se obtienen Faithfulness, Answer Relevancy, Context Precision y Context Recall
      post-ampliación

  Scenario: Comparación explícita contra el cierre de E-11
    Given los resultados de la remedición y el cierre de E-11
      ("tests/eval/results/e11_t02_cierre.md")
    When se documenta la comparación
    Then se indica el delta de cada una de las 4 métricas, sin omitir ni suavizar ninguna
      que empeore o se mantenga por debajo de objetivo

  Scenario: Verificación dirigida de los casos de contexto pobre que motivaron E-11/E-13
    Given los casos de peor Context Precision/Recall documentados en E-09/E-11 (p. ej.
      eval_06, eval_15 y el caso original XIAP/IPEX de D-063)
    When se revisan sus resultados tras la ampliación de E-13
    Then se documenta si mejoran, se mantienen o no cambian, con el valor exacto

  Scenario: docs/kb-sources.md actualizado a "Validada"
    Given los 3 lotes indexados sin fallos y la remedición ya documentada
    When se actualiza la fila de MedlinePlus Genetics en "docs/kb-sources.md" (perfil
      familiar)
    Then el estado pasa de "Propuesta" a "Validada", reflejando las 40 fichas nuevas
      (D-076: 36 de los 3 lotes + 4 revisadas ficha por ficha) ya indexadas

  Scenario: D-084 documentado como limitación conocida en el informe final
    Given el hallazgo D-084 (BM25 no encuentra fichas de MedlinePlus en preguntas de
      listado amplio en español, confirmado con el barrido de "top_k" 5/10/15/20/30 sin
      mejora, y sin caso de tipo "listado" en "tests/eval/dataset_partial.json")
    When se documenta en "docs/evaluation.md"
    Then aparece como modo de fallo conocido de RAG para preguntas de enumeración amplia
      (mismo estilo que el informe final de E-09 T-06), explícito y sin plan de arreglo
      antes del 29 de julio
    And se deja claro que no afecta al caso de uso principal de AIIP (una enfermedad a la
      vez), que sí recupera MedlinePlus correctamente incluso con "RAG_TOP_K" sin cambios

  Scenario: docs/evaluation.md actualizado como actualización post-E-13
    Given todos los resultados de esta tarea
    When se documenta en "docs/evaluation.md"
    Then aparece como actualización post-E-13, con la tabla de métricas de éxito (§7)
      reflejando el valor de E-11 y el valor post-E-13, sin suavizar

  Scenario: Sin cambios a prompts/system_prompt_family.txt en esta épica
    Given que ninguna tarea de E-13 modifica "prompts/system_prompt_family.txt" en
      producción
    When se cierra la épica
    Then no aplica el paso de regresión de prompt que exigiría el checklist de
      epic-start/epic-close
    And si el registro lingüístico de T-01/T-02/T-03 señaló algún ajuste de prompt, queda
      documentado como hallazgo abierto para una épica futura, no aplicado aquí (mismo
      criterio que D-065)

  Scenario: Marcos revisa y confirma el cierre de la épica
    Given "docs/evaluation.md" y "docs/kb-sources.md" ya actualizados
    When Marcos los revisa
    Then confirma si está listo para el cierre de la épica (epic-close) y el paso a E-10
