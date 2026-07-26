# E-14 T-07 — Resultados del smoke test manual E2E (Scenario 1)

Generado: 2026-07-25

Plantilla vacía para el Scenario 1 ("Flujo completo end-to-end sin fallos") de
`tests/features/e14_t07_closure_regression.feature`. Igual que en
`tests/results/e05_t07_smoke_test_results.md` (E-05 T-07), este flujo requiere una
app Chainlit corriendo en local contra Supabase real — no es automatizable desde
Antigravity. Marcos ejecuta cada paso en su propio entorno y rellena los checkboxes
y notas.

Cada entrada queda pendiente de revisión manual de Marcos antes de dar por buena la
tarea y cerrar E-14.

---

## Paso 1 — Signup de un usuario nuevo

**Email usado:** (omitido del registro, cuenta de prueba local)

**Signup completado sin errores:** [x]
**Correo de confirmación recibido y login posterior autentica:** [x]

**Notas:** Confirmado OK por Marcos.

---

## Paso 2 — Gate de consentimiento de datos de salud (T-02)

**El gate aparece en `on_chat_start`, antes de cualquier mensaje del chat:** [x]
**Requiere una acción afirmativa real (no un checkbox premarcado ni "continuar" implícito):** [x]
**Tras aceptar, `profiles.health_data_consent_at` queda registrado (verificar en Supabase):** [x]
**En un login posterior, el gate no se repite:** [x]

**Notas:** Confirmado OK por Marcos.

---

## Paso 3 — Onboarding por chat (T-03): distinción `user_name` / `patient_name`

**El onboarding pregunta explícitamente quién chatea (tutor) y de quién son los datos (paciente):** [x]
**Si son personas distintas, el sistema no las confunde en el resto de la conversación:** [x]
**Los datos recogidos (nombre, diagnóstico, edad, contexto) se persisten en `profiles`:** [x]

**Notas:** Confirmado OK por Marcos.

---

## Paso 4 — Edición de un dato desde ajustes (T-05)

**El icono de ajustes (`cl.ChatSettings` / `chat_settings_location`) es accesible desde el chat:** [x]
**Se puede editar al menos un dato del perfil (p. ej. `patient_context` o `patient_age`):** [x]
**El cambio se persiste y se refleja en una pregunta posterior (ver Paso 5):** [x]

**Notas:** Confirmado OK por Marcos.

---

## Paso 5 — Pregunta al chat con verificación de perfil (T-06)

**Pregunta:** (no registrada en detalle — confirmado OK por Marcos)

**Streaming:** [x]
**La respuesta usa el nombre real del paciente, no "el paciente":** [x]
**La respuesta no reintroduce el diagnóstico como si fuera información nueva:** [x]
**El registro/tono es coherente con la edad del paciente (más simple si es menor):** [x]
**Fuentes citadas:** [x]
**Disclaimer de cierre presente:** [x]

**Notas:** Confirmado OK por Marcos.

---

## Conclusión

**¿El Scenario 1 pasa sin fallos de principio a fin?** Sí.

**Notas finales:** Marcos confirma el flujo completo end-to-end sin fallos (25 jul 2026). Sin
detalle paso a paso más allá de lo indicado arriba — confirmación directa, no transcripción.

**Revisión manual (Marcos):** ✅ Confirmado — 25 jul 2026.
