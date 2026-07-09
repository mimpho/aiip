# backlog/epics.md — Épicas del proyecto AIIP

> Backlog estructurado por épicas y fases.  
> Metodología: BDD + Gherkin + TDD — ver D-006 en `decisions.md`.  
> Cada épica se descompone en tareas con especificación Gherkin una vez el TDD esté cerrado.

---

## Fase 0 — Planificación y documentación técnica
*Hito: 12 de junio de 2026*

### E-00 — Documentación técnica del TFM
Generación y cierre de toda la documentación técnica base del repositorio.

**Entregables**
- Estructura base del repo: README, AGENTS, CITATION, decisions, backlog
- `docs/tech-spec.md` — stack, arquitectura, diagramas Mermaid
- `docs/PRD.md` — espejo del PRD v1.9 con stack cerrado
- `docs/security.md` — Falso Negativo Cero, OWASP, RGPD
- `docs/evaluation.md` — RAGAS, métricas, checklist CHART
- `prompts.md` — log histórico inicial

**Estado:** ✅ Completada — 11 jun 2026

---

## Fase 1 — MVP core
*Hito: 10 de julio de 2026 — código funcional*

Perfil familias. Pipeline RAG completo. Seguridad. Autenticación básica.

> **Nota sobre numeración:** los IDs son correlativos al orden de ejecución, no al orden arquitectónico del sistema.

| ID | Épica | Bloqueada por |
|---|---|---|
| E-01 | Setup del entorno de desarrollo | — |
| E-02 | Identidad visual mínima | E-01 |
| E-03 | Autenticación y separación de perfiles | E-02 |
| E-04 | Pipeline RAG + módulo de seguridad | E-01 |
| E-05 | Interfaz conversacional (Chainlit) | E-02, E-04 |
| E-06 | Ingesta y procesamiento de la KB | E-01 |
| E-07 | Evaluación RAGAS parcial | E-06 |
| E-08 | Memoria de perfil e histórico | E-03, E-04, E-06 |

---

### E-01 — Setup del entorno de desarrollo
Configuración de todos los servicios, credenciales y estructura de carpetas necesarios para arrancar el desarrollo.

**Criterios de aceptación de alto nivel**
- Proyecto creado en Supabase (región EU — Frankfurt)
- API key de Google AI (Gemini Flash) obtenida y verificada
- Token de Hugging Face para descarga de bge-m3
- Estructura de carpetas en Google Drive para notebooks Colab
- `.env.example` creado en el repo con todas las variables necesarias
- `.gitignore` actualizado para excluir `.env`

**Estado:** ✅ Completada — 25 jun 2026

---

### E-02 — Identidad visual mínima
Definición de design tokens base (colores, tipografía, espaciado) y aplicación en auth pages y theming de Chainlit. Ver D-013.

**Criterios de aceptación de alto nivel**
- `public/tokens.css` con CSS custom properties como única fuente de verdad
- Logo definido (placeholder o definitivo)
- Paleta de colores y tipografía documentadas
- Theming de Chainlit consume los tokens via `public/style.css`
- Auth pages de Supabase consumen los tokens via `auth/style.css`

**Proceso**
- Usar Claude Design o v0 con el brief en `docs/design-brief.md` como contexto
- La propuesta exploratoria de Lovable está incluida en el brief como referencia, no como constraint
- Revisar y aprobar antes de traducir a tokens

**Estado:** ✅ Completada — 27 jun 2026

**Entregables**
- `design/public/tokens.css` — fuente de verdad con dark/light mode y swap de accent por perfil
- `design/public/style.css` — Chainlit theme con glassmorphism y borde gradiente animado en input
- `design/auth/style.css` — Supabase Auth UI theme con selectores reales y swap de perfil
- `docs/logo-aiip.svg` — logomark Recraft (célula protegida), `currentColor` listo para producción
- `docs/design/` — screens de referencia (identity, auth, chat) con logo actualizado

---

### E-03 — Autenticación básica y separación de perfiles
Registro, login y URLs separadas por perfil (familiar / profesional). Auth pages usan Supabase Auth UI con la identidad visual de E-02. Look & feel completo de la interfaz conversacional se aborda en E-05.

**Criterios de aceptación de alto nivel**
- Registro con rol definido: familiar o profesional
- Autenticación via Supabase Auth (OAuth Google + email/password)
- URLs separadas: el familiar no ve que existe la versión profesional
- El rol determina la KB consultada y el tono del agente

**Estado:** ✅ Completada — 30 jun 2026

### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | OAuth Google — configuración en Supabase y Google Cloud | ✅ Completada |
| T-02 | Esquema Supabase: tabla `profiles` + RLS | ✅ Completada |
| T-03 | Registro y login con email/password, rol fijo por app | ✅ Completada |
| T-04 | Login con Google OAuth, rol fijo por app | ✅ Completada |
| T-05 | Integración de autenticación en Chainlit | ✅ Completada |
| T-06 | Separación de URLs por perfil (familiar real + profesional stub) | ✅ Completada |

**Entregables**
- `auth/supabase_client.py` — signup, login, Google OAuth y get_or_create_profile
- `main_familiar.py` — entrypoint Chainlit perfil familiar con auth callback
- `main_profesional.py` — entrypoint stub profesional (auth bloqueada, sin RAG)
- `.chainlit/config.toml` — config Chainlit app familiar
- `.chainlit_profesional/config.toml` — config Chainlit app profesional
- `design/profesional/stub.js` — banner "En construcción" + deshabilitado de formulario
- `design/profesional/style.css` — accent profesional (#2FC18C) extendiendo tokens E-02
- `supabase/migrations/20260628021829_create_profiles.sql` — tabla profiles + RLS
- `scripts/verify_oauth_google.py` — script de verificación manual T-01
- `tests/features/e03_t01_*.feature` a `e03_t06_*.feature` — escenarios Gherkin por tarea
- `tests/step_defs/test_e03_t02.py` a `test_e03_t06.py` — step definitions pytest-bdd
- `tasks/E03-T02-plan.md` a `E03-T06-plan.md` — planes de implementación
- `decisions.md` — D-014 (Supabase único broker OAuth), D-015 (criterios TDD por épica)

---

### E-04 — Pipeline RAG + módulo de seguridad
Flujo completo: query → detección de idioma → embedding → retrieval → generación → respuesta en idioma del usuario. Incluye el módulo de seguridad (Falso Negativo Cero), ya que son inseparables en el pipeline.

**Criterios de aceptación de alto nivel**
- Pipeline end-to-end funcional con LangChain v1.0
- Gemini Flash como LLM (configurable via `.env`)
- bge-m3 para embeddings — cross-lingual retrieval funcionando en español
- Detección automática de idioma via `langdetect`
- Respuesta generada en el idioma del usuario
- El agente nunca confirma que una situación es segura (Falso Negativo Cero)
- Ante síntomas de alarma, deriva siempre a consulta médica
- Parámetros de inferencia implementados y testeados
- OWASP Top 10 para LLMs cubierto con mitigaciones

**Estado:** ✅ Completada — 05 jul 2026

### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | Setup de dependencias y estructura del módulo RAG | ✅ Completada |
| T-02 | Embeddings y retriever con ChromaDB | ✅ Completada |
| T-03 | Detección de idioma e integración en pipeline | ✅ Completada |
| T-04 | Generador: LLM Gemini Flash via LangChain | ✅ Completada |
| T-05 | Módulo de seguridad: Falso Negativo Cero | ✅ Completada |
| T-06 | Pipeline end-to-end y tests de integración | ✅ Completada |

**Entregables**
- `rag/config.py` — variables de entorno del pipeline (`RAG_TOP_K`, `LLM_MODEL/TEMPERATURE/TOP_P/MAX_TOKENS`, `CHROMA_PATH`)
- `rag/embeddings.py` — carga de embeddings BAAI/bge-m3
- `rag/retriever.py` — retriever ChromaDB (métrica coseno, Top-K configurable)
- `rag/language.py` — detección de idioma (`langdetect`, determinista, fallback para texto corto)
- `rag/generator.py` — generador LLM Gemini Flash via LangChain
- `rag/safety.py` — módulo de seguridad: triggers de alarma + filtro post-generación (Falso Negativo Cero)
- `rag/pipeline.py` — `RAGPipeline`, orquesta el flujo end-to-end
- `config/alarm_triggers.json` — triggers de alarma (placeholder pendiente de validación clínica)
- `prompts/system_prompt_familiar.txt` — system prompt del perfil familiar
- `.env.example` — variables nuevas del pipeline RAG documentadas
- `tests/features/e04_t01_*.feature` a `e04_t06_*.feature` — escenarios Gherkin por tarea
- `tests/step_defs/test_e04_t01.py` a `test_e04_t06.py` — step definitions pytest-bdd
- `tasks/E04-T01-plan.md` a `E04-T06-plan.md` — planes de implementación
- `decisions.md` — D-016 (retriever ChromaDB), D-017 (detección de idioma), D-018 (generador LLM), D-019 (módulo de seguridad), D-020 (pipeline end-to-end)

---

### E-05 — Interfaz conversacional (Chainlit) — perfil familias
Interfaz de usuario para el perfil familias con visualización del pipeline RAG.

**Criterios de aceptación de alto nivel**
- Chat funcional con streaming nativo de tokens
- Visualización de pasos intermedios del RAG (documentos recuperados, chunks usados)
- Diseño responsive desde el inicio (D-007)
- Tono y UX adaptados al perfil familiar según PRD
- Theming completo basado en tokens de E-02

**Nota metodológica:** D-015 clasificó E-05 como "sin TDD" a nivel de épica. Tras la descomposición en tareas (8 jul 2026), D-030 refina ese criterio a nivel de tarea: T-01/T-02/T-03 (lógica de integración del pipeline, streaming, exposición de pasos intermedios) sí aplican TDD; T-04/T-05/T-07 (onboarding estático, theming/CSS, smoke test) siguen sin TDD, con validación manual (revisión visual + prueba funcional en browser). T-06 (UI de auth) es TDD parcial: la lógica de wiring es testeable, el redirect completo de Google OAuth se verifica manualmente (mismo patrón que E-03 T-04).

**Nota de alcance (8 jul 2026):** al revisar la épica se detectó que E-03 dejó sin construir la UI de signup y de login con Google dentro de la app (solo las funciones de backend, testeadas de forma aislada) y que `design/auth/style.css` (E-02) nunca llegó a cargarse — Chainlit solo admite un `custom_css` por app. D-031 reconcilia esto: toda la autenticación vive dentro de Chainlit, sin superficie separada. D-032 fija el mecanismo concreto de login con Google: `@cl.oauth_callback` nativo de Chainlit + sincronización server-side con Supabase (reabre D-014), no el `sign_in_with_oauth()` client-side que D-031 planteaba inicialmente. Se añade T-06 para resolverlo; el antiguo T-06 (smoke test) pasa a T-07 y amplía su alcance a signup y login Google.

**Nota de alcance (9 jul 2026):** al arrancar T-05 (task-start) se detectó, inspeccionando el CSS compilado real de Chainlit 2.11.1 y `chainlit/server.py`, que `design/public/style.css` (entregable de E-02) define variables `--cl-color-*` y clases `.cl-*` que no existen en el DOM/CSS real de Chainlit (que usa el esquema shadcn/Tailwind: `--primary`, `--background`, `--foreground`, `--accent`, `--border`, `--sidebar-*`, `--radius`, `--font-sans`/`--font-mono`) ni se usa el mecanismo oficial de theming (`public/theme.json`, inyectado por Chainlit como `window.theme`). Con alta probabilidad el theming de E-02 nunca se aplicó al chat real — nunca se verificó visualmente contra un servidor Chainlit corriendo, solo contra comps de v0/Claude Design. D-038 documenta el hallazgo y amplía el alcance de T-05: no es solo "repasar y hacer responsive" sino crear `design/public/theme.json` + corregir selectores de `style.css` a clases reales (verificación de clases exactas se hace en Antigravity con devtools durante la implementación, dado que Cowork no tiene navegador conectado al Chainlit local).

**Nota de alcance (9 jul 2026):** al formalizar T-06 (task-start) se detectó que Chainlit no soporta signup ni recuperación de contraseña de forma nativa (solo login vía `password_auth_callback`, formulario fijo sin mensajes custom). D-040 amplía el alcance original de T-06 (que solo cubría signup + login Google + `auth/style.css`) para incluir también la recuperación de contraseña completa: rutas propias sobre la misma app de Chainlit (`/auth/forgot-password`, `/auth/confirm` compartida con la confirmación de signup), plantillas de email de Supabase reescritas, y un `custom_js` mínimo para la descubribilidad del enlace.

**Estado:** 🔵 En curso

### Tareas

| ID | Tarea | TDD | Estado |
|---|---|---|---|
| T-01 | Integración del pipeline RAG en el chat | Sí | ✅ Completada |
| T-02 | Streaming nativo de tokens | Sí | ✅ Completada |
| T-03 | Visualización de pasos intermedios del RAG | Sí | ✅ Completada |
| T-04 | Onboarding y disclaimers de seguridad | No | ✅ Completada |
| T-05 | Theming completo (tokens E-02) + responsive del chat | No | ✅ Completada |
| T-06 | UI de autenticación en Chainlit: signup + login Google + fusión de auth/style.css | Parcial | 🔄 En progreso |
| T-07 | Smoke test manual E2E — chat + signup + login Google (configuración, sin TDD) | No | ⚪ Pendiente |

---

### E-06 — Ingesta y procesamiento de la Knowledge Base
Carga, limpieza, chunking e indexación de las fuentes de IDP en ChromaDB.

**Criterios de aceptación de alto nivel**
- Fuentes procesadas: IPOPI, IDF, upiip.com, guías clínicas validadas — cada fuente indexada en su idioma original (amplía D-011: bge-m3 resuelve cross-lingual retrieval en cualquier dirección, no solo EN→consulta)
- Estrategia de chunking definida y documentada
- Colección `familiar` separada en ChromaDB (continuidad de métrica coseno de D-016)

**Notas**
- Datasheet DAIMS (arXiv 2501.14094) de la KB formalizado como T-06 (documentación, sin TDD). Ver `backlog/ideas.md`.
- "Business rules como chunk indexado en la KB" descartado para esta épica — redundante con D-019 (detección de alarma determinista por JSON+substring, no por retrieval). Ver `backlog/ideas.md`.
- Ficheros crudos (PDFs/guías de terceros) fuera del repo por copyright — viven en Drive/local (`data/raw/`, gitignored), indexados en `docs/kb-sources.md`. Trazabilidad vía `data/raw/manifest.json` (checksum, URL, fecha), este sí versionado.
- Fuentes ya reunidas en Google Drive (`AIIP/data/raw/`): UPIIP, IPOPI, IDF, AFPA/HAS — no es una lista cerrada, se puede ampliar/ajustar durante y después de esta épica.
- La revisión de Jacques Rivière sobre estas fuentes es consultiva (¿es suficiente esta base para el perfil familias, cambiaría o ampliaría algo?), no bloqueante para arrancar la épica — construir el pipeline de ingesta no requiere validación clínica previa. Lo único que sí requiere su validación antes de darse por bueno es `config/alarm_triggers.json` (D-019), por estar enchufado a la capa de seguridad de Falso Negativo Cero.
- Ronda 1 y 2 de feedback de Jacques sobre `alarm_triggers.json` ya aplicadas en la rama `docs/D019-alarm-triggers-jacques` (creada desde esta épica, sin integrar hasta que confirme la lista definitiva) — no bloquea el trabajo de esta épica. Ver actualización de D-019 en `decisions.md`.
- T-07 nace de un hueco detectado tras T-04: ni los tests de E-04 (mocks/fixtures pequeños) ni el `.feature` de T-05 (fuentes de fixture en carpeta) validan el pipeline RAG con el contenido real de la KB. T-07 corre un script contra `RAGPipeline` real con preguntas representativas del perfil familias y deja el resultado para revisión manual — antes de arrancar E-05 (diseño/interfaz), para no construir la UI sobre un backend sin verificar con datos reales. Es deliberadamente más ligero que la evaluación RAGAS de E-07 (sin métricas, solo lectura humana de pregunta/respuesta/chunks recuperados). Durante T-07 surgieron tres hallazgos que se documentaron como D-025, D-026 y D-027 en `decisions.md` (thinking de gemini-2.5-flash truncando respuestas, citación inline verbosa, y cambio de modelo a gemini-2.5-flash-lite por límite de cuota).
- T-08 nace de una propuesta de Marcos al revisar los resultados de T-07: la sección "Fuentes consultadas" (D-026) cita el fichero interno (ej. `idf/manual-....pdf`), no la URL pública original. `data/raw/manifest.json` (D-021) ya tiene un campo `url` por documento, hoy en `null` para los 29 documentos actuales — la infraestructura ya está pensada para esto, falta rellenar las URLs reales (Marcos, manualmente, documento por documento — no inventar enlaces) y propagarlas: manifest → metadata del chunk (toca `ingestion/chunker.py`, T-03 ya cerrado) → render como enlace markdown en `_build_sources_section` de `rag/pipeline.py` (fallback a nombre de fichero si no hay URL). Especificidad del enlace: preferir el enlace directo al documento sobre el dominio genérico cuando se tenga con confianza (el coste de un 404 es bajo — no es un fallo de Falso Negativo Cero, y el documento sigue trazable localmente vía checksum) — cadena de fallback en tres niveles: enlace directo → página de la fuente en `docs/kb-sources.md` → solo nombre de fichero. Verificación de que la URL sigue viva: en tiempo de ingesta o script de mantenimiento aparte (nunca en el path de latencia del chat, mismo principio que D-022 para el chunking) — guardar el resultado cacheado en el manifest (ej. `url_status`/`url_checked_at` junto a `url`), la citación en el chat solo lee ese estado cacheado, sin red por pregunta. Pendiente de que Marcos rellene el manifest antes de formalizar la tarea con `task-start`.

**Estado:** ✅ Completada — 08 jul 2026

### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | Setup de dependencias y estructura del módulo de ingesta | ✅ Completada |
| T-02 | Loader de documentos fuente | ✅ Completada |
| T-03 | Estrategia de chunking multiidioma | ✅ Completada |
| T-04 | Indexer: indexación en ChromaDB (colección `family`) | ✅ Completada |
| T-05 | Pipeline de ingesta end-to-end | ✅ Completada |
| T-06 | Datasheet DAIMS de la KB (documentación, sin TDD) | ✅ Completada |
| T-07 | Smoke test manual del pipeline RAG con datos reales de la KB (configuración, sin TDD) | ✅ Completada |
| T-08 | Enlazar fuentes citadas a su URL original (manifest → metadata de chunk → citación) | ✅ Completada |

**Entregables**
- `ingestion/loader.py`, `ingestion/chunker.py`, `ingestion/indexer.py`, `ingestion/pipeline.py`, `ingestion/manifest.py`, `ingestion/config.py` — módulo de ingesta completo (loader → chunking multiidioma con tokenizer real de bge-m3 → indexación ChromaDB con IDs deterministas → orquestación end-to-end con borrado-antes-de-reinsertar)
- `data/raw/manifest.json` — trazabilidad de fuentes crudas (checksum, URL, fecha), 37 documentos, único fichero versionado de `data/raw/`
- `docs/kb-datasheet.md` — datasheet DAIMS de la KB (T-06)
- `docs/kb-maintenance.md` + `skills/kb-maintenance/SKILL.md` — runbook y skill de mantenimiento de fuentes de la KB
- `scripts/smoke_test_rag.py` + `tests/results/e06_t07_smoke_test_results.md` — smoke test manual del pipeline RAG con datos reales de la KB indexada (T-07)
- `rag/pipeline.py`, `rag/generator.py` — citación de fuentes con enlace a URL original, fallback a nombre de fichero (T-08)
- `prompts/system_prompt_family.txt` — system prompt del perfil familiar (renombrado de `system_prompt_familiar.txt`, lenguaje inclusivo paciente/cuidador)
- `supabase/migrations/20260706214852_rename_profile_roles_to_english.sql` — roles de perfil `familiar/profesional` → `family/professional`
- `tests/features/e06_t01_*.feature` a `e06_t08_*.feature` — escenarios Gherkin por tarea
- `tests/step_defs/test_e06_t01.py` a `test_e06_t08.py` — step definitions pytest-bdd
- `tasks/E06-T01-plan.md` a `E06-T08-plan.md` — planes de implementación
- `decisions.md` — D-021 a D-029 (manifest, chunking, indexer, pipeline de ingesta, thinking de Gemini, citación de fuentes, cambio de modelo, runbook de KB, citación con URL original)

---

### E-07 — Evaluación RAGAS (parcial)
Dataset de prueba y métricas básicas funcionando, ejecutada inmediatamente después del hito del 10 de julio.

**Criterios de aceptación de alto nivel**
- Dataset de preguntas representativas del perfil familias definido
- Faithfulness y Answer Relevancy implementadas y funcionando contra el pipeline real (Context Precision y Context Recall quedan para E-09, Fase 1.5 — ver `docs/evaluation.md` sección 3)
- Safety Compliance: primer resultado (baseline, sin ciclo de mejora todavía)
- Primeros resultados documentados

**Notas**
- **Corrección (7 jul 2026):** el criterio original decía "las cuatro métricas RAGAS implementadas" — no coincidía con el plan de fases de `docs/evaluation.md` (sección 3), que solo asigna Faithfulness + Answer Relevancy a la Fase 1 parcial. Se alinea este criterio con `evaluation.md`, que es el documento con el desglose técnico detallado.
- **Reprioridad (7 jul 2026):** E-05 (interfaz Chainlit) pasa por delante de E-07 en la ejecución. El hito del 10 de julio se llama "código funcional" (ver `README.md`) — lo entrega E-05, no E-07. El ciclo de mejora basado en RAGAS (la parte que realmente aporta valor de iteración) ya estaba asignado a Fase 1.5 (29 jul) en `evaluation.md`, así que ejecutar E-07 parcial unos días después del 10 de julio no compromete el hito. Única dependencia real a vigilar: E-09 (RAGAS completa, necesaria para la entrega final del 29 jul) está bloqueada por E-07 — no debe retrasarse mucho más allá del 10 de julio para no comprimir el margen antes del 29.
- Hito de cierre de Fase 1 (10 jul, vía E-05). Al cerrar E-07: ejecutar `pytest tests/ -v` sobre el sistema completo acumulado hasta este punto — primera validación de integración real del pipeline.

**Estado:** ⚪ No iniciada

---

### E-08 — Memoria de perfil e histórico de conversaciones
Onboarding, datos estables del paciente y persistencia de conversaciones entre sesiones.

**Nota de alcance (9 jul 2026):** D-040 (E-05 T-06) guarda el nombre del
usuario en `user_metadata.full_name` de Supabase Auth como solución
provisional — el formulario de signup de Chainlit no admite un campo de
nombre, así que se pide por chat en el primer `on_chat_start`. Es un lugar
provisional, no el "registro más decente" que le corresponde: cuando esta
épica diseñe el esquema de onboarding/perfil, migrar `full_name` (y
cualquier otro dato ya capturado en `user_metadata`) a esa estructura
propia, no dejarlo repartido entre Auth y `profiles`.

**Nota de alcance (8 jul 2026):** al hacer QA manual de E-05 T-04 se confirmó
que `rag/pipeline.py` (`retrieve()`/`aquery_stream()`) no recibe ningún
historial — cada turno del chat se procesa de forma aislada, incluso dentro
de una misma sesión abierta (el chat "olvida" lo dicho dos mensajes antes,
aunque siga visible en pantalla). Marcos señaló que esto son en realidad
**tres capas distintas**, y el criterio original las mezclaba en una sola:
1. **Memoria conversacional de corto plazo (intra-sesión):** pasar el
   historial reciente del chat abierto al LLM para que pueda seguir la
   conversación de forma natural (ej. resolver referencias como "¿recuerdas
   a quién quiero visitar?"). No implica persistencia en BBDD — puede vivir
   en memoria de la sesión de Chainlit (`cl.user_session`).
2. **Memoria de perfil:** datos estables del paciente (tipo de IDP, edad,
   contexto) capturados en onboarding y usados para contextualizar
   respuestas — precisa de persistencia porque debe sobrevivir a cerrar el
   chat.
3. **Persistencia entre sesiones:** histórico de conversaciones guardado por
   usuario en Supabase — implica autenticación (ya resuelta en E-03) +
   escritura en BBDD, y es lo único de las tres que requiere ambas cosas.

Al descomponer esta épica en tareas, evaluar si (1) debe resolverse antes o
de forma independiente de (2)/(3) — la memoria de corto plazo mejora la
experiencia de chat ya con la arquitectura actual, sin depender de diseño de
esquema en Supabase ni de UI de borrado de datos.

**Criterios de aceptación de alto nivel**
- Memoria conversacional de corto plazo: el agente mantiene el hilo de la
  conversación dentro de una misma sesión de chat abierta (sin necesidad de
  persistencia en BBDD)
- Onboarding captura datos del paciente: tipo de IDP, edad, contexto relevante
- El agente usa la memoria de perfil para contextualizar respuestas
- Histórico de conversaciones persistente por usuario en Supabase
- El usuario puede borrar sus datos (derecho al olvido — D-009)

**Estado:** ⚪ No iniciada

---

## Fase 1.5 — MVP completo
*Hito: 29 de julio de 2026 — entrega final*

Completa el MVP con evaluación cerrada y pulido final.

### E-09 — Evaluación RAGAS completa
Cierre del plan de evaluación con al menos un ciclo de mejora.

**Criterios de aceptación de alto nivel**
- Resultados RAGAS completos documentados en `docs/evaluation.md`
- Al menos un ciclo de mejora basado en los resultados
- Checklist CHART completado como anexo

**Estado:** ⚪ No iniciada

---

### E-10 — Pulido: responsive, CORS y UX
Ajustes finales para la entrega.

**Criterios de aceptación de alto nivel**
- Interfaz validada en móvil y escritorio
- CORS configurado para futura integración web (D-007)
- Revisión de UX con criterios del PRD

**Notas**
- Al cerrar esta épica: ejecutar tests RAGAS end-to-end (E-07/E-09) sobre el sistema completo antes del PR final. Es el único momento en que se valida el pipeline integrado en su totalidad.

**Estado:** ⚪ No iniciada

---

## Backlog de features opcionales
*Entre entrega parcial y final, o post-TFM según tiempo disponible*

### F-01 — Perfil profesional
KB científica (PubMed, ESID literatura), tono clínico, interfaz adaptada.

**Nota:** KB distinta a la del perfil familiar, aunque comparten base común sobre IDP. El LLM para este perfil puede evolucionar a uno más potente en producción (ver D-004). Colección separada en ChromaDB.

**Esfuerzo estimado:** alto — KB nueva, tono diferente, posiblemente UI distinta.

---

### F-02 — Input multimodal para imágenes de síntomas
El agente acepta imágenes de síntomas y las describe sin diagnosticar.

**Nota:** Gemini Flash es nativo multimodal y Chainlit soporta upload de imágenes de fábrica — el stack ya lo facilita. El esfuerzo real está en el prompt engineering y en mantener el límite clínico. Excluye explícitamente interpretación de resultados médicos (analíticas, informes).

**Esfuerzo estimado:** medio — más feature grande que fase nueva gracias al stack.

---

### F-03 — Selector explícito de idioma en interfaz
Dropdown en Chainlit para selección manual de idioma, complementando la detección automática.

**Esfuerzo estimado:** bajo.

---

### F-04 — Integración web: responsive avanzado y CORS
Preparación para embeber el AIIP como widget o iframe en la web de la fundación (upiip.com).

**Esfuerzo estimado:** bajo-medio.

---

*Última actualización: junio 2026*
