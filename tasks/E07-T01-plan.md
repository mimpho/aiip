# Plan — E-07 T-01 Dataset de evaluación parcial

## Contexto técnico

- Dataset ya redactado y verificado en `tests/eval/dataset_partial.json` (35 casos: 20
  informativos + 15 de alarma, sin duplicados, schema completo) — ver D-044. Contenido
  todavía marcado `borrador_pendiente_revision_marcos` en el bloque `meta`: Marcos revisa
  el contenido clínico antes de cerrar la tarea, pero la implementación de código no
  depende de ese cambio (el schema no varía).
- Validación con `pydantic` (D-045, revisita D-044). `pydantic` estaba en `requirements.txt`
  solo como dependencia transitiva (arrastrada por `langchain`/Supabase); pasa a ser
  dependencia intencional del proyecto a partir de esta tarea — no requiere cambio de
  versión, ya está pinned (`pydantic==2.13.4`). `ingestion/manifest.py` (patrón previo,
  validación manual con dict + `json`) queda como precedente histórico, no como convención
  a seguir aquí: el schema de E-09 (65 casos, campos opcionales/condicionales) se beneficia
  de un modelo declarativo, y adoptarlo ya evita reescribir `evaluation/dataset.py` más
  adelante.
- No existe distinción de "categoría informativa" como campo explícito en el schema de
  `docs/evaluation.md` — Fase 1 solo tiene dos categorías (informativa / alarma), así que
  `is_alarm: false` ya identifica sin ambigüedad los 20 casos informativos.
- Cada entrada lleva `id` (D-046, corregido por D-047): `eval_01`..`eval_35`, secuencial y
  desacoplado de la categoría. Se descartó el prefijo por categoría (`info_`/`alarm_`)
  porque `is_alarm` es una valoración que puede revisarse (p. ej. al corregir el
  contenido), y encadenar el id a un valor mutable obligaría a renombrarlo si la categoría
  cambia — rompiendo cualquier referencia ya hecha en resultados de T-02/T-03. `is_alarm`
  sigue siendo el único campo que determina la categoría.
- `config/alarm_triggers.json` (E-04, ya cerrada) tenía el mismo acoplamiento id↔categoría
  (`resp_01`, `hemato_01`...) y claves en castellano (`texto`, `categoria`, `fuente`,
  `estado`, `fuentes`, `nota`). D-048 lo corrige fuera del alcance formal de esta tarea,
  aprovechando que se estaba revisando el mismo problema en el dataset de T-01: ids
  secuenciales desacoplados (`trigger_01`..`trigger_37`) y claves en inglés (`text`,
  `category`, `source`; `meta.status`, `meta.sources`, `meta.note`). `rag/safety.py` y
  `tests/step_defs/test_e04_t05.py` ya están actualizados a las claves nuevas —
  **verificado con la suite real** (`PYTHONPATH=. pytest tests/step_defs/test_e04_t05.py -v`,
  ejecutado por Marcos: 7 passed, sin cambios de comportamiento). `tests/eval/dataset_partial.json`
  también pasa `meta.estado`/`meta.nota` a `meta.status`/`meta.note` por la misma razón (los
  campos de cada caso ya estaban en inglés desde el borrador inicial).

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `tests/eval/dataset_partial.json` | ya existe | Dataset de 35 casos (ver Contexto técnico) |
| `evaluation/__init__.py` | crear | Inicializa el paquete `evaluation/` (nuevo, paralelo a `rag/`, `ingestion/`, `auth/`) |
| `evaluation/dataset.py` | crear | `EvalCase` (`BaseModel` de pydantic), `load_dataset(path)` y `validate_dataset(entries)` |
| `tests/step_defs/test_e07_t01.py` | crear | Step definitions del `.feature` |

## Orden de implementación TDD

1. **Conteo total y por categoría del dataset** — `tests/eval/e07_t01_partial_eval_dataset.feature`
   - Step definitions en: `tests/step_defs/test_e07_t01.py`
   - Implementación en: `evaluation/dataset.py::load_dataset(path) -> list[dict]`
   - Notas: `load_dataset` lee el JSON y devuelve `data["cases"]`. El step "contiene
     exactamente 35 entradas" y los conteos de informativas (`is_alarm is False`) / alarma
     (`is_alarm is True`) se verifican directamente sobre la lista cargada, sin lógica
     adicional en `dataset.py` todavía.

2. **Todas las entradas cumplen el schema obligatorio** — mismo `.feature`
   - Step definitions: mismo fichero
   - Implementación en: `evaluation/dataset.py::EvalCase` (`pydantic.BaseModel`) y
     `validate_dataset(entries) -> list[EvalCase]`
   - Notas: `EvalCase` declara `id: str`, `question: str`, `expected_answer: str`,
     `is_alarm: bool`, `profile: Literal["familiar"]`, `language: Literal["es"]`, con
     `model_config = ConfigDict(extra="forbid")` para que la presencia de `relevant_chunks`
     (u otro campo no previsto) haga fallar la validación igual que un campo obligatorio
     ausente. `validate_dataset` construye un `EvalCase` por entrada
     (`EvalCase.model_validate(entry)`); pydantic ya se encarga de tipos y campos
     obligatorios.

3. **No hay preguntas ni identificadores duplicados en el dataset** — mismo `.feature`
   - Implementación en: `evaluation/dataset.py::validate_dataset` — tras construir los
     `EvalCase`, añade dos chequeos sobre la lista ya validada: duplicados exactos de
     `question` (comparación de texto tal cual, sin normalizar mayúsculas/acentos) y
     duplicados de `id`. Ambos son lógica de dataset completo, fuera del modelo de pydantic
     (no son responsabilidad de una entrada individual).

4. **El validador rechaza una entrada con un campo obligatorio ausente** — mismo `.feature`
   - Step definitions: mismo fichero
   - Implementación: ya cubierta por `EvalCase` (punto 2) — este escenario prueba el caso
     negativo con un dict de entrada construido ad hoc en el test (sin `expected_answer`).
     `validate_dataset` debe capturar la `pydantic.ValidationError` resultante y relanzarla
     (o envolverla) de forma que el mensaje identifique el campo `expected_answer` como
     ausente — pydantic ya incluye el nombre del campo en el error, pero conviene verificar
     que el mensaje final sigue siendo legible para quien ejecute los tests.

## Restricciones a respetar

- **Falso Negativo Cero:** no aplica al código de validación de schema en sí (no genera
  respuestas), pero si Marcos, al revisar el contenido del dataset, detecta algún
  `expected_answer` de un caso de alarma que suene a "confirmación de seguridad" en vez de
  derivar a consulta médica, corregirlo es parte del cierre de la tarea, no solo un
  detalle de redacción.
- **Privacy by design:** las 35 preguntas son sintéticas, sin datos identificables de
  pacientes reales — no introducir nombres, edades exactas ni datos que parezcan de un
  caso real al editar el dataset.

## Lo que queda fuera de esta tarea

- Ejecutar el pipeline RAG contra las preguntas del dataset (T-02).
- Añadir el campo `relevant_chunks` (E-09, cuando entren Context Precision/Context Recall).
- Validación clínica del contenido por el inmunólogo (Fase 1.5 / E-09) — la revisión de
  Marcos en esta tarea es un baseline de trabajo, no una validación clínica formal.
- Los otros 30 casos del dataset completo (diagnóstico, casos límite, otros idiomas,
  prompt injection) — quedan para E-09.
