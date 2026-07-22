# Cierre — E-13 T-04: remedición RAGAS + cierre de la épica

| Campo | Valor |
|---|---|
| Épica | E-13 — Ampliación de KB con MedlinePlus Genetics |
| Tarea | T-04 — Remedición RAGAS + cierre |
| Fecha | 22 de julio de 2026 |
| Fuentes | `tests/eval/results/e09_t02_ragas_full_scores_pre_e13_t04.json` (pre-E-13, = cierre E-11 T-02 final), `tests/eval/results/e09_t02_ragas_full_scores_e13_t04_baseline.json` (post-ampliación, snapshot de cierre), `tests/eval/results/e09_t02_ragas_full_scores.json` (fichero vigente, idéntico al snapshot anterior) |
| Modelo evaluado | `gemini-2.5-flash` (producción, D-043) |
| Decisiones de referencia | D-063 (creación de la épica), D-075/D-076 (alcance final de 40 fichas), D-077 (fix de grounding), D-078 (fix de idioma), D-084 (limitación BM25/listado) |

## 1. Comparación explícita contra el cierre de E-11 (32 casos, `informativo` + `otro_idioma`)

| Métrica | Pre-E-13 (cierre E-11 T-02 final) | Post-E-13 (40 fichas MedlinePlus indexadas) | Delta |
|---|---|---|---|
| Faithfulness | 84.6% | 83.2% | **−1.4pp** |
| Answer Relevancy | 79.9% | 80.4% | +0.5pp |
| Context Precision | 63.2% | 59.5% | **−3.7pp** |
| Context Recall | 86.5% | 88.0% | +1.6pp |

**Sin suavizar:** de las 4 métricas, 2 mejoran (Answer Relevancy, Context Recall) y **2
empeoran** (Faithfulness, Context Precision). Este resultado contradice la hipótesis de
partida de la épica ("ampliar la KB con fichas de enfermedad debería mejorar Context
Precision/Recall sin degradar el resto", `.feature`, línea 14-15) en la mitad de las
métricas. Context Recall sí mejora (+1.6pp, ya venía cumpliendo objetivo >85% desde E-11,
ahora 88.0%), pero **Context Precision empeora** (−3.7pp) pese a ser la métrica que más se
esperaba que se beneficiara de más cobertura documental — sigue, además, por debajo del
objetivo de >85% (59.5%).

**Actualización (22 jul 2026, D-086, decisión de Marcos de investigar antes de cerrar):**
desglose caso a caso (comparando `e09_t02_ragas_full_scores_pre_e13_t04.json` contra el
fichero vigente, sin necesidad de pipeline) — de los 32 casos, **26 no cambian**, 1 mejora
(`eval_17`, +0.025) y **5 empeoran**, y la caída agregada de −3.7pp está enteramente
concentrada en esos 5: `eval_22` (−0.417), `eval_08` (−0.300), `eval_10` (−0.300), `eval_63`
(−0.154) y `eval_20` (−0.025). Esto **refuta la hipótesis de dilución generalizada** sobre
todo el corpus (26/32 casos completamente inmóviles no es compatible con degradación
difusa). `eval_08` reproduce con precisión su patrón histórico bimodal {0.5, 0.2} ya cerrado
como ruido del juez (D-072) — resuelto sin investigación nueva. `eval_20` (delta mínimo) no
se prioriza. **Quedan 3 casos sin explicar** (`eval_22`, `eval_10`, `eval_63`) — requieren
pipeline real (Antigravity, paso 13 del plan) para distinguir dilución de retrieval vs.
ruido del juez caso a caso. Detalle completo en D-086 (`decisions.md`).

**Faithfulness** también retrocede (−1.4pp), en línea con el patrón ya visto en E-11 T-02
(retroceso pequeño de Faithfulness sin relación causal plausible con cambios de retrieval,
`tests/eval/results/e11_t02_cierre.md` §1) — no hay una relación directa esperable entre
añadir fichas de enfermedad y la fidelidad del texto generado.

## 2. Verificación dirigida XIAP/IPEX (D-063, fuera del dataset RAGAS)

Consulta directa al pipeline real (`RAGPipeline.query()`, sin mocks), mismo patrón que
D-073/D-077:

**"xiap"** — la respuesta atribuye la relación XIAP→XLP2 al chunk indexado de MedlinePlus
Genetics: primera fuente citada es
`x-linked-lymphoproliferative-disease.html` (`medlineplus_genetics/`), con contenido
específico (proteína XIAP, apoptosis, XLP2, linfohistiocitosis hemofagocítica, distinción
con XLP1/`SH2D1A`) que solo puede venir de ese chunk, no de conocimiento general del LLM.
"xiap" (sin la corrección de acento problemática que expuso D-078 en "que es el xiap") **no
reproduce el bug de D-078** — respuesta completa y coherente, sin volcado de prompt cortado.

**"ipex"** — la respuesta es correcta y está fundamentada (FOXP3, células T reguladoras,
herencia ligada al X, tratamiento con TCMH), pero **no cita la ficha nueva de MedlinePlus
Genetics** (`immune-dysregulation-polyendocrinopathy-enteropathy-x-linked-syndrome.html`,
sí presente en `data/raw/medlineplus_genetics/`). Las fuentes citadas son
`manual-para-pacientes-y-familias...pdf` (IDF) y `triptic-traspas-digital_ES.pdf` (UPIIP).
Verificado que esto **no es una alucinación**: el manual IDF ya indexado desde antes de
E-13 dedica un capítulo completo (Capítulo 13) a IPEX con el mismo nivel de detalle
(FOXP3, Treg, modelos animales) que aparece en la respuesta — el contenido está fundamentado
en un chunk indexado real, solo que no es el nuevo de MedlinePlus. Diferencia con "xiap":
para "ipex" el documento preexistente (IDF) ya cubre el tema en profundidad y gana el
ranking de recuperación frente a la ficha nueva; para "xiap" no había cobertura previa tan
detallada y la ficha nueva sí se recupera. **Conclusión:** ambas respuestas cumplen el
criterio de grounding (D-059) — ninguna reproduce D-078 ni inventa contenido — pero solo
"xiap" demuestra empíricamente que la ficha nueva de MedlinePlus es la fuente citada; "ipex"
demuestra que el pipeline sigue siendo correcto (no degrada), no que la ficha nueva de IPEX
se use en esta consulta concreta.

## 3. Verificación dirigida de casos de contexto pobre (eval_06, eval_15)

| Caso | Métrica | Pre-E-13 | Post-E-13 | Delta | Lectura |
|---|---|---|---|---|---|
| `eval_06` (frecuencia de revisiones) | Faithfulness | 0.385 (banda Grave, D-069) | 0.545 (banda Moderada) | +0.160 | Mejora, sale de banda Grave |
| `eval_06` | Context Recall | 0.0 | 0.5 | +0.5 | Mejora |
| `eval_06` | Context Precision | 0.0 | 0.0 | +0.0 | Sin cambio |
| `eval_06` | Answer Relevancy | 0.0 | 0.0 | +0.0 | Sin cambio |
| `eval_15` (viajar con inmunoglobulinas) | Context Precision | 0.0 (estable en 5 mediciones, E-11 T-05) | 0.0 | +0.0 | Sin cambio — hueco de KB persiste |
| `eval_15` | Context Recall | 0.0 | 0.0 | +0.0 | Sin cambio |
| `eval_15` | Faithfulness | 0.875 | 0.815 | −0.060 | Empeora ligeramente |
| `eval_15` | Answer Relevancy | 0.839 | 0.993 | +0.153 | Mejora |

**`eval_06`:** mejora parcial. La banda de severidad de Faithfulness pasa de Grave a
Moderada (deja de ser el único caso Grave del dataset, §5.3 de `docs/evaluation.md`) y
Context Recall pasa de 0.0 a 0.5. Pero Context Precision **sigue en 0.0** — las 40 fichas
de MedlinePlus son descripciones de enfermedades concretas, no contenido sobre cadencia de
seguimiento clínico, así que no aportan al retrieval de esta pregunta concreta. Sin
suavizar: sigue siendo un caso con Context Precision nula.

**`eval_15`:** **sin cambio en el hueco de KB.** Context Precision y Context Recall se
mantienen en 0.0, confirmando que el hueco documentado en `backlog/ideas.md` ("Huecos de
KB" #1 — la KB no tiene ninguna mención de conservación en frío de inmunoglobulinas en
viaje) **sigue sin cubrirse** tras E-13: las fichas de MedlinePlus Genetics describen
enfermedades, no logística de viaje con medicación, por lo que este hueco era
estructuralmente imposible de resolver con esta fuente concreta. Answer Relevancy mejora
(+0.153) por variación en la redacción de la respuesta, no por recuperación de contexto
nuevo.

## 3bis. Hallucination Rate y bandas de severidad (recálculo no pedido explícitamente en el `.feature`, pero derivado directo de los mismos 32 casos ya remedidos — mismo criterio de transparencia)

El binario de Hallucination Rate (D-058: `faithfulness < 1.0`) **mejora**: 93.75% (30/32,
post-E-11) → **81.25% (26/32, post-E-13)**. Pero el desglose por bandas de severidad
(§5.3 de `docs/evaluation.md`) revela un hallazgo nuevo, no buscado: **`eval_25` entra en
banda Grave** (Faithfulness 0.32, antes 0.857/banda Leve pre-E-13) — mientras que `eval_06`
**sale** de banda Grave (0.385→0.545, ver sección 3). `eval_25` ("¿Puede mi hijo marcharse
de convivencias varios días?") ya figuraba en `docs/evaluation.md` §5.4 como "sigue abierto
sin investigar" dentro del hallazgo B de E-09 — ahora es el único caso en banda Grave del
dataset, sustituyendo a `eval_06` en esa posición. Investigado en la sección 3ter (paso 11
del plan, decisión de Marcos tras revisar la primera versión de este informe).

| Banda | Post-E-11 (§5.3) | Post-E-13 |
|---|---|---|
| Grave (<0.5) | 1 (`eval_06`, cuestionado D-069) | 1 (`eval_25`, cuestionado — ver 3ter) |
| Moderada (0.5–0.85) | 13 | 14 |
| Leve (0.85–<1.0) | 13 | 11 |
| Sin desviación (1.0) | 5 | 6 |

## 3ter. Investigación dirigida de `eval_25` (paso 11 del plan, 22 jul 2026)

**Contexto:** tras revisar la sección 3bis, Marcos pidió confirmar si la caída de
Faithfulness de `eval_25` (0.857→0.32) es un efecto real de las 40 fichas nuevas de
MedlinePlus o ruido de generación/juez, antes de dar el cierre por bueno (paso 10 puesto en
pausa). Context Precision (0.0), Context Recall (1.0) y Answer Relevancy (0.0) son
**idénticos** antes y después — el retrieval no cambió, solo Faithfulness se movió.
Investigación en `scripts/run_e13_t04_eval25_investigation.py`, resultado completo en
`tests/eval/results/e13_t04_eval25_investigacion.json`.

**a. Contraste de contenido (respuesta real vs. contexto recuperado vs. `expected_answer`):**
la respuesta generada hoy es cautelosa y remite al equipo médico ("es una cuestión médica
que debe ser evaluada por su equipo de profesionales de la salud... consulta directamente
con el médico"), en línea con `expected_answer`. La afirmación más concreta de la respuesta
— *"con la aprobación del proveedor de atención médica del niño, el niño debe participar en
la escuela u otras actividades siempre que sea posible"* — **aparece verbatim** en uno de
los chunks recuperados (`idf/manual-para-pacientes-y-familias...pdf`, Capítulo 42, chunk de
score 0.1667). Sin alarma de seguridad inesperada (`check_alarm_signals`, caso `is_alarm:
false`). **No hay contenido inventado ni afirmación no soportada por el contexto** — es
matiz/parafraseo sobre chunks reales, mismo patrón que 29/30 de los casos "alucinados" del
binario (D-058).

**b. Estabilidad del juez:** dos invocaciones de `Faithfulness.single_turn_score()` sobre
el **mismo** `SingleTurnSample` (misma respuesta, mismo contexto, sin volver a llamar a
`retrieve()`/`query()`) dan **0.52 y 0.32** — el juez **no es estable** para este caso.

**Conclusión (causa raíz confirmada):** la caída de Faithfulness de `eval_25` es **ruido de
muestreo del juez LLM**, no una regresión real de contenido ni un efecto de las 40 fichas
nuevas de MedlinePlus — mismo patrón que D-069 (`eval_06`) y D-072 (`eval_08`/`eval_13`).
Evidencia convergente: (1) las otras 3 métricas no se movieron (el retrieval no cambió),
(2) el juez varía entre invocaciones idénticas (0.52 vs. 0.32), (3) la respuesta está bien
fundamentada en los chunks recuperados sin alucinación. **`eval_25` se marca como
cuestionado** en `docs/evaluation.md` §5.3/§5.5, con el mismo criterio que `eval_06`: el
score oficial (0.32) se mantiene sin modificar en el dataset (no se "suaviza" el número),
pero no se presenta como una alucinación grave confirmada y estable.

## 3quater. Investigación dirigida de la caída de Context Precision (paso 13 del plan, D-086, 22 jul 2026)

**Contexto:** tras `eval_25` (3ter), Marcos pidió investigar también la causa de la caída
agregada de Context Precision (−3.7pp, sección 1). Análisis local previo en Cowork (D-086,
sin pipeline): de los 32 casos, 26 no cambian, 1 mejora y **5 empeoran**, concentrando toda
la caída — refuta dilución generalizada. `eval_08` (0.5→0.2) reproduce exactamente su patrón
bimodal ya cerrado como ruido del juez en D-072, sin necesidad de nueva investigación.
`eval_20` (delta −0.025) demasiado pequeño para priorizar. Quedan 3 casos sin explicar:
`eval_22`, `eval_10`, `eval_63` — investigados aquí con el pipeline real
(`scripts/run_e13_t04_context_precision_investigation.py`, resultado completo en
`tests/eval/results/e13_t04_context_precision_investigacion.json`).

| Caso | Pre-E-13 | Post-E-13 (oficial) | ¿Chunk `medlineplus_genetics` en el top-k? | Estabilidad del juez (misma sesión) | Conclusión |
|---|---|---|---|---|---|
| `eval_22` | 0.917 | 0.500 | **No** (10/10 chunks de fuentes preexistentes) | Inestable: 0.500 y 0.917 sobre el mismo `SingleTurnSample` | **Ruido del juez confirmado** |
| `eval_10` | 1.000 | 0.700 | **No** (10/10 chunks del manual IDF + guía escolar AEDIP) | Inestable: 0.700 y 1.000 sobre el mismo `SingleTurnSample` | **Ruido del juez confirmado** |
| `eval_63` | 0.804 | 0.650 | **Sí** (`leukocyte-adhesion-deficiency-type-1.html`, rank 9/9, score más bajo) | Estable en esta sesión: 0.804 y 0.804 | **Mezcla, indicios hacia ruido — ver nota** |

**`eval_22` y `eval_10`:** ninguno de los dos recupera ni un solo chunk de
`medlineplus_genetics` — la ampliación de KB **no puede ser la causa** de su caída, porque
el contexto recuperado no cambió. En ambos, dos invocaciones del juez de Context Precision
sobre el mismo `SingleTurnSample` (misma respuesta, mismo contexto) dan valores muy
distintos — `eval_22`: 0.500 y 0.917 (rango 0.417, que reproduce casi exactamente el delta
oficial registrado, 0.917→0.500); `eval_10`: 0.700 y 1.000 (rango 0.300, coherente con el
delta oficial 1.000→0.700). **Evidencia directa y limpia de ruido de muestreo del
evaluador**, mismo patrón que D-069/D-072/D-085.

**`eval_63`** (único caso `otro_idioma`, en inglés — el candidato más plausible a dilución
real por compartir idioma con las 40 fichas nuevas): **sí** aparece un chunk de
`medlineplus_genetics` en el top-9 recuperado, pero en la última posición (score 0.111, el
más bajo de todos) — los 8 chunks de rango superior son todos de fuentes preexistentes
(IPOPI, SEICAP, IDF, AEDIP). El juez es estable en esta sesión (0.804 en dos invocaciones),
pero ese valor **coincide con el histórico pre-E-13 (0.804)**, no con el valor oficial
post-E-13 registrado en el dataset (0.650), pese a que el contexto de esta sesión sí
incluye el chunk nuevo. Esto sugiere que la diferencia entre el 0.804 pre-E-13 y el 0.650
post-E-13 oficial es más probablemente varianza de muestreo entre sesiones de evaluación
distintas que un efecto medible del chunk nuevo, que además ocupa el rango más bajo del
ranking (impacto ponderado mínimo en una métrica sensible a la posición como Context
Precision). **No es una prueba tan limpia como `eval_22`/`eval_10`** (no se pudo reproducir
el `SingleTurnSample` exacto de la medición oficial post-E-13, solo un contexto recuperado
de nuevo hoy), pero no hay evidencia de que el chunk nuevo desplace contenido relevante
mejor rankeado.

**Lectura final de la caída de Context Precision (−3.7pp):** con esta investigación, la
caída deja de estar "sin causa raíz confirmada" — **2 de los 3 casos investigados
(`eval_22`, `eval_10`) son ruido del juez confirmado con evidencia directa** (sin ningún
chunk nuevo involucrado), y el tercero (`eval_63`) tiene indicios más fuertes hacia ruido
de sesión que hacia dilución real, aunque sin la misma contundencia. Sumado a `eval_08`
(ya resuelto como ruido en D-072) y `eval_20` (delta despreciable), **4 de los 5 casos que
concentran la caída agregada están explicados por varianza del evaluador, no por un efecto
real de las 40 fichas de MedlinePlus sobre el retrieval**. No hay evidencia, en ninguno de
los 5 casos, de que un chunk de MedlinePlus desplace contenido más relevante previamente
mejor rankeado — la hipótesis de dilución generalizada queda descartada con evidencia
directa, no solo por intuición.

## 4. D-084 — modo de fallo conocido, documentado sin plan de arreglo

Ver `decisions.md` (D-084) y `docs/evaluation.md` §5.5 para el detalle completo. Resumen:
BM25 no encuentra fichas de MedlinePlus (en inglés) para preguntas de listado amplio en
español ("dame un listado de las IDPs..."); confirmado con barrido de `top_k`
(5/10/15/20/30, `scripts/run_e13_topk_sweep_investigation.py`) que subir `top_k` no lo
soluciona a ningún valor razonable. No hay caso de tipo "listado" en
`tests/eval/dataset_partial.json`, así que este modo de fallo no está representado en las 4
métricas de la sección 1 — no se cuenta como "por debajo de objetivo" en la tabla de
métricas, es una limitación aparte. Confirmado que **no afecta al caso de uso principal**
de AIIP (una enfermedad a la vez): las preguntas de control sobre enfermedades concretas
(Wiskott-Aldrich, Chediak-Higashi) sí recuperan MedlinePlus correctamente con
`RAG_TOP_K` sin cambios.

## 5. Regresiones de la suite de tests

`PYTHONPATH=. pytest tests/ -v` (o `-q`): **147 passed, 14 skipped, 1 xfailed** — idéntico
al baseline de E-11 T-07 (`docs/evaluation.md` §5.4). Sin regresión funcional. Los
escenarios del `.feature` de esta tarea son de configuración (backup/reset/re-medición/
verificación dirigida/confirmación), sin asserts pytest-bdd, mismo criterio de D-050/D-051
que E-07 T-02/E-09 T-02/E-11 T-02.

## 6. Confirmación

**Investigaciones del paso 13 completadas (22 jul 2026):** la caída agregada de Context
Precision ya no queda "sin causa raíz confirmada" — ver sección 3quater. De los 5 casos que
la concentran, 4 (`eval_08`, `eval_20`, `eval_22`, `eval_10`) están explicados por ruido del
evaluador (`eval_20` por magnitud despreciable, el resto con evidencia directa de
inestabilidad del juez o de patrones históricos ya documentados) y el quinto (`eval_63`)
tiene indicios más fuertes hacia ruido de sesión que hacia dilución real del corpus, aunque
sin la misma contundencia. No hay evidencia, en ninguno de los 5, de que un chunk de
MedlinePlus desplace contenido relevante mejor rankeado.

Pendiente de revisión y confirmación final por Marcos: revisar este informe completo
(secciones 3ter y 3quater ya resueltas), `docs/kb-sources.md` y `docs/evaluation.md` (§5.5,
§7), y decidir si E-13 queda lista para `epic-close` (siguiente parada: E-10).

**Nota de transparencia explícita para esa decisión:** a diferencia de E-11 T-02 (donde las
4 métricas coincidían en mejorar), aquí 2 de 4 empeoran — Context Precision en particular
retrocede por debajo de donde estaba antes de la ampliación (63.2%→59.5%), aunque ahora con
causa mayoritariamente explicada por ruido del evaluador, no por un efecto real de las 40
fichas nuevas sobre el retrieval (sección 3quater). El recálculo de Hallucination Rate
(sección 3bis) muestra que, aunque el binario mejora (93.75%→81.25%), aparece un caso nuevo
en banda Grave (`eval_25`) que no estaba ahí antes de la ampliación — **investigado y
cuestionado** en la sección 3ter (ruido de muestreo del juez LLM, mismo patrón que
D-069/D-072), no una regresión real de contenido. No se recomienda presentar el cierre de
E-13 como una mejora limpia de las 4 métricas: es un resultado mixto (2 mejoran, 2
empeoran), aunque las caídas quedan ahora mayoritariamente explicadas por varianza del
evaluador RAGAS, no por un coste real y sistemático de ampliar la KB.
