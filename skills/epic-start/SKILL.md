---
name: epic-start
description: >
  Arranque de una épica de desarrollo en AIIP. Se lanza desde Cowork. Úsala al
  inicio de cualquier épica con estado "No iniciada" en backlog/epics.md. Descompone
  la épica en tareas con Gherkin informal, aplica auto-revisión crítica antes del
  gate, y obtiene aprobación de Marcos. Las tareas individuales se formalizan
  después con task-start. Actívala cuando el usuario diga "arrancamos la E-XX",
  "empezamos con la épica", "vamos con E-XX" o similar.
---

# epic-start

Workflow de arranque para épicas de desarrollo (E-03 en adelante). El AGENTS.md
define el qué; esta skill ejecuta el cómo paso a paso.

## Antes de empezar

Lee en este orden:
1. `AGENTS.md` — principios no negociables y reparto de responsabilidades
2. `backlog/epics.md` — criterios de aceptación de alto nivel de la épica
3. `decisions.md` — decisiones relevantes que afecten a la épica (busca las
   referenciadas en los criterios o en el stack)

Si la épica tiene dependencias (`Bloqueada por`), verifica que estén completadas.

---

## Paso 0 — Rama de épica [ejecutar antes de tocar nada]

Proporciona los comandos exactos para que Marcos cree la rama de épica desde `main`
antes de que el agente cree ningún fichero:

```bash
git checkout main
git pull origin main
git checkout -b epic/E[nn]-nombre
git push -u origin epic/E[nn]-nombre
```

Nomenclatura: `epic/E03-auth`, `epic/E04-rag`, `epic/E05-chainlit`, etc.

**Espera confirmación de Marcos antes de continuar.**
La rama debe existir en origin antes de crear los `.feature` y actualizar el backlog,
para evitar conflictos con `git pull` posterior.

---

## Paso 1 — Descomposición en tareas [GATE: Marcos aprueba]

Propón la lista de tareas de la épica con este formato para cada una:

```
### T-XX — Nombre descriptivo

Como [rol]
Quiero [capacidad]
Para [objetivo]

Criterios de aceptación (Gherkin informal):
- Dado que... cuando... entonces...
- Dado que... cuando... entonces...

Notas de implementación: [dependencias, ficheros afectados, riesgos]
```

Criterios para una buena descomposición:
- Cada tarea es entregable de forma independiente (puede hacer PR propio)
- El orden refleja dependencias reales entre tareas
- Los criterios cubren happy path + casos de error relevantes
- El Gherkin es legible por alguien sin conocimiento técnico (validación clínica)

### Auto-revisión antes del gate

Antes de presentar la lista a Marcos, hazte estas preguntas sobre cada tarea y anota cualquier problema encontrado:

1. **Ambigüedad de responsabilidades** — ¿Queda claro qué sistema/librería hace qué? (ej: si hay un OAuth, ¿quién es el broker? Si hay callbacks, ¿quién los gestiona?)
2. **Pasos de configuración de terceros** — ¿Hay configuración en consolas externas (Google Cloud, Supabase, etc.) que no aparece como criterio ni como tarea? ¿Falta algún paso manual no trivial?
3. **Puntos abiertos que bloqueen la aprobación** — ¿Hay decisiones de diseño sin tomar que afectan a los criterios? ¿Hay tareas con un "¿qué pasa si...?" sin respuesta?
4. **Riesgo de confusión entre elementos similares** — ¿Hay credenciales, variables de entorno, o configuraciones que se podrían confundir entre sí? (ej: clave OAuth vs clave de API del LLM)
5. **Tareas de configuración vs tareas de código** — ¿Alguna tarea es en realidad configuración manual (estilo E-01, sin rama ni PR)? Márcala explícitamente si es así.

Si encuentras problemas, corrígelos en la propuesta antes de presentarla. Si hay puntos abiertos que no puedes resolver solo (decisiones de arquitectura, preferencias de producto), preséntalos explícitamente como **⚠️ Punto abierto** junto con las opciones posibles.

**Espera aprobación explícita de Marcos antes de continuar.**
Ajusta según el feedback recibido.

Una vez aprobada la lista, actualiza dos ficheros:

**`backlog/epics.md`** — cambia el estado de la épica a `🔵 En curso` y añade la tabla de tareas justo antes de los criterios de aceptación:

**`README.md`** — cambia el estado de la épica en la tabla de épicas a `🔵 En curso`.

```markdown
### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | [nombre] | ⚪ Pendiente |
| T-02 | [nombre] | ⚪ Pendiente |
| ...  | ...       | ...         |
```

Esta tabla es la fuente de verdad del estado de las tareas durante toda la épica.
`task-start` y `task-close` la actualizan; `epic-close` la cierra.

---

## Paso 2 — Formalización de .feature [GATE: Marcos aprueba — validación de comportamiento]

Para cada tarea aprobada, crea `tests/features/eXX_tYY_nombre.feature`:

```gherkin
# E-XX T-YY — Nombre de la tarea
# Criterio: [qué comportamiento valida este escenario]

Feature: [nombre de la tarea]

  Como [rol]
  Quiero [capacidad]
  Para [objetivo]

  Background:
    Given [precondición común a todos los escenarios, si aplica]

  Scenario: [happy path]
    Given [estado inicial]
    When [acción]
    Then [resultado esperado]
    And [resultado adicional si es necesario]

  Scenario: [caso de error o borde relevante]
    Given [estado inicial]
    When [acción que falla]
    Then [comportamiento esperado ante el error]
```

Reglas para los .feature:
- Un fichero por tarea, no por épica
- Escenarios atómicos: un comportamiento por escenario
- Si la tarea toca el principio de Falso Negativo Cero, incluye siempre un
  escenario que valide que el agente deriva a consulta médica
- Los nombres de escenarios deben ser autoexplicativos sin leer el cuerpo

**Espera aprobación explícita de Marcos antes de continuar.**
Este es el gate clínico: el .feature define exactamente qué se va a testear.

---

## Resumen de gates

La estructura de ramas del proyecto es:

```
main
  └── epic/E[nn]-nombre     ← rama de épica (vive hasta cerrar la épica)
        ├── task/E[nn]-T[nn]-descripcion  ← rama de tarea → PR → merge en epic/
        ├── task/E[nn]-T[nn]-descripcion
        └── ...
```

La rama de la primera tarea la crea `task-start` — no hace falta crearla aquí.

| Paso | Qué aprueba / ejecuta Marcos | Por qué es un gate |
|---|---|---|
| 0 | Crea la rama de épica en git | Los ficheros deben crearse sobre la rama correcta, no sobre main |
| 1 | Lista de tareas + Gherkin informal | Define el alcance de la épica |
| 2 | Ficheros .feature (pytest-bdd) | Valida que los tests miden lo correcto antes de escribir código |
