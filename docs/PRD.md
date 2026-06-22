# PRD — Product Requirements Document
## AIIP — Asistente Inteligente de Inmunodeficiencias Primarias

| Campo | Valor |
|---|---|
| Versión | 1.9 (destilada para repositorio) |
| Fecha | Mayo–junio 2026 |
| Autor | Marcos de la Torre — TFM Máster en IA |
| Colaborador clínico | Jacques Rivière (inmunólogo pediátrico) |
| Estado | Activo — pendiente validación clínica en ítems marcados |
| Documento de referencia | PRD v1.9 en Google Drive (documento de colaboración con el inmunólogo) |

> Este documento es el espejo en Markdown del PRD v1.9. El documento de trabajo con el colaborador clínico vive en Google Drive. Las decisiones técnicas se desarrollan en `decisions.md` y `docs/tech-spec.md`.

---

## 1. Visión del producto

Las familias que conviven con una Inmunodeficiencia Primaria (IDP) se enfrentan diariamente a dudas clínicas urgentes y no urgentes que requieren orientación inmediata. La falta de acceso a información rigurosa fuera del horario de consulta genera ansiedad, decisiones desinformadas y una sobrecarga innecesaria de los canales del equipo médico.

AIIP es un asistente conversacional disponible 24/7 diseñado para **acompañar e informar** a las familias y profesionales ante sus dudas sobre IDP — orientando, informando y facilitando el acceso a información contrastada. No es una herramienta de diagnóstico ni reemplaza la consulta médica.

### Lo que AIIP no es

- No es una herramienta diagnóstica
- No sustituye al criterio médico ni de enfermería bajo ninguna circunstancia
- No emite recomendaciones terapéuticas propias
- No interpreta resultados médicos (analíticas, informes, radiografías)

---

## 2. Usuarios objetivo

### Persona 1 — Familia (Fase 1 — MVP)

**Quién:** Padre, madre o tutor legal de un niño diagnosticado con IDP, en seguimiento por un equipo de inmunología pediátrica.

**Contexto:** Convive con la enfermedad de forma continua. Conocimiento básico-medio adquirido en consulta, sin formación médica formal.

**Canal de uso:** Dispositivo móvil principalmente. Web responsive embebible (evolución futura).

**Necesidades principales:**
- Resolver dudas a cualquier hora sin saturar al equipo médico
- Entender términos médicos en lenguaje accesible
- Saber cuándo una situación requiere urgencias vs. esperar a consulta
- Conocer los canales disponibles para contactar con el equipo sanitario

### Persona 2 — Profesional sanitario (Backlog — post-Fase 1)

**Quién:** Inmunólogo/a pediatra o enfermero/a especializado/a en inmunodeficiencias.

**Contexto:** Atiende casos de baja prevalencia y alta complejidad. Necesita acceso rápido a literatura científica actualizada.

**Canal de uso:** Ordenador de consulta o dispositivo profesional.

**Necesidades principales:**
- Consultar evidencia científica sobre casos específicos o genes concretos
- Acceder a síntesis de literatura de Orphanet, ESID, PubMed de forma estructurada
- Obtener una segunda opinión documental para casos de baja prevalencia

---

## 3. Fases de desarrollo

| Fase | Nombre | Hito | Perfil | Alcance |
|---|---|---|---|---|
| Fase 0 | Planificación y documentación | 12 jun 2026 | — | Documentación técnica cerrada |
| Fase 1 | MVP core | 10 jul 2026 | Familiar | Pipeline RAG + autenticación básica |
| Fase 1.5 | MVP completo | 29 jul 2026 | Familiar | Memoria de perfil + RAGAS + pulido |
| Backlog | Features opcionales | Post-TFM | Familiar + Profesional | Perfil profesional, multimodal, integraciones |

Ver roadmap completo en `backlog/epics.md`.

---

## 4. Casos de uso — Fase 1 (perfil familiar)

| ID | Caso de uso | Ejemplo de consulta | Respuesta esperada |
|---|---|---|---|
| CU-01 | Signos de alarma | "Mi hijo tiene 38.5°C, ¿es urgente?" | Información sobre umbrales de fiebre en IDP + recomendación activa de urgencias si aplica |
| CU-02 | Medicación prescrita | "¿Diferencia entre jarabe y pastillas recetadas?" | Explicación informativa del formato + recordatorio de que cambios de pauta requieren validación médica |
| CU-03 | Términos médicos | "¿Qué significa que los neutrófilos están bajos?" | Explicación accesible + fuente oficial + invitación a consultar con el especialista |
| CU-05 | Canales de atención | "¿A quién llamo si es fin de semana?" | Información de contacto del equipo `[Pendiente validación clínica — Jacques Rivière]` |
| CU-06 | Restricciones y cuidados | "¿Puede ir al colegio esta semana?" | Información basada en guías oficiales + recordatorio de que la decisión la toma el equipo médico |

> CU-04 (síntomas visuales) se traslada al backlog de features opcionales — requiere el agente multimodal.

---

## 5. Knowledge Base

> AIIP no responde desde el conocimiento general del LLM, sino desde documentos curados e indexados. Toda fuente debe ser aprobada por el inmunólogo colaborador antes de su incorporación. Ver D-011 en `decisions.md` para la estrategia de idioma de la KB.

### KB Perfil familiar (Fase 1)

| Fuente | Tipo | Idioma original |
|---|---|---|
| IPOPI | Guías divulgativas para pacientes | ES / EN |
| IDF (Immune Deficiency Foundation) | Guías y recursos para familias | EN |
| upiip.com | Protocolos del equipo de inmunología `[Confirmado por Jacques Rivière]` | ES |
| Guías clínicas validadas por el equipo médico | Documentación interna validada | ES |
| Signos de alarma específicos por grupo IDP | `[Pendiente validación clínica — Jacques Rivière]` | ES |

### KB Perfil profesional (Backlog)

| Fuente | Tipo |
|---|---|
| Orphanet | Base de datos de enfermedades raras |
| ESID | Guías clínicas especializadas |
| PubMed | Literatura científica peer-reviewed |

---

## 6. Principios éticos y módulo de seguridad

### 6.1. Principios no negociables

Implementados a nivel de arquitectura (system prompt persistente + parámetros de inferencia). No pueden ser alterados por el usuario:

- AIIP acompaña e informa, nunca diagnostica
- Ante cualquier consulta que derive hacia recomendación diagnóstica o terapéutica, el sistema redirige explícitamente al equipo médico
- AIIP nunca sustituye al criterio clínico — cada respuesta incluye un recordatorio del rol informativo del sistema
- AIIP siempre facilita el acceso a los canales directos con el equipo sanitario cuando la consulta lo requiera

### 6.2. Filosofía Falso Negativo Cero

El sistema asume deliberadamente el coste de falsos positivos para eliminar los falsos negativos. Ante la duda, siempre alerta.

- **Recomendación activa de urgencias:** si el sistema detecta signos de alarma, recomienda proactivamente el contacto con urgencias. La lista de signos específicos para IDP será definida y validada por el inmunólogo colaborador `[Pendiente — Jacques Rivière]`
- **Restricción de negativos:** AIIP nunca confirmará que "no es necesario ir a urgencias". Ante la duda, siempre instará a la consulta médica
- **Responsabilidad explícita:** el sistema recuerda en todo momento que la responsabilidad final reside en los tutores y en los profesionales sanitarios

Ver desarrollo técnico completo en `docs/security.md`.

---

## 7. Arquitectura técnica (resumen)

> El detalle técnico completo vive en `docs/tech-spec.md`. Este apartado recoge solo los elementos relevantes para el documento de producto.

### Patrón arquitectónico

RAG (Retrieval-Augmented Generation): el sistema recupera información de una base de datos vectorial con documentos validados y los utiliza como contexto de generación. No responde desde el conocimiento general del LLM.

La Vector DB es un servicio compartido con colecciones independientes por perfil (Familiar / Profesional), lo que permite escalar cada KB de forma independiente.

### Stack tecnológico (cerrado)

| Componente | Decisión |
|---|---|
| LLM | Gemini Flash (Google API — free tier) |
| Embeddings | BAAI/bge-m3 |
| Vector DB | ChromaDB 1.x |
| Orquestación | LangChain v1.0 |
| Frontend | Chainlit |
| Autenticación + persistencia | Supabase |

Ver justificación completa en D-004 (`decisions.md`).

### Parámetros de inferencia

| Parámetro | Valor | Justificación |
|---|---|---|
| Temperature | 0.0 – 0.1 | Minimiza alucinaciones. Prioriza determinismo. |
| Top-P | 0.1 | El modelo selecciona solo entre palabras de mayor probabilidad estadística |
| Max Tokens | 150 – 300 | Previene infoxicación y controla respuestas excesivamente largas |

---

## 8. Privacidad y protección de datos

- **Categoría especial RGPD (Art. 9):** los datos de salud requieren consentimiento explícito informado, no un checkbox genérico
- **Minimización de datos:** solo se almacena lo estrictamente necesario
- **Derecho al olvido:** el usuario puede solicitar el borrado completo de sus datos
- **Localización de datos:** Supabase región EU (Frankfurt) — los datos no salen de la UE
- **Menores:** si el paciente es menor, el consentimiento lo otorga el tutor legal
- **Sin entrenamiento:** los datos no serán utilizados para entrenar ni ajustar el modelo
- **Trazabilidad:** toda respuesta incluirá la cita de la fuente utilizada

Ver desarrollo completo en `docs/security.md` (sección RGPD).

---

## 9. Métricas de éxito

| Métrica | Descripción | Objetivo |
|---|---|---|
| Faithfulness | % de respuestas completamente respaldadas por la KB | > 95% |
| Answer Relevance | % de respuestas pertinentes a la consulta | > 90% |
| Safety Compliance | % de consultas de riesgo que activan el módulo de seguridad | 100% |
| Hallucination Rate | % de respuestas con información no presente en la KB | < 2% |
| Latencia | Tiempo de respuesta medio | < 5 segundos |

Framework de evaluación: RAGAS para métricas automáticas + evaluación manual por el inmunólogo colaborador para validación clínica. Ver `docs/evaluation.md`.

---

## 10. Fuera de alcance (TFM)

- Emisión de diagnósticos o recomendaciones terapéuticas propias
- Interpretación de resultados médicos (analíticas, informes, radiografías)
- Integración con sistemas de historia clínica electrónica
- Desarrollo de aplicación móvil nativa (iOS/Android)
- Integración con canales de mensajería (WhatsApp, Telegram)

---

## 11. Ítems pendientes de validación clínica

| # | Ítem | Impacto | Estado |
|---|---|---|---|
| 1 | Signos de alarma específicos por grupo IDP que deben activar urgencias | Define el núcleo clínico del módulo de seguridad | `[Pendiente — Jacques Rivière]` |
| 2 | Validación de fuentes de la KB familiar | Determina la calidad de la Knowledge Base | Parcial — upiip.com confirmado |
| 3 | Información de contacto del equipo para CU-05 | Habilita el caso de uso de canales de atención | `[Pendiente — Jacques Rivière]` |
| 4 | Participación como validador clínico del TFM | Refuerza la validez académica | Confirmado — pendiente aprobación interna |

---

## 12. Prototipo navegable (referencia histórica)

Prototipos generados en fase temprana del proyecto, antes de tener la documentación técnica completa. Contienen respuestas simuladas con fines de prototipado — el contenido médico tiene carácter ilustrativo y debe ser validado antes de cualquier uso real.

| Perfil | URL |
|---|---|
| Familiar | [aiip-familly-app.lovable.app](https://aiip-familly-app.lovable.app/) |
| Profesional | [aiip-professional-app.lovable.app](https://aiip-professional-app.lovable.app/) |

> Los prototipos serán revisados y actualizados una vez la documentación técnica esté cerrada. Ver `backlog/ideas.md`.

---

*PRD v1.9 — destilado junio 2026 | Documento de colaboración con el inmunólogo en Google Drive*
