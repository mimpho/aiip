# Notas para E-12 — Retrospectiva final del roadmap (cierre TFM)

> Scratchpad de trabajo, no el deliverable de E-12 T-01. Recoge observaciones en caliente
> sobre el workflow (Cowork / Antigravity / Marcos como human-in-the-loop) a medida que
> ocurren, para no depender de la memoria al llegar al cierre real de Fase 1.5. E-12 T-01
> sintetiza esto (junto con `docs/process-log.md` y `decisions.md`) en el documento final.
> Añadir entradas fechadas, sin reescribir las anteriores — mismo espíritu append-only que
> `decisions.md`/`prompts.md`.

---

## 22 jul 2026 — Valoración del reparto Cowork / Antigravity / human-in-the-loop

Reflexión de Marcos durante `task-start` de E-13 T-03, al hilo de una sesión que tocó varios
registros distintos en poco tiempo: corrección de cifras heredadas de un borrador desactualizado
(epic-start → task-start), una decisión de alcance con dos opciones reales (D-079), una mejora
de skill descubierta a mitad de tarea (D-080), y un bug de contenido encontrado por revisión
manual que el propio Antigravity no habría cogido solo (D-081, mojibake en letras griegas).

**Valoración (Marcos):** el workflow está funcionando bien. Aunque Cowork y Antigravity corren
sobre el mismo modelo (Sonnet 5), no son intercambiables — el valor no está en el modelo, está
en el contexto y el rol de cada superficie:

- **Cowork como espacio de debate antes de que Antigravity ejecute.** Es "el uso correcto" de
  las herramientas para un proyecto como este, donde hay mucho que debatir, investigar e ir
  perfeccionando sobre la marcha (a diferencia de una tarea de código puro con requisitos ya
  cerrados). El .feature/plan que sale de Cowork es lo que le da a Antigravity una tarea sin
  ambigüedad — así el ciclo TDD/ejecución no tiene que parar a decidir nada.
- **Las skills se han ido afinando con retros reales, no solo al cierre de épica.** D-080 (Paso
  4 de `task-start` también para config ejecutada en Antigravity) salió de un problema concreto
  detectado en caliente (T-03 arranca en una sesión nueva de Antigravity sin memoria de T-01/
  T-02), no de una revisión programada. `docs/process-log.md` ya recoge esto por épica desde
  E-03; este fichero es el mismo espíritu pero a nivel de fase/roadmap.
- **`decisions.md` como trazabilidad real de "qué se decidió y por qué"**, no solo del qué —
  permite que una sesión nueva (Cowork o Antigravity) entienda el contexto sin que Marcos tenga
  que repetirlo. D-073 a D-081 de esta épica son un ejemplo denso: cada una nace de una
  verificación puntual, no de una planificación previa perfecta.

**Candidato a ángulo de la memoria del TFM:** más allá del caso human-in-the-loop ya identificado
(KB limitado → Context Precision, criterio existente de E-12), esto es un segundo ángulo:
metodología de trabajo con agentes de IA en distintos roles (diseño conversacional vs. ejecución
autónoma) como parte del propio proceso de desarrollo del TFM, no solo del producto final. Con
ejemplos concretos y trazables vía `decisions.md`/`process-log.md`, no solo declarado.

---

## 22 jul 2026 — Segundo caso human-in-the-loop: de la intuición de Marcos al hallazgo estructural de E-13 T-04

Distinto del caso ya identificado ("KB limitado → Context Precision", P-032 en `prompts.md`)
pero de la misma familia: intuición de Marcos → verificación empírica en Cowork → hallazgo
documentado, con números, no solo declarado.

**Punto de partida:** al revisar T-04, Marcos preguntó por qué el sistema no "aglutina" bien
información de las 40 fichas nuevas de MedlinePlus para preguntas generales o de grupo
("¿qué IDPs existen ligadas al cromosoma X?"), en vez de asumir sin más que era un problema de
idioma. Se investigó en tres pasos, cada uno con evidencia directa, no intuición:

1. **D-084** (ya en curso antes de esta reflexión): confirmado con BM25 real + barrido de
   `top_k` que un listado totalmente genérico no recupera ninguna ficha de MedlinePlus, a
   ningún valor de `top_k`.
2. **Réplica dirigida (22 jul, esta sesión):** la misma metodología aplicada a "IDPs ligadas al
   cromosoma X" (pregunta con un criterio concreto, no un listado abierto) confirma el mismo
   fallo — BM25 con score 0.0 para el mejor chunk de MedlinePlus (rank 964/1324), y la propia
   respuesta real de producción (`_build_sources_section`, determinista sobre lo recuperado) sin
   ninguna fuente de MedlinePlus entre las citadas. Generaliza D-084 más allá del caso extremo.
3. **Remedición RAGAS de T-04:** Context Precision **empeora** (63.2%→59.5%) pese a ser la
   métrica que la épica esperaba mejorar más — contradice la hipótesis de partida de E-13 en la
   mitad de las métricas (`tests/eval/results/e13_t04_cierre.md`).

**Hallazgo estructural que conecta los tres:** el RAG del proyecto es "naive" (D-005, sin
agregación entre documentos) — funciona bien cuando hay un objetivo específico (léxico o
semántico) al que apuntar, y mal cuando la pregunta requiere reunir información de varios
documentos a la vez (listados, categorías) o cuando el contenido nuevo es temáticamente
adyacente pero no relevante (compite como ruido). Añadir contenido *estrecho* (40 fichas de una
enfermedad cada una) mejora las preguntas estrechas y puede empeorar las preguntas amplias —
explica a la vez por qué "xiap" funciona perfecto y por qué Context Precision cae en el
agregado de 32 casos con tipos de pregunta mixtos.

**Por qué es un buen ángulo para la memoria del TFM:** muestra el ciclo completo de
human-in-the-loop con un resultado que **no** confirma la hipótesis inicial de la épica limpia
(a diferencia del caso KB-limitado, que sí fue una mejora clara) — más honesto y más
interesante metodológicamente: la intuición llevó a una verificación real, la verificación
reveló una limitación estructural (no un bug puntual), y la épica se cierra documentando el
resultado mixto sin suavizarlo (mismo principio de transparencia CHART/TRIPOD-LLM ya aplicado en
D-058/D-072/D-084).

<!-- Añadir próximas entradas debajo, fechadas, sin editar las anteriores. -->
