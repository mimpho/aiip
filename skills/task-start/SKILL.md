---
name: task-start
description: >
  Arranque de una tarea individual dentro de una épica activa. Úsala en Cowork
  para revisar, aprobar y formalizar una tarea antes de pasarla al IDE. Cubre
  el trabajo previo al desarrollo: revisión crítica, resolución de puntos
  abiertos, decisiones de arquitectura pendientes, creación del .feature y
  (si aplica) setup de rama. Actívala cuando Marcos diga "vamos con la T-XX",
  "arrancamos la tarea", "revisamos la T-XX" o similar.
---

# task-start

Workflow de arranque para tareas individuales. Se ejecuta en Cowork, antes de
abrir el IDE. El objetivo es que cuando se abra la rama de tarea, no haya
ambigüedad sobre qué hay que hacer ni cómo validarlo.

## Paso 0 — Setup de rama [solo tareas de código — GATE: Marcos ejecuta]

Este paso va **antes que cualquier otra cosa**, incluida la lectura de
`AGENTS.md`, `decisions.md` o cualquier fichero de la épica. No leas ni
modifiques nada del repositorio todavía.

Para tareas de configuración (sin rama, sin PR — ver "Tipo de tarea" en el
Paso 1), este bloque no aplica: pasa directamente a "Antes de empezar".

Para tareas de código:

1. Identifica únicamente el nombre corto de la tarea leyendo **solo** la fila
   correspondiente en la tabla de tareas de `backlog/epics.md` (no leas el
   resto del fichero todavía — eso es parte de "Antes de empezar").
2. Verifica el nombre real de la epic branch con un comando de solo lectura
   (`git branch -a` o `git ls-remote --heads origin`) **antes** de proponer
   los comandos de checkout. No lo derives ni lo memorices a partir del
   título de la épica en `epics.md` — el nombre de rama puede no coincidir
   (ej. la épica "Ingesta y procesamiento de la KB" usa `epic/E06-kb-ingestion`,
   no `epic/E06-ingesta-procesamiento-kb`). Esta verificación es de solo
   lectura, no choca con el reparto de git de `AGENTS.md`.
3. Según la tabla de "Reparto git" de `AGENTS.md`, `checkout -b` es una acción
   de Marcos, no del agente. **Nunca ejecutes estos comandos tú mismo** —
   preséntaselos a Marcos y pídele que los ejecute, usando el nombre de rama
   verificado en el paso anterior:

   > Nombra la rama siempre en inglés, aunque el nombre corto de la tarea esté
   > en castellano (ej. `task/E06-T03-multilingual-chunking-strategy`, no
   > `chunking-multiidioma`).

   ```bash
   git checkout epic/E[nn]-nombre-real-verificado
   git pull origin epic/E[nn]-nombre-real-verificado
   git checkout -b task/E[nn]-T[nn]-descripcion-corta
   ```

4. **Espera confirmación explícita de Marcos de que la rama está creada**
   antes de leer ningún otro fichero o proponer ningún cambio.

---

## Antes de empezar

Lee en este orden:
1. `AGENTS.md` — principios no negociables
2. `backlog/epics.md` — criterios de la épica a la que pertenece la tarea (aquí sí, completo)
3. `decisions.md` — decisiones relevantes para esta tarea
4. El fichero de handoff si existe (ej: `HANDOFF_E03_epic-start.md`) — puede
   contener la definición de la tarea y puntos abiertos ya identificados
5. `tests/features/` — comprueba si ya existe un `.feature` para esta tarea

Si la tarea tiene dependencias (`Depende de T-XX`), verifica que esas tareas
tienen su `.feature` creado y están aprobadas.

---

## Paso 1 — Revisión crítica de la tarea [GATE: Marcos aprueba]

Presenta la definición actual de la tarea (tomada del handoff o de la épica) y
aplica la siguiente revisión antes de proponer cambios:

### Checklist de revisión

**Claridad de alcance**
- ¿El user story describe quién hace qué y para qué, sin ambigüedad?
- ¿Los criterios de aceptación cubren el happy path y al menos un caso de error relevante?
- ¿Hay algún criterio que sea inverificable (no tiene un "entonces" concreto)?

**Responsabilidades técnicas**
- ¿Queda claro qué sistema/librería hace qué? (si hay integración con terceros: ¿quién orquesta, quién responde?)
- ¿Los criterios mencionan explícitamente los ficheros o componentes que se crean/modifican?
- ¿Hay dependencias de otras tareas que no están reflejadas en las notas?

**Configuración de terceros**
- ¿Hay pasos manuales en consolas externas (Supabase, Google Cloud, etc.) necesarios para esta tarea?
- Si los hay, ¿están capturados como criterios verificables o como notas de implementación?

**Puntos abiertos**
- ¿Hay decisiones de diseño sin tomar que afectan a esta tarea?
- ¿Hay comportamientos de borde sin definir (ej: ¿qué pasa si el usuario X hace Y en el contexto Z)?

**Tipo de tarea**
- ¿Es una tarea de **configuración** (sin rama, sin PR — como T-01 de E-03)?
  → El criterio es: ¿se puede verificar sin ejecutar tests automatizados?
- ¿Es una tarea de **código** (rama + TDD + PR)?
  → Todas las demás.

Presenta el resultado de la revisión con este formato:

```
### Revisión de T-XX — [nombre]

**Tipo:** Configuración | Código

**Problemas encontrados:**
- [problema 1 — y propuesta de resolución]
- [problema 2 — y propuesta de resolución]

**Puntos abiertos (requieren decisión de Marcos):**
- ⚠️ [pregunta concreta — opciones: A / B]

**Propuesta de criterios actualizados:**
[versión revisada del user story + criterios, si hay cambios]
```

Si no hay cambios, indícalo explícitamente: "La definición es correcta, sin
cambios propuestos."

**Espera aprobación explícita de Marcos antes de continuar.**

Tras la aprobación, actualiza **inmediatamente** el estado de la tarea en
`backlog/epics.md` antes de seguir al Paso 2:

```markdown
| T-XX | [nombre] | 🔄 En progreso |
```

---

## Paso 2 — Decisiones de arquitectura pendientes [si aplica]

Si en la revisión aparecieron decisiones de diseño sin registrar, créalas ahora
en `decisions.md` siguiendo el formato existente:

```markdown
## D-0XX — [Título de la decisión]

**Fecha:** [YYYY-MM-DD]
**Épica:** E-XX
**Estado:** Adoptada

**Contexto:** [por qué se necesita esta decisión]

**Decisión:** [qué se decide]

**Consecuencias:** [qué implica — qué queda fuera, qué se simplifica]
```

Actualiza también el índice al inicio de `decisions.md` si existe.

Si no hay decisiones nuevas, salta este paso.

---

## Paso 3 — Formalización del .feature [GATE: Marcos aprueba]

### Para tareas de configuración

Crea `tests/features/eXX_tYY_nombre.feature` con formato checklist verificable
manualmente:

```gherkin
# E-XX T-YY — [Nombre de la tarea]
# Tipo: Configuración manual — verificación sin tests automatizados

Feature: [nombre de la tarea]

  Como [rol]
  Quiero [capacidad]
  Para [objetivo]

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: [paso de configuración 1]
    Given [estado previo o precondición]
    When [acción manual realizada]
    Then [cómo verificar que está correcto]

  Scenario: [paso de configuración 2]
    ...
```

### Para tareas de código

Crea `tests/features/eXX_tYY_nombre.feature` con pytest-bdd:

```gherkin
# E-XX T-YY — [Nombre de la tarea]
# Criterio: [qué comportamiento valida este fichero]

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

  Scenario: [caso de error relevante]
    Given [estado inicial]
    When [acción que falla]
    Then [comportamiento esperado ante el error]
```

Reglas para los .feature:
- Un fichero por tarea
- Escenarios atómicos: un comportamiento por escenario
- Si la tarea toca el principio de Falso Negativo Cero, incluye un escenario
  que valide que el agente deriva a consulta médica
- Los nombres de escenarios deben ser autoexplicativos sin leer el cuerpo

**Espera aprobación explícita de Marcos antes de crear el fichero.**
Este es el gate clave: el .feature define exactamente qué se va a testear
(o verificar manualmente).

---

## Paso 4 — Plan de implementación [solo tareas de código]

Para tareas de configuración, este paso no aplica.

Este paso cierra el trabajo en Cowork y genera el contexto que Antigravity
necesita para empezar a codificar sin ambigüedad. El objetivo es que el agente
del IDE no tome ninguna decisión de diseño — solo ejecute el plan.

### Research previo (si aplica)

Antes de escribir el plan, identifica si hay APIs externas o comportamientos
de librerías que no están documentados en `decisions.md` ni en `tech-spec.md`
y que son necesarios para implementar la tarea. Ejemplos típicos:

- Firma exacta de un método de Supabase/LangChain/Chainlit que no se ha usado antes
- Qué devuelve un callback y en qué formato
- Restricciones no obvias de una librería (ej: Chainlit solo permite un `password_auth_callback`)

Si hay algo que investigar, hazlo aquí (buscando en docs oficiales o en el
código del repo) antes de escribir el plan. Anota lo que encuentres en la
sección "Contexto técnico" del plan.

### Fichero del plan

Crea `tasks/E[nn]-T[nn]-plan.md` con este formato:

```markdown
# Plan — E-XX T-XX [nombre de la tarea]

## Contexto técnico
[Solo lo que no está ya en AGENTS.md, decisions.md o tech-spec.md.
Si el research no encontró nada nuevo, escribe "Sin hallazgos adicionales."]

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `ruta/fichero.py` | crear | [qué hace] |
| `ruta/otro.py` | modificar | [qué añade/cambia] |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **[Scenario del .feature]** — `tests/features/eXX_tXX.feature`
   - Step definitions en: `tests/step_defs/test_eXX_tXX.py`
   - Implementación en: `ruta/fichero.py`
   - Notas: [qué hay que saber para implementar este escenario concreto]

2. **[Siguiente scenario]**
   - ...

## Restricciones a respetar
[Principios de AGENTS.md que aplican especialmente a esta tarea — solo los
relevantes, no copiar la lista entera.]

## Lo que queda fuera de esta tarea
[Qué comportamientos relacionados se excluyen explícitamente — evita scope creep.]
```

Guarda el fichero antes de cerrar la sesión de Cowork. Antigravity lo leerá
al arrancar la sesión de desarrollo.

---

## Resumen de gates

| Paso | Qué aprueba Marcos | Por qué es un gate |
|---|---|---|
| 0 | Ejecuta y confirma la creación de la rama | Working tree limpio *antes* de que el agente lea o toque nada |
| 1 | Definición revisada de la tarea | Cierra puntos abiertos antes de comprometer diseño |
| 2 | Decisiones de arquitectura (si aplica) | Registra antes de implementar |
| 3 | Fichero .feature | Define exactamente qué se valida |
| 4 | Plan de implementación | El IDE ejecuta, no diseña |

---

## Vuelta de Antigravity con tests en verde

Cuando Marcos vuelva a Cowork reportando que el ciclo TDD ha terminado en
Antigravity y los tests pasan, **no los reejecutes en el sandbox de Cowork** —
el entorno no tiene el proyecto configurado (venv, dependencias) para correr
`pytest`. Esto aplica aunque todavía no se haya invocado `task-close`
explícitamente: es el primer momento en que existe la tentación de
"verificar" ejecutando la suite, y ya es tarde para hacerlo aquí. Confía en el
resultado reportado y, si quieres revisar algo, hazlo leyendo el código y el
`.feature`, no ejecutando tests. Cuando Marcos confirme que quiere cerrar la
tarea, continúa con `task-close`.
