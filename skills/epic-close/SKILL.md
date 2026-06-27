---
name: epic-close
description: >
  Cierre de una épica de desarrollo en AIIP. Se lanza desde Cowork. Úsala cuando
  todos los tests de la épica pasan y Marcos confirma que está lista para cerrar.
  Orquesta el cierre completo: revisa el trabajo realizado, prepara la descripción
  del PR final (epic→main), actualiza backlog/epics.md y README.md, genera el
  borrador de entradas para prompts.md, y hace una retrospectiva del workflow con
  mejoras inmediatas a las skills si aplica. Actívala cuando el usuario diga
  "cerramos la E-XX", "épica terminada", "vamos a cerrar" o similar.
---

# epic-close

Workflow de cierre para épicas de desarrollo. El objetivo es dejar todos los
registros actualizados y el repositorio en un estado limpio antes de pasar a
la siguiente épica.

## Antes de empezar

Verifica que la épica está realmente lista para cerrar:
- No hay TODOs pendientes en el código de la épica
- Marcos ha confirmado el cierre
- Todos los tests del proyecto pasan (no solo los de la épica):

```bash
pytest tests/ -v
```

Si algún test de una épica anterior falla, es una regresión — hay que resolverla antes de cerrar.

> **E-10 (última épica):** antes de cerrar, ejecutar también los tests RAGAS end-to-end
> definidos en E-07/E-09 sobre el sistema completo. Es el único momento en que se
> valida el pipeline integrado en su totalidad.

---

## Paso 1 — Revisión del trabajo realizado

Haz un repaso del estado actual antes de escribir nada:

```bash
git log --oneline main..HEAD   # commits de la épica
git diff main --stat           # ficheros modificados
pytest tests/features/eXX_*.feature -v  # confirma que todo pasa
```

Con esto en mano, identifica:
- Entregables concretos (ficheros creados/modificados con su propósito)
- Decisiones de implementación no obvias que merezcan documentarse
- Prompts o system prompts que hayan evolucionado durante el desarrollo

---

## Paso 2 — PR final de la épica

El PR es de la rama de épica a main: `epic/E[nn]-nombre → main`.

Proporciona en el chat el título y descripción del PR, listos para copiar en GitHub:

```
## [título]
feat(E-XX): [descripción en una línea de qué aporta la épica]

## What
[2-3 frases explicando el cambio a nivel de producto/sistema]

## Changes
- `path/fichero.py` — [qué hace]
- `tests/features/eXX_tYY.feature` — [qué comportamiento valida]
- [...]

## Acceptance criteria covered
- [ ] [criterio 1 de la épica en epics.md]
- [ ] [criterio 2]
- [...]

## Test results
All scenarios passing: `pytest tests/features/eXX_*.feature`

## Notes
[Decisiones de implementación relevantes, deuda técnica conocida, etc.]
```

No crees ningún fichero .md para el PR. Solo en el chat.

---

## Paso 3 — Actualización de registros

Actualiza en este orden:

### 3a. `backlog/epics.md`

Cambia el estado de la épica y añade los entregables:

```markdown
**Estado:** ✅ Completada — [mes año]

**Entregables**
- `path/fichero.py` — [descripción]
- `tests/features/eXX_tYY.feature` — [descripción]
```

### 3b. `README.md`

Actualiza la tabla de fases y el Gantt si existe. El estado de la épica debe
reflejar ✅ y la fecha de cierre.

---

## Paso 4 — Borrador para prompts.md

Recupera las fechas aproximadas de los commits de la épica para anclar las entradas:

```bash
git log --oneline --format="%ad %s" --date=short epic/E[nn]-nombre
```

Para cada entrada con valor real (decisión de prompting, system prompt candidato,
razonamiento técnico no obvio), prepara un borrador con este formato:

```
### P-XXX — [título descriptivo]
**Fecha:** [DD mes YYYY]
**Fase:** [épica — ej: E-03]
**Tipo:** [system prompt / decisión de prompting / razonamiento técnico]
**Herramienta:** [Claude Cowork / Antigravity / ambos]

**Prompt / decisión:**
[el prompt exacto, o la decisión con contexto]

**Resultado / aprendizaje:**
[qué funcionó, qué no, por qué importa]
```

Para entradas de sesiones de Cowork (sin rastro en git), usa la fecha aproximada
de la conversación. Es mejor una fecha orientativa que perder el anclaje temporal.

Criterios para incluir una entrada:
- ¿Cambiaría el comportamiento del agente en la siguiente épica saberlo? → incluir
- ¿Es un prompt que se reutilizará o evolucionará? → incluir
- ¿Es una conversación exploratoria sin aprendizaje transferible? → no incluir

Presenta el borrador a Marcos para revisión. Marcos decide qué entra en el log.

---

## Paso 5 — Retrospectiva del workflow

Una revisión corta del proceso, no del producto. El objetivo es detectar
fricciones o mejoras en las skills y el workflow antes de arrancar la siguiente
épica.

Presenta en el chat (sin crear fichero) una retro con este formato:

```
## Retro — E-XX [nombre]

**¿Qué funcionó bien en el proceso?**
[1-3 puntos concretos — skills, handoffs, gates, reparto Cowork/IDE]

**¿Qué generó fricción o retraso?**
[1-3 puntos concretos — ambigüedades, pasos que faltaban, idas y vueltas]

**¿Qué cambiaría en las skills o el workflow?**
[Propuestas concretas — si implica editar una skill, indícalo explícitamente]
```

Basa la retro en evidencia observable: el historial de la conversación, los
puntos abiertos que aparecieron durante la épica, las decisiones de arquitectura
que se añadieron a mitad de desarrollo, y cualquier tarea que requirió más de
un ciclo de revisión.

Si la retro identifica mejoras a las skills (`epic-start`, `task-start`,
`epic-close`), edítalas directamente antes de cerrar la sesión — no las dejes
como "pendiente".

---

## Resumen de entregables del cierre

| Entregable | Destino | Quién ejecuta |
|---|---|---|
| Descripción del PR | Chat (copiar en GitHub) | Marcos |
| Estado + entregables de la épica | `backlog/epics.md` | Agente |
| Tabla de fases actualizada | `README.md` | Agente |
| Borrador de entradas | `prompts.md` | Marcos (tras revisión) |
| Retrospectiva del workflow | Chat | Agente (Marcos valida) |
