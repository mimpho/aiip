# Cierre — E-11 T-04: Hallazgo E, revisión cualitativa del registro lingüístico

| Campo | Valor |
|---|---|
| Épica | E-11 — Mejora de calidad post-E-09 |
| Tarea | T-04 — Hallazgo E: revisión cualitativa del registro lingüístico |
| Fecha | 19 de julio de 2026 |
| Fuentes | `tests/eval/results/e11_t04_transcripcion.json` (transcripción íntegra), `scripts/run_e11_t04_linguistic_review.py` |
| Modelo evaluado | `gemini-2.5-flash` (producción, D-043), perfil familiar (`prompts/system_prompt_family.txt`) |
| Decisiones de referencia | D-002 (Falso Negativo Cero), D-056 (hallazgo E quedó fuera del ciclo de mejora de E-09), D-065 (tipo de tarea sin TDD) |

## 1. Muestra y método

7 preguntas dirigidas contra `RAGPipeline.query()` real (producción, `apply_safety_filter`
interno), cubriendo los dos temas ya identificados en el hallazgo original
(`backlog/ideas.md`, hallazgo #3, 8 jul 2026) más 4 temas adicionales con vocabulario clínico
denso detectados al revisar `data/raw/aedip/` (cribado neonatal, hipogammaglobulinemia,
diagnóstico inmunológico, clasificación de IDP):

| ID | Tema | Pregunta |
|---|---|---|
| `ling_01` | Trasplante de médula (progenitores hematopoyéticos) | ¿En qué consiste el trasplante de médula ósea para tratar una inmunodeficiencia primaria? |
| `ling_02` | Acondicionamiento pre-trasplante | ¿Qué implica el proceso de acondicionamiento antes de un trasplante de médula y cómo afecta a las defensas del niño mientras se recupera? |
| `ling_03` | Inmunoglobulinas | ¿Cómo actúa el tratamiento con inmunoglobulinas para proteger frente a infecciones? |
| `ling_04` | Diagnóstico inmunológico | ¿Qué pruebas de laboratorio se utilizan para diagnosticar una inmunodeficiencia primaria? |
| `ling_05` | Cribado neonatal | ¿En qué consiste el cribado neonatal para detectar una inmunodeficiencia combinada grave nada más nacer? |
| `ling_06` | Hipogammaglobulinemia | ¿Qué es la hipogammaglobulinemia y qué relación tiene con las inmunodeficiencias primarias? |
| `ling_07` | Clasificación de IDP | ¿Cómo se clasifican los distintos tipos de inmunodeficiencias primarias? |

## 2. Hallazgos por caso (términos citados junto a la respuesta donde aparecen)

### `ling_01` — Trasplante de médula: mayormente accesible, dos términos sueltos sin glosa

La respuesta explica bien la mayoría de conceptos con analogías (p. ej. "régimen de
acondicionamiento" se presenta como "hacer sitio" para las nuevas células antes de nombrar el
término técnico). Dos términos quedan sin explicar:

> "El trasplante busca corregir el sistema inmunitario defectuoso del paciente,
> reemplazándolo por uno normal que pueda producir **linfocitos funcionales**."

> "las células madre del donante se administran al paciente a través de una **vía central**,
> de forma similar a una transfusión de sangre."

"Linfocitos" no se define en ningún punto de la respuesta (a diferencia de `ling_05`, donde sí
se glosa como "un tipo de glóbulos blancos"). "Vía central" tampoco se explica (es un
dispositivo médico, no evidente para un familiar sin formación).

### `ling_02` — Acondicionamiento pre-trasplante: reproduce el hallazgo original

Este es el mismo tema exacto señalado en `backlog/ideas.md` (hallazgo #3). La respuesta usa
una buena analogía inicial ("malas hierbas" / "herbicida" para explicar el acondicionamiento),
pero al detallar el régimen concreto vuelca nombres de fármacos y términos farmacológicos sin
ninguna glosa:

> "Algunos de los medicamentos comunes son **busulfán, fludarabina, melfalán, ciclofosfamida y
> tiotepa**, aunque se pueden usar otros."

> "**Seroterapia:** Son terapias con anticuerpos, a menudo **anticuerpos monoclonales**, que
> son tóxicos para las células del sistema inmunitario... Algunos ejemplos son **alemtuzumab y
> globulina antitimocítica**."

> "para prevenir una complicación llamada **enfermedad de injerto contra huésped (EICH)**."

Los cinco nombres de fármacos y los dos nombres de fármaco biológico se citan tal cual constan
en la fuente (`manual-para-pacientes-y-familias...pdf`), sin ningún matiz de "estos son
ejemplos, tu equipo médico decidirá cuál aplica" ni explicación de qué hace cada tipo de
fármaco. El acrónimo EICH se nombra pero solo se explica de forma parcial (qué le pasa al
paciente, no qué lo causa). Es el caso con más densidad de tecnicismos sin explicar de toda la
muestra.

### `ling_03` — Inmunoglobulinas: accesible, sin hallazgos

Respuesta breve y bien glosada ("terapia de reemplazo de inmunoglobulina" se explica en la
misma frase: "proporcionar al cuerpo estas proteínas que le faltan"). No se marcan términos
problemáticos.

### `ling_04` — Diagnóstico inmunológico: varios tecnicismos densos sin glosa

La pregunta pide explícitamente "qué pruebas de laboratorio se utilizan", lo que invita a una
respuesta más técnica por naturaleza. Aun así, varios términos quedan completamente opacos
para un familiar sin formación médica, sin ningún intento de explicación:

> "**Valoración del compartimento de memoria de células B:** Se realiza mediante
> **inmunofenotipo linfocitario por citometría de flujo** en centros especializados."

> "también se debe solicitar un **estudio del complemento (C3, C4 y CH50)**."

> "se buscan inmunodeficiencias que afecten a las **células Th17**."

> "las pruebas se centran en la enfermedad granulomatosa crónica (EGC) y la **deficiencia de
> adhesión leucocitaria (LAD)**."

Por contraste, la propia respuesta sí glosa bien otros términos igual de técnicos en el mismo
párrafo ("linfopenia (cifras bajas de linfocitos)", "neutropenia" definida justo después de
nombrarla) — la inconsistencia no es "toda la respuesta es técnica", sino que unos términos se
explican y otros, igual de opacos, no.

### `ling_05` — Cribado neonatal: accesible, buen ejemplo de glosa en el momento

> "detectar a los bebés que podrían tener un número muy bajo de un tipo de glóbulos blancos
> llamados **'linfocitos T'**."

> "se utiliza una prueba llamada **ensayo TREC**, que mide la cantidad de células T en la
> sangre del recién nacido."

Cada término técnico se introduce con una glosa inmediata en la misma frase. No se marcan
hallazgos.

### `ling_06` — Hipogammaglobulinemia: accesible, un término menor sin glosa

Respuesta clara en general (el propio término del título se define en la primera frase). Un
término secundario queda sin explicar:

> "las personas con hipogammaglobulinemia también pueden presentar **fenómenos autoinmunes**
> y tumores con mayor frecuencia."

Hallazgo menor, no comparable en densidad a `ling_02`/`ling_04`.

### `ling_07` — Clasificación de IDP: listado de síndromes y jerga sin glosa

La pregunta pide explícitamente una clasificación, lo que invita a listar categorías — pero la
respuesta reproduce nombres de síndromes y mecanismos inmunológicos directamente de la fuente,
sin ninguna explicación:

> "**Defectos de la apoptosis linfocitaria.**"

> "**Defectos de la respuesta innata:** Por ejemplo, los defectos de la **vía del
> IFNγ-IL12**."

> "Como el Síndrome de Wiskott-Aldrich o el Síndrome de Hiper IgE... Incluye la Enfermedad
> Granulomatosa Crónica y la Neutropenia congénita... Como la Ataxia-telangiectasia... Un
> ejemplo es el Edema Angioneurótico Familiar."

Ninguno de estos nombres de síndrome se acompaña de una descripción, ni siquiera breve, de qué
implica para la familia — quedan como una lista de nombres propios sin contexto.

## 3. Lectura agregada

El patrón **no es "toda respuesta técnica es inaccesible"**: 4 de los 7 casos (`ling_01`
salvo dos términos, `ling_03`, `ling_05`, `ling_06`) muestran que el modelo, cuando explica un
mecanismo o proceso, sí es capaz de generar analogías y glosas accesibles en el momento
(p. ej. "malas hierbas" para acondicionamiento, "glóbulos blancos llamados 'linfocitos T'"
para cribado neonatal). El problema es más específico: **cuando la respuesta debe enumerar
nombres concretos** — fármacos, acrónimos de pruebas de laboratorio, nombres de síndromes —,
el modelo tiende a reproducirlos tal cual aparecen en la fuente, sin ninguna glosa ni matiz,
incluso en respuestas que en otros párrafos sí explican términos igual de técnicos. Este
patrón aparece en 3 de los 7 casos (`ling_02`, `ling_04`, `ling_07`), y **`ling_02` reproduce
exactamente el tema del hallazgo original** (acondicionamiento pre-trasplante,
`backlog/ideas.md` hallazgo #3) con el ejemplo más denso de toda la muestra (7 nombres de
fármaco/anticuerpo sin explicar en una sola respuesta).

No se observa ninguna dilución del contenido de seguridad en ninguno de los 7 casos: todas las
respuestas mantienen el cierre obligatorio de redirección a consulta médica y ninguna ofrece
diagnóstico ni recomendación terapéutica propia (D-002 no está en riesgo aquí — el hallazgo es
puramente de registro/comprensibilidad).

## 4. Decisión propuesta

**Ajustar la instrucción de tono** (`[TONO — PERFIL FAMILIAR]` en
`prompts/system_prompt_family.txt`). Razones:

- El patrón es específico y describible (listas de nombres de fármacos/acrónimos/síndromes
  sin glosa), no un problema difuso de "el modelo es técnico en general" — el propio modelo ya
  demuestra saber glosar términos igual de técnicos en otros pasajes de las mismas respuestas.
- Reproduce el tema exacto del hallazgo original (`ling_02`, acondicionamiento), con el caso
  más denso de la muestra.
- Aparece en 3 de 7 temas dirigidos (43%), no es un caso aislado y puntual — no encaja bien en
  "backlog abierto".

Propuesta de dirección para el refuerzo (a concretar y aprobar en Cowork, Bloque 2): añadir a
`[TONO — PERFIL FAMILIAR]` una instrucción específica para cuando la respuesta deba nombrar
fármacos concretos, acrónimos de pruebas o nombres de síndromes — exigir una glosa breve en el
momento (mismo patrón que ya usa el modelo espontáneamente en `ling_01`/`ling_05`, p. ej.
"linfocitos T" → "un tipo de glóbulos blancos") o, cuando el detalle no aporte valor
comprensible sin formación médica, indicar explícitamente que esa lista de opciones concretas
la decide el equipo médico caso por caso. El refuerzo debe simplificar vocabulario, no diluir
contenido de seguridad (D-002) — no toca `[RESTRICCIONES ABSOLUTAS]` ni `[CIERRE OBLIGATORIO]`.

## 5. Bloque 2 — redacción y aplicación

Redacción propuesta por el agente en Cowork y aprobada tal cual por Marcos (19 jul 2026), sin
ajustes. Añadida a `[TONO — PERFIL FAMILIAR]` en `prompts/system_prompt_family.txt`, a
continuación del párrafo existente sobre destinatario (paciente/familiar), sin tocar
`[RESTRICCIONES ABSOLUTAS]` ni `[CIERRE OBLIGATORIO]`:

> Cuando la respuesta deba nombrar fármacos concretos, acrónimos de pruebas diagnósticas o
> nombres de síndromes o enfermedades, acompaña cada uno de una glosa breve en el momento
> (p. ej. "linfocitos T" → "un tipo de glóbulos blancos"), igual que ya haces con otros
> conceptos técnicos. Si el detalle no aporta valor sin formación médica, indica que la
> elección concreta la decide el equipo médico caso por caso, en vez de enumerar la lista sin
> explicación.

Decisión registrada en D-067 (`decisions.md`).

## 6. Confirmación

Confirmado por Marcos (19 jul 2026): el hallazgo E queda cerrado con el ajuste de tono
aplicado tal como está documentado en este informe.
