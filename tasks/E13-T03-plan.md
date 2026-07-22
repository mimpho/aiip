# Plan — E-13 T-03 Lote 3 MedlinePlus Genetics (10 fichas, 27-36, C→A)

> Tarea de configuración/curación de contenido, sin TDD (mismo patrón que T-01/T-02,
> [[feedback_task_type_no_tdd]]). Este plan existe como excepción a la regla habitual de
> "Paso 4 no aplica a tareas de configuración" — Antigravity arranca esta tarea en una
> conversación nueva, sin memoria de cómo se ejecutaron T-01/T-02 en sesiones anteriores de
> Cowork/Antigravity. Este fichero traduce el `.feature` y las decisiones relevantes en una
> secuencia de comandos ejecutable sin tener que reconstruir contexto.

## Contexto técnico

- Rama activa: `task/E13-T03-data-prep-batch3` (ya creada sobre `epic/E13-medlineplus`
  actualizada).
- `.feature` de referencia: `tests/features/e13_t03_lote3_medlineplus.feature` — checklist de
  verificación manual, sigue `docs/kb-maintenance.md`.
- Script de extracción (D-073, reutilizado sin cambios desde T-01): `scripts/extract_medlineplus_genetics.py`.
  Flags relevantes para esta tarea: `--build-list`, `--extract-batch START END`,
  `--fill-manifest-urls`. Ayuda completa: `python scripts/extract_medlineplus_genetics.py -h`.
- Este sandbox de Cowork no tiene salida de red hacia medlineplus.gov — el `--build-list` de
  abajo es la primera vez que se valida la lista real de las 10 fichas del lote 3 contra los
  datos en vivo. Si el orden alfabético inverso real difiere ligeramente del rango 27-36
  estimado, confía en la salida de `--build-list`, no en el rango a priori.
- Ya extraídas antes de esta tarea (30 ficheros en `data/raw/medlineplus_genetics/`): 13 del
  Lote 1 + 13 del Lote 2 + 4 de revisión (22q11.2/DiGeorge + 3 subtipos de SCID, D-076). El
  lote 3 son las 10 fichas de base restantes — al terminar, el total sube a 40 fichas nuevas
  de E-13 (36 de base en 3 lotes + 4 de revisión).

## Secuencia de comandos (orden exacto)

1. **Validar la lista real del lote** (red disponible en Antigravity, a diferencia de Cowork):
   ```bash
   python scripts/extract_medlineplus_genetics.py --build-list
   ```
   Confirma que las posiciones 27-36 son 10 fichas y anota sus títulos/slugs reales.

2. **Extraer el lote 3**:
   ```bash
   python scripts/extract_medlineplus_genetics.py --extract-batch 27 36
   ```
   Cada fichero nuevo (descripción + genes relacionados + sección "Causes", D-077) se guarda en
   `data/raw/medlineplus_genetics/`.

3. **Reingestar sin huérfanos**:
   ```bash
   python scripts/smoke_test_rag.py --force-reingest
   ```
   Verificar que el resumen impreso no lista la fuente en `failures`.

4. **Rellenar las URLs reales en el manifest**:
   ```bash
   python scripts/extract_medlineplus_genetics.py --fill-manifest-urls
   ```
   Lee la URL de cada ficha desde `<ghr-page>` en `ghr-summaries.xml` (D-073) — no se inventan
   enlaces.

5. **Revisión de registro lingüístico** (manual, Marcos): muestrear 2-3 fichas nuevas en
   `data/raw/medlineplus_genetics/` y confirmar tono accesible para perfil familiar. Cualquier
   ajuste de prompt derivado queda como hallazgo abierto, no se aplica en esta tarea (D-065).

6. **Verificación de `detect_language()` sobre una frase representativa del lote (D-079)** —
   elegir una frase corta y realista sobre una de las 10 fichas nuevas (ej. "que es la
   [nombre de la ficha]", sin tilde, imitando el patrón que expuso D-078) y comprobar margen:
   ```python
   from rag.language import detect_language, _detector, _ISO_CODES

   text = "que es la <nombre de una ficha del lote 3>"
   values = _detector.compute_language_confidence_values(text)
   top, runner_up = values[0], values[1]
   print(detect_language(text), top.language, top.value, runner_up.language, runner_up.value)
   ```
   Confirmar que el idioma detectado es correcto y el margen (`top.value - runner_up.value`)
   es ≥ 0.2. Si algún caso legítimo baja de ese margen, documentarlo como hallazgo abierto
   (no ajustar el umbral en esta tarea — mismo criterio que la actualización de D-078 en T-02).

7. **Fix de encoding + re-extracción retroactiva (añadido 22 jul 2026, hallazgo de la
   revisión de registro lingüístico, D-081):** `fetch_causes_paragraphs()` en
   `scripts/extract_medlineplus_genetics.py` usaba `response.text` (encoding mal adivinado
   por `requests` para caracteres no-ASCII) en vez de `response.content` — mojibake en letras
   griegas y nbsp ("p110δ" → "p110Î´"). Ya corregido en el script (misma sesión de Cowork).
   Re-extraer solo la sección "Causes" de las 4 fichas afectadas y reingestar — mismo patrón
   retroactivo que D-077 aplicó al Lote 1:
   ```bash
   python scripts/extract_medlineplus_genetics.py --extract-one activated-pi3k-delta-syndrome
   python scripts/extract_medlineplus_genetics.py --extract-one adenosine-deaminase-deficiency
   python scripts/extract_medlineplus_genetics.py --extract-one vici-syndrome
   python scripts/extract_medlineplus_genetics.py --extract-one x-linked-hyper-igm-syndrome
   python scripts/smoke_test_rag.py --force-reingest
   ```
   Nota: `vici-syndrome` y `x-linked-hyper-igm-syndrome` son del Lote 1 (T-01, ya cerrada) —
   se corrigen aquí porque es el mismo root cause y el mismo patrón que D-077, no porque T-03
   reabra el alcance de T-01. Verificar tras la re-extracción que ninguno de los 4 ficheros
   contiene ya "Î´", "Î±" ni "Â" sueltos:
   ```bash
   python3 -c "
   import glob
   for f in ['activated-pi3k-delta-syndrome','adenosine-deaminase-deficiency','vici-syndrome','x-linked-hyper-igm-syndrome']:
       text = open(f'data/raw/medlineplus_genetics/{f}.html', encoding='utf-8').read()
       bad = [p for p in ['Î´','Î±','Â'] if p in text]
       print(f, 'OK' if not bad else f'MOJIBAKE: {bad}')
   "
   ```

8. **Fix de `thinking_budget` (añadido 22 jul 2026, hallazgo transversal al revisar el smoke
   test de E-06 T-07, D-082):** el escenario "Cross-lingual real (inglés)" del smoke test
   devolvía un rechazo autocontradictorio ante preguntas reales en inglés. Root cause aislado
   con `tasks/investigacion-cross-lingual-en.py`: `thinking_budget=0` (D-025). Ya corregido en
   `rag/generator.py` (thinking reactivado) + `rag/config.py`/`.env.example`
   (`LLM_MAX_TOKENS` 1024→2048). Afecta a *toda* consulta en producción, no solo a E-13 — antes
   de dar esto por cerrado, repetir el smoke test completo (las 5 preguntas, no solo la rota):
   ```bash
   python scripts/smoke_test_rag.py
   ```
   Revisar en `tests/results/e06_t07_smoke_test_results.md`:
   - Las 5 respuestas son coherentes (sin el rechazo autocontradictorio ni truncamiento del
     tipo que motivó D-025 originalmente).
   - Repetir 2-3 veces la pregunta cross-lingual en inglés para confirmar que ya no reaparece
     (Test 1 de `investigacion-cross-lingual-en.py` la reproducía 5/5 antes del fix).
   - Si reaparece truncamiento (respuesta cortada a media frase) en alguna pregunta, es el
     problema original de D-025 reabierto — no ajustar `LLM_MAX_TOKENS` sin volver a Cowork a
     registrarlo.
   No hay verificación de latencia/coste en esta tarea (nota ya en D-082) — si el thinking
   reactivado resulta notablemente más lento o caro, es un hallazgo a traer a Cowork, no a
   resolver aquí.

   **Mismo comando también verifica D-083** (fix aparte, mismo hallazgo de revisión manual):
   `_run_question()` ahora usa `pipeline.retrieve()` en vez de una búsqueda vectorial pura, para
   que "Chunks recuperados" muestre lo mismo que realmente alimentó la respuesta. Revisar
   además en el mismo `tests/results/e06_t07_smoke_test_results.md`:
   - Para cada pregunta, los ficheros listados en "Fuentes consultadas" están todos contenidos
     en los ficheros de "Chunks recuperados" de esa misma pregunta (antes del fix podían faltar
     hasta el 60% — ver D-083).
   - El score de cada chunk ahora se etiqueta "score posicional" (1/rank), no "similitud" — es
     esperado que los números sean distintos a smoke tests anteriores a este fix.

9. **Confirmación de cierre** (Marcos): revisar los pasos 1-8 y decidir si el lote 3 queda
   cerrado o si hace falta una ronda adicional antes de pasar a T-04 (remedición RAGAS +
   cierre de E-13, con las 40 fichas nuevas ya indexadas, sin mojibake y con los fixes de
   `thinking_budget` (D-082) y de recuperación mostrada en el smoke test (D-083) verificados).

   **Cerrado (22 jul 2026):** Marcos confirma tras revisar el smoke test completo re-lanzado
   (las 5 preguntas, "Fuentes consultadas" = "Chunks recuperados" en las 5, sin rechazo
   cross-lingual ni truncamiento). `tests/results/e06_t07_smoke_test_results.md` actualizado con
   "Revisión manual (Marcos): revisado — correcto" en las 5 entradas. T-03 queda completada.

## Restricciones a respetar

- No usar `--extract-one` en esta tarea (solo para fichas de revisión fuera de lotes, ya
  resueltas en T-01).
- No modificar `ingestion/manifest.py::sync_entry()` ni el comportamiento estándar del
  loader para otras fuentes de la KB (D-073).
- No ajustar `_MIN_CONFIDENCE_MARGIN` en `rag/language.py` aunque el paso 6 revele un margen
  bajo — eso es un hallazgo a documentar, no un cambio de esta tarea.

## Lo que queda fuera de esta tarea

- RAGAS completo (T-04).
- Cerrar `docs/kb-sources.md` de "Propuesta" a "Validada" (T-04).
- Cualquier ajuste de prompt derivado de la revisión de registro lingüístico (hallazgo
  abierto, no esta tarea).
