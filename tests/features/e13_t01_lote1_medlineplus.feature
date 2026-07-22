# E-13 T-01 — Preparación de datos + Lote 1: 13 fichas MedlinePlus Genetics (Z→P, incluye XIAP)
# Tipo: Configuración/curación de contenido — sin TDD, mismo patrón que E11-T01/E06-T07
# (rama + PR igualmente, precedente feedback_task_type_no_tdd).
#
# Contexto (D-063): consulta real sobre "xiap" devolvía una respuesta centrada en IPEX —
# rastreado a un chunk de manual-para-pacientes-y-familias-...-sexta.pdf donde XIAP aparece
# solo de pasada. MedlinePlus Genetics (NIH/NLM), página curada "Immune System and Disorders"
# (Title.Alternate: Primary Immunodeficiency Diseases), acota a 43 fichas; 3 ya cubiertas de
# forma exacta por data/raw/upiip/ (Bruton's/XLA, CGD, CVID) — quedan 39 fichas nuevas de base.
# El cuarto solapamiento asumido inicialmente ("SCID genérico") se corrigió en D-074: son 3
# subtipos específicos de SCID, no una coincidencia 1:1 — ver escenario de solapamiento.
# D-075 (ejecución T-01): apareció un quinto candidato no detectado antes ("22q11.2 deletion
# syndrome" = síndrome de DiGeorge, ya indexado como upiip/09_Sindrome_DiGeorge_ES.pdf) —
# mismo criterio de revisión ficha por ficha que los 3 subtipos de SCID. Con la lista real
# (43 totales, 3 solapamientos exactos, 4 fichas de revisión), la base de los 3 lotes es 36
# fichas, no 39 — el "39" de D-063 nunca se recalculó tras D-074. Lote 1 se mantiene en 13
# (Z→P, XIAP en posición 2); Lote 2 pasa a fichas 14-26 (O→D, IPEX en posición 20); Lote 3
# queda en 10 fichas (27-36, C→A), no 13.
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
#
# Decisiones de task-start (21 jul 2026):
# - D-073: fuente del XML confirmada — compendio completo en https://medlineplus.gov/download/
#   ghr-summaries.xml (índice de títulos/URLs en https://medlineplus.gov/download/
#   TopicIndex.xml). Deja de ser una precondición externa — el script la descarga. El script lee
#   la URL real de cada ficha directamente del elemento <ghr-page> de su entrada en el XML (no
#   hace falta derivarla de un slug) y rellena el manifest con ella inmediatamente tras el
#   reingest, sin modificar ingestion/manifest.py::sync_entry().
# - D-073: el script acepta el rango de fichas (lote) como parámetro — se reutiliza sin
#   reescritura en T-02 y T-03.
# - D-074: el solapamiento "SCID genérico" no es 1:1 — las 43 fichas de la página curada
#   incluyen 3 subtipos específicos de SCID (JAK3-deficient, X-linked, ZAP70-related), ninguno
#   idéntico al documento genérico ya indexado. Se revisan los 3 ficha por ficha.
# - D-076: resuelta la revisión ficha por ficha — las 4 candidatas (SCID x3 + DiGeorge/22q11.2)
#   se incluyen, ninguna es duplicado exacto. Total E-13: 40 fichas nuevas (36 en 3 lotes + 4).
# - D-077 (verificación en producción tras indexar): "Description" (XML/JSON masivo) no incluye
#   la sección "Causes" de la página — ahí es donde se explica qué gen causa qué subtipo. El
#   script hace una petición adicional por ficha a la página individual para scrapear "Causes"
#   y evitar que la respuesta dependa de que Gemini complete esa relación con conocimiento
#   propio en vez de con la KB (principio de grounding, D-059).
# - D-078 (verificación en producción tras D-077): "que es el xiap" (sin tilde en "qué")
#   devolvía un volcado del prompt cortado a media frase. No era D-077 ni contenido duplicado
#   (descartado por aislamiento de variable) — detect_language() (rag/language.py) clasificaba
#   esa frase como catalán con un margen de confianza de solo 0.035-0.05 (empate técnico),
#   forzando al modelo a traducir el contexto en vez de responder y agotando max_output_tokens.
#   Bug preexistente a E-13, expuesto por escribir justo la palabra que originó la épica (D-063).
#   Corregido con un margen mínimo de confianza (0.2) en detect_language(), sin afectar a
#   ningún caso ya validado.

Feature: Preparación de datos y Lote 1 de MedlinePlus Genetics (Z→P, incluye XIAP)

  Como responsable del proyecto AIIP
  Quiero generar la lista definitiva de las 36 fichas nuevas de base de MedlinePlus Genetics
  (D-075) e
  incorporar el primer lote de 13 (orden alfabético inverso, incluye X-linked
  lymphoproliferative disease/XIAP)
  Para cerrar el hueco de profundidad por enfermedad detectado en D-063, empezando por el
  caso que originó la investigación

  # Checklist de verificación manual — sigue docs/kb-maintenance.md

  Scenario: Lista definitiva de fichas nuevas generada a partir del XML masivo
    Given un script que descarga "https://medlineplus.gov/download/ghr-summaries.xml"
      (compendio completo de MedlinePlus Genetics)
    When el script lo filtra por la página curada "Immune System and Disorders" (43 fichas)
      y descarta el solapamiento exacto ya confirmado con "data/raw/upiip/" (Bruton's/XLA,
      CGD, CVID) — las 4 fichas de revisión (SCID + DiGeorge/22q11.2) se resuelven aparte, ver
      escenario siguiente (D-074, D-075)
    Then produce la lista definitiva de 36 fichas nuevas de base, ordenadas alfabéticamente de
      forma inversa y divididas en 3 lotes (13, 13 y 10 — D-075 corrige el "39"/"3 lotes de 13"
      original de D-063, nunca recalculado tras D-074)

  Scenario: Los temas solapados se revisan ficha por ficha antes de descartarlos
    Given las 3 fichas de MedlinePlus Genetics que solapan de forma exacta con un documento ya
      indexado en "data/raw/upiip/" (Bruton's/XLA, CGD, CVID), las 3 fichas de subtipo
      específico de SCID (JAK3-deficient, X-linked, ZAP70-related) que se comparan contra el
      único documento genérico de SCID ya indexado ("04_Immunodeficiencia_Combinada_Greu_ES.pdf",
      D-074 — ninguna de las 43 fichas de la página curada es "SCID genérico"), y "22q11.2
      deletion syndrome" que se compara contra "09_Sindrome_DiGeorge_ES.pdf" (misma entidad
      clínica bajo otro nombre, hallazgo de ejecución de T-01, D-075)
    When Marcos compara cada ficha de MedlinePlus con el documento ya indexado correspondiente
    Then decide, ficha por ficha, si aporta valor genuino (más completa o mejor redactada
      para el perfil familiar) y se añade igualmente, o si es redundante y se descarta — para
      los 3 subtipos de SCID y para DiGeorge/22q11.2 puede incluir cualquier combinación, ya
      que ninguno es un duplicado exacto del documento ya indexado correspondiente
    And cualquier ficha añadida por este criterio queda fuera de los 3 lotes de 36 (no
      desplaza el orden alfabético inverso ya fijado)

    # Resuelto (D-076): las 4 candidatas se incluyen — ninguna es duplicado exacto. Los
    # documentos genéricos/antiguos de upiip no nombran ningún gen causante; las 4 fichas de
    # MedlinePlus sí (TBX1/COMT para 22q11.2, JAK3/IL2RG/ZAP70 para los subtipos de SCID).
    # Total E-13 tras esta resolución: 40 fichas nuevas (36 en 3 lotes + estas 4 fuera de la
    # numeración). Se extraen con --extract-one dentro del alcance de T-01.

  Scenario: Lote 1 extraído del XML a data/raw/medlineplus_genetics/
    Given el lote 1 (fichas 1-13 de la lista definitiva, incluye XIAP), las 4 fichas de
      revisión ya incluidas (D-076), y, para cada una, su sección "Causes" obtenida de la
      página individual (D-077 — no está en el XML/JSON masivo)
    When el script extrae el texto de descripción del XML, añade "Related gene(s)" y el
      contenido de "Causes" scrapeado de "https://medlineplus.gov/genetics/condition/{slug}/",
      y lo guarda en "data/raw/medlineplus_genetics/", aceptando el rango de fichas (lote)
      como parámetro
    Then cada fichero contiene el contenido relevante de la ficha (descripción + genes
      relacionados + causas, sin navegación, menú ni pie de página ajenos al contenido
      clínico) — incluye la relación causal gen→subtipo explícita, no solo el símbolo del gen
    And el script queda reutilizable sin reescritura para los lotes 2 y 3 (T-02/T-03)
    And si una ficha no tiene sección "Causes", el script continúa sin fallar y registra un
      aviso (D-077)

  Scenario: Reingesta sin huérfanos en ChromaDB
    Given los documentos nuevos ya en "data/raw/medlineplus_genetics/"
    When se ejecuta "python scripts/smoke_test_rag.py --force-reingest"
    Then el resumen impreso no lista la fuente nueva en "failures"
    And "data/raw/manifest.json" tiene una entrada nueva por documento con su URL real, leída
      directamente del elemento "<ghr-page>" de cada ficha en el XML, inmediatamente tras el
      reingest — no queda "null" a la espera de un relleno manual posterior (D-073)
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
      en IPEX, D-063), la redacción exacta tal cual la escribiría un usuario real
      ("que es el xiap", sin tilde en "qué" — la variante que expuso D-078) y el lote 1 ya
      indexado
    When se repite esa consulta contra el pipeline RAG real, incluyendo una comprobación
      directa de detect_language() sobre la frase exacta (determinista, sin llamar a Gemini)
    Then la respuesta recupera el chunk correcto sobre XIAP y detect_language() clasifica la
      frase en el idioma correcto con margen suficiente (D-078) — verificación dirigida
      puntual, no RAGAS completo (eso es T-04)

  Scenario: Marcos confirma el cierre del lote 1 antes de pasar a T-02
    Given los escenarios anteriores completados
    When Marcos los revisa
    Then confirma si el lote 1 queda cerrado o si hace falta una ronda adicional antes de
      pasar al lote 2
