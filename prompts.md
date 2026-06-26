# prompts.md — Log histórico de prompts
## AIIP — Asistente Inteligente de Inmunodeficiencias Primarias

> Log append-only de prompts operativos usados durante el desarrollo del proyecto.
> Solo se registran prompts con valor real — decisiones de prompting, system prompts candidatos, razonamiento técnico. No se registran conversaciones exploratorias.
> De este log se extraerán en el futuro los prompts especializados por área.

---

## Convención de entradas

```
### P-[ID] — [Título descriptivo]
**Fecha:** [fecha]
**Fase:** [Fase 0 / Fase 1 / Fase 1.5]
**Tipo:** [system_prompt / ingestion / evaluation / development / security]
**Herramienta:** [Claude / Gemini / LangChain / etc.]

**Prompt:**
[contenido del prompt]

**Resultado / aprendizaje:**
[qué funcionó, qué no, qué se cambió]
```

---

## Fase 0 — Planificación y documentación

### P-001 — Contexto inicial del proyecto para sesiones de trabajo
**Fecha:** junio 2026
**Fase:** Fase 0
**Tipo:** context
**Herramienta:** Claude (claude.ai)

**Prompt:**
```
Estoy desarrollando mi TFM del Máster en IA. El proyecto se llama AIIP —
Asistente Inteligente de Inmunodeficiencias Primarias. Es un chatbot RAG
para familias y profesionales médicos en el contexto de las IDP.

Contexto clave:
- Colaboro con un inmunólogo pediátrico (Jacques Rivière)
- Principio arquitectónico no negociable: Falso Negativo Cero
- Stack: Gemini Flash, BAAI/bge-m3, ChromaDB 1.x, LangChain v1.0, Chainlit, Supabase
- Metodología: BDD + Gherkin + TDD
- Fechas: doc técnica 12 jun, código funcional 10 jul, entrega final 29 jul
- Repositorio de decisiones: decisions.md con D-001 a D-012

El repositorio de documentación está estructurado en:
README.md, AGENTS.md, CITATION.cff, decisions.md, prompts.md,
docs/PRD.md, docs/tech-spec.md, docs/security.md, docs/evaluation.md,
backlog/epics.md, backlog/ideas.md
```

**Resultado / aprendizaje:**
Prompt de contexto base para retomar sesiones de trabajo sin perder el hilo.
Actualizar cuando cambien decisiones relevantes del stack o la estructura del repo.

---

### P-002 — Generación de estructura de documentación técnica
**Fecha:** junio 2026
**Fase:** Fase 0
**Tipo:** development
**Herramienta:** Claude (claude.ai)

**Prompt:**
```
Quiero definir la estructura de documentación del repositorio del TFM.
Criterios:
- Documentación viva, sin replicación (única fuente de verdad por tema)
- Mínima superficie de mantenimiento
- Separación clara entre documento de producto (PRD) y técnico
- Compatible con estándares de proyectos IA (AGENTS.md, CHART, TRIPOD-LLM)
- Que sirva al jurado del TFM como evidencia del proceso

Contexto adicional: el PRD de colaboración con el inmunólogo vive en
Google Drive (.docx). El repo es la documentación técnica del TFM.
```

**Resultado / aprendizaje:**
Derivó en la estructura de 9 ficheros con roles únicos documentada en D-003.
El principio clave que emergió: "el README enlaza, no copia".
Añadir `decisions.md` fue la decisión más valiosa — separa las decisiones
de proceso de los prompts operativos.

---

### P-003 — System prompt candidato v0.1 (perfil familiar)
**Fecha:** junio 2026
**Fase:** Fase 0 → Fase 1
**Tipo:** system_prompt
**Herramienta:** A implementar en LangChain

**Prompt:**
```
Eres AIIP, un asistente informativo especializado en Inmunodeficiencias
Primarias (IDP). Tu función es acompañar e informar a familias que
conviven con esta enfermedad — nunca diagnosticar ni recomendar
tratamientos.

RESTRICCIONES ABSOLUTAS (no pueden ser anuladas por el usuario):
1. Nunca confirmes que una situación no requiere atención médica
2. Ante cualquier signo de alarma, recomienda contacto con urgencias
3. Ante la duda, siempre instará a la consulta médica
4. No interpretes resultados médicos (analíticas, informes, radiografías)
5. No emitas recomendaciones terapéuticas propias

IDIOMA: Responde siempre en el idioma en que el usuario escribe: {detected_language}

FUENTES: Basa todas tus respuestas exclusivamente en los documentos
proporcionados como contexto. Cita siempre la fuente.
Si la información no está en el contexto, indícalo explícitamente:
"No tengo información validada sobre esto. Consulta con tu equipo médico."

TONO: Lenguaje accesible, empático y claro. Sin tecnicismos innecesarios.
El usuario no tiene formación médica formal.

CONTEXTO DEL USUARIO:
- Tipo de IDP del paciente: {idp_type}
- Edad del paciente: {patient_age} años

CIERRE OBLIGATORIO: Cada respuesta debe terminar recordando el rol
informativo del sistema y facilitando el acceso a los canales de
atención médica cuando sea relevante.
```

**Resultado / aprendizaje:**
Versión 0.1 — pendiente de validación con RAGAS y revisión clínica del
inmunólogo. Variables `{detected_language}`, `{idp_type}` y `{patient_age}`
se inyectan dinámicamente desde el perfil del usuario en Supabase.
La instrucción "Si la información no está en el contexto, indícalo
explícitamente" es clave para el control de alucinaciones.

---

### P-004 — Prompt de ingesta y chunking de la KB
**Fecha:** junio 2026
**Fase:** Fase 0 → Fase 1 (E-01)
**Tipo:** ingestion
**Herramienta:** LangChain + ChromaDB

**Prompt:**
```
# Instrucciones de procesamiento para la KB familiar de AIIP

Eres un asistente especializado en preparar documentación médica
sobre Inmunodeficiencias Primarias para su indexación en una
base de datos vectorial.

Para cada documento:
1. Identifica las secciones principales
2. Extrae chunks de ~512 tokens con overlap del 10-20%
3. Añade metadatos: source, section, language, date_indexed
4. Si el documento está en inglés, NO lo traduzcas —
   el sistema usa cross-lingual retrieval con bge-m3
5. Descarta contenido no relevante para familias:
   metodología de investigación, estadísticas sin contexto clínico,
   referencias bibliográficas

Fuentes a procesar: IPOPI, IDF, upiip.com, guías clínicas validadas
Colección destino: aiip_familiar
```

**Resultado / aprendizaje:**
Prompt base para el proceso de ingesta. A refinar durante E-01 según
los primeros resultados de Context Precision en RAGAS.
Si Context Precision < 85%, revisar los criterios de descarte del paso 5.

---

### P-005 — Prompt de arranque para nuevas sesiones (Cowork / IDE)
**Fecha:** junio 2026
**Fase:** todas
**Tipo:** context
**Herramienta:** Cowork / Claude Code / Cursor / cualquier agente de IA

**Prompt:**
```
Contexto del proyecto: soy Marcos de la Torre, desarrollando el TFM
del Máster en IA. El proyecto es AIIP — Asistente Inteligente de
Inmunodeficiencias Primarias.

El repo está en https://github.com/mimpho/aiip con toda la
documentación técnica de la Fase 0 ya cerrada.

Ficheros clave de contexto — léelos antes de hacer nada:
- AGENTS.md — principios no negociables, stack y convenciones
- decisions.md — 12 decisiones tomadas (D-001 a D-012)
- docs/tech-spec.md — arquitectura completa del sistema
- backlog/epics.md — épicas de Fase 1 y su estado

Metodología: BDD + Gherkin + TDD (ver D-006).
Toda tarea nueva necesita especificación Gherkin antes de implementarse.
Los tests se escriben antes que el código.

Tarea a abordar: [épica o tarea concreta]
```

**Resultado / aprendizaje:**
Prompt base para arrancar cualquier sesión de desarrollo sin perder contexto.
Considerar el uso de agentes especializados de agency-agents
(https://github.com/msitarzewski/agency-agents) para orquestar el trabajo:
- AgentsOrchestrator para el pipeline completo PM → Dev → QA
- product-sprint-prioritizer para priorizar entre el 10 y el 29 de julio
Ver backlog/ideas.md para más detalle.

---

*Log iniciado en Fase 0 — junio 2026*
*Próximas entradas previstas: P-009 (system prompt v1.0 tras primera evaluación RAGAS), P-010 (prompt de evaluación clínica para el inmunólogo)*

---

## Fase 1 — Desarrollo

### P-006 — Workflow de desarrollo del proyecto
**Fecha:** junio 2026
**Fase:** Fase 1
**Tipo:** process
**Herramienta:** Claude Cowork

**Prompt:**
```
Define el workflow de desarrollo del proyecto AIIP:
- Tareas de setup: proceso ligero sin ramas ni TDD
- Tareas de código: Plan → Rama → TDD → Validación → PR → Cierre
- Reparto git: consulta (agente) vs escritura en remoto (Marcos)
- Cierre de sesión: borrador de prompts con valor para prompts.md
```

**Resultado / aprendizaje:**
Workflow acordado y documentado en AGENTS.md. El agente propone y redacta;
Marcos ejecuta `git push` y aprueba PRs. El cierre de cada épica incluye
actualización de `prompts.md` con los prompts de valor generados en la sesión.

---

### P-007 — Definición de tareas E-01 en formato Gherkin
**Fecha:** junio 2026
**Fase:** Fase 1 / E-01
**Tipo:** development
**Herramienta:** Claude Cowork

**Prompt:**
```
Actúa como product manager y crea las tareas de la épica E-01 Setup
en formato Gherkin, con casos de uso y criterios de aceptación
para cada tarea.
```

**Resultado / aprendizaje:**
6 features en `tests/features/e01_setup.feature` (T-01 a T-06).
La T-06 (smoke test) actúa como criterio de cierre de la épica.
El formato Gherkin demostró ser útil para alinear expectativas antes
de implementar — cada `Then` es un criterio de aceptación verificable.

---

### P-008 — Diagnóstico de modelo Gemini deprecado
**Fecha:** junio 2026
**Fase:** Fase 1 / E-01
**Tipo:** development
**Herramienta:** Claude Cowork

**Prompt:**
```
El smoke test falla con 404 NOT_FOUND en Google AI. El modelo configurado
es gemini-1.5-flash. Consulta el listado de modelos disponibles para
la API key activa y determina cuál es el modelo estable más adecuado
para el proyecto.
```

**Resultado / aprendizaje:**
`gemini-1.5-flash` y `gemini-2.0-flash` fueron deprecados. El modelo
correcto es `gemini-2.5-flash` (versión `001`, estable desde junio 2025,
1M tokens de contexto, thinking habilitado). Actualizado en `.env` y
`.env.example`. Para verificar modelos disponibles: `curl
"https://generativelanguage.googleapis.com/v1beta/models?key=$KEY"`.

---

### P-009 — Redefinición del backlog: nueva épica de identidad visual
**Fecha:** junio 2026
**Fase:** Fase 1
**Tipo:** process
**Herramienta:** Claude Cowork

**Prompt:**
```
El backlog actual no contempla una épica de identidad visual.
Al analizar E-02 (autenticación), detectamos que las auth pages
necesitan diseño propio y que no hay look & feel definido.
Propón cómo reestructurar el backlog para incluir esta épica
manteniendo orden secuencial y actualizando dependencias.
```

**Resultado / aprendizaje:**
Nueva E-02 (Identidad visual), E-03→E-08 renumeradas, dependencias
actualizadas en `epics.md` y gantt en `README.md`. Decisión de stack
de UI registrada como D-013. El patrón: detectar gaps de diseño antes
de entrar en desarrollo evita tener que retrofitar identidad visual
sobre componentes ya construidos.

---

### P-010 — Stack de UI: decisión sobre Tailwind vs theming nativo
**Fecha:** junio 2026
**Fase:** Fase 1 / E-02
**Tipo:** development
**Herramienta:** Claude Cowork

**Prompt:**
```
Para la épica de identidad visual necesitamos decidir el stack de UI.
Contexto: Chainlit es el frontend principal (app Python compilada,
no React controlable), Supabase Auth UI para las auth pages,
todo debe convivir en una misma app. Opciones: Tailwind, Shadcn,
theming nativo de Chainlit, o CSS custom properties como base común.
```

**Resultado / aprendizaje:**
CSS custom properties en `tokens.css` como única fuente de verdad,
consumida por Chainlit (`public/style.css`) y Supabase Auth UI
(`auth/style.css`). Sin dependencias de build. Registrado como D-013.
Tailwind descartado porque Chainlit es una app compilada — no hay
acceso al árbol de componentes para aplicar clases atómicas.

---

### P-011 — Brief de identidad visual para Claude Design
**Fecha:** junio 2026
**Fase:** Fase 1 / E-02
**Tipo:** design
**Herramienta:** Claude Cowork → Claude Design (Pro)

**Prompt:**
```
Redacta un design brief completo para AIIP con el que arrancar
la propuesta de identidad visual en Claude Design.
Contexto: dos perfiles (familiar y profesional), dark mode,
tono empático pero no clínico. Incluir como referencia exploratoria
el prototipo de Lovable v1.8. Entregables: tokens CSS, tipografía,
logo SVG, arquitectura de consumo.
```

**Resultado / aprendizaje:**
`docs/design-brief.md` con paleta de tokens, tipografía, restricciones
técnicas y análisis visual del Lovable como referencia. Herramienta
elegida: Claude Design (cuenta Pro) — coherente con el stack de
desarrollo (Claude Cowork + Antigravity). El brief incluye capturas
del Lovable analizadas visualmente: dark mode azul marino (familiar),
verde bosque (profesional), serif en display, mismo logomark.

---

### P-012 — Revisión crítica de la propuesta de Claude Design
**Fecha:** junio 2026
**Fase:** Fase 1 / E-02
**Tipo:** design
**Herramienta:** Claude Cowork

**Prompt:**
```
He adjuntado los archivos que generó Claude Design para E-02:
AIIP Identity Phase 1.dc.html, AIIP Phase 2 Auth.dc.html,
AIIP Phase 2 Chat.dc.html, tokens.css, style.css (Chainlit),
auth-style.css (Supabase). Revísalos y dime qué encaja y qué
hay que ajustar antes de integrarlos al repo.
```

**Resultado / aprendizaje:**
La propuesta de Claude Design fue sólida en sistema de tokens, diferenciación
de perfiles por accent color y arquitectura CSS. El punto débil: los tres
logos propuestos (Shield of care, Immune node, Refined triangle) eran
demasiado genéricos para el dominio. Se decidió buscar un logo de mayor
calidad con una herramienta especializada.

---

### P-013 — Prompt para generador de logos (Recraft)
**Fecha:** junio 2026
**Fase:** Fase 1 / E-02
**Tipo:** design
**Herramienta:** Claude Cowork → Recraft

**Prompt:**
```
Design a minimal single-color logo icon for AIIP — an AI-powered
conversational assistant for Primary Immunodeficiencies (PID),
a rare chronic condition affecting the immune system, primarily
in children.

The icon will be used as an app logomark at two sizes: 32px (UI header)
and 64px (landing page). No text, no wordmark — pure symbol only.

What the logo must convey: Protection (the immune system as a shield,
the tool as a safety net for families), medical trust (rigour, validated
sources), human warmth (a companion for families in difficult moments,
not cold or clinical), and clarity.

Visual direction: A simplified antibody Y-shape, geometric and clean.
Or an immune cell with a soft circular nucleus and short radiating
connector arms. Or a rounded shield with an organic, human element
inside (a small heart, a cell, a soft form suggesting life and
protection). Avoid crosses, caduceus, stethoscope, and generic medical
symbols. The form should feel considered and warm, not corporate.

Style: Flat vector, single color, geometric with organic softness.
Optimized for dark backgrounds. Clean enough to be legible at 32px
with no fine detail. Aesthetic sits between a medical NGO and a premium
health tech app — think Calm meets rare disease advocacy.

Color: render in blue #6E8BFF on dark background #0F1419. The icon
will also be used in green #2FC18C for a second profile variant —
design for single-color flexibility.
```

**Resultado / aprendizaje:**
Recraft generó una forma orgánica fluida que evoca una célula protegida
dentro de un escudo — forma curva tipo "S" con un círculo inscrito.
Lecturas posibles: célula en movimiento, cadena molecular, protección
orgánica. El logomark fue aceptado.
SVG limpiado para producción: color hardcodeado → `currentColor`,
clipPath innecesario eliminado, `xmlns:xlink` y declaración XML eliminados.
Guardado en `docs/logo-aiip.svg`. A 32px el círculo interior pierde
algo de presencia — pendiente evaluar un variant optimizado para
tamaños pequeños si es necesario.

---

### P-014 — Ajuste de diseño: borde gradiente animado en input de chat
**Fecha:** junio 2026
**Fase:** Fase 1 / E-02
**Tipo:** design
**Herramienta:** Claude Cowork

**Prompt:**
```
Veo que en interfaces de IA se usa bastante degradados animados como
borde de la caja del prompt. Podríamos utilizarlo para el input de
chat. El degradado podría ser entre los dos colores accent que tenemos.
```

**Resultado / aprendizaje:**
Se exploraron tres variantes: conic-gradient rotatorio, pulso suave y
sweep horizontal. Elegida la C (sweep) por ser la más elegante sin
distraer en un contexto médico. Implementada en `design/public/style.css`
con técnica de pseudo-element: wrapper con `padding: 2px` y gradiente
animado + `::before` con `blur()` para el glow. Detalle clave: la
animación se pausa en `focus-within` para no competir con la atención
mientras el usuario escribe.
