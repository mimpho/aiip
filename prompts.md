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

*Log iniciado en Fase 0 — junio 2026*
*Próximas entradas previstas: P-005 (system prompt v1.0 tras primera evaluación RAGAS), P-006 (prompt de evaluación clínica para el inmunólogo)*
