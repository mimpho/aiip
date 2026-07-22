# E-13 T-03 — Lote 3: 10 fichas MedlinePlus Genetics (posiciones 27-36, C→A)
# Tipo: Configuración/curación de contenido — sin TDD, rama + PR (mismo patrón que T-01/T-02,
# feedback_task_type_no_tdd).
# Depende de T-01 (lista definitiva de 36 fichas de base, D-075) y T-02 (Lote 2 ya indexado,
# 26 de esas 36 fichas ya extraídas entre T-01 y T-02).
# Sin caso de verificación dirigida propio (ningún tema de este lote motivó la épica, D-063) —
# pero sí lleva un escenario de detect_language() sobre una frase representativa del lote,
# resolución del hallazgo de proceso de D-078 (D-079).
#
# Corrección de cifras (task-start T-03, 22 jul 2026): el borrador de epic-start decía "13
# fichas, posiciones 27-39, 39 fichas nuevas en total" — cifras nunca recalculadas tras D-075/
# D-076 (mismo desfase que ya se corrigió en el .feature de T-01). Cifras reales: Lote 3 = 10
# fichas (27-36, C→A); total E-13 tras este lote = 40 fichas nuevas (36 de base en 3 lotes + 4
# de revisión ya extraídas en T-01, D-076). Confirmado contra data/raw/medlineplus_genetics/,
# que ya contiene 30 ficheros (13 Lote1 + 13 Lote2 + 4 de revisión) antes de ejecutar T-03.
#
# Mismo caveat que T-02: este sandbox de Cowork no tiene salida de red hacia medlineplus.gov
# (--build-list da 403 en el proxy) — los 10 títulos exactos de las posiciones 27-36 quedan sin
# verificar de forma independiente aquí. Antigravity los valida ejecutando
# "python scripts/extract_medlineplus_genetics.py --build-list" al arrancar la tarea.

Feature: Lote 3 de MedlinePlus Genetics (posiciones 27-36, C→A)

  Como responsable del proyecto AIIP
  Quiero incorporar el tercer y último lote de 10 fichas de MedlinePlus Genetics (fichas
  27-36 de la lista definitiva de T-01, orden alfabético inverso, rango real C→A)
  Para completar la ampliación de KB de E-13 antes de la remedición final

  Scenario: Lote 3 extraído del XML a data/raw/medlineplus_genetics/
    Given el lote 3 (fichas 27-36 de la lista definitiva generada en T-01, validadas de nuevo
      con "--build-list" al arrancar la tarea por la falta de red en Cowork)
    When el script de extracción de T-01 se reutiliza sobre este lote ("--extract-batch 27 36")
    Then cada fichero nuevo contiene el contenido relevante de la ficha (descripción + genes
      relacionados + causas, D-077), guardado en "data/raw/medlineplus_genetics/"

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos del lote 3 ya en "data/raw/medlineplus_genetics/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista la fuente en "failures"
    And "data/raw/manifest.json" tiene una entrada nueva por documento, con su URL real
      rellenada vía "--fill-manifest-urls" (D-073)
    And no quedan chunks huérfanos de ejecuciones previas
    And las 40 fichas nuevas de E-13 (36 de base en los 3 lotes + 4 de revisión, D-076) están
      ya indexadas en su totalidad

  Scenario: Registro lingüístico del lote 3 revisado
    Given el lote 3 ya indexado
    When Marcos revisa una muestra del registro lingüístico de las fichas nuevas
    Then confirma que el tono es accesible para el perfil familiar, o señala ajustes
    And cualquier ajuste de prompt que se derive de esta revisión queda documentado como
      hallazgo abierto, no se aplica en esta tarea (mismo criterio que D-065)

  Scenario: detect_language() verificado sobre una frase representativa del lote 3 (D-079)
    Given una frase corta y realista sobre una de las fichas nuevas del lote 3 (elegida durante
      la ejecución de la tarea, sin caso de contenido propio a diferencia de XIAP/IPEX)
    When se llama a detect_language() sobre esa frase tal cual la escribiría un usuario real
      (determinista, sin llamar a Gemini)
    Then clasifica el idioma correcto con un margen de confianza igual o superior a 0.2 (umbral
      de D-078); si algún caso legítimo bajara de ese margen, se documenta como hallazgo abierto
      para revisar el umbral, no se ajusta en esta tarea

  Scenario: Marcos confirma el cierre del lote 3 antes de pasar a T-04
    Given los escenarios anteriores completados
    When Marcos los revisa
    Then confirma si el lote 3 queda cerrado o si hace falta una ronda adicional antes de
      pasar a la remedición final (T-04), que cierra E-13 con las 40 fichas nuevas ya indexadas
