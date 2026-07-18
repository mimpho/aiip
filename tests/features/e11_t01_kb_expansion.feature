# E-11 T-01 — Ampliación de la KB con fuentes generales/FAQ de vida diaria
# Tipo: Configuración/curación de contenido — sin TDD, mismo patrón que E06-T07/T08
# (rama + PR igualmente, precedente feedback_task_type_no_tdd).
#
# Contexto (D-059, 18 jul 2026): `data/raw/manifest.json` tiene 37 documentos, 36
# monográficos por patología/procedimiento. Solo el manual de IDF es genuinamente
# general. Los casos de peor Context Precision/Recall de E-09
# (eval_03/06/08/11/13/15/20/23/25/27/65) coinciden con preguntas de vida diaria/FAQ
# (frecuencia de revisiones, viajar con medicación, convivencias, contagio, cura, por
# qué necesita infusiones) no cubiertas ni por las fuentes ya propuestas en
# `docs/kb-sources.md`. Se ejecuta primero porque (1) puede resolver hallazgos de
# retrieval como efecto colateral (igual que eval_63 con el fix de hallazgo D en E-09)
# y (2) cualquier ajuste de BM25 (T-02) debe calibrarse contra el corpus final.
# Bottleneck: búsqueda y vetado de fuentes depende del tiempo de Marcos (mismo
# criterio que E-06 T-08 — no inventar enlaces), no de trabajo técnico.

Feature: Ampliación de la KB con documentación general/FAQ de vida diaria

  Como responsable del proyecto AIIP
  Quiero ampliar la KB con fuentes generales/FAQ de vida diaria vetadas por Marcos
  Para que las preguntas de vida diaria (revisiones, viajes, convivencias, contagio,
  cura, infusiones) tengan contexto real que recuperar, antes de calibrar el retriever
  híbrido contra un corpus definitivo

  # Checklist de verificación manual — sigue docs/kb-maintenance.md

  Scenario: Fuentes generales/FAQ identificadas y vetadas por Marcos
    Given la lista de preguntas de vida diaria sin cobertura (eval_03/06/08/11/13/15/20/23/25/27/65)
    When Marcos busca y veta fuentes generales/FAQ que las cubran (sin inventar enlaces, mismo
      criterio que E-06 T-08)
    Then las fuentes aprobadas quedan añadidas a "docs/kb-sources.md" con su estado real
      ("Validada"/"Propuesta") y origen

  Scenario: Documentos añadidos a data/raw/ siguiendo el runbook de mantenimiento
    Given las fuentes aprobadas en el escenario anterior
    When se añaden los documentos a "data/raw/{fuente}/" (sección 1/2 de "docs/kb-maintenance.md")
    Then cada documento nuevo queda en la carpeta de su fuente correspondiente
    And no se duplica contenido ya cubierto por el manual general de IDF ya indexado

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos ya en "data/raw/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista las fuentes nuevas en "failures"
    And "data/raw/manifest.json" incluye una entrada nueva por documento (url: null hasta
      rellenar a mano)
    And no quedan chunks huérfanos de ejecuciones previas (mismo cuidado que docs/kb-maintenance.md
      sección 4)

  Scenario: Nueva línea base RAGAS sobre el corpus ampliado
    Given el corpus ya ampliado e indexado
    And el fichero de resultados de E-09 post-T-05 ("tests/eval/results/e09_t02_ragas_full_scores.json")
      respaldado antes de sobrescribir (mismo cuidado que E-09 T-05, D-056 punto 3)
    When se relanza "scripts/run_ragas_eval.py" sobre el subconjunto informativo/otro_idioma (32 casos)
    Then se obtiene una línea base post-ampliación de Faithfulness/Answer Relevancy/Context
      Precision/Context Recall, previa a cualquier ajuste de BM25 (T-02)

  Scenario: Casos de contexto pobre revisados de forma dirigida
    Given los casos eval_03/06/08/11/13/15/20/23/25/27/65 (peor Context Precision/Recall de E-09)
    When se comparan sus scores de la línea base nueva frente a los de E-09
    Then se documenta cuáles mejoran como efecto colateral de la ampliación y cuáles siguen
      necesitando trabajo dirigido en tareas posteriores (T-02/T-05)

  Scenario: Marcos revisa y confirma la cobertura antes de continuar
    Given la línea base post-ampliación y el detalle de qué casos mejoraron
    When Marcos lo revisa
    Then confirma si la cobertura es suficiente para pasar a T-02 (calibración de BM25) o si
      hace falta una ronda adicional de fuentes
