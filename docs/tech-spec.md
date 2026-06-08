# tech-spec.md — Technical Specification
## AIIP — Asistente Inteligente de Inmunodeficiencias Primarias

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | Junio 2026 |
| Autor | Marcos de la Torre — TFM Máster en IA |
| Documento relacionado | `docs/PRD.md` (requisitos de producto), `decisions.md` (registro de decisiones) |

> Este documento describe el **cómo** del sistema AIIP. El **qué** y el **por qué** viven en `docs/PRD.md`. Las decisiones de diseño con sus alternativas descartadas están en `decisions.md`.

---

## 1. Stack tecnológico

| Componente | Decisión | Versión | Justificación |
|---|---|---|---|
| LLM | Gemini Flash | API Google (free tier) | Multimodal nativo, free tier suficiente para TFM, configurable vía `.env` para producción |
| Embeddings | BAAI/bge-m3 | HuggingFace | Multilingüe, 8K tokens, cross-lingual retrieval — consultas en español sobre KB en inglés |
| Vector DB | ChromaDB | 1.x | Persistencia incluida, sin infraestructura adicional, evolución natural a pgvector |
| Orquestación | LangChain | v1.0 | Estable hasta v2.0, abstracción de proveedor LLM, ecosistema RAG + agentes completo |
| Frontend | Chainlit | Latest | Chat-first, streaming nativo, visualización step-by-step del pipeline RAG |
| Auth + persistencia | Supabase | Latest | Auth integrado, PostgreSQL gestionado, región EU (RGPD), MCP connector disponible |
| Detección de idioma | langdetect | Latest | Detección automática del idioma del usuario para respuesta en su idioma |
| IDE | Claude Cowork mode + Antigravity IDE | Claude Sonnet 4.6 | Entorno de desarrollo con IA integrada |

> **Principio rector:** el sistema es agnóstico de proveedor de IA. El modelo LLM se configura en `.env` — cambiar de Gemini Flash a Claude Sonnet o GPT-4o es cambiar una variable. Ver D-010 en `decisions.md`.

---

## 2. Arquitectura del sistema

### 2.1. Visión general de capas

```mermaid
graph TD
    subgraph Frontend ["Frontend — Chainlit"]
        UI_F[Interfaz familiar]
        UI_P[Interfaz profesional]
    end

    subgraph Auth ["Autenticación — Supabase Auth"]
        LOGIN[Login / Registro]
        ROL[Rol: familiar · profesional]
    end

    subgraph Orchestration ["Orquestación — LangChain v1.0"]
        LANG[Detección idioma]
        PROMPT[System prompt]
        RAG[Motor RAG]
        SEC[Módulo seguridad]
    end

    subgraph VectorDB ["Vector DB — ChromaDB 1.x"]
        KB_F[Colección familias]
        KB_P[Colección profesionales]
    end

    subgraph LLM ["LLM — Gemini Flash"]
        GEN[Generación de respuesta]
    end

    subgraph Persistence ["Persistencia — Supabase PostgreSQL"]
        PROFILE[Perfil usuario]
        HISTORY[Historial conversaciones]
    end

    UI_F --> LOGIN
    UI_P --> LOGIN
    LOGIN --> ROL
    ROL --> PROMPT
    PROMPT --> LANG
    LANG --> RAG
    RAG --> KB_F
    RAG --> KB_P
    RAG --> SEC
    SEC --> GEN
    GEN --> PROFILE
    GEN --> HISTORY
```

### 2.2. Flujo RAG completo

```mermaid
sequenceDiagram
    actor U as Usuario
    participant C as Chainlit
    participant L as LangChain
    participant S as Módulo seguridad
    participant E as Embeddings (bge-m3)
    participant V as ChromaDB
    participant G as Gemini Flash

    U->>C: Envía pregunta
    C->>L: Query + perfil + idioma detectado
    L->>S: Validación pre-retrieval (prompt injection, PII)
    S-->>L: Query validada
    L->>E: Genera embedding de la query
    E-->>L: Vector de la query
    L->>V: similarity_search(vector, collection=perfil, top_k=5)
    V-->>L: Top-K chunks relevantes
    L->>S: Validación post-retrieval (Falso Negativo Cero)
    S-->>L: Chunks + instrucciones de seguridad
    L->>G: Prompt = system_prompt + chunks + query + idioma
    G-->>L: Respuesta generada + fuentes citadas
    L->>C: Respuesta + steps intermedios del RAG
    C->>U: Respuesta con streaming + fuentes
```

---

## 3. Configuración de ChromaDB

### 3.1. Estructura de colecciones

```
chromadb/
├── collection: aiip_familiar
│   ├── Fuentes: IPOPI, IDF, upiip.com, guías clínicas validadas
│   ├── Idioma: inglés (fuentes originales) + español (documentación interna)
│   └── Metadatos: source, section, date_indexed, language, validated_by
│
└── collection: aiip_profesional
    ├── Fuentes: Orphanet, ESID, PubMed
    ├── Idioma: inglés
    └── Metadatos: source, doi, date_published, date_indexed, specialty
```

### 3.2. Estrategia de chunking

| Parámetro | Valor | Justificación |
|---|---|---|
| Método | RecursiveCharacterTextSplitter | Default de oro — 69% exactitud en benchmarks 2026 |
| Chunk size | 512 tokens | Equilibrio entre precisión de retrieval y contexto suficiente para el LLM |
| Chunk overlap | 10–20% (~50–100 tokens) | Evita pérdida de contexto en los bordes del chunk |
| Separadores | `\n\n`, `\n`, `. `, ` ` | Respeta estructura natural del documento |

### 3.3. Metadatos por chunk

Cada chunk almacena metadatos que permiten filtrado y trazabilidad:

```python
{
    "source": "IPOPI_guide_2024.pdf",
    "section": "Fiebre en IDP",
    "language": "en",
    "date_indexed": "2026-06-15",
    "validated_by": "Jacques Rivière",
    "profile": "familiar"
}
```

---

## 4. Parámetros de inferencia

| Parámetro | Valor | Justificación clínica |
|---|---|---|
| Temperature | 0.0 – 0.1 | Minimiza alucinaciones. En contexto médico, la variabilidad creativa es un riesgo, no un beneficio |
| Top-P | 0.1 | El modelo selecciona solo entre las palabras de mayor probabilidad estadística |
| Max Tokens | 150 – 300 | Previene infoxicación. Respuestas largas aumentan el riesgo de incluir información no fundamentada |
| Top-K retrieval | 5 | Balance entre contexto suficiente y ruido introducido por chunks poco relevantes |

> Temperature 0 reduce significativamente la variabilidad pero no garantiza determinismo absoluto. Este comportamiento queda documentado en `docs/evaluation.md`.

---

## 5. System prompt (estructura)

El system prompt es el componente que implementa el principio de Falso Negativo Cero. Vive en `prompts/system_prompt_familiar.txt` (nunca embebido en código).

**Estructura del system prompt:**

```
[ROL]
Eres AIIP, un asistente informativo especializado en Inmunodeficiencias Primarias.
Tu función es acompañar e informar — nunca diagnosticar ni recomendar tratamientos.

[RESTRICCIONES ABSOLUTAS]
- Nunca confirmes que una situación es segura o que no requiere atención médica
- Ante cualquier duda sobre urgencia, recomienda siempre consulta médica
- No interpretes resultados médicos (analíticas, informes, radiografías)
- No emitas recomendaciones terapéuticas propias

[IDIOMA]
Responde siempre en el idioma en que el usuario escribe: {detected_language}

[FUENTES]
Basa todas tus respuestas exclusivamente en los documentos proporcionados como contexto.
Cita siempre la fuente: "Según [fuente], sección [X]..."
Si la información no está en el contexto, indícalo explícitamente.

[TONO — PERFIL FAMILIAR]
Lenguaje accesible, empático y claro. Sin tecnicismos innecesarios.
El usuario no tiene formación médica formal.

[CIERRE OBLIGATORIO]
Cada respuesta debe terminar recordando el rol informativo del sistema
y facilitando el acceso a los canales de atención médica cuando sea relevante.
```

> El system prompt para el perfil profesional tendrá tono técnico y terminología clínica. Se define en Fase 2 (perfil profesional).

---

## 6. Módulo de seguridad

Ver desarrollo completo en `docs/security.md`. Resumen de capas:

| Capa | Momento | Qué hace |
|---|---|---|
| Pre-retrieval | Antes del RAG | Validación de prompt injection, filtrado PII, detección de consultas fuera de alcance |
| Post-retrieval | Después del RAG | Verificación Falso Negativo Cero, detección de signos de alarma en la query |
| Post-generación | Después del LLM | Disclaimer obligatorio, cita de fuente, validación de que no hay recomendación diagnóstica |

---

## 7. Autenticación y persistencia

### 7.1. Supabase Auth

- Proveedores: OAuth Google + email/password
- Rol definido en el registro — no hay selector de perfil en la interfaz
- El rol determina la colección de ChromaDB consultada y el system prompt aplicado

### 7.2. Esquema de base de datos

```sql
-- Perfil de usuario (memoria de perfil)
CREATE TABLE profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users,
    role        TEXT NOT NULL CHECK (role IN ('familiar', 'profesional')),
    patient_age INTEGER,
    idp_type    TEXT,
    context     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Conversaciones (memoria de conversación)
CREATE TABLE conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES profiles(id) ON DELETE CASCADE,
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    summary     TEXT
);

-- Mensajes
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    sources         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

> `ON DELETE CASCADE` garantiza que al borrar un usuario se eliminan todos sus datos — implementación del derecho al olvido (D-009).

### 7.3. Memoria de perfil en el contexto RAG

El perfil del usuario se inyecta en el prompt para contextualizar las respuestas:

```python
profile_context = f"""
Contexto del usuario:
- Tipo de IDP del paciente: {profile.idp_type}
- Edad del paciente: {profile.patient_age} años
"""
# Se añade al system prompt en cada conversación
```

---

## 8. Estrategia multiidioma

| Capa | Idioma | Implementación |
|---|---|---|
| KB interna | Inglés | Fuentes indexadas en su idioma original |
| Embeddings | Cross-lingual | bge-m3 resuelve la búsqueda semántica español → inglés |
| Detección | Automática | `langdetect` en cada query |
| Respuesta | Idioma del usuario | Instrucción en system prompt: `{detected_language}` |

Ver D-011 en `decisions.md`.

---

## 9. Estructura del proyecto (código)

```
aiip/
├── .env.example              ← Variables de entorno (modelo, API keys, Supabase URL)
├── requirements.txt          ← Dependencias Python
├── main.py                   ← Entrypoint Chainlit
│
├── prompts/
│   ├── system_prompt_familiar.txt
│   └── system_prompt_profesional.txt   ← (Fase 2)
│
├── rag/
│   ├── pipeline.py           ← Flujo RAG principal (LangChain)
│   ├── retriever.py          ← Configuración ChromaDB + búsqueda
│   └── embeddings.py         ← Configuración bge-m3
│
├── ingestion/
│   ├── loader.py             ← Carga de documentos
│   ├── chunker.py            ← Estrategia de chunking
│   └── indexer.py            ← Indexación en ChromaDB
│
├── security/
│   ├── validator.py          ← Módulo Falso Negativo Cero
│   └── pii_filter.py         ← Filtrado de información personal
│
├── auth/
│   └── supabase_client.py    ← Cliente Supabase Auth + DB
│
├── memory/
│   └── profile_manager.py    ← Gestión de perfil y contexto de usuario
│
└── tests/
    └── features/             ← Escenarios Gherkin (BDD)
```

---

## 10. Variables de entorno

```bash
# .env.example

# LLM — configurable sin tocar código (D-010)
LLM_PROVIDER=google          # google | anthropic | openai
LLM_MODEL=gemini-1.5-flash
LLM_TEMPERATURE=0.1
LLM_TOP_P=0.1
LLM_MAX_TOKENS=300

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_FAMILIAR=aiip_familiar
CHROMA_COLLECTION_PROFESIONAL=aiip_profesional

# Supabase
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=[key]
SUPABASE_SERVICE_KEY=[key]

# RAG
RAG_TOP_K=5
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=50
```

---

## 11. Diagramas de arquitectura

### 11.1. Arquitectura de datos

```mermaid
erDiagram
    USERS ||--|| PROFILES : has
    PROFILES ||--o{ CONVERSATIONS : starts
    CONVERSATIONS ||--o{ MESSAGES : contains

    PROFILES {
        uuid id PK
        text role
        integer patient_age
        text idp_type
        text context
    }

    CONVERSATIONS {
        uuid id PK
        uuid user_id FK
        text summary
        timestamptz started_at
    }

    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        text role
        text content
        jsonb sources
        timestamptz created_at
    }
```

### 11.2. Separación de perfiles

```mermaid
graph LR
    URL_F[fa:fa-link aiip.app/familiar] --> AUTH_F[Supabase Auth\nrol: familiar]
    URL_P[fa:fa-link aiip.app/profesional] --> AUTH_P[Supabase Auth\nrol: profesional]

    AUTH_F --> SP_F[System prompt\nfamiliar]
    AUTH_P --> SP_P[System prompt\nprofesional]

    SP_F --> KB_F[(ChromaDB\ncolección familiar)]
    SP_P --> KB_P[(ChromaDB\ncolección profesional)]

    KB_F --> LLM[Gemini Flash]
    KB_P --> LLM
```

---

## 12. Checklist CHART (anexo)

CHART (Chatbot Assessment Reporting Tool, 2025) — guía de reporte para estudios de chatbots de consejo sanitario. Ítems clave aplicados al AIIP:

| Ítem CHART | Referencia en este documento |
|---|---|
| 3a — Nombre, versión y fecha del modelo | Sección 1 (stack) — Gemini Flash, Google API |
| 5b — Prompts del sistema | Sección 5 (system prompt) + `prompts/` |
| 6b — Fecha y lugar de las consultas | Documentado en `docs/evaluation.md` |
| 6c — Parámetros de inferencia (temperatura, seed) | Sección 4 |
| 9a — Métodos de análisis y reproducibilidad | `docs/evaluation.md` |
| 12e — Repositorio de código y parámetros | Este repositorio |

Ver checklist completo en `docs/evaluation.md`.

---

## 13. Decisiones técnicas pendientes

Las siguientes decisiones están identificadas pero requieren el inicio del desarrollo para cerrarse:

| ID | Decisión | Cuándo |
|---|---|---|
| D-013 | Diseño definitivo del system prompt (versión familiar) | Al arrancar E-02 (Pipeline RAG) |
| D-014 | Configuración definitiva de colecciones ChromaDB | Al arrancar E-04 (Ingesta KB) |
| D-015 | Estrategia de chunking validada con primeros resultados RAGAS | Tras primera evaluación |

---

*tech-spec.md v1.0 — junio 2026*
