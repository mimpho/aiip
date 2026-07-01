# Plan — E-04 T-03 Detección de idioma e integración en pipeline

## Contexto técnico

**Decisión D-017 (nueva, ver `decisions.md`):**
- `langdetect` no es determinista sin fijar semilla. `rag/language.py` fija `DetectorFactory.seed = 0` una sola vez a nivel de módulo (al importar).
- El fallback para texto corto **no** puede basarse en `try/except LangDetectException` ni en el score de `detect_langs()` — confirmado en pruebas: `detect("ok")` no lanza excepción (devuelve `"sk"`), y `detect_langs("hola")` da confianza >0.999 aun detectando mal (galés). La única señal fiable es un umbral de longitud: `MIN_LENGTH_FOR_DETECTION = 10` caracteres (tras `.strip()`). Por debajo, se devuelve el idioma por defecto (`"es"`) sin invocar a `langdetect`.
- `LangDetectException` sigue puede darse con textos de 10+ caracteres sin contenido detectable (símbolos, números). `detect_language()` debe capturarla igualmente como red de seguridad adicional al chequeo de longitud, y devolver el default en ese caso.
- Instrucción de idioma en el prompt: nombres explícitos solo para `es`/`en`/`ca` (idiomas de lanzamiento, D-011). Cualquier otro código usa una instrucción genérica basada en el código ISO, sin diccionario adicional.

**Dependencias:** `langdetect==1.0.9` ya está en `requirements.txt` (añadida en T-01). No se necesita ninguna dependencia nueva.

**Alcance de "integración en pipeline":** igual que estableció D-016 para el retriever en T-02, la integración real dentro de `rag/pipeline.py` queda fuera de esta tarea — es T-06. Los 5 escenarios de `e04_t03_language_detection.feature` prueban `rag/language.py` de forma aislada, sin tocar `rag/pipeline.py` (que sigue siendo stub).

**Módulo nuevo:** `rag/language.py` no tenía stub de T-01 (a diferencia de `embeddings.py`, `retriever.py`, `generator.py`, `safety.py`, `pipeline.py`). Se crea directamente con implementación completa en esta tarea, sin fase de stub previa.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `rag/language.py` | crear | `detect_language(text, default="es")` y `build_language_instruction(language)` — fija `DetectorFactory.seed = 0` al importar |
| `tests/step_defs/test_e04_t03.py` | crear | Step definitions pytest-bdd para `e04_t03_language_detection.feature` |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **Detección de castellano** — `tests/features/e04_t03_language_detection.feature`
   - Step definitions en: `tests/step_defs/test_e04_t03.py`
   - Implementación en: `rag/language.py`
   - Notas: crear `detect_language(text: str, default: str = "es") -> str`. Fijar `DetectorFactory.seed = 0` a nivel de módulo antes de cualquier llamada a `detect()`. Para este escenario basta con delegar directamente en `langdetect.detect()`.

2. **Detección de inglés** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e04_t03.py`
   - Implementación en: `rag/language.py`
   - Notas: sin cambios de implementación si el escenario 1 ya generaliza correctamente — mismo camino de código.

3. **Detección de catalán** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e04_t03.py`
   - Implementación en: `rag/language.py`
   - Notas: verificado en pruebas manuales que `langdetect` reconoce `"ca"` de forma fiable con semilla fija sobre frases de longitud normal. Sin lógica adicional.

4. **Fallback a castellano cuando la detección falla** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e04_t03.py`
   - Implementación en: `rag/language.py`
   - Notas: implementar el chequeo `len(text.strip()) < MIN_LENGTH_FOR_DETECTION` (constante = 10) **antes** de llamar a `detect()` — devuelve `default` directamente. Envolver además la llamada a `detect()` en `try/except LangDetectException` como red de seguridad para textos más largos pero sin contenido detectable (símbolos, números). Verificar que no se propaga ninguna excepción en ningún caso.

5. **Instrucción de idioma incluida en el prompt** — mismo `.feature`
   - Step definitions en: `tests/step_defs/test_e04_t03.py`
   - Implementación en: `rag/language.py`
   - Notas: crear `build_language_instruction(language: str) -> str`. Diccionario interno `{"es": "castellano", "en": "inglés", "ca": "catalán"}` para los tres idiomas de lanzamiento (D-011); para cualquier otro código, generar instrucción genérica con el código ISO (p. ej. `f"Responde siempre en el idioma con código '{language}'."`). El test verifica que, para `language="es"`, el string devuelto contiene la instrucción de responder en castellano — no se prueba la construcción del system prompt completo (eso es T-04/T-05).

## Restricciones a respetar

- **D-011 (multiidioma):** castellano como default; no introducir lógica de traducción — la detección es la única responsabilidad de este módulo.
- **D-017 (esta tarea):** semilla fija de `langdetect`, umbral de longitud de 10 caracteres, sin diccionario ampliado de nombres de idioma más allá de es/en/ca.
- **Configuración:** si en el futuro se quiere hacer configurable `MIN_LENGTH_FOR_DETECTION` o el idioma default, debe ir a `rag/config.py` / `.env.example` — por ahora son constantes de módulo, no hay necesidad expresada de configurarlas por entorno.

## Lo que queda fuera de esta tarea

- Integración real en `rag/pipeline.py` (orquestación end-to-end) — eso es T-06, mismo patrón que D-016 fijó para el retriever en T-02.
- Construcción del system prompt completo (`prompts/system_prompt_familiar.txt`) — eso es T-04/T-05.
- Selector explícito de idioma en interfaz — evolución futura fuera de Fase 1 (D-011).
- Ampliación de nombres de idioma más allá de es/en/ca en la instrucción del prompt.
