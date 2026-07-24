# E-14 T-08 — Pulido UI del onboarding
# Tipo: mixta — puntos 1-4 (CSS/JS) son checklist de verificación manual (D-090,
# mismo patrón que E05-T05/E06-T07: rama + PR, sin pytest); punto 5 (parseo de
# edad) es lógica Python testable con pytest-bdd (mismo patrón que T-02/T-03).
#
# Contexto: D-090 documenta los 5 hallazgos de QA en vivo de T-03. El mecanismo
# de fix para 1/2/3/4 es etiquetado por contenido en design/public/custom.js
# (mismo patrón que tagSourcesSections), no por posición en el DOM — evita
# repetir el bug de asumir que un mensaje concreto es siempre el primero del
# hilo.
#
# Ampliación 1 (24 jul 2026, tras QA en vivo): los gates de botones (consentimiento,
# "sobre quién") perdían la pregunta al responder — Chainlit reescribe el contenido
# del propio AskActionMessage a "**Selected:** <label>" (D-090, hardcoded en
# chainlit/message.py, no en nuestro código), sustituyendo la pregunta en vez de
# sumarse a la conversación como pasa con las preguntas de texto libre
# (AskUserMessage). Fix: la pregunta completa se envía como un cl.Message
# independiente ANTES del AskActionMessage (que pasa a llevar solo un texto corto
# de llamada a la acción), y el paso "Selected: ..." se retexta (sin el prefijo) y
# se restyla como burbuja de usuario alineada a la derecha.
#
# Ampliación 2 (24 jul 2026, segunda ronda de QA en vivo) — rediseño del orden:
# - La cabecera "Antes de empezar..." desaparece. El saludo (_greeting()) y la
#   bienvenida (_WELCOME_MESSAGE, sin la pregunta final) se envían siempre
#   primero, antes de cualquier gate u pregunta de onboarding pendiente.
# - Al completar el onboarding EN VIVO dentro de la misma sesión (se pregunta y
#   responde al menos un campo, y el perfil queda completo como resultado), se
#   muestra un título de cierre "Todo listo, {nombre de quien escribe}" (mismo
#   tratamiento visual de título) justo antes del mensaje final "¿En qué puedo
#   ayudarte hoy?" + starter chips.
#
# Ampliación 3 (24 jul 2026, tercera ronda de QA en vivo) — probada y descartada:
# se probó sustituir el replay literal de la Ampliación 2 por una única línea de
# resumen en cursiva. Descartada en la Ampliación 4: duplicaría lo que ya
# mostrará T-05 (edición de perfil desde `cl.ChatSettings`), sin ser editable
# desde el chat.
#
# Ampliación 4 (24 jul 2026, cuarta ronda de QA en vivo) — diseño final: el
# cambio afecta ÚNICAMENTE al caso de perfil ya completo antes de esta sesión.
# - **Perfil ya completo** (sesión nueva, los cuatro campos con valor): no se
#   muestra nada — ni resumen, ni replay, ni título de cierre. Ver esos datos
#   se delega enteramente a T-05.
# - **Perfil vacío** (consentimiento rechazado o nunca alcanzado): sin cambios,
#   como siempre.
# - **Perfil incompleto** (algún campo guardado, otros vacíos): se mantiene el
#   diseño original de la Ampliación 2 — se reproduce tal cual cada
#   pregunta/respuesta ya guardada, en el mismo orden en que se pidió
#   originalmente, antes de pasar a preguntar en vivo lo que falte.
#
# Textos exactos confirmados por Marcos (24 jul 2026):
# - Prompt corto del gate de consentimiento: "¿Aceptas el tratamiento de estos datos?"
# - Prompt corto de "sobre quién": "Elige una opción:"
# - Título de cierre: "Todo listo, {nombre}" (con coma, p. ej. "Todo listo, Marcos"),
#   sin nombre si no hay full_name guardado (mismo fallback que _greeting()).
#
# Fuera de alcance: el hallazgo abierto de D-090 sobre patient_diagnosis
# repreguntado tras un refresco de página no se investiga en esta tarea —
# pendiente de que Marcos revise consola/Supabase por su cuenta.

Feature: Pulido de UI del flujo de onboarding

  Como familia usando el onboarding por chat de AIIP
  Quiero que el flujo se vea correcto (saludo y bienvenida siempre primero,
  botones centrados, respuestas de botón como burbujas de usuario, contexto
  recuperado entre sesiones, edad reconocida aunque incluya texto)
  Para que la primera impresión del producto sea profesional y no pierda el
  hilo de la conversación entre sesiones

  # Checklist de verificación manual — orden y contenido

  Scenario: El saludo y la bienvenida se muestran siempre primero, antes de cualquier pregunta de onboarding pendiente
    Given un usuario abre el chat, con o sin onboarding pendiente
    When se dispara on_chat_start
    Then el saludo (_greeting()) es el primer mensaje del hilo
    And la bienvenida (_WELCOME_MESSAGE, sin la pregunta final) es el segundo mensaje
    And cualquier gate de consentimiento o pregunta de perfil pendiente aparece después de esos dos mensajes, nunca antes

  Scenario: Los mensajes de título (saludo y cierre) reciben el tratamiento visual por contenido, no por posición
    Given el saludo ya no es siempre el único mensaje con tratamiento de título (también lo lleva "Todo listo {nombre}")
    When se renderiza el chat completo
    Then ambos mensajes reciben el mismo tratamiento visual de título (gradiente, sin avatar) por coincidencia de contenido, no por ser el primer mensaje del hilo

  Scenario: Se muestra un título de cierre "Todo listo, {nombre}" cuando el onboarding se completa EN VIVO en la sesión
    Given al menos un campo de perfil se pregunta y se responde en vivo en esta sesión
    And el perfil queda completo (los cuatro campos con valor) como resultado
    When termina la secuencia de onboarding
    Then se muestra un mensaje de título "Todo listo, {nombre de quien escribe}" (o "Todo listo" a secas si no hay full_name)
    And a continuación el mensaje final "¿En qué puedo ayudarte hoy?" con los starter chips

  Scenario: No se muestra título de cierre ni resumen si el perfil está realmente vacío
    Given un usuario sin "patient_name" guardado nunca (consentimiento rechazado, o nunca alcanzó esa pregunta) y sin ningún gate pendiente de mostrar en esta sesión
    When se dispara on_chat_start
    Then no se envía ningún gate ni pregunta de perfil, ni el título "Todo listo"
    And tras el saludo y la bienvenida se pasa directamente a "¿En qué puedo ayudarte hoy?" con los starter chips

  Scenario: Con el perfil ya completo de antes, no se muestra nada extra (ni resumen ni título)
    Given un usuario con los cuatro campos de perfil ya guardados de una sesión anterior (patient_name, patient_diagnosis, patient_age, patient_context)
    When se dispara on_chat_start en una sesión nueva
    Then no se envía ningún mensaje de perfil (ni resumen, ni replay, ni pregunta en vivo)
    And tras el saludo y la bienvenida se pasa directamente al mensaje final, sin el título "Todo listo"
    And ver esos datos guardados queda para T-05 (edición de perfil desde ajustes), no para el chat

  Scenario: La pregunta de un gate de botones persiste como mensaje propio, no se pierde al responder
    Given el gate de consentimiento o la pregunta "sobre quién"
    When se envía al chat
    Then el texto completo de la pregunta se muestra como un mensaje independiente antes de los botones
    And el AskActionMessage que sigue solo lleva un texto corto de llamada a la acción ("¿Aceptas el tratamiento de estos datos?" / "Elige una opción:"), no la pregunta completa

  Scenario: La respuesta a un gate de botones se muestra como burbuja de usuario, igual que al escribir
    Given el usuario responde a un gate de botones (consentimiento o "sobre quién")
    When Chainlit reescribe el contenido del paso a "**Selected:** <opción>"
    Then se muestra únicamente la opción elegida, sin el prefijo "Selected:"
    And el mensaje aparece con el mismo estilo de burbuja alineada a la derecha que una respuesta escrita en la caja de texto, sin avatar, y sin el tratamiento visual de título

  Scenario: Las filas de botones de consentimiento y de paciente aparecen centradas
    Given el gate de consentimiento (Acepto/Ahora no) o la pregunta "sobre quién" (Sobre mí/Sobre otra persona)
    When se renderizan sus botones
    Then la fila de botones aparece centrada
    And los chips de starter questions (mensaje final, tras el título de cierre o tras la bienvenida) mantienen su alineación actual, sin cambios

  Scenario: Las preguntas del onboarding se acumulan en el hilo como una conversación normal
    Given el flujo completo de onboarding (consentimiento, nombre, "sobre quién", diagnóstico, edad, contexto)
    When el usuario va respondiendo cada pregunta una a una
    Then cada pregunta y su respuesta permanecen visibles en el hilo, sin desaparecer al pasar a la siguiente
    And la siguiente pregunta se muestra debajo de la respuesta anterior, nunca sustituyéndola

  Scenario: Al retomar un onboarding a medias en una sesión nueva, se reproduce tal cual la conversación ya guardada
    Given un usuario con algunos campos de perfil ya guardados de una sesión anterior (p. ej. patient_name y patient_diagnosis) y otros todavía vacíos (p. ej. patient_age, patient_context)
    When se dispara on_chat_start en una sesión nueva
    Then tras el saludo y la bienvenida se reproducen, en el mismo orden en que se pidieron originalmente, la pregunta y la respuesta guardada de cada campo ya completo
    And la pregunta "sobre quién" se reproduce infiriendo "Sobre mí" si patient_name coincide con el full_name de quien escribe, o "Sobre otra persona" con el nombre guardado si no coincide
    And la edad reproducida muestra el entero guardado tal cual (p. ej. "4"), no el texto original tecleado en su momento
    And después se pregunta en vivo, con AskUserMessage/AskActionMessage reales, por cada campo todavía vacío
    And si esas preguntas se responden y el perfil queda completo, se muestra el título de cierre "Todo listo, {nombre}" al final

  Scenario: La caja de texto recibe el foco automáticamente al terminar de escribir el agente
    Given cualquier respuesta del agente (pipeline RAG normal, o una pregunta de onboarding)
    When el agente termina de escribir esa respuesta
    Then la caja de texto del chat recibe el foco automáticamente, sin que el usuario tenga que hacer clic

  # Escenarios TDD — punto 5 (parseo de edad, lógica Python testable)

  Scenario: Edad válida con texto adicional se reconoce
    Given la respuesta del usuario es "12 años"
    When se parsea con _parse_patient_age
    Then devuelve 12

  Scenario: Edad puramente numérica se sigue reconociendo (regresión)
    Given la respuesta del usuario es "45"
    When se parsea con _parse_patient_age
    Then devuelve 45

  Scenario: Entrada sin ningún número se rechaza
    Given la respuesta del usuario es "no sabría decirte"
    When se parsea con _parse_patient_age
    Then devuelve None

  Scenario: Número fuera de rango se rechaza aunque el formato sea válido
    Given la respuesta del usuario es "150 años"
    When se parsea con _parse_patient_age
    Then devuelve None
