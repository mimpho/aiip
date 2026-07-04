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
| E-06 | Ingesta y procesamiento de la KB | E-01, Feedback Jacques Rivière |
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

**Estado:** 🔵 En curso

### Tareas

| ID | Tarea | Estado |
|---|---|---|
| T-01 | Setup de dependencias y estructura del módulo RAG | ✅ Completada |
| T-02 | Embeddings y retriever con ChromaDB | ✅ Completada |
| T-03 | Detección de idioma e integración en pipeline | ✅ Completada |
| T-04 | Generador: LLM Gemini Flash via LangChain | ✅ Completada |
| T-05 | Módulo de seguridad: Falso Negativo Cero | ✅ Completada |
| T-06 | Pipeline end-to-end y tests de integración | 🔄 En progreso |

---

### E-05 — Interfaz conversacional (Chainlit) — perfil familias
Interfaz de usuario para el perfil familias con visualización del pipeline RAG.

**Criterios de aceptación de alto nivel**
- Chat funcional con streaming nativo de tokens
- Visualización de pasos intermedios del RAG (documentos recuperados, chunks usados)
- Diseño responsive desde el inicio (D-007)
- Tono y UX adaptados al perfil familiar según PRD
- Theming completo basado en tokens de E-02

**Nota metodológica:** E-05 no aplica TDD. Los criterios son de UX y presentación visual — streaming, responsive, theming — que no son verificables con pytest de forma significativa. La validación es manual (revisión visual + prueba funcional en browser). Los tests automatizados del pipeline RAG subyacente se cubren en E-04.

**Estado:** ⚪ No iniciada

---

### E-06 — Ingesta y procesamiento de la Knowledge Base
Carga, limpieza, chunking e indexación de las fuentes de IDP en ChromaDB.

**Criterios de aceptación de alto nivel**
- Fuentes procesadas: IPOPI, IDF, upiip.com, guías clínicas validadas — indexadas en inglés (ver D-011)
- Estrategia de chunking definida y documentada
- Colección de familias separada en ChromaDB

**Notas**
- Revisar DAIMS (Datasheets for AI and Medical Datasets, arXiv 2501.14094) al formalizar la KB — checklist de 24 requisitos aplicable directamente a este dataset. Ver `backlog/ideas.md`.
- Valorar si las reglas de seguridad clínica (Falso Negativo Cero) van como chunk indexado en ChromaDB, como system prompt, o en capas. Ver `backlog/ideas.md` → "Business rules como documento indexado en la KB".

**Estado:** ⚪ No iniciada — pendiente feedback de Jacques Rivière (validación de fuentes KB)

---

### E-07 — Evaluación RAGAS (parcial)
Dataset de prueba y métricas básicas funcionando para la entrega del 10 de julio.

**Criterios de aceptación de alto nivel**
- Dataset de preguntas representativas del perfil familias definido
- Las cuatro métricas RAGAS implementadas: Faithfulness, Answer Relevancy, Context Precision, Context Recall
- Primeros resultados documentados

**Notas**
- Hito de cierre de Fase 1 (10 jul). Al cerrar: ejecutar `pytest tests/ -v` sobre el sistema completo acumulado hasta este punto — primera validación de integración real del pipeline.

**Estado:** ⚪ No iniciada

---

### E-08 — Memoria de perfil e histórico de conversaciones
Onboarding, datos estables del paciente y persistencia de conversaciones entre sesiones.

**Criterios de aceptación de alto nivel**
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
