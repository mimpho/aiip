# E-13 T-03 — Lote 3: 13 fichas MedlinePlus Genetics (fichas restantes de la lista)
# Tipo: Configuración/curación de contenido — sin TDD, mismo patrón que T-01/T-02.
# Depende de T-01 (lista definitiva de 39 fichas, fichas 27-39 de esa lista).
# Sin caso de verificación dirigida propio (ningún tema de este lote motivó la épica).

Feature: Lote 3 de MedlinePlus Genetics (fichas restantes de la lista)

  Como responsable del proyecto AIIP
  Quiero incorporar el tercer y último lote de 13 fichas de MedlinePlus Genetics (fichas
  27-39 de la lista definitiva de T-01)
  Para completar la ampliación de KB de E-13 antes de la remedición final

  Scenario: Lote 3 extraído del XML a data/raw/medlineplus_genetics/
    Given el lote 3 (fichas 27-39 de la lista definitiva generada en T-01)
    When el script de extracción de T-01 se reutiliza sobre este lote
    Then cada fichero nuevo contiene solo el contenido relevante de la ficha, guardado en
      "data/raw/medlineplus_genetics/"

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos del lote 3 ya en "data/raw/medlineplus_genetics/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista la fuente en "failures"
    And "data/raw/manifest.json" tiene una entrada nueva por documento con su URL real
    And no quedan chunks huérfanos de ejecuciones previas
    And las 39 fichas nuevas (más las solapadas aprobadas en T-01, si las hubiera) están ya
      indexadas en su totalidad

  Scenario: Registro lingüístico del lote 3 revisado
    Given el lote 3 ya indexado
    When Marcos revisa una muestra del registro lingüístico de las fichas nuevas
    Then confirma que el tono es accesible para el perfil familiar, o señala ajustes
    And cualquier ajuste de prompt que se derive de esta revisión queda documentado como
      hallazgo abierto, no se aplica en esta tarea (mismo criterio que D-065)

  Scenario: Marcos confirma el cierre del lote 3 antes de pasar a T-04
    Given los escenarios anteriores completados
    When Marcos los revisa
    Then confirma si el lote 3 queda cerrado o si hace falta una ronda adicional antes de
      pasar a la remedición final (T-04)
