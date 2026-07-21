# E-13 T-02 — Lote 2: 13 fichas MedlinePlus Genetics (P→F, incluye IPEX)
# Tipo: Configuración/curación de contenido — sin TDD, mismo patrón que T-01.
# Depende de T-01 (lista definitiva de 39 fichas ya generada, fichas 14-26 de esa lista).
#
# NOTA para task-start de T-02 (pendiente de formalizar — este fichero es aún el borrador de
# epic-start, sin corregir contra D-074/D-075/D-076/D-077/D-078 de T-01):
# - El conteo "39"/"fichas 14-26" hay que recalcularlo contra la lista real de T-01 (36 de
#   base + 4 de revisión ya resueltas, D-076) antes de aceptar el alcance tal cual.
# - D-078 (T-01): detect_language() puede clasificar mal frases cortas con términos técnicos
#   (ver rag/language.py). La verificación dirigida de IPEX debe fijar la redacción exacta a
#   probar tal cual la escribiría un usuario real (con/sin tildes) e incluir una comprobación
#   directa de detect_language() sobre esa frase, no solo la verificación de retrieval.

Feature: Lote 2 de MedlinePlus Genetics (P→F, incluye IPEX)

  Como responsable del proyecto AIIP
  Quiero incorporar el segundo lote de 13 fichas de MedlinePlus Genetics (fichas 14-26 de
  la lista definitiva de T-01, incluye Immune dysregulation-polyendocrinopathy-enteropathy-
  X-linked syndrome/IPEX)
  Para seguir cerrando el hueco de profundidad por enfermedad detectado en D-063

  Scenario: Lote 2 extraído del XML a data/raw/medlineplus_genetics/
    Given el lote 2 (fichas 14-26 de la lista definitiva generada en T-01)
    When el script de extracción de T-01 se reutiliza sobre este lote
    Then cada fichero nuevo contiene solo el contenido relevante de la ficha, guardado en
      "data/raw/medlineplus_genetics/"

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos del lote 2 ya en "data/raw/medlineplus_genetics/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista la fuente en "failures"
    And "data/raw/manifest.json" tiene una entrada nueva por documento con su URL real
    And no quedan chunks huérfanos de ejecuciones previas

  Scenario: Registro lingüístico del lote 2 revisado
    Given el lote 2 ya indexado
    When Marcos revisa una muestra del registro lingüístico de las fichas nuevas
    Then confirma que el tono es accesible para el perfil familiar, o señala ajustes
    And cualquier ajuste de prompt que se derive de esta revisión queda documentado como
      hallazgo abierto, no se aplica en esta tarea (mismo criterio que D-065)

  Scenario: Caso IPEX re-verificado tras el lote 2
    Given una consulta sobre IPEX (el síndrome que antes "robaba" la respuesta a XIAP, D-063)
      y el lote 2 ya indexado
    When se repite esa consulta contra el pipeline RAG real
    Then la respuesta recupera el chunk propio de IPEX, no uno centrado en otro síndrome
      (verificación dirigida puntual, no RAGAS completo — eso es T-04)

  Scenario: Marcos confirma el cierre del lote 2 antes de pasar a T-03
    Given los escenarios anteriores completados
    When Marcos los revisa
    Then confirma si el lote 2 queda cerrado o si hace falta una ronda adicional antes de
      pasar al lote 3
