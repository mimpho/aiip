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
LLM:          Claude Sonnet via LangChain (configurable en .env)
Embeddings:   BAAI/bge-m3
Vector DB:    ChromaDB 1.x  
Orquestación: LangChain v1.0
Frontend:     Chainlit
Auth + DB:    Supabase (región EU)
Entorno:      Google Colab + Drive
```

Variables de entorno necesarias — ver `.env.example` (a crear al inicio del desarrollo).

---

## Estructura del repositorio

```
aiip/
├── README.md          ← Índice y estado del proyecto
├── AGENTS.md          ← Este fichero
├── CITATION.cff       ← Cita académica
├── prompts.md         ← Log histórico de prompts. Append-only.
├── decisions.md       ← Registro de decisiones. Leerlo antes de tomar decisiones de diseño.
├── docs/
│   ├── PRD.md         ← Requisitos de producto
│   ├── tech-spec.md         ← Diseño técnico (fuente de verdad técnica)
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

**Configuración:** toda variable sensible o configurable (modelo, temperatura, URLs, API keys) en `.env`. Nunca en código.

**Tests:** bajo `tests/` con estructura que refleje el módulo que testean. Los escenarios Gherkin en `tests/features/`.

**Commits:** mensajes descriptivos en inglés. Una responsabilidad por commit.

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
