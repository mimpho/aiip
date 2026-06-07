# AIIP — Asistente Inteligente de Inmunodeficiencias Primarias

> Trabajo de Fin de Máster en Inteligencia Artificial  
> Máster en IA — junio 2026

---

## ¿Qué es AIIP?

Las familias que conviven con una Inmunodeficiencia Primaria (IDP) se enfrentan a un volumen de información médica compleja, dispersa y difícil de interpretar. Los profesionales que las atienden necesitan acceso ágil a literatura especializada en un campo con alta variabilidad clínica.

AIIP es un asistente conversacional diseñado para acompañar a ambos perfiles ante sus dudas: orienta, informa y facilita el acceso a información contrastada sobre IDP. No es una herramienta de diagnóstico ni reemplaza la consulta médica — su función es reducir la distancia entre la pregunta y la información de calidad, siempre con un profesional como referencia final.

El proyecto se desarrolla en colaboración con un inmunólogo pediátrico y utiliza la IA como instrumento principal en todo el ciclo de vida: producto, diseño, desarrollo, base de conocimiento, testing y evaluación.

---

## Estado del proyecto

| Fase | Estado | Descripción |
|---|---|---|
| Fase 1 — MVP | 🟡 En desarrollo | Agente de texto + perfil familias, autenticación y memoria de perfil |
| Fase 2A — Multimodal | ⚪ Backlog | Agente para imágenes de síntomas |
| Fase 2B — Científico | ⚪ Backlog | Agente de literatura científica para profesionales |

---

## Stack

| Componente | Decisión |
|---|---|
| LLM | Gemini Flash (Google API — free tier) |
| Embeddings | BAAI/bge-m3 |
| Vector DB | ChromaDB 1.x |
| Orquestación | LangChain v1.0 |
| Frontend | Chainlit |
| Autenticación + persistencia | Supabase |
| Entorno de desarrollo | Google Colab + Drive |

---


## Roadmap

```mermaid
gantt
    title AIIP — Planificación por fases
    dateFormat  YYYY-MM-DD
    axisFormat  %d %b

    section Fase 0
    Planificación y documentación     :done,    f0, 2026-06-08, 2026-06-12

    section Fase 1 — MVP core
    Pipeline RAG + Auth básica        :active,  f1, 2026-06-12, 2026-07-10

    section Fase 1.5 — MVP completo
    Memoria + RAGAS + pulido          :         f15, 2026-07-10, 2026-07-29

    section Features opcionales
    Perfil profesional · Multimodal   :         fo, 2026-07-10, 2026-09-01

    section Hitos
    Doc técnica cerrada               :milestone, 2026-06-12, 0d
    Código funcional                  :milestone, 2026-07-10, 0d
    Entrega final TFM                 :milestone, 2026-07-29, 0d
```

> Las fechas internas son orientativas — los únicos hitos inamovibles son el 12 de junio, el 10 de julio y el 29 de julio.

## Estructura de la documentación

```
aiip/
├── README.md          ← Este fichero. Navegación y estado del proyecto.
├── AGENTS.md          ← Contexto para agentes de IA durante el desarrollo.
├── CITATION.cff       ← Cita académica formal del TFM.
├── prompts.md         ← Prompts operativos usados en el desarrollo. Append-only.
├── decisions.md       ← Registro de decisiones relevantes del proyecto.
│
├── docs/
│   ├── PRD.md         ← Product Requirements Document. El qué y el por qué.
│   ├── tech-spec.md         ← Technical Design Document. El cómo.
│   ├── security.md    ← Módulo de seguridad. Falso Negativo Cero en profundidad.
│   └── evaluation.md  ← Plan de evaluación. RAGAS, métricas, validación clínica.
│
└── backlog/
    ├── epics.md       ← Épicas del proyecto. Esqueleto que se puebla durante el desarrollo.
    └── ideas.md       ← Cajón de sastre. Ideas y referencias pendientes.
```

Esta estructura responde a tres principios que se documentan y justifican en detalle en [`decisions.md`](./decisions.md): documentación viva sin replicación, mínima superficie de mantenimiento, y separación clara entre documento de producto y documento técnico.

---

## Documentación clave

| Fichero | Rol | Se actualiza cuando... |
|---|---|---|
| `README.md` | Navegación y estado | Hay un hito o cambia el estado del proyecto |
| `AGENTS.md` | Contexto para agentes de IA | Cambian convenciones de desarrollo |
| `CITATION.cff` | Cita académica formal | Se cierra el TFM |
| `prompts.md` | Prompts operativos del desarrollo | Se añade un prompt relevante. Nunca se edita. |
| `decisions.md` | Registro de decisiones | Se toma una decisión relevante de producto, técnica o de proceso |
| `docs/PRD.md` | Requisitos de producto | Hay cambio de producto o feedback clínico |
| `docs/tech-spec.md` | Diseño técnico | Hay decisión técnica nueva o cambio de stack |
| `docs/security.md` | Módulo de seguridad | Evoluciona el modelo de seguridad |
| `docs/evaluation.md` | Plan de evaluación | Hay resultados o cambio de métricas |
| `backlog/epics.md` | Épicas del proyecto | Se añade una épica o cambia su estado |
| `backlog/ideas.md` | Cajón de sastre | Cuando surge una idea. Sin mantenimiento activo. |

---

## Referencias clave

- **Guía clínica de reporte:** CHART (Chatbot Assessment Reporting Tool), 2025
- **Evaluación RAG:** RAGAS framework
- **Seguridad LLM:** OWASP Top 10 para LLMs
- **Estándares de documentación IA:** AGENTS.md (Agentic AI Foundation / Linux Foundation, 2025)
- **Marco regulatorio:** Reglamento UE de IA 2024/1689, guías AESIA

---

## Prototipo interactivo

- Perfil familias: [aiip-familly-app.lovable.app](https://aiip-familly-app.lovable.app/)
- Perfil profesionales: [aiip-professional-app.lovable.app](https://aiip-professional-app.lovable.app/)

---

*Última actualización: junio 2026 — Fase 1 en desarrollo activo*
