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

<!-- Añadir próximas entradas debajo, fechadas, sin editar las anteriores. -->
