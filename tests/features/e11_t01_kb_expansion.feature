# E-11 T-01 — Ampliación de la KB con fuentes generales/FAQ de vida diaria
# Tipo: Configuración/curación de contenido — sin TDD, mismo patrón que E06-T07/T08
# (rama + PR igualmente, precedente feedback_task_type_no_tdd).
#
# Contexto (D-059, 18 jul 2026): `data/raw/manifest.json` tiene 37 documentos, 36
# monográficos por patología/procedimiento. Solo el manual de IDF es genuinamente
# general. Los casos de peor Context Precision/Recall de E-09 coinciden con
# preguntas de vida diaria/FAQ no cubiertas ni por las fuentes ya propuestas en
# `docs/kb-sources.md`.
#
# Alcance acotado en task-start (D-060, revisa el borrador de epic-start):
# - Sin medición RAGAS en esta tarea: el script `scripts/run_ragas_eval.py` salta los
#   casos ya puntuados (ejecución incremental) y T-02 ya tiene la re-medición como
#   criterio propio — mezclarla aquí duplicaría llamadas a Gemini (cuota limitada) y
#   mezclaría contenido con medición (D-056).
# - Búsqueda de fuentes acotada a los 6 huecos genuinos sin ningún documento que los
#   cubra hoy (comprobado contra el manifest). Otros 4 casos citados originalmente
#   (eval_03/08/11/13/65 — por qué necesita infusiones, antibióticos profilácticos,
#   diagnóstico, cuidados piel inyección subcutánea) ya tienen documento indexado; su
#   mal score en E-09 apunta a retrieval (BM25/chunking), no a contenido — quedan para
#   T-02/T-05, no son objetivo de T-01.

Feature: Ampliación de la KB con documentación general/FAQ de vida diaria

  Como responsable del proyecto AIIP
  Quiero ampliar la KB con fuentes generales/FAQ de vida diaria vetadas por Marcos
  Para que las preguntas de vida diaria sin ningún documento que las cubra tengan
  contexto real que recuperar, antes de calibrar el retriever híbrido (T-02) contra
  un corpus definitivo

  # Checklist de verificación manual — sigue docs/kb-maintenance.md

  Scenario: Huecos genuinos de cobertura identificados como objetivo de búsqueda
    Given los 6 temas de vida diaria sin ningún documento en "data/raw/manifest.json"
      que los cubra: frecuencia de revisiones con el inmunólogo (eval_06), viajar en
      avión con la medicación (eval_15), informar al inmunólogo del destino de
      vacaciones (eval_23), convivencias o salidas de varios días (eval_25), si es
      contagiosa (eval_27) y si tiene cura (eval_20)
    Then esos 6 temas son el objetivo prioritario de búsqueda de fuentes de esta tarea

  Scenario: Fuentes generales/FAQ identificadas y vetadas por Marcos
    Given los 6 temas objetivo del escenario anterior
    When Marcos busca y veta fuentes generales/FAQ que los cubran (sin inventar enlaces,
      mismo criterio que E-06 T-08)
    Then las fuentes aprobadas quedan añadidas a "docs/kb-sources.md" con su estado real
      ("Validada"/"Propuesta") y origen
    And si alguna fuente encontrada cubre además alguno de los 4 casos ya indexados
      (eval_03/08/11/13/65), se puede añadir igualmente sin que sea criterio de cierre
      de esta tarea

  Scenario: Documentos añadidos a data/raw/ siguiendo el runbook de mantenimiento
    Given las fuentes aprobadas en el escenario anterior
    When se añaden los documentos a "data/raw/{fuente}/" (sección 1/2 de
      "docs/kb-maintenance.md")
    Then cada documento nuevo queda en la carpeta de su fuente correspondiente
    And Marcos confirma a criterio propio que no duplica contenido ya cubierto por el
      manual general de IDF ya indexado (no hay check automatizado de deduplicación)

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos ya en "data/raw/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista las fuentes nuevas en "failures"
    And "data/raw/manifest.json" incluye una entrada nueva por documento (url: null
      hasta rellenar a mano)
    And no quedan chunks huérfanos de ejecuciones previas (mismo cuidado que
      docs/kb-maintenance.md sección 4)

  Scenario: Marcos confirma la cobertura antes de pasar a T-02
    Given los 6 temas objetivo y las fuentes añadidas para cubrirlos
    When Marcos revisa manualmente que cada tema tiene al menos un documento nuevo
      relevante en la KB (sin medición RAGAS — eso es T-02)
    Then confirma si la cobertura es suficiente para pasar a T-02 (re-medición RAGAS +
      calibración de BM25 contra el corpus ampliado) o si hace falta una ronda
      adicional de fuentes
