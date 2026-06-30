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
