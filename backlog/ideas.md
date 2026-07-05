# backlog/ideas.md — Cajón de sastre

> Documento de captura libre. No requiere mantenimiento activo.  
> Aquí vive todo lo que puede ser útil en algún momento pero que no tiene sitio definido aún.  
> Sin orden de prioridad. Sin compromiso de ejecución.

---

## Recursos pendientes de explorar

### agency-agents (msitarzewski)
- **Repo:** https://github.com/msitarzewski/agency-agents
- **Qué es:** colección de 112 agentes especializados para Claude Code, Cursor, Gemini CLI y otros. Cada agente es un `.md` con personalidad, misión y métricas de éxito. Nativo en Claude Code.
- **Relevancia para AIIP:** explorar si hay agentes aplicables durante la fase de desarrollo (security engineer, backend developer, QA). Potencialmente útil para estructurar cómo trabajamos con Claude Code en Fase 1.
- **Cuándo revisarlo:** al arrancar el desarrollo real (post-documentación).

### OpenAPI / open spec para la API del agente
- **Qué sería:** fichero `openapi.yaml` en la raíz del repo que especifique formalmente los endpoints, schemas de request/response y parámetros del agente AIIP.
- **Por qué no ahora:** no hay API implementada todavía. Documentar una spec antes de tener implementación genera deuda desde el primer día.
- **Camino propuesto:** en el `tech-spec.md` definimos los contratos de API en pseudospec (bloque de código cercano a OpenAPI). Cuando llegue el desarrollo, ese bloque se convierte en el `openapi.yaml` con esfuerzo mínimo.
- **Cuándo revisarlo:** Fase 2, cuando haya endpoints reales.

### llms.txt
- **Qué es:** propuesta de Jeremy Howard (Answer.AI, sept 2024) para un fichero Markdown en la raíz del dominio que ayuda a los LLMs a consumir el contenido de un sitio en tiempo de inferencia.
- **Relevancia:** si publicamos documentación web del AIIP, podría facilitar que agentes de IA la consuman directamente.
- **Cuándo revisarlo:** si se publica documentación web pública del proyecto.

### DAIMS — Datasheets for AI and Medical Datasets
- **Qué es:** extensión del framework "Datasheets for Datasets" (Gebru et al.) específica para datos médicos. Checklist de 24 requisitos de estandarización (arXiv 2501.14094, 2025).
- **Relevancia:** directamente aplicable a la knowledge base de inmunodeficiencias pediátricas del AIIP.
- **Estado (5 jul 2026, epic-start E-06):** formalizado como T-06 de E-06 (`docs/kb-datasheet.md`) — ver `backlog/epics.md`.

### Model Context Protocol (MCP)
- **Qué es:** estándar abierto de Anthropic (nov 2024), adoptado por OpenAI y Google, para conectar LLMs con herramientas y fuentes de datos externas vía JSON-RPC.
- **Relevancia:** si la arquitectura del AIIP evoluciona hacia un patrón agéntico (herramientas externas, múltiples fuentes), MCP sería la forma estándar de conectarlas.
- **Cuándo revisarlo:** Fase 2B (agente científico) o si se añaden herramientas externas.

---

## Ideas de producto / funcionalidad

### Business rules como documento indexado en la KB
- **Qué sería:** un fichero `knowledge_base/business_rules.md` (o equivalente) con las reglas clínicas explícitas del sistema indexado como chunk en ChromaDB — p.ej. síntomas que siempre requieren derivación urgente, situaciones de alarma en IDP pediátrica, límites del sistema.
- **Por qué es interesante:** refuerza el principio de Falso Negativo Cero con conocimiento *recuperable* vía RAG, no solo con instrucciones estáticas en el system prompt. Si el LLM recupera la regla del vector store, la cita con fuente — más trazable y auditable que una instrucción embebida.
- **Origen:** sesión de agentes del máster (junio 2026) — patrón observado en el laboratorio de chatbot con reglas de negocio.
- **Estado (5 jul 2026, epic-start E-06):** descartado para E-06, no solo pospuesto. D-019 (E-04) ya resolvió la detección de alarma de forma determinista (`config/alarm_triggers.json` + coincidencia de substring contra la query), precisamente para evitar depender de similitud semántica en algo crítico de seguridad. Indexar las mismas reglas también como chunk introduciría una segunda vía de verdad en paralelo — riesgo de que las dos fuentes diverjan sin que nadie lo note. Si en el futuro se quiere reforzar trazabilidad/citación de las reglas de seguridad, revisar primero si eso puede lograrse citando `config/alarm_triggers.json` directamente en la respuesta, sin pasar por retrieval.


### Integración con la web de la fundación (upiip.com)
- **Qué sería:** widget o iframe embebido en la web de la fundación donde colabora el inmunólogo.
- **Requisito técnico ya cubierto en Fase 1:** CORS configurado correctamente.
- **Cuándo revisarlo:** post-TFM, en coordinación con el inmunólogo colaborador.

### App nativa (iOS / Android)
- **Qué sería:** app móvil que consume el AIIP vía webview sobre la web responsive.
- **Nota:** la web responsive de Fase 2 es el prerequisito. No tiene sentido planificar la app antes.
- **Cuándo revisarlo:** solo si hay tracción real de uso post-TFM.

### Enrutados y gestión de sesiones cross-platform
- **Qué es:** decisión de arquitectura de rutas y gestión de sesiones para cuando el AIIP se consuma desde múltiples plataformas (web, webview, widget).
- **Nota:** la autenticación básica está resuelta en Fase 1 via Supabase (ver D-008). Los enrutados avanzados para multi-plataforma son decisión post-TFM.
- **Cuándo revisarlo:** al planificar la evolución web responsive (post-TFM).

---

## Referencias académicas pendientes de leer

*(vacío por ahora)*

---

*Última entrada: junio 2026*

### Expansión a otras patologías
- **Qué sería:** ampliar el AIIP a inmunodeficiencias no primarias, enfermedades raras u otras patologías crónicas.
- **Nota:** el diseño de Fase 1 ya lo contempla — colecciones separadas en ChromaDB, system prompt parametrizado, lógica agnóstica del dominio. Ver D-012.
- **Cuándo revisarlo:** post-TFM, cuando haya tracción real de uso.

### Selector explícito de idioma en interfaz
- **Qué sería:** dropdown o selector en la interfaz de Chainlit para que el usuario elija el idioma explícitamente, en lugar de depender solo de detección automática.
- **Nota:** la detección automática cubre el MVP. El catalán como idioma explícito es especialmente relevante dado el contexto del colaborador clínico.
- **Cuándo revisarlo:** post-TFM o si hay feedback de usuarios que la detección automática falla.

### Prototipos de Lovable
- **Qué son:** dos prototipos interactivos navegables generados en fase temprana del proyecto, antes de tener documentación técnica suficiente.
  - Perfil familias: https://aiip-familly-app.lovable.app/
  - Perfil profesionales: https://aiip-professional-app.lovable.app/
- **Estado:** desactualizados respecto a las decisiones de producto y técnicas tomadas desde entonces.
- **Cuándo revisarlo:** cuando la documentación técnica esté cerrada y haya una base sólida para generar nuevas propuestas de UI. Valorar entonces si usar Lovable o generar propuestas directamente con Claude (HTML/React de alta fidelidad, iterable en conversación, sin necesidad de prototipo navegable externo para la fase de diseño).

---

## Agentes de agency-agents para fase de desarrollo

Repo: https://github.com/msitarzewski/agency-agents

> **Estado (27 jun 2026):** la necesidad de orquestación PM→Dev→QA está cubierta
> por las skills `epic-start` y `epic-close` del propio repo + el workflow de AGENTS.md.
> Revisar solo si surge una necesidad concreta no cubierta.

### product-manager (Alex)
- **Qué es:** agente PM con plantilla de PRD estructurada con evidencia, PRFAQ y gestión de scope creep.
- **Relevancia para AIIP:** útil si hay cambios de alcance por feedback de Jacques Rivière o decisiones de scope durante el desarrollo.
- **Cuándo usarlo:** cuando llegue feedback clínico que obligue a iterar el PRD.
