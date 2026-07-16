# Plan — E-07 T-03 Safety Compliance baseline (15 casos de alarma)

## Contexto técnico

**Decisión ya tomada (Cowork, `task-start`):** D-053. A diferencia de T-02, esta tarea es
TDD normal con asserts (no script sin TDD) porque Safety Compliance, en el alcance de esta
tarea, es 100% determinista: se resuelve con `rag.safety.check_alarm_signals(question)`
(keywords contra `config/alarm_triggers.json`), sin ninguna llamada a LLM. No hace falta
pasar por `RAGPipeline.query()` completo — `apply_safety_filter` añade la derivación en
función de `has_alarm`, con independencia de lo que genere el modelo, así que el resultado
del baseline sería idéntico pasando por el pipeline completo, solo con coste de API
añadido sin señal nueva.

Ya se verificó manualmente (Cowork, sin coste de API) que los 15 casos de alarma del
dataset dan 15/15 = 100% con `check_alarm_signals`. Esto **no** exime de escribir el test:
el valor del test es que quede como regresión permanente en `pytest tests/`, no solo como
verificación puntual.

**Sin hallazgos de research adicionales** — `rag/safety.py` ya existe, ya se usa en
`rag/pipeline.py` y en `scripts/run_ragas_eval.py` (T-02), y su firma es estable:
`check_alarm_signals(query: str, triggers_path: Path = _TRIGGERS_PATH) -> bool`.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `tests/features/e07_t03_safety_compliance_baseline.feature` | ya existe | Creado en `task-start`, define los 3 escenarios |
| `tests/step_defs/test_e07_t03.py` | crear | Step definitions pytest-bdd |
| `tests/eval/results/` | ya existe | Carpeta ya creada en T-02, reutilizar |

No se toca `rag/safety.py` ni ningún módulo de producción — tarea puramente de test/evaluación.

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Todos los casos de alarma activan el módulo de seguridad** —
   `tests/features/e07_t03_safety_compliance_baseline.feature`
   - Step definitions en: `tests/step_defs/test_e07_t03.py`
   - Background: cargar el dataset con `evaluation.dataset.load_dataset("tests/eval/dataset_partial.json")`
     + `evaluation.dataset.validate_dataset(...)` (mismo patrón que `test_e07_t01.py` /
     `scripts/run_ragas_eval.py`), filtrar `case.is_alarm is True` → deben ser exactamente 15
     (ya validado en T-01 que el dataset tiene 15 casos de alarma; no repetir ese assert aquí,
     ya cubierto por `test_e07_t01.py`).
   - When: para cada uno de los 15 casos, llamar a `rag.safety.check_alarm_signals(case.question)`
     y guardar el resultado por caso (`{id, question, triggered}`).
   - Then: `all(r["triggered"] for r in resultados)` — assert simple, sin tolerancia (Falso
     Negativo Cero: un solo caso sin detectar es un fallo, no un dato a documentar y seguir).
   - Then adicional: el agregado (`sum(triggered) / 15 * 100`) es 100.0.

2. **Un caso sin ninguna señal de alarma conocida no activa el módulo** —
   - Given: una pregunta sintética que no comparte ninguna palabra clave (≥6 caracteres) con
     ningún trigger de `config/alarm_triggers.json` (ej. algo genérico tipo "¿qué tal el
     tiempo hoy?" — verificar que efectivamente no solapa keywords antes de fijarla en el
     step, para que el escenario no dé un falso "no detectado" por casualidad léxica).
   - When/Then: `check_alarm_signals(pregunta) is False`.
   - Propósito: probar que el assert del escenario 1 discrimina de verdad (si
     `check_alarm_signals` devolviese siempre `True`, este escenario lo pillaría).

3. **El resultado queda documentado para T-04** —
   - Reutilizar los resultados por caso del escenario 1 (mismo `target_fixture` o recalcular,
     a criterio de Antigravity) y escribir a
     `tests/eval/results/e07_t03_safety_compliance_baseline.json` con esta forma, análoga a
     `e07_t02_ragas_scores.json`:
     ```json
     {
       "cases": [
         {"id": "eval_28", "question": "...", "triggered": true},
         ...
       ],
       "aggregate": {"n_cases": 15, "safety_compliance_pct": 100.0}
     }
     ```
   - Then: el fichero existe, tiene 15 entradas en `cases`, y `aggregate.n_cases == 15`.
   - No hace falta checkpointing (D-051 punto 6): al no haber llamadas de red, el test se
     ejecuta entero en cada corrida sin coste ni riesgo de interrupción a mitad.

## Restricciones a respetar

- **Falso Negativo Cero:** el assert del escenario 1 no debe suavizarse (no convertir en
  "documentar % y seguir" si algún caso fallase) — un caso de alarma no detectado es un
  fallo de test, no un dato de baseline a reportar sin más. Si el test falla, es una señal
  real de que `config/alarm_triggers.json` necesita revisión (fuera de alcance de T-03
  arreglarlo — ver D-019, placeholder pendiente de validación clínica con Jacques).
- **Convención de tests (`AGENTS.md`):** ejecutar con `PYTHONPATH=. pytest tests/ -v`.

## Lo que queda fuera de esta tarea

- Los 3 casos informativos que dispararon la alarma inesperadamente en T-02
  (`unexpected_alarm: true` en `e07_t02_ragas_scores.json`: eval_07, eval_08, eval_25) — no
  son parte del scope de T-03 (que es específicamente los 15 casos de alarma). Quedan
  anotados en D-053 para que T-04 los enlace en el informe, sin acción aquí.
- Los 30 casos completos de Safety Compliance de `docs/evaluation.md` §2.3 (alarmas +
  diagnóstico + casos límite + prompt injection) — el dataset parcial (D-049) solo tiene
  27 informativos + 15 alarma; las categorías de diagnóstico/límite/injection son de
  Fase 1.5 (E-09).
- Validación clínica de `config/alarm_triggers.json` con Jacques Rivière (D-019) — no
  bloquea esta tarea (ver nota de E-09 en memoria de proceso).
- El informe narrativo de resultados — es T-04.
