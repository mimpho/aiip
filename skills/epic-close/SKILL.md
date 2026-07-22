---
name: epic-close
description: >
  Cierre de una épica de desarrollo en AIIP. Se lanza desde Cowork. Úsala cuando
  todos los tests de la épica pasan y Marcos confirma que está lista para cerrar.
  Orquesta el cierre completo: deja la rama de la épica actualizada, revisa el
  trabajo realizado, actualiza backlog/epics.md, README.md y AGENTS.md, redacta
  y escribe en prompts.md las entradas que Marcos apruebe, hace una retrospectiva
  del workflow con mejoras inmediatas a las skills si aplica, y por último — con
  todo lo anterior ya actualizado de verdad en los ficheros, no solo presentado en
  el chat — prepara la descripción del PR final (epic→main).
  Actívala cuando el usuario diga "cerramos la E-XX", "épica terminada", "vamos
  a cerrar" o similar.
---

# epic-close

Workflow de cierre para épicas de desarrollo. El objetivo es dejar todos los
registros actualizados y el repositorio en un estado limpio antes de pasar a
la siguiente épica.

---

## Paso 1 — Rama de la épica actualizada y tests en verde

**Nunca hagas `checkout`/`pull` tú mismo, ni siquiera para inspeccionar** (ver
"Reparto git" en `AGENTS.md`). Un `checkout`/`merge --ff-only` de "solo mirar" ya
dejó un `.git/index.lock` huérfano bloqueando a Marcos en una sesión anterior: el
sandbox de Cowork monta su repo real, no un clon aislado, así que cualquier cambio
de HEAD es un cambio real, aunque la intención fuera solo de lectura.

Como las tareas de la épica se integran vía PR en GitHub, la copia local de
`epic/E[nn]-nombre` puede quedar por detrás del remoto (última tarea mergeada sin
fast-forward local). Además, el propio cierre va a añadir un commit más sobre esta
rama (los registros actualizados en los Pasos 3-4), así que hay que partir de la
rama de épica real y actualizada, no de la rama de la última tarea ni de una copia
desfasada. Pide a Marcos que ejecute él mismo:

```bash
git checkout epic/E[nn]-nombre
git pull origin epic/E[nn]-nombre
```

Con la rama ya actualizada, comprueba el estado (esto sí lo puede hacer el agente
— `status`/`log`/`diff`/`branch`/`fetch` son de lectura):

```bash
git fetch origin --prune                    # antes de comparar nada — el ref local puede ir por detrás
git branch --show-current
git log --oneline main..epic/E[nn]-nombre   # commits de la épica, sin moverte de rama
```

**Haz siempre `git fetch origin` antes de comparar ramas**, incluso si el ref local
parece al día — la última tarea puede haberse mergeado por PR en GitHub sin que el
agente lo sepa todavía. Si tras el fetch `origin/epic/E[nn]-nombre` tiene commits que
el ref local no tiene, compara contra `origin/epic/E[nn]-nombre` en los pasos
siguientes en vez de asumir que el local ya refleja el estado real.

Si Marcos no ha hecho el `checkout`/`pull` todavía, sigue trabajando con
`<rama-A>..<rama-B>` en los comandos de git (o contra `origin/epic/E[nn]-nombre`)
en vez de moverte de HEAD tú mismo.

Verifica que la épica está realmente lista para cerrar:
- No hay TODOs pendientes en el código de la épica
- Marcos ha confirmado el cierre
- Todos los tests del proyecto pasan **sobre la rama de la épica ya actualizada**
  (no solo los de la épica, y no sobre `main` ni sobre una rama de tarea suelta):

```bash
PYTHONPATH=. pytest tests/ -v
```

`PYTHONPATH=.` es obligatorio — varios step_defs importan módulos del repo raíz
(`auth.*`, `rag.*`) vía `main_family`; sin ello la colección falla entera, no solo esos
tests (ver `AGENTS.md` → Convenciones → Tests).

Pide a Marcos la línea de resumen completa de pytest (`X passed, Y failed, Z skipped,
W xfailed...`), no un fragmento — un `xfailed` o `skipped` mencionado suelto y fuera de
contexto es fácil de confundir con un `failed` real.

Si algún test de una épica anterior falla, es una regresión — hay que resolverla antes de cerrar.

> **No correr `pytest` ni instalar dependencias dentro del sandbox de Cowork.**
> El `.venv` del repo es de macOS/Homebrew y no funciona en el Linux del sandbox, y las
> dependencias pesadas (torch, chromadb, transformers) no se instalan limpiamente ahí.
> Pide directamente a Marcos que ejecute `PYTHONPATH=. pytest tests/ -v` en su terminal (con el `.venv`
> activado, sobre la rama de la épica) o en Antigravity, y que te pase el resultado. No
> intentes reconstruir el entorno en el sandbox — es tiempo perdido.

> **Tests de integración contra servicios externos (Supabase, Google, etc.):**
> Los tests que requieren conexión de red a Supabase u otros servicios externos
> fallarán en el sandbox de Cowork por restricciones de red (proxy SOCKS no disponible).
> Esto **no es una regresión** — verificar que pasan en Antigravity con los servicios
> reales y documentarlo. No bloquear el cierre por este motivo.

> **E-10 (última épica):** antes de cerrar, ejecutar también los tests RAGAS end-to-end
> definidos en E-07/E-09 sobre el sistema completo. Es el único momento en que se
> valida el pipeline integrado en su totalidad.

---

## Paso 2 — Revisión del trabajo realizado

Haz un repaso del estado actual antes de escribir nada:

```bash
git log --oneline main..epic/E[nn]-nombre               # commits de la épica, sin moverte de rama
git diff main..epic/E[nn]-nombre --stat                  # ficheros modificados
PYTHONPATH=. pytest tests/features/eXX_*.feature -v      # confirma que todo pasa (pide a Marcos que lo ejecute, ver Paso 1)
```

Con esto en mano, identifica:
- Entregables concretos (ficheros creados/modificados con su propósito)
- Decisiones de implementación no obvias que merezcan documentarse
- Prompts o system prompts que hayan evolucionado durante el desarrollo
- **Relee los "Criterios de aceptación de alto nivel" de la épica en `backlog/epics.md`
  contra las decisiones tomadas durante el desarrollo (`decisions.md`).** No te limites a
  comprobar que las tareas están completadas — un criterio puede acabar cumplido de una
  forma distinta a como se escribió originalmente porque una decisión posterior cambió el
  mecanismo (p. ej. una visualización en UI que se sustituye por logging server-side). Si
  es el caso, anótalo junto al criterio en `epics.md` y márcalo explícitamente en la PR
  description (Paso 6) en vez de dar el criterio por cumplido sin más.

---

## Paso 3 — Actualización de registros

Actualiza en este orden:

### 3a. `backlog/epics.md`

Cambia el estado de la épica, marca todas las tareas como completadas en la
tabla de tareas, y añade los entregables:

```markdown
**Estado:** ✅ Completada — [DD mes YYYY]

| ID | Tarea | Estado |
|---|---|---|
| T-01 | [nombre] | ✅ Completada |
| T-02 | [nombre] | ✅ Completada |

**Entregables**
- `path/fichero.py` — [descripción]
- `tests/features/eXX_tYY.feature` — [descripción]
```

### 3b. `README.md`

Actualiza en este orden:
1. **Tabla de épicas** — estado ✅ con fecha de cierre.
2. **Gantt (roadmap)** — marca la épica como `:done` y ajusta la fecha de fin real.
3. **Árbol del repositorio** — si la épica ha creado ficheros raíz o directorios
   nuevos relevantes para cualquier lector del README, añádelos al árbol.
   (Criterio: ¿lo buscaría alguien que acaba de clonar el repo?)

### 3c. `AGENTS.md`

Revisa la sección "Estructura del repositorio". Si la épica ha creado carpetas
o ficheros raíz nuevos (no ficheros de código individuales, sino directorios o
ficheros raíz relevantes para cualquier agente que trabaje en el repo), actualiza
el árbol para reflejar el estado real del repositorio.

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

> **No confundir con `docs/process-log.md` (Paso 5).** `prompts.md` es para prompts y
> decisiones de prompting puntuales (system prompts, prompts de generación, decisiones de
> arquitectura de IA concretas). Explicaciones del propio workflow de desarrollo (qué hace
> cada skill, cómo se reparte Cowork/Antigravity, etc.) van en `docs/process-log.md`, no aquí
> — evita proponer una entrada de prompts.md para contenido de proceso.

Presenta el borrador a Marcos para revisión. Marcos decide qué entra en el log.

**Una vez que Marcos confirma qué entradas se quedan, escríbelas tú mismo en
`prompts.md`** (edición de fichero — no es una acción git restringida, ver
"Reparto git" en `AGENTS.md`) antes de pasar al Paso 5. No lo dejes como contenido
solo del chat a la espera de que Marcos lo pegue él: eso es precisamente lo que dejó
el Paso 6 en falso en el cierre de E-11 — la PR se redactó dando por "cerrado" un
borrador que en el fichero real seguía sin existir.

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

Una vez validada por Marcos, añade la entrada a `docs/process-log.md` con este formato:

```markdown
## E-XX — [nombre de la épica]
**Periodo:** [DD mes] – [DD mes YYYY]
**Tareas:** T-01 a T-XX (N tareas, todas completadas)

### ¿Qué funcionó bien en el proceso?
[1-3 puntos concretos]

### ¿Qué generó fricción o retraso?
[1-3 puntos concretos]

### ¿Qué cambió en las skills o el workflow?
[Skills editadas, pasos añadidos, decisiones de proceso]

---
```

Este fichero es material para la memoria del TFM — cada entrada debe ser legible
de forma independiente, sin asumir contexto de la sesión.

---

## Paso 6 — PR final de la épica

Este es el último paso, no antes. `epics.md`, `README.md`, `AGENTS.md`, `prompts.md`
(las entradas ya escritas en el fichero, no solo presentadas en el chat — ver Paso 4)
y la retrospectiva en `docs/process-log.md` (Pasos 3-5) ya están cerrados — la retro
también genera documentación del repo, así que cuenta como parte de "todo lo anterior
actualizado". Antes de redactar la PR description, comprueba con `git status`/`git
diff` que los cinco ficheros aparecen modificados de verdad — no solo que se
presentaron en el chat. Generar la PR description en cualquier punto anterior, o sin
verificar que el fichero refleja lo acordado, daría la falsa impresión de que la
épica ya está lista para `main` mientras el propio repo todavía no lo refleja
(precedente: cierre de E-11, donde la PR se redactó con `prompts.md` todavía sin
las entradas acordadas).

El PR es de la rama de épica a main: `epic/E[nn]-nombre → main`.

Genera la PR description **en inglés**, igual que `task-close` — solo el título del
commit/PR y el cuerpo van en inglés; el resto de la sesión (chat, retro, registros) sigue en
español. Proporciona en el chat el título y descripción del PR, listos para copiar en GitHub.

**La primera línea es el título del PR** (campo "Title" de GitHub, no un heading dentro
de la descripción). El resto, a partir de `## What`, es el cuerpo ("Description"):

```
feat(E-XX): [one-line description of what the epic delivers]

## What
[2-3 sentences explaining the change at product/system level]

## Changes
- `path/file.py` — [what it does]
- `tests/features/eXX_tYY.feature` — [what behavior it validates]
- [...]

## Acceptance criteria covered
- [ ] [criterion 1 from epics.md]
- [ ] [criterion 2]
- [...]

## Test results
All scenarios passing: `PYTHONPATH=. pytest tests/features/eXX_*.feature`

## Notes
[Relevant implementation decisions, known technical debt, etc.]
```

No crees ningún fichero .md para el PR. Solo en el chat.

---

## Resumen de entregables del cierre

| Entregable | Destino | Quién ejecuta |
|---|---|---|
| Rama de la épica actualizada (`checkout`/`pull`) | Repo local | Marcos |
| Estado + tareas + entregables | `backlog/epics.md` | Agente |
| Tabla de épicas actualizada | `README.md` | Agente |
| Estructura del repo actualizada | `AGENTS.md` (si aplica) | Agente |
| Entradas escritas en el fichero | `prompts.md` | Agente (tras aprobación de Marcos sobre qué entra) |
| Retrospectiva del workflow | `docs/process-log.md` | Agente (Marcos valida) |
| Descripción del PR (generada al final, Paso 6) | Chat (copiar en GitHub) | Marcos |
