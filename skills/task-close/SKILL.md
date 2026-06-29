---
name: task-close
description: >
  Cierre de una tarea individual dentro de una épica activa. Se lanza desde Cowork
  cuando Antigravity ha terminado el ciclo TDD y todos los escenarios de la tarea
  están en verde. Verifica el estado de los tests, genera la PR description en
  inglés lista para copiar en GitHub, y da el checklist de merge a la rama de
  épica. Actívala cuando el usuario diga "cerramos la T-XX", "tarea terminada",
  "tests en verde", "PR de la tarea" o similar.
---

# task-close

Workflow de cierre para tareas individuales. Se ejecuta en Cowork tras confirmar
que los tests de la tarea pasan en Antigravity. El objetivo es generar la PR
description y dejar todo listo para el merge a `epic/E[nn]-nombre`.

## Antes de empezar

Confirma con Marcos que:
- Todos los escenarios del `.feature` de la tarea están en verde
- No hay TODOs pendientes en el código de la tarea
- No hay credenciales ni valores hardcodeados en el código nuevo

Si alguno de estos puntos falla, no continúes — la tarea no está cerrable.

---

## Paso 1 — Revisión del trabajo

Lee el plan de la tarea (`tasks/E[nn]-T[nn]-plan.md`) y compara contra lo
entregado. Identifica:

- Ficheros creados/modificados y su propósito real (puede diferir del plan)
- Decisiones de implementación tomadas durante el TDD que no estaban en el plan
- Cualquier deuda técnica conocida introducida (TODOs intencionados, simplificaciones)

Presenta un resumen breve en el chat antes de generar la PR. Si hay desviaciones
relevantes del plan, anótalas — irán en la sección "Notes" del PR.

---

## Paso 2 — PR description

Genera la PR description en inglés, en markdown, lista para copiar en GitHub.
El PR va de `task/E[nn]-T[nn]-nombre` a `epic/E[nn]-nombre`.

```markdown
## [tipo](E[nn]-T[nn]): [descripción en una línea]

## What
[1-2 frases explicando qué aporta esta tarea al sistema]

## Changes
- `ruta/fichero.py` — [qué hace]
- `tests/features/eXX_tXX_nombre.feature` — [qué comportamiento valida]
- `tests/step_defs/test_eXX_tXX.py` — [step definitions]

## Acceptance criteria covered
- ✅ Scenario: [nombre del escenario happy path]
- ✅ Scenario: [nombre del escenario de error]

## Test results
All scenarios passing: `pytest tests/features/eXX_tXX_nombre.feature -v`

## Notes
[Decisiones de implementación no obvias, deuda técnica conocida, o vacío
respecto al plan original. Si no hay nada, omite esta sección.]
```

Tipos de commit permitidos: `feat`, `fix`, `refactor`, `test`, `docs`.

---

## Paso 3 — Actualizar tracker y checklist de merge

Actualiza **inmediatamente** el estado de la tarea en `backlog/epics.md`:

```markdown
| T-XX | [nombre] | ✅ Completada |
```

Luego verifica el checklist antes de que Marcos haga el merge:

- [ ] La rama base del PR es `epic/E[nn]-nombre`, no `main`
- [ ] El `.feature` de la tarea está en `tests/features/`
- [ ] El plan `tasks/E[nn]-T[nn]-plan.md` existe y refleja lo que se hizo
- [ ] No hay ficheros de depuración, prints, o credenciales en el diff
- [ ] Si se tomaron decisiones de arquitectura durante el TDD no registradas
      en `decisions.md`, créalas ahora antes del merge

---

## Resumen de entregables

| Entregable | Destino | Quién ejecuta |
|---|---|---|
| Resumen del trabajo | Chat | Agente |
| PR description | Chat (copiar en GitHub) | Marcos |
| Checklist de merge | Chat | Agente verifica, Marcos ejecuta |
