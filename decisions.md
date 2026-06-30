# decisions.md — Registro de decisiones del proyecto AIIP

> Traza de las decisiones relevantes tomadas durante el ciclo de vida del TFM.  
> Cubre decisiones de producto, técnicas, de arquitectura y de proceso.  
> Cada entrada incluye contexto, alternativas consideradas y justificación.  
> Documento vivo: se añaden entradas, no se editan las existentes.

---

## Índice

- [D-001 — Elección del proyecto: agente conversacional para IDP](#d-001--elección-del-proyecto-agente-conversacional-para-idp)
- [D-002 — Principio arquitectónico: Falso Negativo Cero](#d-002--principio-arquitectónico-falso-negativo-cero)
- [D-003 — Estructura de la documentación del repositorio](#d-003--estructura-de-la-documentación-del-repositorio)
- [D-004 — Stack tecnológico: Fase 1](#d-004--stack-tecnológico-fase-1)
- [D-005 — Patrón RAG básico para Fase 1](#d-005--patrón-rag-básico-para-fase-1)
- [D-006 — Metodología de desarrollo: BDD + TDD + Gherkin](#d-006--metodología-de-desarrollo-bdd--tdd--gherkin)
- [D-007 — Plataforma, despliegue y separación de perfiles](#d-007--plataforma-despliegue-y-separación-de-perfiles)
- [D-008 — Autenticación, persistencia y memoria de perfil](#d-008--autenticación-persistencia-y-memoria-de-perfil)
- [D-009 — Protección de datos: RGPD y datos de salud](#d-009--protección-de-datos-rgpd-y-datos-de-salud)
- [D-010 — Agnósticismo de proveedor de IA](#d-010--agnósticismo-de-proveedor-de-ia)
- [D-011 — Estrategia multiidioma](#d-011--estrategia-multiidioma)
- [D-012 — Escalabilidad a otras patologías](#d-012--escalabilidad-a-otras-patologías)
- [D-013 — Stack de UI e identidad visual](#d-013--stack-de-ui-e-identidad-visual)
- [D-014 — Supabase como broker único del OAuth de Google](#d-014--supabase-como-broker-único-del-oauth-de-google)
- [D-015 — Criterios de aplicación de TDD por épica](#d-015--criterios-de-aplicación-de-tdd-por-épica)

---

## D-001 — Elección del proyecto: agente conversacional para IDP

**Fecha:** mayo 2026  
**Fase:** planificación

**Contexto**  
El TFM requería elegir entre tres ideas de proyecto relacionadas con IA: un agente bioinformático para edición génica (XIAP-Rescue), una herramienta de predicción clínica, y un asistente conversacional para IDP.

**Decisión**  
Agente conversacional para Inmunodeficiencias Primarias (AIIP), con dos perfiles de usuario: familias afectadas y profesionales médicos.

**Alternativas descartadas**  
- *XIAP-Rescue:* alta complejidad técnica de dominio, viabilidad comprometida para un TFM acotado en tiempo.  
- *Predicción clínica:* riesgo de cruzar la línea del diagnóstico automático, con implicaciones éticas y regulatorias que exceden el alcance del TFM.

**Justificación**  
El asistente conversacional permite demostrar el ciclo de vida completo de un sistema de IA aplicado (RAG, evaluación, seguridad, producto) dentro del tiempo disponible, con impacto real y colaboración clínica verificable. Existe además conexión personal con la temática y acceso a un colaborador experto (inmunólogo pediátrico).

---

## D-002 — Principio arquitectónico: Falso Negativo Cero

**Fecha:** mayo 2026  
**Fase:** producto / arquitectura

**Contexto**  
En un sistema de información médica, el riesgo más grave no es dar una respuesta incorrecta, sino dar una respuesta tranquilizadora ante una situación que requiere atención médica urgente.

**Decisión**  
AIIP nunca confirma que una situación es segura. Ante cualquier duda, el sistema orienta siempre hacia consulta médica. Este principio es no negociable y condiciona el diseño del system prompt, la lógica de respuesta y los criterios de evaluación.

**Alternativas consideradas**  
- Sistema de triaje con niveles de urgencia: descartado por el riesgo de que el usuario interprete un nivel bajo como señal de que no necesita consultar.

**Justificación**  
En salud pediátrica, un falso negativo (decirle a una familia que todo está bien cuando no lo está) tiene consecuencias potencialmente irreversibles. La asimetría entre el coste de un falso positivo (consulta innecesaria) y un falso negativo (complicación no atendida) justifica una postura conservadora estructural.

---

## D-003 — Estructura de la documentación del repositorio

**Fecha:** junio 2026  
**Fase:** planificación

**Contexto**  
Al inicio del desarrollo se definió la estructura de documentación del repositorio. El criterio rector fue: documentación viva, mantenible y sin replicación — evitando el patrón habitual de muchos documentos que rápidamente quedan desincronizados.

**Decisión**  
Estructura de ficheros con roles únicos y sin solapamiento. Ver árbol completo en `README.md`.

**Principios que guían la estructura**  
1. **Sin replicación:** cada dato vive en un único fichero. El README enlaza, no copia.  
2. **Mínima superficie de mantenimiento:** cada fichero se ganó su sitio. Lo que no justifica doc propio vive dentro del más cercano a su naturaleza.  
3. **Separación producto / técnica:** PRD y TDD tienen audiencias distintas y no se solapan.

**Alternativas consideradas**  
- *Estructura del TFM de referencia (AI4Devs Example2):* README monolítico + `/docs/`. Descartada por riesgo de boilerplate y por no separar claramente documento de producto del técnico.  
- *Documentación mínima (solo README + un doc técnico):* insuficiente para demostrar el proceso al jurado.

**Estándares consultados**  
AGENTS.md (Agentic AI Foundation / Linux Foundation, 2025), CHART (2025), TRIPOD-LLM (Nature Medicine, 2025), convenciones de Hugging Face model cards, análisis de 32K model cards (Stanford/HF, arXiv 2402.05160).

---

## D-004 — Stack tecnológico: Fase 1

**Fecha:** junio 2026  
**Fase:** planificación / técnica

**Contexto**  
El PRD v1.9 dejaba el stack como "opciones candidatas" sin cerrar. Se cerró en la fase de planificación cruzando tres fuentes: el PRD, el módulo 12 del máster (LangChain + RAG) y el TFM de referencia AI4Devs Example2.

**Principio rector del stack**  
El AIIP tiene vocación de convertirse en una herramienta real más allá del TFM. Esto prioriza tecnologías con proyección a producción sobre opciones puramente educativas, y documenta explícitamente las evoluciones naturales de cada componente cuando el sistema escale.

**Decisión**

| Componente | Elección | Alternativas descartadas |
|---|---|---|
| LLM | Gemini Flash (Google API — free tier) | Claude Sonnet API (mejor rendimiento, pero coste por token — candidato natural en producción), GPT-4o, Gemma local (sin infraestructura GPU garantizada, añade ops sin beneficio claro para el TFM) |
| Embeddings | BAAI/bge-m3 | all-MiniLM-L12-v2 (monolingüe inglés, 2021) |
| Vector DB | ChromaDB 1.x | Pinecone (coste), FAISS (sin persistencia), pgvector (infra adicional) |
| Orquestación | LangChain v1.0 | LlamaIndex (mejor RAG puro, menos ecosistema agéntico) |
| Frontend | Chainlit | Streamlit (insuficiente para visualizar pipeline RAG al jurado) |
| Autenticación + DB | Supabase | Firebase (vendor lock-in), SQLite (no escalable), PostgreSQL local (más ops) |
| Entorno desarrollo | Claude Cowork mode + Antigravity IDE (Claude Sonnet 4.6) |

**Justificación clave**  
- *Gemini Flash:* free tier generoso, suficiente para el volumen de un TFM (demos, pruebas, evaluación RAGAS), multimodal nativo (relevante para la feature de imágenes de síntomas del backlog). El TFM demuestra la arquitectura, no la elección del modelo más potente. En producción — especialmente para el perfil profesional — se evaluará un modelo más potente (Claude Sonnet, GPT-4o u otros). Gracias a D-010, ese cambio es una variable de entorno.  
- *bge-m3:* multilingüe, open-source, 8K tokens. Supera directamente al all-MiniLM del módulo 12, monolingüe inglés de 2021.  
- *ChromaDB:* persistencia incluida, sin infraestructura adicional. Evolución natural a pgvector en producción.  
- *LangChain v1.0:* estable hasta v2.0, ecosistema completo para RAG y agentes.  
- *Chainlit:* el propio temario del módulo 12 lo define como "objetivamente mejor cuando el foco es chat con un agente". Visualización step-by-step del RAG, streaming nativo, experiencia cercana a producto real. Elegir Streamlit por ser el stack del módulo sería una justificación de comodidad, no técnica.  
- *Supabase:* autenticación integrada (OAuth Google + email/password), PostgreSQL gestionado en región EU (Frankfurt — datos no salen de la UE), MCP connector disponible. Cubre autenticación, persistencia de conversaciones y perfil de usuario en una sola plataforma.

**Evoluciones previstas hacia producción**  
- ChromaDB → pgvector (cuando haya infraestructura Postgres existente)  
- RAG básico → Corrective RAG o búsqueda híbrida si RAGAS lo justifica  
- Chainlit → versión con autenticación avanzada y threads persistentes (cubierto ya en Fase 1 vía Supabase)

---

## D-005 — Patrón RAG básico para Fase 1

**Fecha:** junio 2026  
**Fase:** técnica

**Contexto**  
Existen múltiples variantes de RAG con distinto nivel de complejidad. La elección del patrón condiciona la complejidad del desarrollo y la evaluabilidad del sistema.

**Decisión**  
RAG básico (naive RAG) para Fase 1: chunk → embed → retrieve top-K → generate.

**Alternativas consideradas**  
- *Agentic RAG:* patrón emergente dominante en 2026. Descartado para Fase 1 por complejidad no justificada en el MVP.  
- *Corrective RAG (CRAG):* añade un grader tras la recuperación. Interesante pero añade coste y complejidad de evaluación.  
- *HyDE:* mejora del 20-40% en precisión en corpus densos. Descartado porque el corpus de IDP es suficientemente específico.

**Justificación**  
El RAG básico es la base sobre la que se construyen todas las variantes. Para el MVP la prioridad es demostrar el ciclo completo (ingesta → retrieval → generación → evaluación RAGAS) con fiabilidad. **Revisión prevista:** evaluar CRAG o búsqueda híbrida si los resultados RAGAS muestran problemas de precisión.

---

## D-006 — Metodología de desarrollo: BDD + TDD + Gherkin

**Fecha:** junio 2026  
**Fase:** planificación / proceso

**Contexto**  
En un TFM donde el ciclo de vida completo es objeto de evaluación, la metodología de desarrollo tiene el mismo peso que las decisiones técnicas. Se necesita un enfoque que conecte producto, desarrollo y testing bajo un lenguaje común.

**Decisión**  
Tres capas metodológicas complementarias:

- **BDD (Behavior Driven Development)** como capa transversal: producto, desarrollo y testing hablan el mismo idioma. Permite que el colaborador clínico valide criterios de aceptación sin conocimiento técnico.
- **Gherkin** como formato de especificación de tareas: sintaxis `Given / When / Then`. Cada tarea del backlog tendrá su especificación Gherkin antes de ser desarrollada.
- **TDD (Test Driven Development)** como práctica de desarrollo: los tests se escriben antes que el código.

**Relación entre las tres capas**  
```
Producto (PRD)
    → BDD: especificación de comportamiento en lenguaje natural
        → Gherkin: formalización en Given/When/Then (backlog de tareas)
            → TDD: test primero, implementación después
                → Evaluación RAGAS: validación del comportamiento del agente
```

**Justificación**  
BDD + Gherkin crea un puente directo entre los casos de uso del PRD y los tests del sistema. El colaborador clínico puede revisar los criterios de aceptación en Gherkin y validar que el comportamiento del agente es clínicamente correcto. TDD garantiza que el principio de Falso Negativo Cero es un comportamiento verificable, no solo una declaración.

**Implicaciones en la estructura del repositorio**  
- `backlog/epics.md` — épicas de Fase 1, se descomponen en tareas Gherkin una vez cerrado el TDD  
- `tests/` — tests con especificación Gherkin (se crea al arrancar el desarrollo)

---

## D-007 — Plataforma, despliegue y separación de perfiles

**Fecha:** junio 2026  
**Fase:** planificación / producto

**Contexto**  
El AIIP tiene vocación de herramienta real. La decisión de plataforma y separación de perfiles condiciona decisiones técnicas de Fase 1 aunque el despliegue inicial sea simple.

**Decisión**  

*Separación de perfiles:* URLs separadas. Familiar y profesional son productos distintos que comparten backend — no una misma app con selector de perfil. Un familiar no necesita saber que existe una versión profesional.

*Despliegue por niveles:*

| Nivel | Plataforma | Compromiso | Cuándo |
|---|---|---|---|
| TFM | URL pública (Chainlit + HuggingFace Spaces o Railway) | Firme | 10 julio 2026 |
| Evolución natural | Web responsive embebible vía webview o iframe | Planificado, sin fecha | Post-TFM |
| Futuro no comprometido | App nativa / widget web fundación (upiip.com) | Posible, no planificado | Indeterminado |

**Alternativas descartadas**  
- *Selector de perfil en una misma URL:* expone la existencia de la versión profesional a los familiares, genera confusión y complica la lógica de KB.  
- *App nativa desde el inicio:* coste desproporcionado para el TFM.

**Implicaciones técnicas en Fase 1**  
1. **Diseño responsive desde el inicio** — Chainlit lo soporta nativamente.  
2. **CORS configurado correctamente** — necesario para futura integración con la web de la fundación.

---

## D-008 — Autenticación, persistencia y memoria de perfil

**Fecha:** junio 2026  
**Fase:** planificación / técnica

**Contexto**  
Un asistente que recuerda el contexto del usuario (tipo de IDP, edad del paciente, historial de conversaciones) es cualitativamente distinto a uno que empieza de cero cada vez. Especialmente para el perfil familiar, la memoria entre conversaciones es una diferencia de producto real, no solo una feature técnica.

**Decisión**  
Autenticación y persistencia incluidas en Fase 1 (MVP), no post-TFM.

**Stack de persistencia:** Supabase  
- Autenticación: OAuth Google + email/password, con **rol definido en el registro** (familiar / profesional). La autenticación es el mecanismo de separación de perfiles — no hay selector en la interfaz.  
- Persistencia de conversaciones: Supabase PostgreSQL  
- Memoria de perfil: tabla de perfil de usuario con datos estables capturados en el onboarding

**Dos tipos de memoria distinguidos por diseño:**

| Tipo | Qué almacena | Cuándo se actualiza |
|---|---|---|
| Memoria de perfil | Datos estables: tipo de IDP, edad del paciente, contexto familiar relevante | Onboarding + cuando el usuario lo indica explícitamente |
| Memoria de conversación | Histórico de sesiones anteriores | Cada conversación |

**Justificación**  
Con código funcional previsto para el 10 de julio y entrega final el 29 de julio, la autenticación básica con Supabase es alcanzable. Chainlit tiene autenticación integrada que se conecta directamente con Supabase Auth. La memoria de perfil cierra el producto como herramienta real: el familiar no tiene que repetir el contexto de su hijo en cada sesión.

**Nota RGPD:** los datos almacenados son de categoría especial (salud). Ver D-009.

---

## D-009 — Protección de datos: RGPD y datos de salud

**Fecha:** junio 2026  
**Fase:** planificación / legal / ética

**Contexto**  
En el momento en que AIIP almacena datos de salud — y potencialmente de menores — opera en el nivel más alto de protección que establece la regulación europea. Esto no es opcional ni post-TFM: condiciona qué datos se pueden almacenar, con qué base legal y cómo se informa al usuario.

**Marco legal aplicable**  
- **RGPD Art. 9** — datos de salud como categoría especial, con requisitos reforzados  
- **LOPDGDD** (España) — capa nacional sobre el RGPD  
- **Reglamento UE de IA 2024/1689** — marco de IA de alto riesgo en entornos de salud  
- **Protección de menores** — capa adicional si el paciente es menor de edad

**Decisiones de diseño con implicaciones legales**

| Requisito | Decisión de diseño |
|---|---|
| Consentimiento explícito | Formulario de registro con consentimiento informado específico para datos de salud, no un checkbox genérico |
| Minimización de datos | Solo almacenar lo estrictamente necesario. Tipo de IDP en lugar de diagnóstico exacto cuando sea suficiente |
| Derecho al olvido | El usuario puede solicitar borrado completo de sus datos desde la interfaz |
| Política de privacidad | Visible y comprensible antes del registro, redactada en lenguaje no técnico |
| Cookies | Banner con opciones reales (no solo "aceptar todo") |
| Localización de datos | Supabase región EU (Frankfurt) — los datos no salen de la UE |
| Menores | Si el paciente es menor, el consentimiento lo otorga el tutor legal |

**Para el TFM específicamente**  
No se requiere implementar un sistema de compliance completo, pero sí demostrar que las decisiones de diseño lo tienen en cuenta. El jurado valorará que el sistema está diseñado con privacidad por defecto (*privacy by design*), no como un añadido posterior.

**Implicaciones en la documentación**  
- `docs/security.md` incluirá una sección dedicada a protección de datos además de OWASP y Falso Negativo Cero.

---

## D-010 — Agnósticismo de proveedor de IA

**Fecha:** junio 2026  
**Fase:** planificación / arquitectura

**Contexto**  
El proyecto se desarrolla con Claude como herramienta principal de desarrollo e inferencia, pero el diseño no debe crear dependencias innecesarias con ningún proveedor específico. Si en algún momento es necesario cambiar de modelo — por coste, disponibilidad, rendimiento o decisión estratégica — el cambio debe ser una operación de configuración, no de refactoring.

**Decisión**  
El AIIP es agnóstico de proveedor de IA por diseño. Aplica a cuatro niveles:

| Nivel | Principio | Implementación |
|---|---|---|
| LLM | El proveedor es configurable, no hardcodeado | Modelo y parámetros en variables de entorno / fichero de config |
| Prompts | Sin dependencias de features propias de un proveedor | System prompts en ficheros separados, versionados, compatibles con cualquier modelo instruction-tuned |
| Orquestación | Usar la abstracción de LangChain, no el SDK nativo | Nunca llamar directamente al SDK del proveedor — siempre via la capa de LangChain |
| Evaluación | RAGAS es agnóstico de proveedor | Sin cambios necesarios |

**Lo que esto NO implica**  
No significa optimizar para todos los modelos simultáneamente. Significa que el diseño no crea dependencias innecesarias que luego sean costosas de deshacer.

**Alternativas consideradas**  
- *Optimizar prompts para Claude (XML tags, etc.) como práctica general:* descartado. Si se usan features específicas de un proveedor, han de estar aisladas y documentadas explícitamente.

**Justificación**  
La elección de Claude como herramienta principal es una decisión práctica del TFM, no una decisión de arquitectura. El sistema debe poder continuar con otro proveedor sin problema si las circunstancias cambian.

**Implicaciones en `AGENTS.md`**  
Este principio se documenta explícitamente en `AGENTS.md` para que cualquier agente de IA que trabaje en el repositorio lo respete por defecto.

---

## D-011 — Estrategia multiidioma

**Fecha:** junio 2026  
**Fase:** planificación / técnica

**Contexto**  
Las fuentes de conocimiento del AIIP (Orphanet, ESID, PubMed) son nativamente en inglés o tienen su versión más completa y actualizada en inglés. Los usuarios objetivo son principalmente hispanohablantes, pero el sistema tiene vocación de proyección internacional.

**Decisión**  
Arquitectura de dos capas:

| Capa | Idioma | Justificación |
|---|---|---|
| KB interna | Inglés | Idioma nativo de las fuentes. Más completo y actualizado. bge-m3 resuelve el cross-lingual retrieval. |
| Interfaz y respuestas | Idioma del usuario (detección automática) | El LLM recibe chunks en inglés pero genera la respuesta en el idioma detectado |

**Tres decisiones concretas:**

**1. Idiomas de lanzamiento**  
Castellano como idioma por defecto. Detección automática cubre el resto desde el inicio — inglés, catalán y otros idiomas funcionan sin configuración adicional. Selector explícito de idioma en interfaz como evolución futura.

**2. Detección de idioma**  
Automática via `langdetect` (integrado con LangChain). El idioma detectado se pasa al system prompt: *"responde siempre en el idioma en que el usuario escribe"*. Sin selector explícito en MVP — la experiencia más natural y sin esfuerzo adicional significativo.

**3. KB multilingüe**  
La KB se indexa en inglés. bge-m3 tiene capacidad de búsqueda semántica cross-lingual — una pregunta en castellano recupera chunks en inglés con buena precisión. No es necesario traducir la KB ni mantener versiones paralelas.

**Alternativas descartadas**  
- *KB en castellano:* dependencia de traducciones potencialmente incompletas o desactualizadas respecto al original en inglés.  
- *Selector explícito de idioma:* añade fricción innecesaria en el MVP. La detección automática cubre el caso de uso sin esfuerzo adicional.  
- *Inglés como idioma de interfaz desde el inicio:* no es prioritario para el perfil familiar hispanohablante. Viene solo con la detección automática si un usuario escribe en inglés.

**Justificación**  
bge-m3 fue elegido precisamente por su capacidad multilingüe y cross-lingual (ver D-004). Esta decisión activa esa capacidad de forma coherente: la KB en inglés maximiza la calidad y actualidad del conocimiento, y el cross-lingual retrieval elimina la necesidad de duplicar o traducir contenido.

**Implicaciones en Fase 1**  
- System prompt incluye instrucción de respuesta en idioma del usuario  
- `langdetect` como dependencia del pipeline  
- No hay trabajo adicional de KB por esta decisión — se indexa en el idioma original de las fuentes

**Evolución futura**  
- Selector explícito de idioma en interfaz  
- Catalán como idioma de interfaz explícito (relevante dado el contexto del colaborador clínico)  
- Expansión de KB a fuentes en castellano cuando estén disponibles con calidad equivalente

---

## D-012 — Escalabilidad a otras patologías

**Fecha:** junio 2026  
**Fase:** planificación / arquitectura

**Contexto**  
El AIIP nace centrado en Inmunodeficiencias Primarias, pero tiene potencial de expandirse a otras ramas — inmunodeficiencias no primarias, otras patologías raras, o incluso otras enfermedades crónicas.

**Decisión**  
El diseño de Fase 1 no hardcodea "IDP" en la lógica del agente. La arquitectura es extensible por diseño:

- **KB:** colecciones separadas en ChromaDB por dominio, no por patología específica. Añadir una nueva KB es añadir una colección sin tocar el core.
- **System prompt:** parametrizado por perfil y dominio, no con referencias hardcodeadas a IDP.
- **Lógica del agente:** agnóstica del dominio médico concreto — el dominio lo define la KB, no el código.

**Lo que esto NO implica**  
No significa diseñar un sistema genérico desde el inicio — eso sería sobreingeniería. Significa evitar decisiones que cierren la puerta a la extensión futura sin necesidad.

**Justificación**  
El coste de hacer el diseño extensible en Fase 1 es mínimo. El coste de refactorizar dependencias hardcodeadas en Fase 3 puede ser significativo.

**Evolución futura**  
Anotado en `backlog/ideas.md` — expansión a otras patologías como línea de desarrollo post-TFM.

---

## D-013 — Stack de UI e identidad visual

**Fecha:** junio 2026
**Fase:** Fase 1 / E-02

**Contexto**
Al definir la épica de identidad visual (E-02) se necesitó decidir cómo gestionar estilos, theming y componentes de UI de forma coherente entre las páginas de autenticación (Supabase Auth UI) y la interfaz conversacional (Chainlit).

**Decisión**
Design tokens centralizados en CSS custom properties como única fuente de verdad, consumidos por cada sistema vía su mecanismo de theming nativo. Sin frameworks CSS adicionales (sin Tailwind, sin Shadcn).

```
public/tokens.css     ← fuente de verdad: colores, tipografía, espaciado
    ↓
public/style.css      ← Chainlit consume los tokens, sobreescribe sus variables CSS
auth/style.css        ← Supabase Auth UI consume los mismos tokens
```

**Alternativas descartadas**
- *Tailwind CSS:* Chainlit es una app Python con frontend compilado — no es una app React controlable con clases atómicas. La fricción de integración no justifica el beneficio.
- *Shadcn/ui:* pensado para React; no encaja con la arquitectura de Chainlit.
- *Theming solo en Chainlit:* no resuelve las auth pages de Supabase, que viven fuera del frontend de Chainlit.

**Justificación**
Los CSS custom properties son el único mecanismo que funciona de forma nativa en ambos sistemas sin dependencias adicionales. Un cambio en `tokens.css` se propaga a toda la app. Mínima complejidad, máxima coherencia visual.

**Implicaciones**
- E-02 (Identidad visual) define los tokens base
- E-03 (Auth) consume los tokens en las páginas de Supabase
- E-05 (Interfaz Chainlit) consume los tokens en el theming del chat

---

## D-014 — Supabase como broker único del OAuth de Google

**Fecha:** junio 2026
**Fase:** Fase 1 / E-03

**Contexto**
Al descomponer T-01 de E-03 (configurar el login con Google) surgió una ambigüedad no resuelta: Chainlit soporta su propio mecanismo nativo de OAuth (`@cl.oauth_callback` contra un proveedor configurado directamente en Chainlit), independiente de Supabase. Había que decidir si ese era el camino, o si Supabase Auth debía seguir siendo el único punto de identidad, también para OAuth.

**Decisión**
Supabase Auth es el único broker de identidad del sistema, tanto para email/password como para OAuth Google. Chainlit nunca implementa su propio flujo OAuth nativo: dispara `signInWithOAuth` contra Supabase y consume la sesión que Supabase devuelve tras el callback. El Client ID/Secret de Google se configuran una sola vez en Supabase Authentication > Providers — nunca en código ni en `.env` del repo (no confundir con `GOOGLE_API_KEY`, que es la key de Gemini en un proyecto de Google Cloud distinto).

**Alternativas descartadas**
- *Chainlit OAuth nativo + sincronización manual a Supabase:* introduce dos sistemas de identidad en paralelo que habría que mantener sincronizados a mano, duplicando lógica que Supabase ya resuelve.

**Justificación**
Un único mecanismo de identidad para los dos métodos de login es más simple de razonar y testear, y es coherente con D-008 (Chainlit "se conecta directamente con Supabase Auth"). Un solo Client ID de Google compartido por las dos apps (familiar/profesional), ya que ambas comparten el mismo proyecto Supabase (D-007) — la app a la que vuelve el usuario tras el login se resuelve con el parámetro `redirectTo`, no con credenciales distintas por app.

**Implicaciones técnicas**
- Redirect URI registrada en Google Cloud Console: `https://<project-ref>.supabase.co/auth/v1/callback` (única, no una por app)
- Supabase Auth > URL Configuration > Redirect URLs debe incluir las URLs de ambas apps (familiar y profesional, dev y producción a medida que se definan)
- La pantalla de consentimiento de Google ("OAuth consent screen") se configura con scopes mínimos (`email`, `profile`, `openid`); en modo "Testing" solo los usuarios añadidos explícitamente como testers podrán autenticarse

---

## D-015 — Criterios de aplicación de TDD por épica

**Fecha:** junio 2026  
**Fase:** proceso / metodología

**Contexto**  
D-006 establece BDD + TDD + Gherkin como metodología de desarrollo. Sin embargo, no todas las épicas tienen el mismo tipo de entregable: configuración de servicios, diseño visual y lógica de negocio son categorías distintas con necesidades de validación distintas. Aplicar TDD de forma uniforme a todo el proyecto introduciría coste sin valor en algunas épicas y podría dar una falsa sensación de cobertura en otras.

**Decisión**  
TDD con pytest-bdd se aplica selectivamente según el tipo de épica:

| Épica | Tipo | TDD | Justificación |
|---|---|---|---|
| E-00 | Documentación | No | No hay código ejecutable que testear |
| E-01 | Configuración de entorno | No | Verificación manual de servicios y credenciales |
| E-02 | Identidad visual | No | CSS y diseño — la validación es visual, no automatizable con pytest |
| E-03 | Autenticación | Sí | Lógica de negocio con integración real contra Supabase |
| E-04 | Pipeline RAG + seguridad | Sí — prioritario | El módulo de Falso Negativo Cero (D-002) requiere tests demostrables |
| E-05 | Interfaz Chainlit (UX) | No | Streaming, responsive y theming — validación manual en browser |
| E-06 | Ingesta de KB | Sí | Pipeline de procesamiento con criterios verificables automáticamente |
| E-07 / E-09 | Evaluación RAGAS | Sí | Las métricas son numéricas y automatizables |
| E-08 | Memoria e histórico | Sí | Lógica de persistencia con integración Supabase |

**Alternativas descartadas**  
- *TDD en E-05:* el valor de testear con pytest que un mensaje aparece en pantalla o que el diseño es responsive es mínimo; la verificación visual directa en el browser es más efectiva y menos costosa de mantener.  
- *Sin TDD en E-04:* descartado explícitamente — el Falso Negativo Cero es el principio de seguridad central del sistema y necesita evidencia objetiva y reproducible.

**Justificación**  
El coste de TDD es alto en las primeras épicas de setup (E-00 a E-02), pero se amortiza a partir de E-03, donde el patrón de fixtures e integración ya está establecido y reutilizable. La distinción clave es: si el comportamiento es verificable automáticamente y el fallo tiene consecuencias (lógica de negocio, seguridad, persistencia de datos), TDD aplica. Si la verificación requiere juicio humano (diseño, UX), no aplica.

**Implicaciones**  
- `epic-start` y `task-start` deben identificar el tipo de épica/tarea antes de proponer `.feature` y plan TDD.
- E-05 se valida con revisión manual documentada, no con pytest. Esto queda anotado en `backlog/epics.md`.

---

*Próximas decisiones previstas: diseño del system prompt (D-015) — al arrancar E-04 (Pipeline RAG), configuración definitiva de colecciones ChromaDB (D-016) — al arrancar E-06 (Ingesta KB), estrategia de chunking validada (D-017) — tras primera evaluación RAGAS*
