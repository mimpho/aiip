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

7. **Confirmación de cierre** (Marcos): revisar los pasos 1-6 y decidir si el lote 3 queda
   cerrado o si hace falta una ronda adicional antes de pasar a T-04 (remedición RAGAS +
   cierre de E-13, con las 40 fichas nuevas ya indexadas).

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
