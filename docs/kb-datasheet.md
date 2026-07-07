# Datasheet for AI and medical datasets (DAIMS): "AIIP — Knowledge Base, perfil familiar"

> Adaptación del framework DAIMS (Marandi, Frahm, Milojevic — arXiv 2501.14094, 2025), que a su vez
> extiende "Datasheets for Datasets" (Gebru et al., 2018), a un corpus de **documentos de texto**
> (guías divulgativas y clínicas) usado como base de recuperación (RAG) — no a un dataset tabular
> de instancias-paciente, que es el caso de uso original de DAIMS.
>
> Donde una pregunta de la plantilla asume datos tabulares (ID de paciente, variable outcome,
> splits train/test), se responde "no relevante, porque..." siguiendo la instrucción propia de
> DAIMS, en vez de omitirla.
>
> Fuente de verdad de las fuentes indexadas: [`docs/kb-sources.md`](kb-sources.md) (no se duplica
> aquí su contenido). Trazabilidad de checksum/URL/fecha por documento: `data/raw/manifest.json`
> (D-021, no versionado en el repo).
>
> Este fichero se mantiene bajo el nombre `docs/kb-datasheet.md` (convención de `docs/` del
> repositorio AIIP) en vez del nombre versionado que sugiere DAIMS
> (`DAIMS_DatasetName_DDMMYYYY.md`) — ver sección 8.

---

## 1) Motivation

### a) ¿Para qué se creó este corpus? ¿Había una tarea específica en mente?

Sí. El corpus alimenta el pipeline RAG (Retrieval-Augmented Generation) del asistente conversacional
AIIP para el perfil **familiar** — familias de pacientes pediátricos con Inmunodeficiencias
Primarias (IDP). La tarea es recuperación semántica de pasajes relevantes (chunks) para fundamentar
las respuestas del asistente con fuentes divulgativas y clínicas validadas, en vez de depender solo
del conocimiento paramétrico del LLM.

### b) ¿Quién lo creó y en nombre de qué entidad?

Marcos, autor de este Trabajo de Fin de Máster (TFM — Máster en Inteligencia Artificial), con
sugerencias de fuentes aportadas por Jacques Rivière (inmunólogo colaborador del proyecto). No hay
una entidad institucional distinta del propio TFM.

### c) ¿Quién financió la creación del corpus?

No relevante — proyecto académico de TFM sin financiación externa asociada.

### d) ¿Algún otro comentario?

El corpus se reúne durante la épica E-06 (julio de 2026) con prioridad al desarrollo funcional de
la herramienta sobre el rigor exhaustivo de fuentes — selección abierta y ampliable a propósito
(ver `backlog/ideas.md`, nota de `kb-sources.md`).

---

## 2) Composition

### a) ¿Hay múltiples tipos de instancia?

Un único tipo: documentos de texto (páginas HTML de guías divulgativas y PDFs de protocolos/guías
clínicas), convertidos a objetos `Document` de LangChain con metadatos (`source`, `filename`,
`language`, `date_indexed`, `profile`).

### b) ¿Cuántas instancias hay en total?

El recuento exacto por fuente vive en `data/raw/manifest.json` (checksum, URL, fecha — no
versionado en el repo por tamaño/copyright). A la fecha de esta redacción el corpus organiza sus
fuentes crudas en carpetas por origen (UPIIP, IPOPI, IDF, AFPA/HAS) más un documento suelto —
ver estructura completa en `docs/kb-sources.md`. No se copian aquí cifras exactas para evitar que
este fichero quede desactualizado respecto al manifest real.

### c) ¿Contiene todas las instancias disponibles o es un subconjunto?

Es un subconjunto deliberado y no exhaustivo: selección de fuentes relevantes para el perfil
familiar de IDP pediátrica, guiada por el PRD v1.9 y por enlaces sugeridos por Jacques Rivière.
Fuentes candidatas adicionales ("Propuesta"/"Por explorar" en `kb-sources.md`) quedan fuera del
corpus indexado en esta épica — ver sección 7 (Maintenance).

### d) ¿Qué datos componen cada instancia?

Texto extraído de HTML/PDF ("raw"), sin transformación de contenido más allá de la extracción del
loader (`ingestion/loader.py`) y el troceado en chunks (`ingestion/chunker.py`, T-03). No se generan
features derivadas del contenido (no hay extracción de entidades, clasificación, etc.).

### e) ¿Hay una etiqueta, target u outcome asociado a cada instancia?

No relevante — el corpus no es un dataset de entrenamiento supervisado, es una base de recuperación
semántica (RAG). No existe variable outcome.

### f) ¿Falta información en instancias individuales?

Sí, en dos sentidos: (1) ficheros con formato no soportado o corruptos se omiten silenciosamente
con aviso (`warnings.warn` + `continue` en `loader.py`, D-024) en vez de bloquear el resto del
pipeline; (2) fuentes candidatas aún no confirmadas (revisión consultiva de Jacques Rivière,
no bloqueante) no están representadas todavía.

### g) ¿Hay relaciones explícitas entre instancias?

No — no hay pacientes ni vínculos familiares en este corpus (es contenido editorial de terceros,
no historiales). Cada documento es independiente; su procedencia se traza por `source`+`filename`.

### h) ¿Hay splits recomendados (train/dev/test)?

No relevante — no es un dataset de entrenamiento de ML, es un corpus de recuperación para RAG. No
aplican splits train/validation/test.

### i) ¿Hay datasets similares?

Sí, para un futuro perfil profesional (Fase 2B, condicional): Orphanet, ESID y PubMed, ya validadas
en el PRD para ese perfil pero **no indexadas** en esta épica (ver `docs/kb-sources.md`, sección
Perfil Profesional).

### j) ¿Es autocontenido o depende de recursos externos?

Depende de recursos externos: los documentos originales viven en las webs de las organizaciones de
origen (ipopi.org, primaryimmune.org, upiip.com, afpa.org). No hay garantía de que permanezcan
disponibles o sin cambios; la única versión archivada es la copia local en `data/raw/` (gitignored,
fuera del repo por copyright), trazada por checksum en `manifest.json`. No hay archivo oficial
versionado más allá de esa copia local/Drive.

### k) ¿Contiene datos que puedan considerarse confidenciales?

No — son publicaciones divulgativas/clínicas ya públicas de las organizaciones de origen, no
historiales clínicos ni comunicaciones privadas.

### l) ¿Contiene datos que, vistos directamente, puedan resultar ofensivos o generar ansiedad?

No, más allá de la naturaleza propia del tema (síntomas y signos de alarma de una enfermedad
pediátrica), tratado en tono divulgativo/clínico estándar por las fuentes originales.

### m) ¿El corpus se relaciona solo con no-humanos?

No — no aplica, se salta el resto de preguntas de esta sección solo si la respuesta fuera sí.

### n) ¿Identifica subpoblaciones?

No de forma explícita — el corpus no segmenta por edad/sexo u otra variable; su audiencia implícita
(familias de pacientes pediátricos con IDP) es la que define el perfil "familiar" del proyecto, no
una subpoblación dentro del propio corpus.

### o) ¿Es posible identificar individuos a partir del corpus?

No — son documentos editoriales de organizaciones, no contienen datos personales de pacientes.

### p) ¿Contiene datos que puedan considerarse sensibles?

No a nivel de dato personal (no hay individuos identificables). El *contenido* trata información de
salud (IDP) de forma general y divulgativa, no datos de salud de una persona concreta —
distinto del principio de privacidad por diseño de `AGENTS.md`/D-009, que aplica a los datos que
generan los *usuarios finales* de AIIP (conversaciones, cuentas en Supabase), no a este corpus de
fuentes de terceros.

### q) ¿Algún otro comentario?

No relevante adicional.

---

## 3) Collection process

### a) ¿Cómo se adquirió el dato de cada instancia?

Observado directamente: descarga manual de páginas HTML y PDFs publicados por las organizaciones de
origen. No son datos reportados por sujetos ni inferidos/derivados de otros datos.

### b) ¿Qué mecanismos o procedimientos se usaron para recolectar el dato?

Curación manual humana (Marcos): navegación de las webs oficiales (IPOPI, IDF/primaryimmune.org,
upiip.com, AFPA/HAS) y descarga de los documentos relevantes, organizados por carpeta de fuente en
Google Drive (`AIIP/data/raw/`) y localmente en `data/raw/` (gitignored). Validación por revisión
visual antes de incluir cada fuente; sin apoyo de scraping automatizado.

### c) Si es una muestra de un conjunto mayor, ¿cuál fue la estrategia de muestreo?

No probabilística — selección determinista guiada por relevancia clínica/divulgativa para el
perfil familiar de IDP pediátrica (PRD v1.9 §5, enlaces sugeridos por Jacques Rivière).

### d) ¿Quién participó en la recolección y cómo fue compensado?

Marcos (autor del TFM), sin compensación económica — trabajo académico. Jacques Rivière colaboró
sugiriendo enlaces/fuentes en su rol de colaborador clínico del proyecto, sin compensación por esta
tarea concreta.

### e) ¿En qué periodo de tiempo se recolectó el dato?

Durante la épica E-06 (julio de 2026). No necesariamente coincide con la fecha de creación de cada
documento original (algunas guías fuente son de años anteriores) — la fecha de creación de cada
documento se conserva, cuando está disponible, como parte de su contenido, no como metadato
estructurado adicional en esta épica.

### f) ¿Se realizaron procesos de revisión ética (p. ej., comité institucional)?

No relevante — no es investigación primaria con sujetos humanos; son fuentes secundarias ya
publicadas públicamente por las organizaciones de origen. No requiere revisión de comité ético.

### g) ¿El corpus se relaciona solo con no-humanos?

No — no aplica, no se salta el resto de la sección.

### h) ¿El dato se recolectó directamente de los individuos o vía terceros?

Vía terceros — los documentos están escritos y publicados por las organizaciones de origen (IPOPI,
IDF, upiip.com, AFPA/HAS), no recolectados directamente de individuos/pacientes.

### i) ¿Se notificó a los individuos sobre la recolección?

No relevante — no se recolectan datos personales de individuos en este corpus.

### j) ¿Los individuos consintieron la recolección y uso de su dato?

No relevante — no aplica, mismo motivo que (i).

### k) Si se obtuvo consentimiento, ¿había mecanismo de revocación?

No relevante.

### l) ¿Se realizó un análisis de impacto (p. ej., evaluación de impacto de protección de datos)?

No relevante para este corpus (sin datos personales). El análisis de impacto de privacidad del
proyecto AIIP (D-009, `docs/security.md`) cubre los datos de los *usuarios finales* de la
aplicación, no las fuentes documentales de esta KB.

### m) ¿Algún otro comentario?

No relevante adicional.

---

## 4) Preprocessing, cleaning, labeling

### a) Checklist de limpieza y estandarización

> Adaptado de un corpus tabular a un corpus documental: cada "instancia" es un documento fuente
> (`source` + `filename`), no una fila de paciente.

| Cumplido | Con dudas | Ítem | Comentario |
|---|---|---|---|
| — | — | 1. Formato wide: cada fila es una instancia, cada columna una variable | No relevante, corpus documental no tabular |
| — | — | 2. Cada paciente tiene un ID único | No relevante, no hay pacientes; cada documento se identifica por `source`+`filename` en metadatos |
| Sí | — | 3. Sin caracteres Unicode corruptos | Adaptado: el corpus es multiidioma (ES/EN/CA/FR) y usa Unicode legítimo (acentos, ñ, ç); se verifica ausencia de bytes corruptos/ilegibles, no ausencia de Unicode |
| Sí | — | 4. Sin filas/columnas duplicadas | Adaptado: `manifest.json` (D-021) detecta duplicados por checksum; el pipeline borra chunks del documento antes de reinsertar (D-024), evitando duplicados de chunk |
| — | — | 5. Primera columna es el ID de paciente | No relevante, tabular |
| — | — | 6. Última columna es la variable outcome | No relevante, tabular |
| — | — | 7. Sin separadores de miles ni caracteres extra en números | No relevante, no hay datos numéricos tabulares |
| Sí | — | 8. Entradas faltantes marcadas de forma consistente | Ficheros que fallan al cargar se omiten con `warnings.warn` consistente (`loader.py`) |
| Sí | — | 9. Ninguna instancia con todas las variables vacías | El loader omite (warn + continue) ficheros ilegibles en vez de indexarlos vacíos |
| Sí | — | 10. Diccionario de datos que define variables, tipos y unidades | Adaptado: metadatos de cada chunk documentados en D-022 (`source`, `filename`, `language`, `date_indexed`, `profile`) |
| — | — | 11. Valores continuos dentro del rango del diccionario | No relevante, no hay variables continuas |
| — | — | 12. Categorías de variables categóricas listadas | No relevante en sentido tabular; único valor categórico es `profile="familiar"` (D-022), sin lógica de selección aún |
| — | — | 13. Categorías raras agrupadas | No relevante |
| — | — | 14. Variables perfectamente colineales eliminadas | No relevante |
| Con dudas | Sí | 15. Observaciones irrelevantes que sesgan resultados eliminadas | Parcial: algunas fuentes candidatas descartadas explícitamente en revisión (`backlog/ideas.md`), pero no hay proceso sistemático de detección de outliers documental |
| Sí | — | 16. Fecha y hora formateadas según el diccionario | `date_indexed` en formato ISO (`date.today().isoformat()`), generado en T-03 (D-022) |
| — | — | 17. Separador decimal "." | No relevante, no hay datos numéricos tabulares |
| Sí | — | 18. Entradas no inglesas traducidas | **Decisión explícita en contra**: no se traduce (D-022, amplía D-011) — cada fuente se indexa en su idioma original; bge-m3 resuelve cross-lingual retrieval en cualquier dirección |
| No | — | 19. Términos siguen estándares internacionales (MEDCIN/ICD/SNOMED) | No aplicado — las fuentes son guías divulgativas/clínicas de terceros, no se re-codifican con terminología estándar en esta épica; fuera del alcance de E-06 |
| — | — | 20. Todas las entradas siguen el mismo estándar | No relevante, ligado al ítem 19 |
| Sí | — | 21. Datos erróneos corregidos o eliminados | A nivel documento: ficheros corruptos se detectan (try/except en `loader.py`, D-024) y se omiten con aviso |
| — | — | 22. Missingness informativo codificado | No relevante, no hay codificación de "no testado" u homólogo en este corpus |
| — | — | 23. Variables irrelevantes para el estudio eliminadas | No relevante en sentido tabular |
| Sí | — | 24. Sin datos sensibles (nombre, dirección, ID de individuos) | El contenido es editorial público, sin datos personales de pacientes |

### b) ¿Se realizó algún otro preprocesamiento, limpieza o etiquetado?

Sí: troceado (chunking) con `RecursiveCharacterTextSplitter.from_huggingface_tokenizer` usando el
tokenizer real de bge-m3 (512 tokens, overlap 64 — D-022), y detección de idioma por documento
(`rag.language.detect_language`, D-017/D-022). No se aplica OCR — los formatos de origen (HTML,
PDF con texto extraíble) no lo requieren.

### c) ¿Hay consideraciones de error de medición en los procesos de preparación?

No relevante — no hay mediciones de instrumento; el único "error" posible es de extracción de texto
(PDF mal formateado), cubierto por el manejo de excepciones del loader (D-024).

### d) ¿Queda preprocesamiento pendiente?

Sí — las fuentes "Propuesta"/"Por explorar" de `kb-sources.md` (Acadip, AEDIP, guías clínicas
internas del equipo) no están todavía descargadas/procesadas. Ver sección 7 (Maintenance).

### e) ¿Se conservó el dato "raw" además del procesado?

Sí — `data/raw/` (crudo, gitignored, fuera del repo por copyright) se mantiene separado de la
colección `familiar` en ChromaDB (procesada/indexada). Trazabilidad entre ambos vía
`data/raw/manifest.json` (checksum, URL, fecha).

### f) ¿Está disponible el software usado para preprocesar/limpiar/etiquetar?

Sí — `ingestion/loader.py`, `ingestion/chunker.py`, `ingestion/indexer.py`, `ingestion/pipeline.py`
y `ingestion/manifest.py`, en este mismo repositorio (E-06).

### g) ¿El corpus incluye datos sintéticos o imputados?

No.

### h) ¿Hay variables equivalentes o secundarias del outcome?

No relevante — no hay outcome en este corpus.

### i) ¿Algún otro comentario?

No relevante adicional.

---

## 5) Uses

### a) ¿Se ha usado ya el corpus para una tarea particular?

Sí — recuperación semántica (RAG) para el asistente conversacional AIIP, perfil familiar (E-04,
pipeline `RAGPipeline`). No se han realizado análisis estadísticos ni inferencias sobre el corpus en
sí mismo.

### b) ¿Se ha usado para otras tareas?

No, por ahora.

### c) ¿Hay un repositorio que enlace papers/sistemas que usan el corpus?

No relevante fuera del propio repositorio AIIP (`README.md`, `docs/tech-spec.md`).

### d) ¿Para qué otras tareas podría usarse el corpus?

Evaluación RAGAS del pipeline (E-07), smoke test manual con datos reales (T-07 de esta misma épica),
y potencialmente una futura ampliación al perfil profesional si se decide indexar Orphanet/ESID/
PubMed (Fase 2B, condicional a decisión de alcance).

### e) ¿Algo de la composición o recolección que pueda impactar usos futuros?

Sí: (1) el corpus no es exhaustivo — prioriza avance funcional del TFM sobre cobertura completa de
fuentes; (2) cobertura desigual entre idiomas (más fuentes en ES/EN que en CA/FR); (3) no está
validado clínicamente al 100% — la revisión de Jacques Rivière sobre suficiencia de fuentes es
consultiva y no bloqueante (ver `backlog/epics.md`, nota de E-06). Un uso futuro fuera del contexto
familiar/pediátrico de IDP para el que se reunió debería revisar de nuevo esta cobertura.

### f) ¿Hay tareas para las que el corpus NO debería usarse?

Sí: no debe usarse como única fuente de decisión clínica — el asistente AIIP deriva siempre a
consulta médica ante cualquier duda (principio de Falso Negativo Cero, `AGENTS.md`). Tampoco debe
usarse todavía para el perfil profesional: sus fuentes (Orphanet, ESID, PubMed, HAS) no están
indexadas en esta épica.

### g) ¿Algún otro comentario?

No relevante adicional.

---

## 6) Distribution

### a) ¿Se distribuirá el corpus a terceros fuera de la entidad creadora?

No — uso interno del backend de AIIP (TFM), sin redistribución del corpus crudo ni procesado.

### b) ¿Cómo se distribuye? ¿Tiene DOI?

No se distribuye como artefacto independiente. El corpus procesado vive como colección `familiar`
en la instancia ChromaDB del backend de AIIP. Sin DOI.

### c) ¿Cuándo se distribuirá?

No relevante.

### d) ¿Se distribuirá bajo licencia/términos de uso?

Los documentos originales pertenecen a sus organizaciones de origen (IPOPI, IDF, upiip.com,
AFPA/HAS); el proyecto AIIP no reclama propiedad sobre su contenido. Uso exclusivamente educativo/
interno en el contexto de este TFM. Por esta razón los ficheros crudos viven fuera del repositorio
(Drive/local, `data/raw/`, gitignored) — ver `AGENTS.md`/`backlog/epics.md`.

### e) ¿Terceros han impuesto restricciones de PI sobre el dato?

Sí, implícitamente — el copyright de cada documento pertenece a su organización de origen (ver d).
No se han solicitado licencias explícitas de redistribución, porque no hay redistribución.

### f) ¿Aplican controles de exportación u otras restricciones regulatorias?

No relevante.

### g) ¿Algún otro comentario?

No relevante adicional.

---

## 7) Maintenance

### a) ¿Quién mantiene/aloja el corpus?

Marcos, como parte del repositorio AIIP.

### b) ¿Cómo se puede contactar al responsable?

mimpho@gmail.com

### c) ¿Hay una fe de erratas?

No, por ahora.

### d) ¿Se actualizará el corpus?

Sí, mediante el pipeline de ingesta reproducible (`run_ingestion_pipeline`, T-05): reprocesa el
corpus completo (borrado + reinserción por documento, D-024) cuando cambian las fuentes en
`data/raw/`. Fuentes pendientes de confirmar como ampliación futura (no bloqueante para esta épica):

- Acadip — PIDs (signos de alerta) y webinars (CA)
- AEDIP — 10 señales de aviso, clasificación de inmunodeficiencias, tratamiento con
  inmunoglobulinas, directorio de hospitales (ES)
- Protocolos internos del equipo de inmunología, pendientes de recepción (ES)
- Resultado final de la revisión consultiva de Jacques Rivière sobre suficiencia de fuentes

Ver `docs/kb-sources.md` para el estado actualizado de cada una.

### e) ¿Aplican límites de retención de datos?

No relevante — no son datos personales de individuos con derecho de retención/olvido, son
documentos públicos de terceros.

### f) ¿Se mantendrán versiones antiguas del corpus?

No hay versionado formal de snapshots del corpus. `data/raw/manifest.json` registra checksum y
fecha por documento, permitiendo detectar cuándo cambió una fuente respecto a la última ejecución
del pipeline.

### g) ¿Hay mecanismo para que terceros extiendan o contribuyan al corpus?

No formalizado como proceso abierto. En la práctica, Jacques Rivière (colaborador clínico) sugiere
fuentes nuevas de forma consultiva, que se incorporan a `kb-sources.md` como "Propuesta" hasta su
confirmación e indexación.

### h) ¿Algún otro comentario?

Pendiente de validación clínica consultiva de Jacques Rivière sobre si esta base de fuentes es
suficiente para el perfil familiar — no bloqueante para el cierre de esta épica (ver
`backlog/epics.md`, nota E-06).

---

## 8) Correspondence

| Nombre | Email | Afiliación | Secciones |
|---|---|---|---|
| Marcos | mimpho@gmail.com | TFM — Máster en Inteligencia Artificial | 1, 2, 3, 4, 5, 6, 7 |

---

## References

1. Marandi RZ, Frahm AS, Milojevic M. Datasheets for AI and medical datasets (DAIMS): a data
   validation and documentation framework before machine learning analysis in medical research.
   arXiv preprint arXiv:2501.14094. 2025. Available from: https://arxiv.org/abs/2501.14094
2. Gebru T, Morgenstern J, Vecchione B, Vaughan JW, Wallach H, Daumé H, et al. Datasheets for
   Datasets. 2018 Mar 23. Available from: http://arxiv.org/abs/1803.09010
3. `docs/kb-sources.md` — índice de fuentes de la KB de AIIP.
4. `decisions.md` — D-011, D-016, D-019, D-021, D-022, D-024.
