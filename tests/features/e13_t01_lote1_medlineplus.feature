# E-13 T-01 — Preparación de datos + Lote 1: 13 fichas MedlinePlus Genetics (Z→P, incluye XIAP)
# Tipo: Configuración/curación de contenido — sin TDD, mismo patrón que E11-T01/E06-T07
# (rama + PR igualmente, precedente feedback_task_type_no_tdd).
#
# Contexto (D-063): consulta real sobre "xiap" devolvía una respuesta centrada en IPEX —
# rastreado a un chunk de manual-para-pacientes-y-familias-...-sexta.pdf donde XIAP aparece
# solo de pasada. MedlinePlus Genetics (NIH/NLM), página curada "Immune System and Disorders"
# (Title.Alternate: Primary Immunodeficiency Diseases), acota a 43 fichas; 4 ya cubiertas por
# data/raw/upiip/ (Bruton's/XLA, CGD, SCID genérico, CVID) — quedan 39 fichas nuevas.
#
# Decisiones de epic-start (21 jul 2026):
# - Extracción por script que parsea el XML masivo de MedlinePlus Genetics (no copia manual
#   página a página, a diferencia de E-11 T-01) — ventaja explícita de esta fuente sobre
#   Orphanet en D-063.
# - RAGAS completo solo en T-04, al final de los 3 lotes — cada lote solo lleva verificación
#   dirigida puntual, para no triplicar llamadas a Gemini por contenido que no toca
#   retrieval/algoritmo (a diferencia de E-11 T-02, que sí cambiaba código).
# - Los 4 temas solapados con upiip no se descartan de forma automática: revisión rápida
#   ficha por ficha, se añaden solo si aportan valor genuino (más completos/mejor redactados
#   para el perfil familiar) sin duplicar contenido sin criterio (mismo cuidado que E-11 T-01).

Feature: Preparación de datos y Lote 1 de MedlinePlus Genetics (Z→P, incluye XIAP)

  Como responsable del proyecto AIIP
  Quiero generar la lista definitiva de las 39 fichas nuevas de MedlinePlus Genetics e
  incorporar el primer lote de 13 (orden alfabético inverso, incluye X-linked
  lymphoproliferative disease/XIAP)
  Para cerrar el hueco de profundidad por enfermedad detectado en D-063, empezando por el
  caso que originó la investigación

  # Checklist de verificación manual — sigue docs/kb-maintenance.md

  Scenario: Lista definitiva de fichas nuevas generada a partir del XML masivo
    Given el XML completo de MedlinePlus Genetics descargado
    When un script lo filtra por la página curada "Immune System and Disorders" (43 fichas)
      y descarta el solapamiento ya confirmado con "data/raw/upiip/" (Bruton's/XLA, CGD,
      SCID genérico, CVID)
    Then produce la lista definitiva de 39 fichas nuevas, ordenadas alfabéticamente de forma
      inversa y divididas en 3 lotes de 13

  Scenario: Los 4 temas solapados se revisan ficha por ficha antes de descartarlos
    Given las 4 fichas de MedlinePlus Genetics que solapan con un documento ya indexado en
      "data/raw/upiip/"
    When Marcos compara cada ficha de MedlinePlus con el documento ya indexado
    Then decide, ficha por ficha, si aporta valor genuino (más completa o mejor redactada
      para el perfil familiar) y se añade igualmente, o si es redundante y se descarta
    And cualquier ficha añadida por este criterio queda fuera de los 3 lotes de 39 (no
      desplaza el orden alfabético inverso ya fijado)

  Scenario: Lote 1 extraído del XML a data/raw/medlineplus_genetics/
    Given el lote 1 (fichas 1-13 de la lista definitiva, incluye XIAP) y, si aplica, las
      fichas solapadas aprobadas en el escenario anterior
    When el script extrae el texto de cada ficha del XML y lo guarda en
      "data/raw/medlineplus_genetics/"
    Then cada fichero contiene solo el contenido relevante de la ficha (sin navegación,
      menú ni pie de página ajenos al contenido clínico)

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos ya en "data/raw/medlineplus_genetics/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista la fuente nueva en "failures"
    And "data/raw/manifest.json" tiene una entrada nueva por documento con su URL real (la
      URL de la ficha es conocida de antemano, no queda "null")
    And no quedan chunks huérfanos de ejecuciones previas

  Scenario: Fuente añadida a docs/kb-sources.md
    Given el lote 1 ya indexado sin fallos
    When se actualiza "docs/kb-sources.md" (perfil familiar)
    Then la fila de MedlinePlus Genetics refleja el estado real de avance (sigue "Propuesta"
      hasta que T-04 la cierre como "Validada")

  Scenario: Registro lingüístico del lote 1 revisado
    Given el lote 1 ya indexado
    When Marcos revisa una muestra del registro lingüístico de las fichas nuevas
    Then confirma que el tono es accesible para el perfil familiar, o señala ajustes
    And cualquier ajuste de prompt que se derive de esta revisión queda documentado como
      hallazgo abierto, no se aplica en esta tarea (mismo criterio que D-065)

  Scenario: Caso original XIAP/IPEX re-verificado tras el lote 1
    Given la consulta original que motivó E-13 ("xiap" devolviendo una respuesta centrada
      en IPEX, D-063) y el lote 1 ya indexado
    When se repite esa consulta contra el pipeline RAG real
    Then la respuesta recupera el chunk correcto sobre XIAP (verificación dirigida puntual,
      no RAGAS completo — eso es T-04)

  Scenario: Marcos confirma el cierre del lote 1 antes de pasar a T-02
    Given los escenarios anteriores completados
    When Marcos los revisa
    Then confirma si el lote 1 queda cerrado o si hace falta una ronda adicional antes de
      pasar al lote 2
