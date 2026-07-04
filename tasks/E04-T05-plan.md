# Plan — E-04 T-05 Módulo de seguridad: Falso Negativo Cero

## Contexto técnico

Decisión de arquitectura completa en **D-019** (`decisions.md`). Resumen operativo:

- Dos funciones en `rag/safety.py`, sustituyendo el stub `apply_safety_filter`
  de T-01 (que hoy solo tiene `raise NotImplementedError`):
  - `check_alarm_signals(query: str) -> bool` — evalúa la query del usuario
    contra los triggers cargados desde `config/alarm_triggers.json`.
  - `apply_safety_filter(response: str, has_alarm: bool) -> str` — postprocesa
    la respuesta generada por el LLM.
- **Detección:** coincidencia de subcadena/palabra clave, case-insensitive,
  entre la query y el campo `texto` de cada trigger. Sin LLM, sin embeddings
  (D-019). Normalizar tanto la query como los triggers con `.lower()` antes
  de comparar; no hace falta stemming ni tokenización — sustring simple es
  suficiente para los escenarios del `.feature`.
- **Frases tranquilizadoras a interceptar (Scenario "Intercepción..."):** a
  diferencia de los triggers de alarma (contenido clínico, debe vivir en
  `config/alarm_triggers.json`), esta es una lista lingüística genérica, no
  clínica — puede vivir hardcodeada como constante en `rag/safety.py`
  (`REASSURING_PHRASES`). Ejemplo mínimo que cubre el escenario: `"no es
  grave"`, `"no te preocupes"`, `"no es necesario ir al médico"`, `"no hace
  falta consulta"`, `"todo está bien"`. Ampliable sin decisión de arquitectura
  nueva.
- **Ruta del fichero de triggers:** resuelta relativa a la raíz del repo,
  mismo patrón que `rag/generator.py` con el system prompt:
  `Path(__file__).resolve().parent.parent / "config" / "alarm_triggers.json"`.
- **Derivación explícita añadida por el módulo:** cuando `apply_safety_filter`
  decide intervenir (por `has_alarm=True` o por detectar una frase
  tranquilizadora), añade al final de la respuesta una frase fija y
  determinista, por ejemplo:
  `"\n\nAnte esta situación, te recomendamos consultar con tu equipo médico
  cuanto antes."` — el texto exacto es libre para Antigravity siempre que
  contenga literalmente una invitación a "consulta médica" (o equivalente:
  "médico", "especialista"), que es lo que verifican los step defs.

### Contenido completo de `config/alarm_triggers.json`

Contenido definitivo a crear tal cual — no requiere ninguna decisión de
diseño adicional. Combina la fuente primaria (signos de alarma avanzados en
pacientes ya diagnosticados, aportada por Marcos) con la fuente secundaria
(criterios diagnósticos IDP, documento KB en francés, traducido) y las dos
señales de emergencia aguda ya aprobadas en el `.feature` original.

```json
{
  "meta": {
    "estado": "pendiente_validacion_clinica",
    "fuentes": [
      "Signos de Alarma Avanzados en Pacientes Diagnósticos de IDP (aportado por Marcos, 2026-07-04)",
      "Documento KB de señales de alerta IDP (referencia CEREDIH/ESID, francés, secciones chez l'enfant / chez l'adulte)",
      "Señales de emergencia pediátrica estándar (fiebre alta, dificultad respiratoria)"
    ],
    "nota": "Lista placeholder para TDD (D-019). Validar con Jacques Rivière antes de producción."
  },
  "triggers": [
    {"id": "resp_01", "texto": "tos con flema verde, con pus o con sangre desde hace más de tres semanas", "categoria": "respiratorio", "fuente": "signos_avanzados"},
    {"id": "resp_02", "texto": "cansancio o falta de aire al caminar o subir escaleras que antes no le pasaba", "categoria": "respiratorio", "fuente": "signos_avanzados"},
    {"id": "resp_03", "texto": "dolor en el pecho o la espalda al respirar hondo o toser", "categoria": "respiratorio", "fuente": "signos_avanzados"},
    {"id": "resp_04", "texto": "dedos hinchados en la punta o uñas curvadas hacia abajo", "categoria": "respiratorio", "fuente": "signos_avanzados"},
    {"id": "hemato_01", "texto": "manchas rojas o moradas en la piel, o moratones grandes, sin haberse golpeado", "categoria": "hematologia_autoinmunidad", "fuente": "signos_avanzados"},
    {"id": "hemato_02", "texto": "labios o encías muy pálidos con cansancio extremo", "categoria": "hematologia_autoinmunidad", "fuente": "signos_avanzados"},
    {"id": "hemato_03", "texto": "dolor, hinchazón o rigidez en las articulaciones que no mejora", "categoria": "hematologia_autoinmunidad", "fuente": "signos_avanzados"},
    {"id": "hemato_04", "texto": "fiebre que va y viene sin encontrarse ninguna causa", "categoria": "hematologia_autoinmunidad", "fuente": "signos_avanzados"},
    {"id": "neuro_01", "texto": "dolor de cabeza fuerte, sobre todo por la mañana, que despierta por la noche", "categoria": "neurologia", "fuente": "signos_avanzados"},
    {"id": "neuro_02", "texto": "vómitos repentinos sin haber tenido náuseas antes", "categoria": "neurologia", "fuente": "signos_avanzados"},
    {"id": "neuro_03", "texto": "pérdida de memoria o cambios de comportamiento que no son normales en él o ella", "categoria": "neurologia", "fuente": "signos_avanzados"},
    {"id": "neuro_04", "texto": "torpeza al caminar, pérdida de equilibrio o debilidad en brazos o piernas", "categoria": "neurologia", "fuente": "signos_avanzados"},
    {"id": "gastro_01", "texto": "diarrea que dura más de dos semanas", "categoria": "gastrointestinal", "fuente": "signos_avanzados"},
    {"id": "gastro_02", "texto": "heces muy grasientas, brillantes o que huelen muy mal", "categoria": "gastrointestinal", "fuente": "signos_avanzados"},
    {"id": "gastro_03", "texto": "ha perdido peso sin explicación", "categoria": "gastrointestinal", "fuente": "signos_avanzados"},
    {"id": "gastro_04", "texto": "se ha parado de crecer o ha bajado en las tablas de crecimiento", "categoria": "gastrointestinal", "fuente": "signos_avanzados"},
    {"id": "gastro_05", "texto": "dolor de barriga fuerte después de comer, de forma repetida", "categoria": "gastrointestinal", "fuente": "signos_avanzados"},
    {"id": "derma_01", "texto": "llagas grandes en la boca que no se curan en varias semanas", "categoria": "dermatologia_mucosas", "fuente": "signos_avanzados"},
    {"id": "derma_02", "texto": "erupción en la piel muy extendida con picor fuerte que no mejora con cremas", "categoria": "dermatologia_mucosas", "fuente": "signos_avanzados"},
    {"id": "derma_03", "texto": "heridas pequeñas que no cicatrizan y se infectan", "categoria": "dermatologia_mucosas", "fuente": "signos_avanzados"},
    {"id": "linfo_01", "texto": "ganglios grandes, duros y que no duelen", "categoria": "linfoproliferativo", "fuente": "signos_avanzados"},
    {"id": "linfo_02", "texto": "suda muchísimo por la noche, tiene que cambiar la ropa o las sábanas", "categoria": "linfoproliferativo", "fuente": "signos_avanzados"},
    {"id": "linfo_03", "texto": "se llena enseguida al comer poco, o le duele el lado izquierdo de la barriga", "categoria": "linfoproliferativo", "fuente": "signos_avanzados"},
    {"id": "labo_01", "texto": "el nivel de IgG ha bajado antes de la próxima infusión", "categoria": "laboratorio", "fuente": "signos_avanzados"},
    {"id": "labo_02", "texto": "los linfocitos o los neutrófilos han bajado en el análisis", "categoria": "laboratorio", "fuente": "signos_avanzados"},
    {"id": "labo_03", "texto": "la PCR o la VSG siguen altas sin tener ninguna infección", "categoria": "laboratorio", "fuente": "signos_avanzados"},
    {"id": "diag_inf_01", "texto": "muchas otitis al año, más de seis, en menores de cuatro años", "categoria": "diagnostico_general_infantil", "fuente": "kb_fr_ceredih"},
    {"id": "diag_inf_02", "texto": "una infección bacteriana grave, como meningitis o sepsis", "categoria": "diagnostico_general_infantil", "fuente": "kb_fr_ceredih"},
    {"id": "diag_inf_03", "texto": "más de un mes de antibióticos en un año, o antibiótico por vena", "categoria": "diagnostico_general_infantil", "fuente": "kb_fr_ceredih"},
    {"id": "diag_inf_04", "texto": "hongos en la piel o en la boca que no se curan o que vuelven", "categoria": "diagnostico_general_infantil", "fuente": "kb_fr_ceredih"},
    {"id": "diag_inf_05", "texto": "alergias muy graves o eccema muy grave", "categoria": "diagnostico_general_infantil", "fuente": "kb_fr_ceredih"},
    {"id": "diag_adu_01", "texto": "más de dos sinusitis, otitis o neumonías al año", "categoria": "diagnostico_general_adulto", "fuente": "kb_fr_ceredih"},
    {"id": "diag_adu_02", "texto": "bronquitis repetidas o bronquiectasias sin explicación", "categoria": "diagnostico_general_adulto", "fuente": "kb_fr_ceredih"},
    {"id": "diag_adu_03", "texto": "más de dos meses de antibióticos al año", "categoria": "diagnostico_general_adulto", "fuente": "kb_fr_ceredih"},
    {"id": "diag_adu_04", "texto": "una infección bacteriana grave por neumococo o meningococo", "categoria": "diagnostico_general_adulto", "fuente": "kb_fr_ceredih"},
    {"id": "emerg_01", "texto": "fiebre muy alta, de 40 grados, que dura varios días", "categoria": "emergencia_aguda", "fuente": "estandar_pediatrico"},
    {"id": "emerg_02", "texto": "dificultad para respirar, o labios morados o azulados", "categoria": "emergencia_aguda", "fuente": "estandar_pediatrico"}
  ]
}
```

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `config/alarm_triggers.json` | crear | Contenido literal de arriba — triggers de alarma, no hardcodeados en código |
| `rag/safety.py` | modificar | Implementar `check_alarm_signals()` y `apply_safety_filter()`, sustituye el `NotImplementedError` del stub de T-01 |
| `tests/step_defs/test_e04_t05.py` | crear | Step definitions pytest-bdd para `e04_t05_safety_module.feature` |

## Orden de implementación TDD

Sigue el orden de los escenarios del `.feature` (ya en secuencia lógica:
detección → filtrado → carga de config).

1. **Detección de señal de alarma en la query — fiebre alta** y
   **— dificultad respiratoria** — `tests/features/e04_t05_safety_module.feature`
   - Step definitions en: `tests/step_defs/test_e04_t05.py`
   - Implementación en: `rag/safety.py` (`check_alarm_signals`)
   - Notas: cargar `config/alarm_triggers.json` una vez (a nivel de módulo o
     con cache simple), no releer el fichero en cada llamada. Comparación
     `trigger["texto"].lower() in query.lower()`.

2. **Query sin señal de alarma — pregunta informativa**
   - Implementación en: `rag/safety.py` (`check_alarm_signals`)
   - Notas: confirma que `check_alarm_signals` devuelve `False` cuando
     ninguna subcadena de trigger aparece en la query.

3. **Refuerzo de derivación médica cuando hay alarma detectada en la query**
   - Implementación en: `rag/safety.py` (`apply_safety_filter`)
   - Notas: con `has_alarm=True`, la función añade la frase de derivación
     (ver Contexto técnico) al final de la respuesta recibida, incluso si la
     respuesta no contenía ninguna frase tranquilizadora.

4. **Intercepción de afirmación tranquilizadora absoluta aunque no haya
   alarma en la query**
   - Implementación en: `rag/safety.py` (`apply_safety_filter`,
     `REASSURING_PHRASES`)
   - Notas: con `has_alarm=False` pero la respuesta contiene una frase de
     `REASSURING_PHRASES`, la función también añade la derivación. Verificar
     que el test cubre la coincidencia case-insensitive.

5. **Respuesta informativa sin alarma no añade alarmismo innecesario**
   - Implementación en: `rag/safety.py` (`apply_safety_filter`)
   - Notas: con `has_alarm=False` y ninguna frase de `REASSURING_PHRASES`
     presente, la función devuelve la respuesta sin modificar (o como mucho
     sin añadir la frase de derivación forzada) — el test verifica que el
     contenido informativo original se conserva íntegro.

6. **Triggers de alarma cargados desde fichero de configuración**
   - Implementación en: `rag/safety.py` (carga de `config/alarm_triggers.json`)
   - Notas: el test debe demostrar que el origen es el fichero, no una lista
     en el código — por ejemplo, apuntando `check_alarm_signals` a un fichero
     de triggers de test distinto (via monkeypatch de la ruta o parámetro
     inyectable) y comprobando que una query que solo coincide con ese
     trigger de test se detecta como alarma. Evita que este escenario sea
     una tautología (leer el JSON de producción y comprobar que existe).

## Restricciones a respetar

- Falso Negativo Cero (`AGENTS.md`, D-002): ante duda, la función siempre
  añade la derivación — nunca debe existir una rama de código que "confirme"
  seguridad de forma explícita.
- Triggers de alarma nunca hardcodeados en `rag/safety.py` — viven
  exclusivamente en `config/alarm_triggers.json` (D-019, Scenario 6).
- No introducir llamadas a LLM ni a red dentro de `rag/safety.py` — la
  detección es determinista y local (D-019).

## Lo que queda fuera de esta tarea

- Integración de `check_alarm_signals` / `apply_safety_filter` en
  `rag/pipeline.py` — es T-06, mismo patrón que D-016/D-017 establecieron
  para retriever y language.
- Validación clínica del contenido de `config/alarm_triggers.json` por
  Jacques Rivière — deuda técnica documentada en D-019, no bloquea el cierre
  de T-05 (que valida el mecanismo, no el contenido clínico).
- Capa *pre-retrieval* del módulo de seguridad (prompt injection, filtrado
  PII — OWASP LLM01/LLM06 de `docs/security.md`) — sin `.feature` que la
  cubra, queda como backlog de seguridad separado.
