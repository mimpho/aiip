# Plan — E-09 T-01 Ampliación del dataset de evaluación a cobertura completa

## Contexto técnico

- **Contenido ya redactado y verificado en Cowork.** `tests/eval/dataset_partial.json` ya
  tiene los 72 casos (los 42 de E-07 con el campo `category` añadido, más los 30 nuevos
  `eval_43`..`eval_72`: 10 diagnóstico + 10 límite + 5 otro idioma + 5 prompt injection).
  Verificado con un script ad hoc (fuera del repo) contra `rag.safety.check_alarm_signals`
  real: los 15 casos de alarma y los 10 casos límite activan la alarma tal como se espera;
  sin duplicados de `id` ni de `question`. Antigravity **no necesita redactar contenido**,
  solo implementar el schema que lo valide — el trabajo de esta tarea es 100% código.
- **`is_alarm` de `eval_72` es `False` a propósito**, aunque su categoría es
  `prompt_injection` con `expected_safety_trigger: true`. Es un caso en inglés
  ("shortness of breath...") y `check_alarm_signals()` solo compara contra
  `config/alarm_triggers.json`, que está en castellano — el filtro determinista no lo
  detecta. `is_alarm=False` refleja el comportamiento real de la función, no una
  inconsistencia de datos. El propio campo `expected_answer` de esa entrada documenta la
  razón inline. No "arreglar" este valor al implementar — es intencional (D-054,
  relacionado con el hallazgo F de `backlog/ideas.md`).
- **Pydantic ya es dependencia intencional del proyecto** desde D-045 (E-07 T-01),
  `pydantic==2.13.4` — no requiere cambios en `requirements.txt`.
- **Decisión de schema ya tomada en D-054** (ver `decisions.md`): `category` como campo
  obligatorio y autoritativo, `is_alarm` se mantiene por compatibilidad con el código ya
  escrito de E-07 (T-02/T-03 filtran por `is_alarm`), `language` pasa de
  `Literal["es"]` a `Literal["es", "en", "ca"]`, y tres campos opcionales
  (`attack_type`, `expected_behavior`, `expected_safety_trigger`) obligatorios solo
  cuando `category="prompt_injection"`.
- **Coherencia `category` ↔ `is_alarm`:** solo se valida en los dos extremos
  (`category="alarma"` ⇒ `is_alarm=True`; `category="informativo"` ⇒ `is_alarm=False`).
  Para el resto de categorías (`diagnostico`, `limite`, `otro_idioma`, `prompt_injection`)
  no hay ninguna relación forzada — el validador no debe imponer nada ahí (ver caso
  `eval_72` arriba, que sería rechazado por un validador demasiado estricto).
- **No romper `evaluation.dataset.validate_dataset`** tal como lo usan
  `tests/step_defs/test_e07_t01.py` y `tests/features/e07_t03_safety_compliance_baseline.feature`
  (E-07, ya cerrada) — la firma de `load_dataset`/`validate_dataset` no cambia, solo el
  modelo `EvalCase` que usan internamente.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `tests/eval/dataset_partial.json` | ya existe (Cowork) | 72 casos con `category`, ver Contexto técnico |
| `evaluation/dataset.py` | modificar | `EvalCase` ampliado (D-054) + `model_validator` de coherencia |
| `tests/step_defs/test_e09_t01.py` | crear | Step definitions del `.feature` de T-01 |

## Orden de implementación TDD

Sigue `tests/eval/e09_t01_full_eval_dataset.feature`, en este orden:

1. **Conteo total y por categoría del dataset ampliado**
   - Step definitions en: `tests/step_defs/test_e09_t01.py`
   - Implementación en: `evaluation/dataset.py::EvalCase` — añadir
     `category: Literal["informativo", "alarma", "diagnostico", "limite", "otro_idioma", "prompt_injection"]`
     como campo obligatorio.
   - Notas: reutiliza `load_dataset` tal cual (ya devuelve `data["cases"]` como lista de
     dicts); el conteo por categoría se hace sobre las entradas ya cargadas, antes incluso
     de pasar por `EvalCase` — igual que el escenario equivalente de E07-T01.

2. **`is_alarm` es coherente con `category` en todo el dataset**
   - Implementación en: `evaluation/dataset.py::EvalCase` — `model_validator(mode="after")`
     que falla si `category == "alarma" and not is_alarm`, o si
     `category == "informativo" and is_alarm`. No añadir ninguna otra restricción entre
     `category` e `is_alarm` (ver Contexto técnico, caso `eval_72`).

3. **Los casos de prompt injection incluyen los campos de ataque obligatorios**
   - Implementación: añadir a `EvalCase` los campos opcionales
     `attack_type: str | None = None`, `expected_behavior: str | None = None`,
     `expected_safety_trigger: bool | None = None`, más un segundo
     `model_validator(mode="after")` que exige los tres no-`None` cuando
     `category == "prompt_injection"`.

4. **Los casos de otros idiomas están en inglés o catalán, no en castellano**
   - Implementación: cambiar `language: Literal["es"]` a
     `language: Literal["es", "en", "ca"]`. No se necesita lógica adicional — pydantic ya
     rechaza cualquier otro valor por typing.

5. **El validador rechaza una entrada de prompt injection sin `attack_type`**
   - Step definitions: mismo fichero. Construye un dict de entrada `category="prompt_injection"`
     sin `attack_type` y comprueba que `validate_dataset` lanza `ValueError` (mismo patrón
     de captura de `pydantic.ValidationError` que ya usa `validate_dataset`, ver
     `evaluation/dataset.py` actual).

6. **El validador rechaza una entrada con `category` e `is_alarm` incoherentes**
   - Step definitions: mismo fichero. Dict de entrada con `category="alarma"`,
     `is_alarm=False` → debe fallar la validación (escenario 2 en negativo).

7. **No hay preguntas ni identificadores duplicados en el dataset ampliado**
   - Reutiliza la lógica ya existente en `validate_dataset` (comparación de `question`/`id`
     sobre la lista completa de `EvalCase`) — no requiere cambios, solo correr sobre las 72
     entradas en vez de 42.

8. **El subconjunto de seguridad completo queda identificable por category**
   - Step definitions: filtra `dataset_entries` (o los `EvalCase` ya validados) por
     `category in {"alarma", "diagnostico", "limite", "prompt_injection"}` y comprueba que
     da 40. No requiere código nuevo en `evaluation/dataset.py` — es una selección que hace
     el propio test/step_def, no una función de la librería (ninguna otra tarea de la
     épica necesita una función reutilizable para esto, se resuelve con una list
     comprehension en el step).

9. **Marcos revisa y aprueba el contenido de los 30 casos nuevos**
   - No es un escenario con asserts — déjalo en el `.feature` como recordatorio, pero no
     escribas step definition para él (mismo tratamiento que el escenario equivalente de
     E07-T01, que tampoco tiene asserts automatizados para la revisión de Marcos).

## Restricciones a respetar

- **Falso Negativo Cero:** no aplica directamente al código de validación de schema, pero
  si al revisar el contenido ya redactado (Contexto técnico) detectas algún
  `expected_answer` que suene a confirmación de seguridad en vez de derivar a consulta
  médica, avísalo — no lo corrijas tú mismo, es contenido ya revisado en Cowork.
- **Privacy by design:** las 30 preguntas nuevas son sintéticas, sin datos identificables
  de pacientes reales.
- **D-010 (agnóstico de proveedor):** no aplica, esta tarea no toca ningún LLM.

## Lo que queda fuera de esta tarea

- Ejecutar el pipeline RAG o RAGAS contra las preguntas del dataset (T-02, T-03, T-04).
- Redactar o revisar el contenido clínico de los 30 casos nuevos (ya hecho en Cowork,
  pendiente solo de la revisión final de Marcos y de la validación clínica no bloqueante
  del inmunólogo).
- Cualquier ajuste a `rag/safety.py` o `rag/language.py` (hallazgos A/F) — eso es T-05.
- Corregir las inconsistencias numéricas de `docs/evaluation.md` (65→72, 30→40) — eso es
  T-06.
