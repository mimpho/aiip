# Plan — E-11 T-04 Hallazgo E: revisión cualitativa del registro lingüístico

## Contexto técnico

Decisiones ya tomadas (Cowork, `task-start`):

- **Tipo de tarea:** sin TDD, revisión cualitativa dirigida (mismo patrón que E07-T04 y
  E11-T03) — no hay pytest-bdd con asserts, `.feature` en formato checklist manual:
  `tests/features/e11_t04_registro_linguistico.feature`.
- **Origen del hallazgo:** `backlog/ideas.md` (hallazgo #3, 8 jul 2026) — detectado en QA
  manual de E-05 T-04, respuestas sobre trasplante de médula usan vocabulario clínico
  ("acondicionamiento", "recuperación del sistema inmunitario") pese a que
  `prompts/system_prompt_family.txt` (sección `[TONO — PERFIL FAMILIAR]`) ya pide lenguaje
  accesible. Quedó fuera del ciclo de mejora de E-09 (D-056).
- **Tamaño de muestra fijado en `task-start`:** 5–8 preguntas dirigidas, cubriendo como
  mínimo los temas ya identificados (trasplante de médula/acondicionamiento,
  inmunoglobulinas) más cualquier tema nuevo con vocabulario denso que aparezca al revisar.
- **Fichero de cierre fijado en `task-start`:** `tests/eval/results/e11_t04_cierre.md`
  (mismo patrón que `e11_t02_cierre.md` / `e11_t03_cierre.md`).

**Sin hallazgos adicionales de research** — no hay firma de librería ni comportamiento de
API externo que investigar; `RAGPipeline.query()` ya se usa tal cual en E-09/E-11 T-03.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `scripts/run_e11_t04_linguistic_review.py` | crear | Ejecuta las 5–8 preguntas dirigidas contra `RAGPipeline.query()` real (perfil familiar) y vuelca pregunta + respuesta completa a un JSON de transcripción |
| `tests/eval/results/e11_t04_transcripcion.json` | generar (por el script) | Transcripción completa de las preguntas y respuestas, para la lectura cualitativa manual |
| `tests/eval/results/e11_t04_cierre.md` | crear (manual, tras la lectura) | Informe de cierre: términos técnicos marcados, contraste contra `[TONO — PERFIL FAMILIAR]`, decisión final (ajustar prompt / backlog abierto / sin cambio) |
| `prompts/system_prompt_family.txt` | modificar (solo si la decisión es "ajustar", y solo tras aprobación explícita de Marcos de la redacción) | Refuerzo puntual de la instrucción de tono, si el hallazgo resulta sistemático |
| `tests/features/e11_t04_registro_linguistico.feature` | ya existe, ya aprobado | Sin más cambios |

## Orden de implementación (sin TDD)

No hay ciclo rojo→verde con pytest-bdd. Esta tarea tiene **un gate de aprobación de Marcos
en medio**, solo si la decisión final implica tocar el system prompt — si la decisión es
"backlog abierto" o "sin cambio", el Bloque 2 no aplica y la tarea cierra en el Bloque 1.

### Bloque 1 — Selección, ejecución y lectura cualitativa

1. **Selección de preguntas** — 5–8 preguntas dirigidas sobre temas con vocabulario clínico
   denso: partir de los ya identificados (trasplante de médula/acondicionamiento,
   inmunoglobulinas) y, si al revisar el dataset (`tests/eval/dataset_partial.json`) o el
   propio KB aparecen otros temas candidatos (ej. procedimientos con nombre técnico,
   terminología inmunológica), añadirlos hasta completar la muestra.

2. **Setup del script `run_e11_t04_linguistic_review.py`** — mismo patrón de `main()` que
   `scripts/run_e09_t04_eval.py` / `run_e11_t03_grounding_investigation.py`:
   `load_rag_config()`, `RAGPipeline(rag_config)`, perfil familiar. Para cada pregunta,
   `pipeline.query(pregunta)` (ya pasa por `apply_safety_filter` internamente — no hace
   falta aplicar nada manualmente, a diferencia de T-03, porque aquí no se genera ninguna
   variante alternativa del prompt).

3. **Volcado** — escribir pregunta + respuesta completa de cada caso a
   `tests/eval/results/e11_t04_transcripcion.json` (transcripción íntegra, no resumida).

4. **Lectura cualitativa manual** — sobre la transcripción, marcar cada término técnico no
   explicado en lenguaje accesible, contrastando contra `[TONO — PERFIL FAMILIAR]` de
   `prompts/system_prompt_family.txt`. Citar el término junto a la respuesta completa donde
   aparece (no solo el veredicto agregado).

5. **Redacción de `tests/eval/results/e11_t04_cierre.md`** — mismo formato de cabecera que
   `e11_t03_cierre.md` (Épica / Tarea / Fecha / Fuentes / Decisiones de referencia), con los
   hallazgos citados y una propuesta de decisión: ajustar la instrucción de tono, dejarlo
   como backlog abierto (si es puntual, no sistemático), o no requiere cambio.

6. **Parada explícita si la propuesta es "ajustar":** el informe no se aplica solo a
   `prompts/system_prompt_family.txt` — Antigravity reporta que el Bloque 1 está listo y
   que la redacción exacta requiere aprobación en Cowork antes de tocar el fichero de
   producción. Si la propuesta es "backlog abierto" o "sin cambio", no hay Bloque 2 y la
   tarea pasa directamente a la revisión final de Marcos (Scenario 5 del `.feature`).

### Bloque 2 — Redacción y aprobación (en Cowork, solo si aplica)

7. El agente (en Cowork) lee `e11_t04_transcripcion.json` y `e11_t04_cierre.md`, propone la
   redacción exacta del refuerzo de tono para `[TONO — PERFIL FAMILIAR]`. Marcos aprueba la
   redacción exacta o pide ajustes (gate — no se continúa sin esto).

8. Tras la aprobación: aplicar el texto aprobado a `prompts/system_prompt_family.txt`
   (edición directa de texto, puede hacerse en Cowork).

## Restricciones a respetar

- **Falso Negativo Cero (D-002):** cualquier refuerzo de tono debe simplificar vocabulario,
  no diluir ni suavizar el contenido de seguridad (alarmas, derivación a consulta médica).
- **Agnosticismo de proveedor (D-010):** el script usa `RAGPipeline`/`RAGGenerator` vía
  `rag_config` tal cual, sin SDK nuevo.
- `PYTHONPATH=.` no aplica — es un script, no pytest.

## Lo que queda fuera de esta tarea

- `eval_15`, `eval_63`, `guia_antibiotics_esp_0.pdf` — T-05 de esta épica.
- Hallucination Rate por bandas de severidad — T-06.
- El informe final consolidado (`docs/evaluation.md`) — T-07.
