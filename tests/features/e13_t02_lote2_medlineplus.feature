# E-13 T-02 — Lote 2: 13 fichas MedlinePlus Genetics (O→D, incluye IPEX)
# Tipo: Configuración/curación de contenido — sin TDD, mismo patrón que T-01.
# Depende de T-01 (lista definitiva de 36 fichas de base ya generada, D-075/D-076; fichas
# 14-26 de esa lista).
#
# Formalizado en task-start (21 jul 2026):
# - Corrige el rango del borrador de epic-start ("P→F") a "O→D" — la última ficha de base de
#   Lote 1 ya es "PGM3-congenital disorder of glycosylation" (posición 13, letra P), confirmado
#   contra los 17 ficheros ya extraídos en data/raw/medlineplus_genetics/, así que Lote 2 no
#   puede volver a empezar en "P" sin solaparse.
# - Este sandbox de Cowork no tiene salida de red hacia medlineplus.gov (--build-list falla con
#   403 en el proxy) — los 13 títulos exactos de las posiciones 14-26 y el slug/título exacto
#   de IPEX quedan sin verificar de forma independiente aquí. Antigravity los valida ejecutando
#   "python scripts/extract_medlineplus_genetics.py --build-list" al arrancar la tarea.
# - D-078 (T-01): detect_language() puede clasificar mal frases cortas con términos técnicos
#   (rag/language.py). La verificación dirigida de IPEX fija la redacción exacta a probar tal
#   cual la escribiría un usuario real e incluye una comprobación directa de detect_language()
#   sobre esa frase, no solo la verificación de retrieval (mismo patrón que cerró T-01).

Feature: Lote 2 de MedlinePlus Genetics (O→D, incluye IPEX)

  Como responsable del proyecto AIIP
  Quiero incorporar el segundo lote de 13 fichas de MedlinePlus Genetics (fichas 14-26 de
  la lista definitiva de T-01, incluye Immune dysregulation-polyendocrinopathy-enteropathy-
  X-linked syndrome/IPEX)
  Para seguir cerrando el hueco de profundidad por enfermedad detectado en D-063

  Scenario: Lote 2 extraído del XML a data/raw/medlineplus_genetics/
    Given el lote 2 (fichas 14-26 de la lista definitiva generada en T-01, validadas de nuevo
      con "--build-list" al arrancar la tarea por la falta de red en Cowork)
    When el script de extracción de T-01 se reutiliza sobre este lote ("--extract-batch 14 26")
    Then cada fichero nuevo contiene el contenido relevante de la ficha (descripción + genes
      relacionados + causas, D-077), guardado en "data/raw/medlineplus_genetics/"

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos del lote 2 ya en "data/raw/medlineplus_genetics/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista la fuente en "failures"
    And "data/raw/manifest.json" tiene una entrada nueva por documento, con su URL real
      rellenada vía "--fill-manifest-urls" (D-073)
    And no quedan chunks huérfanos de ejecuciones previas

  Scenario: Registro lingüístico del lote 2 revisado
    Given el lote 2 ya indexado
    When Marcos revisa una muestra del registro lingüístico de las fichas nuevas
    Then confirma que el tono es accesible para el perfil familiar, o señala ajustes
    And cualquier ajuste de prompt que se derive de esta revisión queda documentado como
      hallazgo abierto, no se aplica en esta tarea (mismo criterio que D-065)

  Scenario: Caso IPEX re-verificado tras el lote 2
    Given una consulta sobre IPEX (el síndrome que antes "robaba" la respuesta a XIAP, D-063),
      la redacción exacta tal cual la escribiría un usuario real, y el lote 2 ya indexado
    When se repite esa consulta contra el pipeline RAG real, incluyendo una comprobación
      directa de detect_language() sobre la frase exacta (determinista, sin llamar a Gemini)
    Then la respuesta recupera el chunk propio de IPEX, no uno centrado en otro síndrome, y
      detect_language() clasifica la frase en el idioma correcto con margen suficiente (D-078)
      — verificación dirigida puntual, no RAGAS completo (eso es T-04)

  Scenario: Marcos confirma el cierre del lote 2 antes de pasar a T-03
    Given los escenarios anteriores completados
    When Marcos los revisa
    Then confirma si el lote 2 queda cerrado o si hace falta una ronda adicional antes de
      pasar al lote 3
