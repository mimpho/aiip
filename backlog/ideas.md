# backlog/ideas.md — Cajón de sastre

> Documento de captura libre. No requiere mantenimiento activo.  
> Aquí vive todo lo que puede ser útil en algún momento pero que no tiene sitio definido aún.  
> Sin compromiso de ejecución — pero cada entrada lleva un campo **Criticidad** (Alta/Media/Baja,
> criterio de Marcos/Claude, no una métrica formal) para saber con qué merece la pena ponerse
> antes si hay que elegir. Entradas ya resueltas o descartadas lo indican en vez de un nivel.

---

## Recursos pendientes de explorar

### agency-agents (msitarzewski)
- **Criticidad:** 🟢 Baja
- **Repo:** https://github.com/msitarzewski/agency-agents
- **Qué es:** colección de 112 agentes especializados para Claude Code, Cursor, Gemini CLI y otros. Cada agente es un `.md` con personalidad, misión y métricas de éxito. Nativo en Claude Code.
- **Relevancia para AIIP:** explorar si hay agentes aplicables durante la fase de desarrollo (security engineer, backend developer, QA). Potencialmente útil para estructurar cómo trabajamos con Claude Code en Fase 1.
- **Cuándo revisarlo:** al arrancar el desarrollo real (post-documentación).

### OpenAPI / open spec para la API del agente
- **Criticidad:** 🟢 Baja
- **Qué sería:** fichero `openapi.yaml` en la raíz del repo que especifique formalmente los endpoints, schemas de request/response y parámetros del agente AIIP.
- **Por qué no ahora:** no hay API implementada todavía. Documentar una spec antes de tener implementación genera deuda desde el primer día.
- **Camino propuesto:** en el `tech-spec.md` definimos los contratos de API en pseudospec (bloque de código cercano a OpenAPI). Cuando llegue el desarrollo, ese bloque se convierte en el `openapi.yaml` con esfuerzo mínimo.
- **Cuándo revisarlo:** Fase 2, cuando haya endpoints reales.

### llms.txt
- **Criticidad:** 🟢 Baja
- **Qué es:** propuesta de Jeremy Howard (Answer.AI, sept 2024) para un fichero Markdown en la raíz del dominio que ayuda a los LLMs a consumir el contenido de un sitio en tiempo de inferencia.
- **Relevancia:** si publicamos documentación web del AIIP, podría facilitar que agentes de IA la consuman directamente.
- **Cuándo revisarlo:** si se publica documentación web pública del proyecto.

### DAIMS — Datasheets for AI and Medical Datasets
- **Criticidad:** ✅ Resuelta — no aplica nivel
- **Qué es:** extensión del framework "Datasheets for Datasets" (Gebru et al.) específica para datos médicos. Checklist de 24 requisitos de estandarización (arXiv 2501.14094, 2025).
- **Relevancia:** directamente aplicable a la knowledge base de inmunodeficiencias pediátricas del AIIP.
- **Estado (5 jul 2026, epic-start E-06):** formalizado como T-06 de E-06 (`docs/kb-datasheet.md`) — ver `backlog/epics.md`.

### Script de verificación de vida de las URLs del manifest (`url_status`/`url_checked_at`)
- **Criticidad:** 🟢 Baja
- **Qué sería:** script de mantenimiento aparte (nunca en el path de latencia del chat, mismo
  principio que D-022 para el chunking) que recorra las URLs de `data/raw/manifest.json` y
  compruebe si siguen vivas, guardando el resultado cacheado en el propio manifest (campos
  `url_status`/`url_checked_at` junto a `url`). La citación en el chat solo leería ese estado
  cacheado — sin red por pregunta.
- **Por qué no ahora:** surgió durante la revisión de E-06 T-08 (enlazar fuentes citadas a su
  URL original). Con el manifest ya al 100% de URLs rellenadas a mano por Marcos (7 jul 2026),
  T-08 se cierra con citación de enlace directo sin esta capa de verificación — el coste de un
  404 ocasional es bajo (no es un fallo de Falso Negativo Cero, el documento sigue trazable
  localmente vía checksum).
- **Cuándo revisarlo:** si el volumen de la KB crece y el riesgo de enlaces rotos deja de ser
  marginal, o si se detectan varios 404 reales en producción.

### Model Context Protocol (MCP)
- **Criticidad:** 🟢 Baja
- **Qué es:** estándar abierto de Anthropic (nov 2024), adoptado por OpenAI y Google, para conectar LLMs con herramientas y fuentes de datos externas vía JSON-RPC.
- **Relevancia:** si la arquitectura del AIIP evoluciona hacia un patrón agéntico (herramientas externas, múltiples fuentes), MCP sería la forma estándar de conectarlas.
- **Cuándo revisarlo:** Fase 2B (agente científico) o si se añaden herramientas externas.

---

## Ideas de producto / funcionalidad

### Business rules como documento indexado en la KB
- **Criticidad:** 🚫 Descartada — no aplica nivel
- **Qué sería:** un fichero `knowledge_base/business_rules.md` (o equivalente) con las reglas clínicas explícitas del sistema indexado como chunk en ChromaDB — p.ej. síntomas que siempre requieren derivación urgente, situaciones de alarma en IDP pediátrica, límites del sistema.
- **Por qué es interesante:** refuerza el principio de Falso Negativo Cero con conocimiento *recuperable* vía RAG, no solo con instrucciones estáticas en el system prompt. Si el LLM recupera la regla del vector store, la cita con fuente — más trazable y auditable que una instrucción embebida.
- **Origen:** sesión de agentes del máster (junio 2026) — patrón observado en el laboratorio de chatbot con reglas de negocio.
- **Estado (5 jul 2026, epic-start E-06):** descartado para E-06, no solo pospuesto. D-019 (E-04) ya resolvió la detección de alarma de forma determinista (`config/alarm_triggers.json` + coincidencia de substring contra la query), precisamente para evitar depender de similitud semántica en algo crítico de seguridad. Indexar las mismas reglas también como chunk introduciría una segunda vía de verdad en paralelo — riesgo de que las dos fuentes diverjan sin que nadie lo note. Si en el futuro se quiere reforzar trazabilidad/citación de las reglas de seguridad, revisar primero si eso puede lograrse citando `config/alarm_triggers.json` directamente en la respuesta, sin pasar por retrieval.


### Integración con la web de la fundación (upiip.com)
- **Criticidad:** 🟢 Baja
- **Qué sería:** widget o iframe embebido en la web de la fundación donde colabora el inmunólogo.
- **Requisito técnico ya cubierto en Fase 1:** CORS configurado correctamente.
- **Cuándo revisarlo:** post-TFM, en coordinación con el inmunólogo colaborador.

### App nativa (iOS / Android)
- **Criticidad:** 🟢 Baja
- **Qué sería:** app móvil que consume el AIIP vía webview sobre la web responsive.
- **Nota:** la web responsive de Fase 2 es el prerequisito. No tiene sentido planificar la app antes.
- **Cuándo revisarlo:** solo si hay tracción real de uso post-TFM.

### Enrutados y gestión de sesiones cross-platform
- **Criticidad:** 🟢 Baja
- **Qué es:** decisión de arquitectura de rutas y gestión de sesiones para cuando el AIIP se consuma desde múltiples plataformas (web, webview, widget).
- **Nota:** la autenticación básica está resuelta en Fase 1 via Supabase (ver D-008). Los enrutados avanzados para multi-plataforma son decisión post-TFM.
- **Cuándo revisarlo:** al planificar la evolución web responsive (post-TFM).

### Edición de perfil: cambiar correo, contraseña y nombre estando ya autenticado
- **Criticidad:** 🟡 Media — mencionado ya dos veces (E-03, E-05) sin capturarse, señal de que reaparece
- **Qué sería:** una forma de editar, ya logueado, los tres datos que hoy solo se fijan en el
  momento del signup/login: contraseña (`update_user({"password": ...})`, sin correo de por
  medio a diferencia de "olvidé mi contraseña"), correo (`type="email_change"` de Supabase,
  misma familia de `verify_otp` que confirmación/recuperación), y nombre (ya hay wiring para
  esto desde E-05 T-06 — `update_user_metadata`, solo falta un comando en el chat para
  reeditarlo, hoy solo se pregunta una vez).
- **Por qué no ahora:** mencionado como pendiente ya en E-03 T-03 (jun 2026) y otra vez en E-05
  T-06 (9 jul 2026) sin llegar a capturarse — anotado ahora para que no se vuelva a perder.
  Chainlit no tiene pantalla de "ajustes de cuenta" nativa, así que requeriría el mismo patrón
  de rutas propias que T-06 (o comandos dentro del chat para el nombre).
- **Cuándo revisarlo:** cuando haya señal real de que hace falta (usuario con contraseña débil
  que quiere cambiarla, correo mal escrito en el signup, etc.) — no hay urgencia sin esa señal.

### Acceso como invitado (sin cuenta)
- **Criticidad:** 🟢 Baja — riesgo de cuota de Gemini si se implementa sin control de uso
- **Qué sería:** un modo de usar el chat sin registrarse — Chainlit no soporta auth "mixta"
  (algunos logueados, otros no; `require_login()` es todo o nada en cuanto hay
  `password_auth_callback`), así que la única vía realista es una credencial fija conocida que
  `password_auth_callback` reconozca y autentique sin pasar por Supabase.
- **Por qué no ahora (9 jul 2026, task-start E-05 T-06):** riesgo de cuota de Gemini — D-025 y
  D-027 ya documentan que el proyecto se quedó corto de cuota durante las pruebas. Una
  credencial de invitado conocida es una puerta sin límite de uso por persona, justo el
  escenario que ya causó problemas antes. Si se retoma, valorar algún límite de uso básico antes
  de exponerlo. A favor: cero PII almacenada para invitados, alineado con D-009. Identidad
  compartida entre todos los invitados — inofensivo hoy (D-033, pipeline sin estado), pero hay
  que excluir explícitamente al invitado de cualquier persistencia cuando llegue E-08.
- **Cuándo revisarlo:** si hay señal de que el registro es una barrera real de adopción, y con
  algún control de cuota/rate-limit ya pensado.

### Despliegue online del perfil familias (demo funcional, no solo prototipo estático)
- **Criticidad:** 🟡 Media — hoy solo hay prototipos estáticos de diseño (Lovable, ver "Prototipo
  interactivo" en `README.md`), no una instancia real del chat funcionando en la nube
- **Qué sería:** desplegar `chainlit/main_family.py` en un hosting accesible online para demo del
  TFM, no solo en local.
- **Requisitos técnicos identificados (10 jul 2026):** Supabase y Gemini ya están en la nube, no
  bloquean nada. El embedding model (`BAAI/bge-m3`, vía `sentence_transformers`) se descarga y
  corre en el propio proceso — pesa un par de GB, necesita una máquina con RAM decente, no una
  función serverless minúscula. La base vectorial (`data/chroma/`, ~69 MB hoy) está en
  `.gitignore` — no viaja con el repo, hay que empaquetarla en la imagen de despliegue o
  regenerarla en el build. Secrets necesarios: `GOOGLE_API_KEY`, `HF_TOKEN`, `CHROMA_PATH`,
  credenciales de Supabase, `CHAINLIT_AUTH_SECRET`, `OAUTH_GOOGLE_CLIENT_ID`/`SECRET`.
- **Opciones evaluadas:** Hugging Face Spaces con Docker (tier gratuito 2 vCPU/16 GB RAM, de sobra
  para bge-m3, se duerme tras ~48h de inactividad pero arranca solo con tráfico — razonable para
  un demo) o Fly.io (también gratuito, pero sus websockets no son sticky por defecto si se escala
  a más de una instancia — irrelevante para una sola instancia de demo).
- **Por qué no ahora:** es trabajo de infraestructura real (Docker, cuentas, gestión de secrets)
  fuera del alcance de Cowork — requiere credenciales de Marcos y probablemente terminal/Antigravity.
- **Cuándo revisarlo:** encaja de forma natural en E-10 (Pulido: responsive, CORS y UX) o como
  epic propia si se decide antes.

---

## Referencias académicas pendientes de leer

*(vacío por ahora)*

---

*Última entrada: junio 2026*

### Expansión a otras patologías
- **Criticidad:** 🟢 Baja
- **Qué sería:** ampliar el AIIP a inmunodeficiencias no primarias, enfermedades raras u otras patologías crónicas.
- **Nota:** el diseño de Fase 1 ya lo contempla — colecciones separadas en ChromaDB, system prompt parametrizado, lógica agnóstica del dominio. Ver D-012.
- **Cuándo revisarlo:** post-TFM, cuando haya tracción real de uso.

### Selector explícito de idioma en interfaz
- **Criticidad:** 🟡 Media — alternativa real al punto 4 de "Hallazgos del RAG" (fallo de `langdetect`) más abajo, si esa vía no se resuelve
- **Qué sería:** dropdown o selector en la interfaz de Chainlit para que el usuario elija el idioma explícitamente, en lugar de depender solo de detección automática.
- **Nota:** la detección automática cubre el MVP. El catalán como idioma explícito es especialmente relevante dado el contexto del colaborador clínico.
- **Cuándo revisarlo:** post-TFM o si hay feedback de usuarios que la detección automática falla.

### Prototipos de Lovable
- **Criticidad:** 🟢 Baja
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
- **Criticidad:** 🟢 Baja
- **Qué es:** agente PM con plantilla de PRD estructurada con evidencia, PRFAQ y gestión de scope creep.
- **Relevancia para AIIP:** útil si hay cambios de alcance por feedback de Jacques Rivière o decisiones de scope durante el desarrollo.
- **Cuándo usarlo:** cuando llegue feedback clínico que obligue a iterar el PRD.

---

## Hallazgos del RAG para optimización en E-07

Durante la validación de E-05 T-03 (visualización de pasos intermedios) se evidenciaron dos áreas de mejora para el motor RAG que deberán resolverse y evaluarse formalmente en la épica E-07 (Evaluación RAGAS):

### 1. Grounding estricto vs. Conocimiento del mundo (Alucinación)
- **Criticidad:** 🟡 Media — respuesta demasiado conservadora, no incorrecta ni insegura
- **Problema:** El LLM está instruido para usar "exclusivamente" el contexto. Si se pregunta por un hospital cerca de "Vic", y el chunk recuperado dice "Barcelona", el LLM se niega a deducir que están cerca porque "Vic" no aparece en el texto. Ante la duda, se escuda en el "Falso Negativo Cero" dando una respuesta genérica.
- **Idea/Solución:** Refinar el System Prompt para permitir el uso de conocimiento del mundo general (como geografía básica o distancias) para conectar conceptos, manteniendo el grounding estricto únicamente para datos clínicos y médicos.

### 2. Ruido en Dense Vector Search (Falta de coincidencia exacta)
- **Criticidad:** 🔴 Alta — puede llevar a recomendar un hospital equivocado, no solo una respuesta pobre
- **Problema:** El modelo de embeddings BGE-M3 (búsqueda semántica pura) asocia la pregunta de "hospitales en Barcelona" a cualquier chunk de la lista de hospitales de España (recuperando Alicante, Gran Canaria, Oviedo) porque semánticamente todos hablan de hospitales con inmunología. La palabra "Barcelona" no tiene fuerza suficiente para hacer de filtro.
- **Idea/Solución:** Implementar **Hybrid Search** (combinando Dense Search para semántica con BM25 para coincidencias exactas por palabra clave), de forma que nombres propios o geográficos fuercen la coincidencia estricta y eliminen el ruido.

**Actualización — 10 jul 2026 (smoke test E-05 T-07, CU-05):** segunda confirmación real
del mismo patrón, con el documento causante identificado. La pregunta "¿A quién llamo
si es fin de semana?" recuperó el teléfono de Urgencias Pediátricas de un hospital
concreto (`data/raw/upiip/guia_antibiotics_esp_0.pdf`, real, no alucinado — verificado
contra el PDF), pero **no** citó `aedip/Hospitales-con-Servicios-de-Inmunologia.html`,
que es el directorio de hospitales con servicio de inmunología — a priori la fuente más
canónica para ese tipo de pregunta. Inspeccionado el HTML: el contenido útil (nombre de
hospital, dirección, teléfono) está diluido entre mucho boilerplate de maquetación
(`dfd-spacer-module`, `data-parallax_sense`, clases CSS largas, atributos de imagen
repetidos) que probablemente degrada la señal semántica del chunk en el embedding,
haciendo que compita en desventaja frente a un PDF con una sección "Datos de contacto"
limpia y bien delimitada. Mismo diagnóstico de fondo (falta de coincidencia exacta/ruido),
pero aquí el ruido está en el propio documento fuente, no solo en la pregunta.
Idea adicional de Marcos, más ligera que Hybrid Search completo: mantener por documento
una lista de keywords manual que aporte peso extra a la hora de puntuar/priorizar ese
documento para ciertas consultas — un balanceo manual en vez de BM25 automático. Es
desarrollo custom (curación manual de keywords por fuente), pero podría ser un parche
más barato de implementar antes de abordar Hybrid Search completo. Revisar ambas
opciones juntas en E-07/E-09; para el directorio de hospitales en concreto, limpiar el
HTML antes de indexar (quitar boilerplate de maquetación) sería una mejora previa barata
independiente de cuál de las dos estrategias se elija.

### 3. Registro lingüístico no siempre accesible (8 jul 2026)
- **Criticidad:** 🟡 Media — problema de comprensión, no de información incorrecta
- **Problema:** detectado al hacer QA manual de E-05 T-04 — algunas respuestas generadas (ej. sobre el proceso de trasplante de médula) usan vocabulario clínico ("acondicionamiento", "recuperación del sistema inmunitario") que puede no ser comprensible para cualquier familiar sin formación médica, pese a que `[TONO — PERFIL FAMILIAR]` en `prompts/system_prompt_family.txt` ya pide "lenguaje accesible... sin tecnicismos innecesarios".
- **Idea/Solución:** revisar en E-07/E-09 si el registro lingüístico real generado por el LLM es consistente con la instrucción de tono del system prompt — posible ítem adicional a evaluar junto a Faithfulness/Answer Relevancy (métrica de legibilidad, o revisión cualitativa dirigida como parte del ciclo de mejora).

### 4. `langdetect` falla en frases cortas de síntomas en español, más allá de lo ya documentado en D-017 (9 jul 2026)
- **Criticidad:** 🔴 Alta — falla justo cuando un familiar describe un síntoma preocupante, no en un caso genérico
- **Problema:** detectado en QA manual de Marcos sobre el chat real (E-05 T-06 en curso) — el mensaje
  `"mi hermano con IDP ha hecho heces con sangre"` se detectó como inglés y la respuesta llegó en
  inglés. Investigado en Cowork con `langdetect` fuera del venv del proyecto (mismo `DetectorFactory.seed = 0`
  que usa `rag/language.py`):
  - Las 37 frases de `config/alarm_triggers.json` (D-019), tal como están redactadas, detectan
    bien como español — 0 fallos.
  - Sobre una muestra de 25 frases realistas (preguntas de starter, frases en primera persona
    tipo familiar describiendo un síntoma, catalán, coloquialismos), 2 fallos (8%):
    `"mi hermano con IDP ha hecho heces con sangre"` → inglés, y `"ha perdido mucho peso sin
    motivo"` → portugués. El acrónimo "IDP" no es la causa (`"mi hermano con gripe ha hecho
    heces con sangre"`, sin IDP, también falla igual); el patrón real parece ser frases
    declarativas cortas tipo "ha hecho/ha perdido X" en español, con confianza reportada por
    `langdetect` por encima de 0.999 pese a estar equivocado — mismo tipo de "confianza falsa"
    que D-017 ya documentó para texto muy corto (`"hola"`→galés), pero aquí en frases de 30-45
    caracteres, bastante por encima del umbral `MIN_LENGTH_FOR_DETECTION=10` que D-017 fijó como
    mitigación. El umbral de longitud no protege de este caso.
  - Justo el peor momento para que falle: son frases de un familiar describiendo un síntoma
    preocupante, no una pregunta genérica.
- **Idea/Solución:** dos vías, no excluyentes:
  1. Lista de exclusión de acrónimos propios del dominio (IDP, IPOPI, ESID, PIDCAP, AIIP) que se
     eliminan del texto antes de pasarlo a `detect()` — barata, pero no habría arreglado el caso
     de "ha perdido mucho peso sin motivo" (sin ningún acrónimo).
  2. Evaluar sustituir `langdetect` por una librería con mejor track record en texto corto
     (`fasttext` con el modelo `lid.176`, o `lingua-py`) — ataca la causa, no el síntoma, pero es
     un cambio más grande (nueva dependencia, posible descarga de modelo).
  Revisar dentro de E-07/E-09 (evaluación) o como fix puntual antes si se considera prioritario
  dado que toca directamente la calidad de respuesta ante síntomas.
- **Cuándo revisarlo:** al abordar E-07, junto con los hallazgos 1-3 de esta misma sección — o
  antes, si se decide que es bloqueante para el hito del 10 de julio.

**Actualización — 10 jul 2026 (smoke test E-05 T-07):** tercer caso real, esta vez con un número
en la frase: `"Mi hijo tiene 38.5°C, ¿es urgente?"` (CU-01) se detectó como neerlandés y la
respuesta completa se generó en ese idioma. Hipótesis de Marcos: el número/símbolo `"38.5°C"`
diluye la señal lingüística del resto de la frase — coherente con el patrón de "confianza falsa"
ya descrito arriba, ahora también con dígitos en el texto, no solo con frases declarativas
puramente textuales. El contenido de seguridad de la respuesta fue correcto (antipirético, aviso
de urgencias, 112) — el fallo es solo de idioma, Falso Negativo Cero no se vio comprometido.
Evaluado como no bloqueante para el hito del 10 de julio (decisión de Marcos): se documenta aquí
y se revisa junto al resto en E-07/E-09, no se aborda como fix puntual ahora. Detalle completo en
`tests/results/e05_t07_smoke_test_results.md`.
