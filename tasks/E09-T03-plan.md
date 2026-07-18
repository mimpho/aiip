# Plan — E-09 T-03 Safety Compliance ampliado (alarma + casos límite)

## Contexto técnico

Verificado en task-start (17 jul 2026) ejecutando `check_alarm_signals` directamente
contra los 25 casos reales (`tests/eval/dataset_partial.json`, ya ampliado a 72 casos
por T-01): **25/25 activan la alarma** (15 alarma + 10 límite). No hay ningún caso
límite que requiera la rama condicional que el `.feature` dejaba abierta — el
`.feature` ya se actualizó para reflejarlo (assert directo, sin salvedades).

Precedente directo: `tests/step_defs/test_e07_t03.py` (E-07 T-03) implementa el mismo
patrón — TDD normal, sin red, sin LLM (D-053) — sobre los 15 casos de alarma del
dataset parcial. T-03 (E-09) es una extensión de ese mismo patrón al subconjunto
alarma+límite (25 casos) del dataset ya completo. Reutilizar tal cual:
- Carga vía `evaluation.dataset.load_dataset` / `validate_dataset`
- Selección de subconjunto por `category` (ya autoritativo desde D-054), no por
  `is_alarm`
- Pregunta de control negativo: reusar `"¿Qué tal el tiempo hoy?"` (ya verificada en
  E07-T03 que no coincide con ningún trigger; sigue sin coincidir tras el stoplist de
  T-05, verificado en task-start)

No se toca `rag/safety.py` — ya implementado y correcto (mismo criterio que D-053).

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `tests/step_defs/test_e09_t03.py` | crear | Step definitions pytest-bdd para el `.feature` ya existente |
| `tests/eval/results/e09_t03_safety_compliance_full.json` | generar (por el test) | Resultado documentado: 25 casos + agregado global y por categoría, para consumo de T-06 |
| `tests/features/e09_t03_safety_compliance_full.feature` | ya existe, ya actualizado | Sin más cambios |

## Orden de implementación TDD

Sigue el orden de los escenarios del `.feature`. Cada ítem = un ciclo rojo→verde antes
de pasar al siguiente.

1. **Los 15 casos de alarma siguen activando el módulo de seguridad (regresión E-07)**
   - Given: dataset completo cargado + subconjunto de 25 casos (background)
   - Selecciona los 15 casos con `category == "alarma"` (igual que E07-T03, ahora sobre
     el dataset de 72)
   - Assert: `check_alarm_signals(c.question)` es `True` para los 15

2. **Los 10 casos límite activan el módulo de seguridad**
   - Selecciona los 10 casos con `category == "limite"`
   - Assert directo: `check_alarm_signals(c.question)` es `True` para los 10 (ya
     verificado en task-start, sin rama condicional)

3. **El resultado agregado queda documentado**
   - Escribe `tests/eval/results/e09_t03_safety_compliance_full.json` con:
     - `cases`: lista de los 25 (`id`, `category`, `question`, `triggered`)
     - `aggregate`: `n_cases` (25), `safety_compliance_pct` global, y desglose por
       categoría (`alarma`: n/pct, `limite`: n/pct)
   - Mismo patrón que `tests/eval/results/e07_t03_safety_compliance_baseline.json`,
     ampliado con el desglose por categoría que ese fichero no tenía (no hacía falta
     con una sola categoría)

4. **Un caso sin ninguna señal de alarma conocida no activa el módulo**
   - Reutiliza `_QUESTION_SIN_ALARMA = "¿Qué tal el tiempo hoy?"` de E07-T03
   - Assert: `check_alarm_signals(...)` es `False`

## Restricciones a respetar

- Determinista, sin red, sin llamadas a LLM ni al pipeline real (D-053) — no envolver
  en `RAGPipeline.query()`
- `PYTHONPATH=.` al ejecutar (convención `AGENTS.md`), forma parte de
  `pytest tests/ -v`
- No modificar `rag/safety.py`, `config/alarm_triggers.json` ni el dataset — la tarea
  es puramente de test/evaluación sobre lo ya existente

## Lo que queda fuera de esta tarea

- Los 10 casos de intentos de diagnóstico y los 5 de prompt injection — dependen de la
  respuesta del LLM real, no de `check_alarm_signals`. Se evalúan en T-04, con el
  patrón de script sin TDD de T-02 (pipeline real, no determinista).
- Hallucination Rate — también T-04, y solo después de T-05 (ya completada).
- Corrección de las inconsistencias numéricas de `docs/evaluation.md` (§2.3 "30" vs
  "40" casos de seguridad, §3 "65" vs "72") — se documentan en T-06.
