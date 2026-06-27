# AGENTS.md — Contexto para agentes de IA

> Este fichero proporciona contexto operativo a cualquier agente de IA que trabaje en este repositorio (Claude Code, Cursor, Gemini CLI, etc.).  
> Estándar: AGENTS.md (Agentic AI Foundation / Linux Foundation, 2025).  
> Fuente de verdad técnica: `docs/tech-spec.md`. Decisiones de diseño: `decisions.md`.

---

## Arranque de sesión

Si estás iniciando una sesión de trabajo en este repositorio, lee en este orden antes de tocar nada:

1. **Este fichero** (`AGENTS.md`) — contexto operativo, principios y workflow
2. **`decisions.md`** — decisiones de diseño ya tomadas. No las repitas ni las contradiges sin leerlas.
3. **`backlog/epics.md`** — estado actual de las épicas. La próxima en ejecutar es la primera con estado `⚪ No iniciada`.
4. **`prompts.md` → sección P-001** — prompt de contexto base del proyecto para orientarte si la sesión es conversacional.

Una vez orientado, consulta la épica activa para ver sus criterios de aceptación y el workflow que corresponde (ver sección "Workflow" abajo).

## Skills del proyecto

Las skills en `skills/` cubren el workflow completo de épica a tarea:

- **`skills/epic-start/SKILL.md`** — descomposición en tareas, revisión crítica automática, Gherkin informal, gates de aprobación, rama lista. Se lanza desde el IDE (Antigravity) al inicio de una épica.
- **`skills/task-start/SKILL.md`** — arranque de una tarea individual: revisión crítica, resolución de puntos abiertos, decisiones de arquitectura, `.feature` formal, preparación de rama. Se lanza desde **Cowork** antes de abrir el IDE para cada tarea.
- **`skills/epic-close/SKILL.md`** — PR description, actualización de registros, borrador para prompts.md. Se lanza desde el IDE al cerrar la épica.

---

## Qué es este proyecto

AIIP es un asistente conversacional RAG para familias y profesionales médicos en el contexto de las Inmunodeficiencias Primarias (IDP). Es un TFM con vocación de herramienta real.

Dos perfiles de usuario con URLs separadas, KB separada y tono distinto. Comparten backend.

---

## Principios de diseño no negociables

**1. Agnóstico de proveedor de IA**  
El proyecto usa Claude en este momento, pero el diseño no debe crear dependencias de proveedor. Esto significa:
- Nunca llamar directamente al SDK nativo de un proveedor — siempre via la abstracción de LangChain
- Modelo y parámetros de inferencia en variables de entorno, nunca hardcodeados en código
- System prompts en ficheros separados bajo `prompts/`, nunca embebidos en el código
- Si usas una feature específica de Claude (XML tags, etc.), documéntalo explícitamente como deuda técnica de proveedor

**2. Falso Negativo Cero**  
El agente nunca confirma que una situación es segura. Siempre orienta a consulta médica ante cualquier duda. Este principio afecta al system prompt, a la lógica de respuesta y a los tests. No lo comprometas bajo ninguna circunstancia.

**3. Privacy by design**  
El sistema almacena datos de salud de categoría especial (RGPD Art. 9), potencialmente de menores. No introduzcas almacenamiento de datos adicional sin revisar D-009 en `decisions.md`. Minimización de datos por defecto.

---

## Stack

```
LLM:          Gemini Flash (Google API — free tier), configurable en .env
Embeddings:   BAAI/bge-m3
Vector DB:    ChromaDB 1.x  
Orquestación: LangChain v1.0
Frontend:     Chainlit
Auth + DB:    Supabase (región EU)
IDE:          Antigravity IDE (código) + Claude Cowork (decisiones y debate)
```

Variables de entorno necesarias — ver `.env.example` (a crear al inicio del desarrollo).

---

## Estructura del repositorio

```
aiip/
├── README.md          ← Índice y estado del proyecto
├── AGENTS.md          ← Este fichero
├── CITATION.cff       ← Cita académica y referencias clave (documentación viva)
├── prompts.md         ← Log histórico de prompts. Append-only.
├── decisions.md       ← Registro de decisiones. Leerlo antes de tomar decisiones de diseño.
├── docs/
│   ├── PRD.md         ← Requisitos de producto
│   ├── tech-spec.md   ← Diseño técnico (fuente de verdad técnica)
│   ├── security.md    ← Seguridad: Falso Negativo Cero + OWASP + RGPD
│   └── evaluation.md  ← Evaluación: RAGAS + CHART
├── backlog/
│   ├── epics.md       ← Épicas de Fase 1
│   └── ideas.md       ← Cajón de sastre
├── tasks/             ← Planes de implementación por tarea (E[nn]-T[nn]-plan.md)
│                         Generados en Cowork por task-start. Léelos al arrancar en el IDE.
└── tests/             ← Tests con especificación Gherkin (se crea al arrancar desarrollo)
```

---

## Convenciones

- **Prompts:** ficheros bajo `prompts/`. Nunca embebidos en código Python.
- **Configuración:** toda variable sensible o configurable en `.env`. Nunca en código.
- **Tests:** bajo `tests/`. Escenarios Gherkin ejecutables en `tests/features/` (pytest-bdd).
- **Commits:** mensajes en inglés. Una responsabilidad por commit.

---

## Workflow

### Setup y configuración (E-01, E-02)

1. Ejecutar pasos de configuración
2. Verificar manualmente los criterios de aceptación Gherkin
3. Marcar tarea completada

### Desarrollo con código (E-03 en adelante)

Metodología BDD + TDD + pytest-bdd. Seguir las skills:
- **Arranque de épica** → `skills/epic-start/SKILL.md` (en el IDE)
- **Arranque de tarea** → `skills/task-start/SKILL.md` (en Cowork) — genera el `.feature` y el plan de implementación en `tasks/E[nn]-T[nn]-plan.md`
- **Al abrir el IDE para una tarea:** lee `tasks/E[nn]-T[nn]-plan.md` antes de tocar código
- **Tarea a tarea (TDD):** step definitions fallan ✗ → implementar → tests pasan ✓ → PR de tarea
- **Cierre de épica** → `skills/epic-close/SKILL.md` (en el IDE)

### Reparto git

| Acción | Quién |
|---|---|
| `status`, `log`, `diff`, `branch` | Agente |
| `checkout -b`, `push`, `merge`, `tag` | Marcos |

> **`main` está protegida.** Nunca proponer commits directos a main. Todo el trabajo va en rama + PR.

---

## Antes de tomar cualquier decisión de diseño

Lee `decisions.md`. Si la decisión ya está registrada, respétala. Si introduces una nueva decisión relevante, documéntala.

---

## Lo que NO debes hacer

- Hardcodear el nombre del modelo LLM en el código
- Embeber prompts en ficheros Python
- Almacenar datos de usuario fuera de Supabase sin justificación
- Comprometer el principio de Falso Negativo Cero
- Crear dependencias de proveedor sin documentarlas explícitamente
