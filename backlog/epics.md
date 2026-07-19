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

**Estado:** ✅ Completada — 10 jul 2026 (hito "código funcional" cerrado por E-05; E-07 y E-08 se mueven a Fase 1.5, ver notas de cada una — ninguna era requisito de este hito)

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
- Visualización de pasos intermedios del RAG (documentos recuperados, chunks usados) — retirada de la UI en T-07 (D-041): redundante con el listado de fuentes ya existente (D-026), se resuelve vía logging server-side + reutilización de resultados sin segunda consulta, no vía `cl.Step` visible
- Diseño responsive desde el inicio (D-007)
- Tono y UX adaptados al perfil familiar según PRD
- Theming completo basado en tokens de E-02

**Nota metodológica:** D-015 clasificó E-05 como "sin TDD" a nivel de épica. Tras la descomposición en tareas (8 jul 2026), D-030 refina ese criterio a nivel de tarea: T-01/T-02/T-03 (lógica de integración del pipeline, streaming, exposición de pasos intermedios) sí aplican TDD; T-04/T-05/T-07 (onboarding estático, theming/CSS, smoke test) siguen sin TDD, con validación manual (revisión visual + prueba funcional en browser). T-06 (UI de auth) es TDD parcial: la lógica de wiring es testeable, el redirect completo de Google OAuth se verifica manualmente (mismo patrón que E-03 T-04).

**Nota de alcance (8 jul 2026):** al revisar la épica se detectó que E-03 dejó sin construir la UI de signup y de login con Google dentro de la app (solo las funciones de backend, testeadas de forma aislada) y que `design/auth/style.css` (E-02) nunca llegó a cargarse — Chainlit solo admite un `custom_css` por app. D-031 reconcilia esto: toda la autenticación vive dentro de Chainlit, sin superficie separada. D-032 fija el mecanismo concreto de login con Google: `@cl.oauth_callback` nativo de Chainlit + sincronización server-side con Supabase (reabre D-014), no el `sign_in_with_oauth()` client-side que D-031 planteaba inicialmente. Se añade T-06 para resolverlo; el antiguo T-06 (smoke test) pasa a T-07 y amplía su alcance a signup y login Google.

**Nota de alcance (9 jul 2026):** al arrancar T-05 (task-start) se detectó, inspeccionando el CSS compilado real de Chainlit 2.11.1 y `chainlit/server.py`, que `design/public/style.css` (entregable de E-02) define variables `--cl-color-*` y clases `.cl-*` que no existen en el DOM/CSS real de Chainlit (que usa el esquema shadcn/Tailwind: `--primary`, `--background`, `--foreground`, `--accent`, `--border`, `--sidebar-*`, `--radius`, `--font-sans`/`--font-mono`) ni se usa el mecanismo oficial de theming (`public/theme.json`, inyectado por Chainlit como `window.theme`). Con alta probabilidad el theming de E-02 nunca se aplicó al chat real — nunca se verificó visualmente contra un servidor Chainlit corriendo, solo contra comps de v0/Claude Design. D-038 documenta el hallazgo y amplía el alcance de T-05: no es solo "repasar y hacer responsive" sino crear `design/public/theme.json` + corregir selectores de `style.css` a clases reales (verificación de clases exactas se hace en Antigravity con devtools durante la implementación, dado que Cowork no tiene navegador conectado al Chainlit local).

**Nota de alcance (9 jul 2026):** al formalizar T-06 (task-start) se detectó que Chainlit no soporta signup ni recuperación de contraseña de forma nativa (solo login vía `password_auth_callback`, formulario fijo sin mensajes custom). D-040 amplía el alcance original de T-06 (que solo cubría signup + login Google + `auth/style.css`) para incluir también la recuperación de contraseña completa: rutas propias sobre la misma app de Chainlit (`/auth/forgot-password`, `/auth/confirm` compartida con la confirmación de signup), plantillas de email de Supabase reescritas, y un `custom_js` mínimo para la descubribilidad del enlace.

**Nota de cierre (10 jul 2026):** `pytest tests/ -v` al cerrar la épica reveló una regresión real sobre código de E-03: `signup()` (`auth/supabase_client.py`) no detectaba emails ya registrados y confirmados desde que D-040 activó "Confirm email" — Supabase, por protección anti-enumeración, deja de elevar error en ese caso y devuelve un usuario ofuscado, lo que producía un 500 en vez de un mensaje claro. D-042 documenta el hallazgo y el fix. De paso, las precondiciones de `test_e03_t03.py` que hacían `signup()` público innecesariamente se cambiaron a Admin API, eliminando también un rate limit de Supabase que enmascaraba el bug.

**Estado:** ✅ Completada — 10 jul 2026

### Tareas

| ID | Tarea | TDD | Estado |
|---|---|---|---|
| T-01 | Integración del pipeline RAG en el chat | Sí | ✅ Completada |
| T-02 | Streaming nativo de tokens | Sí | ✅ Completada |
| T-03 | Visualización de pasos intermedios del RAG | Sí | ✅ Completada |
| T-04 | Onboarding y disclaimers de seguridad | No | ✅ Completada |
| T-05 | Theming completo (tokens E-02) + responsive del chat | No | ✅ Completada |
| T-06 | UI de autenticación en Chainlit: signup + login Google + fusión de auth/style.css | Parcial | ✅ Completada |
| T-07 | Smoke test manual E2E — chat + signup + login Google (configuración, sin TDD) | No | ✅ Completada |

**Entregables**
- `chainlit/main_family.py` — pipeline RAG cableado al chat con streaming nativo (`aquery_stream`), saludo dinámico (`_greeting()`, D-039), onboarding con disclaimers de seguridad, `@cl.oauth_callback` para login Google, `_ensure_full_name()`; sin `cl.Step` de retrieval (retirado en D-041)
- `rag/pipeline.py`, `rag/generator.py` — `RAGPipeline.retrieve()` público + `aquery_stream(question, raw_results=None)` retrocompatible (T-01/T-03)
- `design/public/theme.json`, `design/public/style.css`, `design/public/tokens.css` — theming real de Chainlit sobre selectores shadcn/Tailwind reales, responsive (D-038)
- `chainlit/family/.chainlit/config.toml`, `chainlit/family/public` (symlink a `design/public/`), `.chainlit/translations/` — arranque vía `CHAINLIT_APP_ROOT` + symlinks (D-039)
- `auth/supabase_client.py` — sincronización server-side de usuarios de Google OAuth con Supabase
- `chainlit/family/templates/{auth_base,confirm,forgot_password}.html`, `design/public/auth-pages.css`, `design/public/auth.js` — signup con confirmación por email y recuperación de contraseña sobre rutas propias de Chainlit (D-031/D-032/D-040)
- `prompts/system_prompt_family.txt` — ajustes de tono/onboarding del perfil familiar
- `tests/features/e05_t01_*.feature` a `e05_t07_*.feature`, `tests/step_defs/test_e05_t01.py` a `test_e05_t06.py` — escenarios TDD/parcial por tarea
- `tests/results/e05_t07_smoke_test_results.md` — smoke test manual E2E: chat con KB real, signup + confirmación de email, login Google, recuperación de contraseña, responsive — todo validado sin incidencias; 3 hallazgos no bloqueantes documentados en `backlog/ideas.md` para E-07/E-09
- `tasks/E05-T01-plan.md` a `E05-T06-plan.md` — planes de implementación por tarea
- `auth/supabase_client.py::signup()` — fix de regresión: detecta emails ya registrados y confirmados tras D-040 (D-042)
- `tests/step_defs/test_e03_t03.py` — precondiciones movidas a Admin API, evita rate limit propio del test
- `decisions.md` — D-030 a D-042

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

## Fase 1.5 — MVP completo
*Hito: 29 de julio de 2026 — entrega final*

Completa el MVP con evaluación cerrada y pulido final.

**Movimiento de fase (10 jul 2026):** E-07 y E-08 se trasladan aquí desde
Fase 1. E-07: la reprioridad del 7 jul ya establecía que no era requisito
del hito "código funcional" (lo entrega E-05), y ejecutarla inmediatamente
después del 10 de julio la sitúa cronológica y funcionalmente junto al
resto de evaluación de Fase 1.5. E-08 (memoria de perfil e histórico): es
una ampliación de producto sobre el MVP ya funcional, no un requisito del
hito del 10 de julio — coherente con cómo el Gantt del README ya la
situaba, aunque la estructura de este documento no lo reflejara hasta
ahora.

**Prioridad de ejecución (15 jul 2026):** a 5 días del hito del 10 de julio,
ninguna épica de esta fase se ha arrancado todavía — el Gantt orientativo
del README (E-07 10-13 jul, E-08 10-18 jul en paralelo) ya ha quedado
desfasado. Decisión de Marcos: orden de ejecución **E-07 → E-09 → E-10,
por delante de E-08**. Razones: (1) la dependencia E-09 bloqueada por E-07
ya estaba documentada en la nota de reprioridad del 7 jul — no es una
opción, es la única secuencia posible; (2) sin E-08 el sistema sigue
siendo un agente RAG completo y funcional (demostrado en el smoke test de
E-05); sin E-09 cerrada, en cambio, falta el bloque de evaluación
completo del TFM (4 métricas + ciclo de mejora + checklist CHART) — el
riesgo de dejarla fuera es mayor. E-08 pasa a ejecutarse con el tiempo que
quede antes del 29 de julio, no en paralelo.

Dentro de E-08, si el calendario aprieta, priorizar la capa de memoria
conversacional de corto plazo (intra-sesión, sin tocar Supabase — barata y
ya identificada como hueco visible: el chat "olvida" lo dicho dos mensajes
antes) sobre la persistencia entre sesiones + derecho al olvido (la capa
más cara: esquema en Supabase, UI de borrado). Ver criterios de aceptación
de E-08 más abajo.

**Reordenamiento (18 jul 2026, D-059):** al plantear si E-08 podía arrancar
justo después de E-09, se detectó un riesgo de secuenciación: E-09 cerró
con 4 de 6 métricas por debajo de objetivo (ver resultados de E-09 más
abajo) y varios hallazgos abiertos o fuera de alcance de su ciclo de
mejora (D-056). Activar la capa 1 de E-08 (memoria conversacional de corto
plazo, historial crudo pasado al LLM) sobre un pipeline cuya generación de
una sola respuesta ya falla en la mayoría de métricas añadiría una
variable de contexto no controlada, encareciendo el diagnóstico de
cualquier fallo nuevo — mismo principio que D-056 ya aplicó ("medición
específica → mejora específica", sin mezclar causas). Se crea **E-11**
para cerrar/acotar esos hallazgos antes de tocar la capa 1 de E-08. Orden
de ejecución actualizado: **E-09 → E-11 → E-10 → E-08 (capas 2 y 3: perfil
+ persistencia) → E-08 capa 1 (memoria conversacional)**, esta última
candidata a quedar como seguimiento post-TFM si no hay margen antes del 29
de julio. Detalle completo en D-059.

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
- **Movimiento de fase (10 jul 2026):** trasladada de Fase 1 a Fase 1.5 al cerrar E-05 — ver nota de la fase arriba. El hito de Fase 1 ya quedó cerrado por E-05, sin esperar a esta épica.
- **Arranque (15 jul 2026):** el plan original de `docs/evaluation.md` (Faithfulness + Answer Relevancy vía RAGAS contra `RAGPipeline.query()` real) choca con un punto abierto de cuota de la API de Gemini: D-027 documentaba "1.500 RPD" para `gemini-2.5-flash-lite`, pero D-037 (9 jul) registró agotamiento real a las ~20 peticiones ese día. Investigado de nuevo al arrancar esta épica: la documentación oficial de Google ya no publica una cifra fija por tier — remite al dashboard de AI Studio, específico de cada proyecto.
- **Confirmado (15 jul 2026):** Marcos consultó el dashboard (`aistudio.google.com/rate-limit`, proyecto AIIP, nivel gratuito). D-037 tenía razón, no D-027: el límite real era **20 RPD** tanto para `gemini-2.5-flash` como para `gemini-2.5-flash-lite` en este proyecto — y `flash-lite` ya lo había superado en la ventana de 28 días (25/20).
- **Resuelto (15 jul 2026, D-043):** Marcos activó facturación (Nivel 1, prepago de 10 EUR) — cuota ya no es un bloqueo (RPD sube a 10K en flash y a ilimitado en flash-lite). Aprovechando que había que activar facturación de todas formas, y dado que el coste adicional es irrelevante (céntimos/hora), se decide además subir de `gemini-2.5-flash-lite` a `gemini-2.5-flash` como modelo de producción — mejor grounding reportado (FACTS Grounding), relevante para Falso Negativo Cero. Detalle completo, alternativas descartadas (comparación empírica lado a lado, Claude Haiku 4.5) y justificación en D-043. `rag/config.py`, `rag/generator.py` y `.env.example` ya actualizados. T-02/T-03 se construyen igualmente con ejecución incremental/reanudable (checkpointing) como buena práctica, ya sin la presión de cuota que lo motivó originalmente.

**Estado:** ✅ Completada — 16 jul 2026

### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | Dataset de evaluación parcial (42 casos: 27 informativos + 15 alarma) | ✅ Completada |
| T-02 | RAGAS: Faithfulness + Answer Relevancy contra el pipeline real | ✅ Completada |
| T-03 | Safety Compliance baseline (15 casos de alarma) | ✅ Completada |
| T-04 | Informe parcial de resultados (documentación, sin TDD) | ✅ Completada |

**Entregables**
- `evaluation/dataset.py`, `evaluation/__init__.py` — loader/validator del dataset de evaluación (`EvalCase`, pydantic)
- `tests/eval/dataset_partial.json` — dataset de 42 casos (27 informativos + 15 alarma), redactado por Claude a partir de la KB real y revisado por Marcos (D-044/D-049)
- `tests/eval/e07_t01_partial_eval_dataset.feature`, `tests/step_defs/test_e07_t01.py` — escenarios T-01 (TDD)
- `scripts/run_ragas_eval.py` — script de evaluación RAGAS (Faithfulness + Answer Relevancy) contra `RAGPipeline` real, documentado sin TDD (D-050/D-051)
- `tests/eval/e07_t02_ragas_faithfulness_relevancy.feature`, `tests/eval/results/e07_t02_ragas_scores.json` — escenario y resultados brutos de T-02
- `tests/eval/e07_t03_safety_compliance_baseline.feature`, `tests/step_defs/test_e07_t03.py`, `tests/eval/results/e07_t03_safety_compliance_baseline.json` — TDD y resultados de Safety Compliance (D-053)
- `tests/eval/e07_t04_informe_parcial.feature`, `tests/eval/results/e07_t04_informe_parcial.md` — informe parcial de resultados (T-04)
- `config/alarm_triggers.json`, `rag/safety.py` — claves de triggers renombradas a inglés, id desacoplado de categoría (D-048, fuera de alcance de E-07)
- `rag/config.py`, `rag/generator.py`, `.env.example` — modelo de producción `LLM_MODEL` a `gemini-2.5-flash` (D-043)
- `tasks/E07-T01-plan.md` a `E07-T03-plan.md` — planes de implementación
- `decisions.md` — D-043 a D-053

**Resultados (baseline, sin ciclo de mejora)**

| Métrica | Resultado | Objetivo | Estado |
|---|---|---|---|
| Faithfulness | 79.7% | > 95% | Por debajo del objetivo |
| Answer Relevancy | 77.8% | > 90% | Por debajo del objetivo |
| Safety Compliance | 100% (15/15) | 100% | Cumplido |

Dos hallazgos abiertos remitidos al ciclo de mejora de E-09: posible sobre-activación del filtro de seguridad en 3 casos informativos, y 2 casos con Answer Relevancy en 0.0 sin causa diagnosticada. Detalle en `tests/eval/results/e07_t04_informe_parcial.md`.

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

**Nota de prioridad (15 jul 2026):** E-08 se ejecuta después de E-07/E-09
(ver nota de prioridad de la fase, arriba). Si el tiempo antes del 29 de
julio no da para las tres capas, la capa (1) —memoria de corto plazo— es la
candidata a mantener por barata y por resolver un hueco de UX ya visible;
la capa (3) —persistencia entre sesiones + derecho al olvido— es la
candidata a recortar o dejar como versión mínima, por ser la más costosa
(esquema Supabase, UI de borrado) y la que menos compromete que el agente
siga siendo un producto completo sin ella.

**Nota de bloqueo (18 jul 2026, D-059):** esta prioridad interna a E-08 queda
invertida por una condición externa a la épica. La capa (1) —memoria
conversacional, antes la más barata y prioritaria— es ahora la que más
riesgo tiene de ejecutarse antes de tiempo: mezclar historial de
conversación con un pipeline de generación de una sola respuesta cuya
calidad todavía no está resuelta (ver E-09) haría muy difícil diagnosticar
fallos nuevos. La capa (1) queda bloqueada hasta cerrar **E-11** (ciclo de
mejora de calidad); las capas (2) y (3), al no tocar el contexto de
generación de la misma forma, pueden ejecutarse después de E-10 sin
esperar a E-11. Ver nota de reordenamiento en la introducción de esta fase.

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

### E-09 — Evaluación RAGAS completa
Cierre del plan de evaluación con al menos un ciclo de mejora.

**Nota de alcance (16 jul 2026):** la entrega es un TFM, no una validación médica. La
revisión clínica de Jacques Rivière (`docs/evaluation.md` sección 1.2: signos de alarma,
tono, respuestas peligrosas) no es un requisito bloqueante para la entrega del 29 de
julio — es trabajo importante de cara a un uso real post-entrega, no una condición de
cierre de E-09. Sí conviene lanzarla en paralelo cuanto antes (su turnaround histórico es
de días/rondas, ver la revisión de signos de alarma de junio-julio, aún no cerrada del
todo), pero si su feedback no llega a tiempo, E-09 se cierra igualmente con los resultados
RAGAS + ciclo de mejora + CHART ya completados, dejando la validación clínica como
seguimiento abierto post-TFM.

**Arranque (17 jul 2026):** al descomponer la épica en `epic-start` surgieron dos
inconsistencias numéricas en `docs/evaluation.md` no detectadas hasta ahora: §3 (Fase
1.5) dice "65 casos" cuando §2.2 ya desglosaba 72 tras la ampliación de D-049 (27+15+10+
10+5+5); y §2.3 dice "30 casos" para el subconjunto de seguridad cuando la suma de sus
propias categorías (alarma+diagnóstico+límite+prompt injection = 15+10+10+5) da 40, no
30 — error preexistente a D-049, no causado por ella. Ambas se corrigen al documentar en
T-06. Marcos confirmó 72 como cifra objetivo del dataset.

**Alcance del ciclo de mejora (17 jul 2026):** de los 6 hallazgos remitidos a E-09 (2 del
informe parcial E-07 T-04 §4.1/§4.2 + 4 de `backlog/ideas.md`), Marcos decidió acotar
T-05 a los 3 de menor coste/mayor relación con lo ya medido en esta épica:
- **A** — sobre-activación del filtro de seguridad en eval_07/eval_08/eval_25 (D-053 §4.1)
- **B** — Answer Relevancy en 0.0 sin causa diagnosticada, eval_06/eval_15 (D-053 §4.2)
- **F** — `langdetect` falla en frases cortas de síntomas en español (`ideas.md` #4)

Quedan fuera de este ciclo (backlog abierto, no perdidos): **C** (grounding demasiado
estricto ante conocimiento de mundo) y **E** (registro lingüístico no siempre
accesible). Razón: con ~6-7 días de margen para E-09 antes de encadenar E-08/E-10 hasta
el 29 de julio, cubrir los 6 arriesgaba tanto el timing de esta épica como el de las
siguientes. **D se reincorpora al alcance el 17 de julio — ver nota de reordenamiento
abajo.**

**Reordenamiento mid-sprint (17 jul 2026, D-056):** al cerrar T-02 y ver los resultados
reales (Faithfulness 79.2%, Answer Relevancy 75.9%, Context Precision 53.8%, Context
Recall 70.3% — los cuatro por debajo de objetivo), Marcos planteó que medir todas las
tareas restantes antes de mejorar nada arriesgaba acabar con una épica llena de
mediciones y ninguna mejora real si el tiempo se agotaba. Se revisó qué mediciones
pendientes son causalmente independientes de los arreglos de T-05 y cuáles no:

- **T-03 (Safety Compliance, alarma+límite)** es determinista y ortogonal — confirmado en
  `rag/safety.py`: `check_alarm_signals()` es keyword matching puro sobre el texto crudo de
  la pregunta, no depende de retrieval, generación, ni del idioma detectado (hallazgo F).
  Da igual en qué momento se mida; su resultado no cambia por los arreglos de T-05 y no
  hace falta repetirla.
- **T-04**, la parte de comportamiento (rechazo de diagnóstico, resistencia a inyección)
  es igual de independiente. Pero **Hallucination Rate** (también en T-04) está atado a la
  calidad de retrieval/grounding — el mismo terreno que el hallazgo D. Medirlo antes de
  arreglar D daría un número que quedaría obsoleto en cuanto se toque retrieval.
- Las 4 métricas ya medidas en T-02 son exactamente las que A, B y D deberían mover.

**Decisión de reordenamiento:**
1. **T-05 se adelanta** y se ejecuta a continuación, antes de T-03/T-04 (no al final de la
   épica como estaba planeado).
2. **Alcance de T-05 ampliado de A/B/F a A, B, D y F** — D se reincorpora dado que hoy
   tenemos su impacto medido y cuantificado (Context Precision/Recall), en vez de quedar
   como limitación documentada sin más.
3. **T-05 no se considera cerrada solo con el arreglo del código** — su criterio de cierre
   incluye re-ejecutar `scripts/run_ragas_eval.py` sobre el pipeline ya arreglado para
   obtener un antes/después real de las 4 métricas de T-02. Importante: el script tiene
   checkpointing por id — relanzarlo tal cual sobre
   `tests/eval/results/e09_t02_ragas_full_scores.json` se saltaría los 32 casos ya
   presentes y no los recalcularía. Antes de la re-ejecución hay que mover ese fichero a un
   nombre de respaldo (o apuntar `_RESULTS_PATH` a uno nuevo) para que la comparación
   antes/después sea honesta.
4. **T-03 puede ejecutarse en cualquier momento** a partir de ahora, sin depender de T-05.
5. **T-04** puede dividirse: la parte de comportamiento (diagnóstico/prompt injection) no
   depende de T-05 y puede medirse cuando convenga; **Hallucination Rate debe medirse
   después de T-05**, no antes, para no repetirla también.

Principio general para el resto de la épica (y precedente para E-10 si aplica): medición
específica → mejora específica de lo que esa medición detectó, en vez de medir todo primero
y dejar la mejora para un único ciclo al final. Evita el escenario de acabar con una
herramienta que no funciona pero con mediciones exhaustivas de que no funciona.

**Decisiones técnicas por hallazgo (`task-start` T-05, D-057):**
- **A** — `check_alarm_signals()` incorpora una stoplist de 3 palabras sin señal de alarma
  (después, varios, infusión) y un chequeo de contexto para "antibióticos" (exige un
  término de duración/frecuencia). Validado sin regresiones contra los 27 casos reales de
  alarma/límite + los 27 informativos.
- **B** — tratado como **Plan B**, no scope comprometido: se investiga solo si sobra
  margen tras A, D y F.
- **D** — `EnsembleRetriever` de LangChain (BM25 + vectorial, RRF), no el `Search()`
  nativo de Chroma (confirmado exclusivo de Chroma Cloud, no disponible para Chroma local).
- **F** — sustituir `langdetect` por `lingua-py`, restringido a es/en/ca.

**Criterios de aceptación de alto nivel**
- Resultados RAGAS completos documentados en `docs/evaluation.md`
- Al menos un ciclo de mejora basado en los resultados
- Checklist CHART completado como anexo
- Validación clínica de Jacques: deseable en paralelo, no bloqueante para la entrega (ver nota de alcance)

### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | Ampliar el dataset de evaluación a cobertura completa (72 casos) | ✅ Completada |
| T-02 | RAGAS completo: Context Precision + Context Recall | ✅ Completada |
| T-05 | Ciclo de mejora (hallazgos A, B, D, F) — **se ejecuta a continuación** (D-056) | ✅ Completada |
| T-03 | Safety Compliance ampliado: alarma + casos límite (25 casos, determinista) — sin dependencia de T-05, cualquier momento | ✅ Completada |
| T-04 | Comportamiento ante diagnóstico/prompt injection (sin dependencia) + Hallucination Rate (**medir después de T-05**) | ✅ Completada |
| T-06 | Checklist CHART + informe final en `docs/evaluation.md` | ✅ Completada |

**Estado:** ✅ Completada — 18 jul 2026

**Entregables**
- `evaluation/dataset.py` — schema `EvalCase` ampliado con `category` explícito y campos opcionales de idioma/prompt injection (T-01, D-054)
- `tests/eval/dataset_partial.json` — dataset ampliado a 72 casos (D-046 a D-049), corrección de inconsistencias numéricas de `evaluation.md` §2.3/§3
- `scripts/run_ragas_eval.py` — evaluación RAGAS completa (Faithfulness, Answer Relevancy, Context Precision, Context Recall) sobre 32 casos `informativo`/`otro_idioma`, con checkpointing (T-02, D-055)
- `tests/eval/results/e09_t02_ragas_full_scores_pre_t05.json`, `e09_t02_ragas_full_scores.json` — resultados antes/después del ciclo de mejora
- `rag/safety.py`, `config/alarm_triggers.json` — hallazgo A: stoplist + chequeo de contexto contra sobre-activación del filtro de seguridad (T-05, D-057)
- `rag/retriever.py`, `rag/pipeline.py` — hallazgo D: `EnsembleRetriever` (BM25 + vectorial, RRF) — mitigación parcial de Context Precision (T-05, D-057)
- `rag/language.py` — hallazgo F: sustitución de `langdetect` por `lingua-py` (T-05, D-057)
- `tests/eval/results/e09_t05_cierre.md`, `e09_t05_plan_b_investigacion.md` — cierre del ciclo de mejora e investigación de hallazgo B (abierto, sin fix aplicado)
- `tests/features/e09_t03_safety_compliance_expanded.feature`, `tests/eval/results/e09_t03_safety_compliance_full.json` — Safety Compliance ampliado, 25/25 casos (T-03, D-053)
- `scripts/run_e09_t04_eval.py`, `tests/eval/results/e09_t04_behavior_hallucination.json` — comportamiento diagnóstico/prompt injection (LLM-as-judge + confirmación manual) y Hallucination Rate derivado de Faithfulness (T-04, D-058)
- `prompts/system_prompt_family.txt` — restricción añadida contra repetir/confirmar frases inyectadas que contradigan el comportamiento de seguridad (hallazgo `eval_71`, D-058 addendum)
- `docs/evaluation.md` — informe final: resultados RAGAS/Safety Compliance/Hallucination Rate, ciclo de mejora (§5), checklist CHART + TRIPOD-LLM (§6), métricas de éxito consolidadas (§7)
- `tasks/E09-T01-plan.md` a `E09-T05-plan.md` — planes de implementación
- `decisions.md` — D-054 a D-058

**Resultados (Fase 1.5, post-ciclo de mejora)**

| Métrica | Objetivo | Resultado | Estado |
|---|---|---|---|
| Faithfulness | > 95% | 83.7% (32 casos) | 🔴 Por debajo |
| Answer Relevancy | > 90% | 79.5% (32 casos) | 🔴 Por debajo |
| Context Precision | > 85% | 52.1% (32 casos) | 🔴 Por debajo |
| Context Recall | > 85% | 75.5% (32 casos) | 🔴 Por debajo |
| Safety Compliance | 100% | 100% (40/40) | ✅ Cumple |
| Hallucination Rate | < 2% | 93.75% (30/32 casos) | 🔴 Muy por debajo |
| Validación clínica | Deseable | Feedback de alarma aplicado (rondas 1-2); validación del conjunto E-09 no recibida a fecha de cierre | 🟡 Seguimiento post-TFM, no bloqueante |

4 de las 6 métricas RAGAS/Hallucination quedan por debajo de objetivo tras el ciclo de mejora — el ciclo resolvió los hallazgos A y F, mitigó D solo parcialmente y dejó B abierto (investigado, sin fix). Documentado sin suavizar, siguiendo CHART/TRIPOD-LLM (`docs/evaluation.md` §6-7). Los criterios de aceptación de la épica (resultados documentados, ciclo de mejora ejecutado, checklist CHART completado) se cumplen igualmente — no exigían alcanzar los objetivos numéricos, solo completar el proceso de medición y mejora. Safety Compliance (Falso Negativo Cero) sí se cumple al 100%.

---

### E-10 — Pulido: responsive, CORS y UX
Ajustes finales para la entrega.

**Criterios de aceptación de alto nivel**
- Interfaz validada en móvil y escritorio
- CORS configurado para futura integración web (D-007)
- Revisión de UX con criterios del PRD

**Notas**
- Al cerrar esta épica: ejecutar tests RAGAS end-to-end (E-07/E-09) sobre el sistema completo antes del PR final. Es el único momento en que se valida el pipeline integrado en su totalidad.
- **Orden de ejecución (18 jul 2026):** E-11 pasa por delante de esta épica — ver nota de reordenamiento al inicio de la fase y D-059.

**Estado:** ⚪ No iniciada

---

### E-11 — Ciclo de mejora de calidad (hallazgos post-E-09)

Cierre acotado de los hallazgos de calidad que quedaron abiertos o fuera de alcance en el ciclo de mejora de E-09 (D-056), más una ampliación de la KB. Precede a la capa 1 de E-08 (memoria conversacional) — ver nota de bloqueo en E-08 y D-059.

**Nota de origen (18 jul 2026):** surge al plantear si E-08 podía arrancar justo después de E-09. E-09 cerró con 4 de 6 métricas por debajo de objetivo (Faithfulness 83.7%, Answer Relevancy 79.5%, Context Precision 52.1%, Context Recall 75.5%, Hallucination Rate 93.75% vs <2%) y varios hallazgos sin resolver o fuera de alcance del ciclo de mejora de T-05. Mezclar memoria conversacional con una generación de una sola respuesta ya no resuelta encarecería el diagnóstico de fallos nuevos — mismo principio de D-056 ("medición específica → mejora específica"). Detalle completo del razonamiento en D-059.

**Nota de alcance — ideas descartadas (18 jul 2026):** se evaluó y se descarta para esta épica subir `LLM_TEMPERATURE` (hoy 0.1, `rag/config.py`) y/o conectar el LLM a búsqueda web en vivo (Gemini "grounding with Google Search"), ambas propuestas para paliar la intuición de que la KB es limitada. Temperatura no es la palanca correcta: controla aleatoriedad de muestreo, no si el modelo usa el contexto recuperado o su conocimiento general — subirla tiende a empeorar Faithfulness, no a mejorarlo. Búsqueda web en vivo rompe la trazabilidad de fuentes (`data/raw/manifest.json`, D-021) y aumenta el riesgo frente a Falso Negativo Cero (D-002, no negociable) — contenido no vetted por Jacques en un dominio pediátrico es más peligroso que una respuesta evasiva. Si se retoma en el futuro, requiere épica propia + revisión clínica explícita, no un cambio de configuración. Se conserva sí la idea metodológica de Marcos de contrastar una respuesta con grounding más laxo frente a la estricta (pasando ambas por los mecanismos de seguridad existentes) como **técnica de investigación offline** del hallazgo C — nunca como comportamiento de producción.

**Nota de alcance — ampliación de KB como primera tarea (18 jul 2026):** comprobado contra `data/raw/manifest.json` (37 documentos): 36 son monográficos por patología/procedimiento; solo `idf/manual-para-pacientes-y-familias-sobre-inmunodeficiencias-primarias-sexta.pdf` es un documento genuinamente general. Los casos con peor Context Precision/Recall de E-09 (eval_03/06/08/11/13/15/20/23/25/27/65) coinciden sistemáticamente con preguntas de vida diaria/FAQ (frecuencia de revisiones, viajar con medicación, convivencias, contagio, cura, por qué necesita infusiones) no cubiertas ni siquiera por las fuentes ya propuestas en `docs/kb-sources.md`. Esta tarea se ejecuta primero, antes que el resto del alcance técnico, por dos motivos: (1) puede resolver varios hallazgos de retrieval como efecto colateral, igual que le pasó a `eval_63` con el fix de hallazgo D en E-09 — evita investigar a fondo casos que podrían desaparecer solos; (2) cualquier ajuste del peso de BM25 debe calibrarse contra el corpus final, no contra uno que va a cambiar después. Cuello de botella: la búsqueda y vetado de fuentes depende del tiempo de Marcos (mismo criterio que E-06 T-08 — no inventar enlaces), no de trabajo técnico; arrancarla en paralelo al resto de la épica.

**Criterios de aceptación de alto nivel**
- KB ampliada con documentación general/FAQ de vida diaria (primera tarea) y casos de contexto pobre remedidos de forma dirigida tras la ampliación
- Peso de BM25 en el retriever híbrido revisado (adaptativo o recalibrado) contra el corpus ya ampliado
- Hallazgo C (grounding excesivamente estricto) acotado a una regla concreta y limitada (qué tipo de conector no-clínico se permite), no una relajación general del grounding
- Hallazgo E (registro lingüístico) revisado con al menos una lectura cualitativa dirigida
- `eval_15` investigado en profundidad como prioridad (más grave que el resto de "hallazgo B": único caso con Faithfulness bajo, 0.38, además de 0.0 en las otras tres métricas); cierre de `eval_63` confirmado antes de investigarlo de nuevo
- Documento `guia_antibiotics_esp_0.pdf` investigado como sospechoso recurrente (3 apariciones espurias documentadas en `backlog/ideas.md`)
- Decisión tomada sobre cómo reportar Hallucination Rate en el informe final — el 93.75% actual es un conteo binario (D-058: cualquier caso con faithfulness < 1.0 cuenta como "alucinado"); de los 30 casos, solo `eval_15` está realmente mal (< 0.5), el resto está entre 0.69 y 0.96 — valorar un desglose por severidad como métrica complementaria, no solo el binario
- Resultados documentados en `docs/evaluation.md` como actualización post-E-09, con re-medición antes/después dirigida a los casos afectados (mismo criterio de transparencia que E-09 T-05)

**Descomposición y decisiones de `epic-start` (18 jul 2026):** aprobada por Marcos con tres
puntos resueltos sobre la propuesta inicial:
- **T-02:** prioridad confirmada en el peso adaptativo de BM25 (activar/ponderar solo ante
  señal léxica fuerte — nombre propio, término de baja frecuencia, patrón geográfico), con la
  recalibración simple del peso fijo (ej. 0.2/0.8) como fallback barato solo si el adaptativo
  no cierra a tiempo.
- **T-03:** Marcos aprueba explícitamente la redacción exacta de la regla de grounding para
  conectores no-clínicos antes de que toque `prompts/system_prompt_family.txt` en producción —
  no se despliega solo con el veredicto de la investigación offline.
- **T-06:** aclarado que el 93.75% no refleja un fallo de medición — RAGAS Faithfulness
  calcula bien el soporte por afirmación, pero D-058 cuenta como "alucinado" cualquier caso con
  faithfulness < 1.0, sin matices; de los 30 casos, 29 están entre 0.69 y 0.96 (matiz/parafraseo,
  no dato inventado) y solo `eval_15` es grave (0.38). Bandas de severidad aprobadas: **Grave**
  (< 0.5), **Moderada** (0.5–0.85), **Leve** (0.85–<1.0), **Sin desviación** (1.0). El binario
  93.75% se mantiene en el informe por continuidad con E-09, acompañado de este desglose.

### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | Ampliación de la KB (fuentes generales/FAQ de vida diaria) | ✅ Completada |
| T-02 | Re-medición RAGAS + peso adaptativo de BM25 contra el corpus ampliado | ✅ Completada — revisada y confirmada por Marcos (19 jul 2026), `tests/eval/results/e11_t02_cierre.md` |
| T-03 | Hallazgo C: regla acotada de grounding para conectores no clínicos | ⚪ Pendiente |
| T-04 | Hallazgo E: revisión cualitativa del registro lingüístico | ⚪ Pendiente |
| T-05 | Investigación dirigida: `eval_15`, confirmación `eval_63`, documento sospechoso `guia_antibiotics_esp_0.pdf` | ⚪ Pendiente |
| T-06 | Hallucination Rate: desglose por bandas de severidad | ⚪ Pendiente |
| T-07 | Cierre: informe final en `docs/evaluation.md` | ⚪ Pendiente |

Orden de ejecución: T-01 primero (bottleneck: tiempo de Marcos para vetar fuentes), en
paralelo con T-03/T-04/T-06 (no dependen del corpus). T-02 y T-05 dependen de T-01/T-02
respectivamente. T-07 cierra la épica.

**Estado:** 🔵 En curso

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

*Última actualización: 19 julio 2026 — E-11 T-02 cerrada técnicamente (peso adaptativo de BM25, D-061; resultado en `tests/eval/results/e11_t02_cierre.md`), pendiente de confirmación de Marcos*
