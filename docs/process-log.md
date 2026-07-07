# Process Log — AIIP

Registro de retrospectivas del workflow de desarrollo. Una entrada por épica, generada al cierre.
Formato: qué funcionó, qué generó fricción, qué cambió en las skills o el proceso.

Este documento es material para la memoria del TFM — refleja cómo evolucionó el workflow de
desarrollo asistido por IA a lo largo del proyecto.

---

## E-03 — Autenticación y separación de perfiles
**Periodo:** 27–30 jun 2026  
**Tareas:** T-01 a T-06 (6 tareas, todas completadas)

### ¿Qué funcionó bien en el proceso?

- **BDD + TDD como contrato entre Cowork y Antigravity.** Los `.feature` generados en task-start
  actuaron como especificación ejecutable sin ambigüedad. Antigravity no necesitó interpretar
  requisitos — los criterios Gherkin eran la fuente de verdad.

- **Decisiones de arquitectura en Cowork antes del código.** D-014 (Supabase único broker OAuth)
  se tomó en Cowork y se registró en `decisions.md` antes de tocar código. Esto evitó retrabajo
  en Antigravity y dejó trazabilidad de por qué se descartaron alternativas.

- **Double-layer blocking para el stub profesional.** La solución (callback Python siempre None +
  JS disable de inputs) surgió de iterar en Cowork sobre los constraints de Chainlit. El diseño
  quedó documentado en P-019 antes de implementarse.

### ¿Qué generó fricción o retraso?

- **Divergencia skills repo ≠ skills instaladas en Cowork.** Los cambios a las skills durante
  una épica no se reflejan en la sesión actual — hay que empaquetar y reinstalar manualmente.
  Genera un ciclo de fricción al final de cada épica. Solución actual: packaging al cierre.

- **Orden de pasos en epic-close.** Se aplicaron cambios en ficheros estando en `main` en lugar
  de en la rama de épica. Hubo que corregir el orden y añadir `git checkout epic/E[nn]-nombre`
  al inicio de la skill.

- **Tests de integración fallan en Cowork.** Los tests contra Supabase fallan en el sandbox por
  restricciones de red (proxy SOCKS). No son regresiones, pero generan ruido al verificar el
  estado antes del cierre. Documentado en epic-close para no bloquear por este motivo.

- **Fechas sin día.** El template inicial de epic-close usaba `mes YYYY` en lugar de `DD mes YYYY`.
  Corregido en la skill y retroaplicado a E-00, E-01, E-02, E-03 en epics.md.

### ¿Qué cambió en las skills o el workflow?

- **epic-close:** añadido `git checkout epic/E[nn]-nombre` al inicio; nota sobre tests de
  integración en Cowork; paso 3b ampliado para incluir gantt + árbol de repo en README;
  template de fecha cambiado a `DD mes YYYY`.

- **epic-start:** añadido bloque "Setup de rama de épica" antes del Paso 1 — la rama se crea
  antes de cualquier otro paso, no después de la descomposición.

- **process-log.md:** creado este fichero — la retro de cada épica se registra aquí como
  material para la memoria del TFM.

---

## E-04 — Pipeline RAG + módulo de seguridad
**Periodo:** 27 jun – 05 jul 2026
**Tareas:** T-01 a T-06 (6 tareas, todas completadas)

### ¿Qué funcionó bien en el proceso?

- **Estrategia de test híbrida para módulos con LLM real.** Los escenarios deterministas
  mockean `ChatGoogleGenerativeAI` en el punto exacto donde se instancia; embeddings (bge-m3)
  y ChromaDB corren reales por ser locales y sin coste; un único escenario `@integration`,
  gateado por `RUN_LLM_INTEGRATION_TESTS=1`, valida el extremo a extremo real. Patrón adoptado
  en T-04 y confirmado en T-06 (D-018, D-020) — reutilizable en cualquier tarea futura que
  integre un servicio de pago o con latencia (candidato: E-06 ingesta, E-07/E-09 RAGAS).
- **Ciclo task-start → TDD en Antigravity → task-close sin fricción.** Las 6 tareas de la
  épica se cerraron en secuencia limpia, con PR y merge a `epic/E04-rag` ya resueltos antes de
  llegar a este cierre. 52 tests passed, 2 skipped, sin regresiones sobre E-01/E-02/E-03.
- **Las cuatro skills del workflow (epic-start, task-start, task-close, epic-close)** separan
  con claridad la decisión (Cowork) de la ejecución (Antigravity): `epic-start` y `task-start`
  cierran gates de diseño y generan `.feature` + plan antes de tocar código; Antigravity
  ejecuta el plan sin margen para decisiones de arquitectura propias; `task-close` y
  `epic-close` cierran con PR description y registros actualizados. Viven en `skills/` del
  repo (fuente de verdad, leída nativamente por Antigravity) y se sincronizan al plugin de
  Cowork vía `scripts/sync_skills.sh`.

### ¿Qué generó fricción o retraso?

- **El sandbox de Cowork no puede escribir en el `.git` real de forma fiable.** Cualquier
  comando git que toque el índice (incluso `git status`) deja un `index.lock` huérfano que el
  propio sandbox no puede borrar — el puente FUSE deniega `unlink`/`rename` sobre ficheros que
  el propio proceso acaba de crear. Hubo que pedir a Marcos que borrara el lock manualmente en
  su Terminal varias veces durante este cierre.
- **Entorno Python no reproducible en el sandbox de Cowork.** El `.venv` del repo es de
  macOS/Homebrew (rutas Homebrew, binarios no compatibles con Linux) y las dependencias pesadas
  (torch, chromadb, transformers, sentence-transformers) no se instalan limpiamente en el
  sandbox. Se perdió tiempo intentando reconstruir el entorno antes de pedir directamente a
  Marcos que corriera `pytest tests/ -v` en su propio entorno.
- **Confusión de alcance entre documentos de proceso.** Se propuso una entrada en `prompts.md`
  explicando el funcionamiento de las 4 skills del workflow — contenido de proceso, no de
  prompting. El sitio correcto ya existía (`docs/process-log.md`, este mismo fichero) pero no
  estaba presente en el contexto de la sesión.

### ¿Qué cambió en las skills o el workflow?

- **`epic-close`:** añadida nota explícita de no instalar dependencias ni correr `pytest`
  dentro del sandbox de Cowork — pedir el resultado directamente a Marcos desde su entorno
  real (terminal con `.venv` o Antigravity).
- **`epic-close`:** añadida nota de alcance en el Paso 4 para no confundir `prompts.md`
  (prompts y decisiones de prompting puntuales) con `docs/process-log.md` (narrativa de
  proceso/workflow) — evita proponer entradas de proceso en el fichero equivocado.

---

## E-06 — Ingesta y procesamiento de la KB
**Periodo:** 27 jun – 08 jul 2026
**Tareas:** T-01 a T-08 (8 tareas, todas completadas)

### ¿Qué funcionó bien en el proceso?

- **El reparto Cowork/Antigravity se mantuvo limpio en las 8 tareas** — decisiones y planes en
  Cowork, TDD puro en Antigravity, sin fricción de `index.lock`.
- **T-07 (smoke test manual contra datos reales, sin TDD) resultó clave.** Detectó dos problemas
  reales que los mocks de E-04 no podían ver — thinking de Gemini agotando el presupuesto de
  tokens (D-025) y verbosidad de citación inline (D-026) — justo entre T-05 (pipeline) y E-05
  (UI), como estaba planeado en la nota de la épica. Confirma el patrón anticipado en la retro de
  E-04: "reutilizable en cualquier tarea futura que integre un servicio de pago o con latencia".
- **La skill `kb-maintenance` nueva** (runbook + skill) queda como infraestructura reutilizable
  para futuras ampliaciones de fuentes sin necesidad de otra épica.

### ¿Qué generó fricción o retraso?

- **T-08 nació fuera del plan original de `epic-start`** — surgió de una propuesta de Marcos al
  revisar los resultados de T-07. El manifest tenía checksums/URLs vacíos que había que rellenar
  manualmente antes de poder formalizar la tarea, lo que la dejó pendiente un tiempo.
- **Trabajo de última hora sin commitear en el cierre** — checksums de 4 fuentes AEDIP nuevas y
  un ajuste de system prompt quedaron sin commitear al llegar a `epic-close`, lo que generó una
  pausa para confirmar con Marcos si contaban como parte del alcance de E-06 antes de seguir.

### ¿Qué cambió en las skills o el workflow?

- Ninguna edición a las skills esta vez. El patrón de "smoke test real antes de construir UI
  encima" (T-07) funcionó bien y merece repetirse en épicas futuras con integraciones externas
  nuevas, pero ya está implícito en el criterio de la nota de E-06 — no hace falta formalizarlo
  como regla de skill todavía.

---
