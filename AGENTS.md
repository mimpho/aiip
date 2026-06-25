# AGENTS.md — Contexto para agentes de IA

> Este fichero proporciona contexto operativo a cualquier agente de IA que trabaje en este repositorio (Claude Code, Cursor, Gemini CLI, etc.).  
> Estándar: AGENTS.md (Agentic AI Foundation / Linux Foundation, 2025).  
> Fuente de verdad técnica: `docs/tech-spec.md`. Decisiones de diseño: `decisions.md`.

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
IDE:          Claude Cowork mode + Antigravity IDE (Claude Sonnet 4.6)
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
└── tests/             ← Tests con especificación Gherkin (se crea al arrancar desarrollo)
```

---

## Convenciones de desarrollo

**Metodología:** BDD + TDD + Gherkin. Toda tarea del backlog tiene especificación Gherkin antes de ser implementada. Los tests se escriben antes que el código.

**Prompts:** siempre en ficheros bajo `prompts/`. Nunca embebidos en código Python. Versionados como cualquier otro fichero.

**Log de prompts (`prompts.md`):** al cerrar cada épica o sesión de trabajo relevante, el agente prepara un borrador de las entradas del log con valor real — decisiones de prompting, system prompts candidatos, razonamiento técnico — formateadas según la convención del fichero (P-ID, fecha, fase, tipo, herramienta, prompt, resultado). Marcos revisa y añade las entradas al log. No se registran conversaciones exploratorias ni prompts sin aprendizaje transferible.

**Configuración:** toda variable sensible o configurable (modelo, temperatura, URLs, API keys) en `.env`. Nunca en código.

**Tests:** bajo `tests/` con estructura que refleje el módulo que testean. Los escenarios Gherkin en `tests/features/`.

**Commits:** mensajes descriptivos en inglés. Una responsabilidad por commit.

---

## Workflow por tipo de tarea

### Tareas de setup y configuración (E-01)

Proceso ligero sin ramas ni TDD. Para cada tarea:

1. Ejecutar los pasos de configuración
2. Verificar manualmente cada criterio de aceptación Gherkin
3. Marcar la tarea como completada cuando todos los criterios pasan

### Tareas de código (E-02 en adelante)

Proceso completo en 6 pasos:

1. **Plan** — el agente propone el plan de implementación de la tarea antes de tocar código. Marcos lo aprueba.
2. **Rama** — el agente proporciona el comando para crear la rama. Marcos lo ejecuta.
   - Nomenclatura: `task/E[nn]-T[nn]-descripcion-corta` (ej: `task/E02-T01-supabase-auth`)
3. **TDD** — el agente escribe el test primero (Gherkin → pytest), luego la implementación.
4. **Validación** — el agente ejecuta los tests en el sandbox local. Si pasan, prepara el resumen.
5. **PR** — el agente prepara título, descripción y checklist del PR. Marcos crea el PR en GitHub y mergea.
6. **Cierre** — el agente actualiza el estado de la tarea en `epics.md` y prepara el borrador de `prompts.md`.

### Reparto de responsabilidades con git

| Acción | Quién | Motivo |
|---|---|---|
| `git status`, `git log`, `git diff`, `git branch` | Agente | Consulta — solo lectura |
| `git checkout -b`, `git push`, `git merge`, `git tag` | Marcos | Escritura en remoto |

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
