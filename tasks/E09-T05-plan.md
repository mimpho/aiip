# Plan — E-09 T-05 Ciclo de mejora (hallazgos A, B, D, F)

## Contexto técnico

**Decisiones ya tomadas (Cowork, `task-start`):** ver D-056 (reordenamiento y ampliación
de alcance a A, B, D, F; criterio de cierre con re-medición) y D-057 (solución técnica por
hallazgo, con investigación empírica documentada — no repetirla en Antigravity, ya está
validada contra el dataset real).

**A — stoplist y contexto (validado contra los 27 casos reales de alarma/límite + 27
informativos, sin regresiones):**
- Stoplist de 3 palabras sin señal de alarma por sí solas: `"después"`, `"varios"`,
  `"infusión"`. Van como constante en `rag/safety.py` (mismo patrón que
  `REASSURING_PHRASES`, ya existente en el fichero) — no en `config/alarm_triggers.json`,
  porque no son propiedad de un trigger concreto sino de la función de matching en general.
- `requires_context` es distinto: sí es propiedad de un trigger concreto (`trigger_29`,
  `trigger_34`, ambos sobre "antibióticos"). Va como campo opcional en cada objeto de
  `config/alarm_triggers.json`: `"requires_context": ["mes", "meses", "año", "vena"]`.
  Si el trigger no tiene el campo, no se exige contexto adicional (comportamiento actual
  sin cambios).
- Algoritmo en `check_alarm_signals`: intersección de keywords (≥6 caracteres) menos la
  stoplist, igual que ahora; si la intersección resultante es exactamente el conjunto de
  keywords de un trigger con `requires_context` y ninguna palabra de `requires_context`
  aparece en la query, ese trigger no cuenta como match (se sigue comprobando el resto).

**D — EnsembleRetriever, no Chroma nativo (confirmado por investigación, D-057):**
El `Search()`/hybrid search nativo de Chroma es exclusivo de Chroma Cloud
(`docs.trychroma.com/cloud/search-api/overview`: *"Search API is available in Chroma
Cloud only. Future support on single-node Chroma is planned."*). El proyecto usa Chroma
local persistente — esa vía no es viable sin migrar de infraestructura, fuera de alcance.

Research pendiente de confirmar en Antigravity (no verificable desde el sandbox de
Cowork, sin venv):
- Import de `BM25Retriever`: `from langchain_community.retrievers import BM25Retriever`
  (confirmado por documentación oficial de LangChain). Requiere el paquete `rank_bm25`.
- Import de `EnsembleRetriever`: la referencia más reciente encontrada es
  `from langchain.retrievers import EnsembleRetriever`, pero hay indicios de que en
  versiones recientes de LangChain (el proyecto usa `langchain==1.3.11`) parte de los
  retrievers "clásicos" se reorganizó bajo un paquete `langchain_classic`. Confirmar el
  import exacto al implementar; si `langchain.retrievers.EnsembleRetriever` no resuelve,
  probar `langchain_classic.retrievers.EnsembleRetriever`.
- `EnsembleRetriever(retrievers=[bm25_retriever, vector_retriever], weights=[w_bm25, w_vec])`,
  fusión por Reciprocal Rank Fusion. Punto de partida: `weights=[0.4, 0.6]` (40% BM25 /
  60% vectorial) — ajustar contra Context Precision/Recall en la re-medición, no es un
  valor cerrado.
- El corpus para `BM25Retriever` se construye desde los documentos ya indexados en
  Chroma: `vectorstore.get(include=["documents", "metadatas"])`, envueltos en
  `Document(page_content=..., metadata=...)`, vía `BM25Retriever.from_documents(docs)`.
  No hace falta releer `data/raw/` ni tocar `ingestion/`.
- El retriever vectorial se obtiene con `Chroma.as_retriever(search_kwargs={"k": top_k})`
  sobre el vectorstore ya construido por `get_retriever()` — sin cambios en esa función.

**F — lingua-py (validado por documentación oficial del proyecto, D-057):**
`lingua-language-detector` (PyPI), import `from lingua import Language, LanguageDetectorBuilder`.
Construir el detector una vez a nivel de módulo (mismo patrón que `DetectorFactory.seed = 0`
actual), restringido a los 3 idiomas del proyecto:
```python
_detector = LanguageDetectorBuilder.from_languages(
    Language.SPANISH, Language.ENGLISH, Language.CATALAN
).build()
```
`detect_language()` mantiene la misma firma pública (`text: str, default: str = "es") -> str`)
— internamente usa `_detector.detect_language_of(text)` y mapea el resultado a los códigos
ISO 639-1 ya usados (`"es"`, `"en"`, `"ca"`) vía `language.iso_code_639_1.name.lower()`.
Si `detect_language_of` devuelve `None` (texto ambiguo), se devuelve `default`, igual que
el fallback actual de `MIN_LENGTH_FOR_DETECTION`. Confirmar en Antigravity si
`MIN_LENGTH_FOR_DETECTION` sigue siendo necesario o si lingua-py ya maneja bien el texto
corto sin ese umbral adicional (probarlo contra los 3 casos reales del `.feature` antes de
decidir si se elimina).

**B — Plan B (D-057):** no forma parte del research previo. Se aborda solo si sobra
margen tras A, D y F — ver el escenario dedicado en el `.feature`.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/safety.py` | modificar | Stoplist de matching + soporte de `requires_context` en `check_alarm_signals()` |
| `config/alarm_triggers.json` | modificar | Añadir `requires_context` a `trigger_29` y `trigger_34` |
| `rag/retriever.py` | modificar | Construcción del `BM25Retriever` desde el vectorstore y ensamblado con `EnsembleRetriever` |
| `rag/pipeline.py` | modificar | `retrieve()`/`query()`/`aquery_stream()` usan el retriever híbrido en vez de `similarity_search_with_score()` directo |
| `rag/language.py` | modificar | Sustituir `langdetect` por `lingua-py`, misma firma pública |
| `requirements.txt` | modificar | Quitar `langdetect==1.0.9`, añadir `lingua-language-detector` y `rank_bm25` |
| `tests/step_defs/test_e09_t05.py` | crear | Step definitions de los tres bloques (A, D, F) + Plan B |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **eval_07/08/25 dejan de activar el filtro de seguridad** — `tests/features/e09_t05_ciclo_mejora.feature`
   - Step definitions en: `tests/step_defs/test_e09_t05.py`
   - Implementación en: `rag/safety.py` (stoplist)
   - Notas: cargar los casos reales desde `tests/eval/dataset_partial.json` por `id`
     (`evaluation.dataset.load_dataset`/`validate_dataset`, mismo patrón que
     `tests/step_defs/test_e07_t03.py`), no hardcodear el texto de las preguntas en el
     step def.

2. **"antibióticos" solo dispara con contexto de duración/frecuencia**
   - Implementación en: `rag/safety.py` (`requires_context`) + `config/alarm_triggers.json`
   - Notas: usa eval_08 (sin contexto, no debe activar) y eval_62 (con contexto "año",
     debe seguir activando) — ambos ya en el dataset.

3. **Regresión: ningún caso de alarma/límite real deja de activarse**
   - Notas: filtrar `category in ("alarma", "limite")` más cualquier caso con
     `is_alarm=True` en otra categoría — la investigación de `task-start` encontró 27
     casos con ese filtro (no 25; el número de T-03 en `epics.md` es el subconjunto que
     usará esa tarea específicamente, pero para esta regresión usa el conjunto más amplio
     que ya se validó). Assert: `check_alarm_signals(c.question) is True` para todos.

4. **Retriever híbrido recupera contenido con coincidencia léxica exacta (nombres geográficos)**
   - Implementación en: `rag/retriever.py` (BM25 + EnsembleRetriever), `rag/pipeline.py`
   - Notas: usar una colección de prueba con chunks sintéticos de hospitales en distintas
     ciudades (mismo patrón que `tests/step_defs/test_e04_t02.py`, que ya construye
     colecciones ad-hoc con `add_texts`), no depender de la KB real indexada para el test.

5. **El directorio aedip aparece para preguntas de contacto genéricas**
   - Notas: este escenario sí puede requerir la colección real de producción (`family`) si
     no es viable reproducir el problema con chunks sintéticos — confirmar en Antigravity;
     si depende de la KB real, considerar marcarlo como verificación manual documentada en
     vez de assert automatizado (mismo criterio que D-053 aplicó a T-03: si no es
     reproducible de forma determinista con fixtures, no forzar TDD sobre ello).

6. **Regresión: casos ya bien recuperados no empeoran**
   - Notas: comprobación cualitativa (el contenido sigue siendo relevante), no una
     comparación exacta de scores — los scores cambian de naturaleza al pasar de
     similarity-only a RRF.

7. **Frases cortas de síntomas en español se detectan como español**
   - Implementación en: `rag/language.py` (lingua-py)
   - Notas: los 3 casos ya están en el `.feature` (Scenario Outline). Confirmar si
     `MIN_LENGTH_FOR_DETECTION` se mantiene o se retira (ver nota en "Contexto técnico").

8. **Regresión: frases que ya detectaban bien siguen detectando bien**
   - Notas: las 37 frases de `config/alarm_triggers.json` + la muestra ya validada en
     `tests/features/e04_t03_language_detection.feature`.

9. **Plan B (condicional)** — solo si hay margen tras 1-8
   - Notas: investigación abierta, sin asserts predefinidos — si se aborda, documentar el
     hallazgo (causa raíz o "no diagnosticado") en vez de forzar un test verde.

10. **Cierre: backup de `_RESULTS_PATH` + re-medición completa** — paso operativo, no TDD
    - Notas: sigue el patrón de D-050 (script documentado, sin asserts automáticos, porque
      depende de un LLM evaluador no determinista) — mover o renombrar
      `tests/eval/results/e09_t02_ragas_full_scores.json` antes de relanzar
      `scripts/run_ragas_eval.py`, y documentar el antes/después de las 4 métricas.

## Restricciones a respetar

- **Falso Negativo Cero** (AGENTS.md): el escenario de regresión del punto 3 es la
  comprobación no negociable del ajuste de A. Si un solo caso real deja de activarse, el
  ajuste se descarta o se refina — no se hace merge con esa regresión en rojo.
- **Agnosticismo de proveedor** (D-010): no aplica directamente aquí (no se toca el LLM
  generador), pero `EnsembleRetriever`/`BM25Retriever`/`lingua-py` son dependencias de
  infraestructura, no de proveedor de IA — no generan la deuda técnica que D-010 vigila.
- **Convención de tests** (AGENTS.md): ejecutar siempre con `PYTHONPATH=. pytest tests/ -v`.

## Lo que queda fuera de esta tarea

- Hallazgos **C** (grounding vs. conocimiento de mundo) y **E** (registro lingüístico) —
  quedan en `backlog/ideas.md`, fuera de este ciclo.
- Migración a Chroma Cloud — descartada para el hallazgo D (D-057).
- Selector explícito de idioma en interfaz — alternativa a F ya descartada para el MVP
  (`backlog/ideas.md`).
- T-03 y T-04 — tareas separadas, no dependen de T-05 en su parte determinista (D-056).
- Documentación del informe final (T-06) — solo se referencia el estado de cada hallazgo
  al cerrar T-05, el informe en sí es tarea aparte.
