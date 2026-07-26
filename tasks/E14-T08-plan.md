# Plan — E-14 T-08 Pulido UI del onboarding

## Contexto técnico

Mecanismo de tagging por contenido ya en uso en el repo (D-026, `tagSourcesSections` en
`design/public/custom.js`): un `MutationObserver` sobre `document.body`, idempotente vía
comprobación de `classList`, que recorre `[role="article"]` (o el contenedor de step
correspondiente), compara `textContent.trim()` contra strings/prefijos conocidos y añade una
clase CSS propia si coincide. Se reutiliza el mismo patrón para todo lo de abajo, en vez de
depender de la posición en el DOM (`:first-child`).

**Ronda 1 (D-090, puntos 1-5) — ya con criterio cerrado:**

- **Título por contenido:** las 4 reglas de `style.css` (líneas ~216-232, ~295) que usaban
  `[data-step-type="assistant_message"]:first-child` pasan a usar
  `[data-step-type="assistant_message"].aiip-heading-title`. La clase la añade una función en
  `custom.js` que recorre `[data-step-type="assistant_message"]`, lee el texto de su
  `.message-content [role="article"]` y compara contra una lista de matchers (ver "Ronda 2" para
  la lista final — cambia respecto al primer borrador).

  Riesgo aceptado (mismo perfil que `SOURCES_HEADINGS`, D-026): si una respuesta del pipeline
  RAG empezara literalmente por uno de los prefijos de la lista, se etiquetaría como título por
  error. Baja probabilidad, no se mitiga en esta tarea.

- **"Selected:" pierde la pregunta al responder un gate de botones:** al responder un
  `AskActionMessage`, Chainlit reescribe el contenido de ese mismo paso a `"**Selected:**
  <label>"`, sustituyendo la pregunta en vez de sumarse a la conversación (a diferencia de
  `AskUserMessage`, donde la pregunta queda fija y la respuesta es un paso nuevo). Fix en dos
  partes:

  1. **La pregunta persiste.** Antes de cada `AskActionMessage` de botones (gate de
     consentimiento en `_ensure_health_consent()`, pregunta "sobre quién" en
     `_ensure_patient_profile()`), se envía un `cl.Message` normal con el texto completo de la
     pregunta (`_HEALTH_CONSENT_MESSAGE` / `_PATIENT_WHO_MESSAGE`, ya existentes). El
     `AskActionMessage` que sigue pasa a llevar un texto corto de llamada a la acción:
     - `_HEALTH_CONSENT_PROMPT = "¿Aceptas el tratamiento de estos datos?"`
     - `_PATIENT_WHO_PROMPT = "Elige una opción:"`

  2. **La respuesta se ve como si se hubiera escrito.** Función de tagging en `custom.js` que
     detecta pasos `[data-step-type="assistant_message"]` cuyo contenido empieza por
     `"**Selected:**"`: reescribe el texto del `[role="article"]` quitando ese prefijo (deja solo
     la opción, p. ej. "Acepto") y añade una clase `aiip-selected-as-user-bubble`. Nueva regla en
     `style.css` que mimetiza `[data-step-type="user_message"] .bg-accent` (mismo `background`,
     `border-radius`, `padding`, tipografía) sobre esa clase, oculta el avatar (mismo truco
     `span:has(> img[alt^="Avatar for"])` que el resto del fichero) y alinea el paso a la derecha
     — mecanismo exacto (`margin-left: auto` en `.message-content` vs. `justify-content:
     flex-end` en `.ai-message.flex`) a verificar contra el DOM real en vivo, mismo criterio que
     el resto de selectores de este fichero ("verified in the live DOM"). Al no coincidir ya con
     los matchers de `aiip-heading-title`, deja de heredar el estilo de título — sin necesidad de
     una exclusión aparte.
     **Este mismo mecanismo se reutiliza en la Ronda 2 para las burbujas de "replay"** — ver
     abajo, no es exclusivo de las respuestas de botón en vivo.

- **Botones centrados:** la clase compartida `.-ml-1\.5.flex.items-center.flex-wrap`
  (`style.css` línea ~494) no se toca — la usan también los starter chips (T-05) y los iconos de
  copiar/editar mensaje. Función en `custom.js` que recorre esos wrappers, lee las `label` de sus
  `<button>` hijos y, si el conjunto coincide exactamente con `{"Acepto", "Ahora no"}` o con
  `{"Sobre mí", "Sobre otra persona"}`, añade la clase `aiip-centered-actions` al wrapper. Nueva
  regla en `style.css`: `.aiip-centered-actions { justify-content: center; }`.

- **Edad:** `_parse_patient_age` cambia de `int(raw.strip())` a extracción del primer número vía
  `re.search(r"\d+", raw)` — cubre `"12"`, `"12 años"`, `"tiene 12 años"`. No cubre números en
  palabras ("doce") — fuera de alcance.

**Ronda 2 (24 jul 2026, segunda QA en vivo) — rediseño del orden y recuperación de contexto:**

- **La cabecera "Antes de empezar..." desaparece.** Se sustituye por reordenar el propio saludo y
  la bienvenida al principio de `on_chat_start`, siempre, antes de cualquier gate o pregunta:

  ```python
  await cl.Message(content=_greeting()).send()
  await cl.Message(content=_WELCOME_MESSAGE).send()   # ahora sin la pregunta final
  await _ensure_health_consent()
  await _ensure_full_name()
  onboarding_completed_now = await _ensure_patient_profile()
  if onboarding_completed_now:
      await cl.Message(content=_onboarding_complete_title(user.metadata.get("full_name"))).send()
  actions = [...]
  await cl.Message(content=_WELCOME_PROMPT, actions=actions).send()
  ```

  Solo `_ensure_patient_profile()` devuelve `bool` (ver más abajo la condición exacta);
  `_ensure_health_consent()`/`_ensure_full_name()` no cambian su firma. `_WELCOME_MESSAGE` se
  recorta (quita la última línea, "¿En qué puedo ayudarte hoy?"); esa línea pasa a una constante
  nueva `_WELCOME_PROMPT`, enviada al final junto con los `actions` de starter questions (mismo
  `cl.Message` que hoy, solo que ahora con contenido más corto).

- **Matchers de `aiip-heading-title` (actualiza la Ronda 1):** ya no incluye el texto exacto
  "Antes de empezar..." (ese mensaje deja de existir). Pasa a ser:
  - prefijo `"Buenos días"` / `"Buenas tardes"` / `"Buenas noches"` (saludo, sin cambios)
  - prefijo `"Todo listo"` (título de cierre nuevo, dinámico igual que el saludo: con o sin
    ", {nombre}" según haya `full_name`)

- **Título de cierre "Todo listo {nombre}":** nueva función en `main_family.py`, mismo patrón que
  `_greeting()`:

  ```python
  def _onboarding_complete_title(full_name: str | None) -> str:
      if full_name:
          return f"Todo listo, {full_name}"
      return "Todo listo"
  ```

  Confirmado con Marcos (24 jul 2026): con coma, consistente con `_greeting()` —
  `"Todo listo, Marcos"`, no `"Todo listo Marcos"` (la captura original no la llevaba, pero se
  prioriza la consistencia con el saludo).

- **Resumen compacto — probado y descartado (24 jul 2026, tercera ronda de QA):** se probó una
  línea de resumen en cursiva (`{patient_name} / {patient_diagnosis} / {patient_context}
  ({patient_age} años)`) para todos los casos con datos previos. Descartada en la cuarta ronda:
  duplicaría lo que ya va a mostrar T-05 (edición de perfil desde `cl.ChatSettings`), y encima sin
  ser editable desde el chat. Ver el punto siguiente para el diseño final.

- **Diseño final (24 jul 2026, cuarta ronda de QA) — replay literal solo si queda algo pendiente,
  nada si el perfil ya está completo:**

  - **Perfil ya completo antes de esta sesión** (los cuatro campos con valor): no se muestra nada
    — ni resumen, ni replay, ni título de cierre. Se pasa directo de la bienvenida a la pregunta
    del pipeline/al mensaje final. Ver esos datos queda enteramente para T-05 (perfil editable
    desde ajustes) — mostrarlos también aquí sería una segunda fuente de la misma información, y
    encima no editable desde el chat.
  - **Perfil vacío** (`patient_name` nunca guardado — consentimiento rechazado o nunca alcanzado):
    sin cambios, como siempre — nada que reproducir.
  - **Perfil incompleto** (algún campo guardado, algún campo vacío — el caso que motivó esta
    conversación, capturas de pantalla de un onboarding a medias): **sí se reproduce tal cual**
    cada pregunta/respuesta ya guardada, en el mismo orden en que se pidió originalmente, antes de
    pasar a preguntar en vivo lo que falte. Se reinstaura el mecanismo descrito en la Ronda 2
    original (antes de la simplificación a resumen, luego descartada): dos `cl.Message` por campo
    ya guardado (pregunta interpolada + burbuja de respuesta, reutilizando
    `aiip-selected-as-user-bubble` para el estilo de burbuja de usuario), con la edad mostrando el
    entero guardado tal cual (no el texto original tecleado, que no se persiste) y "sobre quién"
    inferido comparando `patient_name` con `user.metadata.get("full_name")` (coincide → "Sobre
    mí"; si no, "Sobre otra persona" + nombre guardado).

  `_ensure_patient_profile()` usa el `profile = get_profile(user_id)` capturado al principio para
  decidir, antes de nada, si el perfil está completo, vacío, o incompleto:
  - completo → `return False` inmediatamente, sin enviar ningún mensaje.
  - vacío o incompleto → recorre los cuatro campos en orden; por cada uno, si ya estaba en el
    `profile` inicial (y el perfil global no es "completo", caso ya descartado arriba), lo
    reproduce; si no, lo pregunta en vivo. Trackea `answered_live` (si preguntó y obtuvo
    respuesta a algo en vivo). Al final, `return answered_live and <perfil completo tras esta
    llamada>`.

- **Título de cierre "Todo listo, {nombre}":** se muestra solo si `_ensure_patient_profile()`
  devuelve `True` — es decir, solo cuando el perfil llega a completarse como resultado de
  responder en vivo algo en esta sesión (no cuando ya estaba completo de antes, no cuando sigue
  incompleto tras un timeout).

**Ronda 3 (24 jul 2026, quinta pieza de QA en vivo) — foco automático en la caja de texto:**

Comportamiento general del chat (no específico de onboarding, confirmado con Marcos): al
terminar de escribir el agente cualquier respuesta (RAG normal u onboarding), la caja de texto
(`<textarea>` dentro de `#message-composer`, ver bloque "Input area" de `style.css`) recibe el
foco automáticamente, para que el usuario pueda escribir sin tener que hacer clic primero. Se
mete en T-08 por conveniencia (ya se está tocando `custom.js`), aunque no es un hallazgo de D-090.

Mecanismo: nueva función en `custom.js`, mismo patrón `MutationObserver` que el resto del
fichero. Ojo: no basta con reutilizar `isThinking()`/`stopThinking()` tal cual — esas detectan el
INICIO del streaming (`.message-content` pasa de 0 hijos a tener contenido), no el final. Hay que
detectar cuándo el ÚLTIMO `.ai-message` termina de recibir tokens (fin real del streaming) — a
verificar en vivo contra el DOM real cuál es la señal fiable (candidatos: cursor de streaming que
desaparece, o un debounce corto sobre mutaciones de `.message-content` del último mensaje sin
cambios durante un intervalo breve), mismo criterio "verified in the live DOM" que el resto de
`custom.js`. Una vez detectado, `document.querySelector("#message-composer textarea")?.focus()`
(selector exacto del `<textarea>` real a confirmar en vivo, no asumido).

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `design/public/custom.js` | modificar | Tagging para `aiip-heading-title` (saludo + "Todo listo", lista de matchers actualizada), `aiip-centered-actions` (filas de botones por label), `aiip-selected-as-user-bubble` (reescribe "**Selected:** ..." de respuestas de botón en vivo y de replay, y lo etiqueta), y nueva función que enfoca el `<textarea>` de `#message-composer` cuando el último mensaje del asistente termina de escribirse (cualquier respuesta, no solo onboarding). |
| `design/public/style.css` | modificar | Sustituye `:first-child` por `.aiip-heading-title` en las 4 reglas del bloque "Greeting title"; añade `.aiip-centered-actions { justify-content: center; }`; añade regla para `.aiip-selected-as-user-bubble`. |
| `chainlit/main_family.py` | modificar | Reordena `on_chat_start` (saludo + bienvenida primero, título de cierre condicional al final); `_WELCOME_MESSAGE` recortado + `_WELCOME_PROMPT` nuevo; `_onboarding_complete_title()` nueva; `_profile_summary_line()` nueva; `_HEALTH_CONSENT_PROMPT`/`_PATIENT_WHO_PROMPT` nuevas; `_ensure_patient_profile()` reescrita: envía el resumen compacto si hay datos previos, pregunta en vivo los campos que falten, devuelve `bool` (completado en vivo ahora); `_parse_patient_age()` con `re.search(r"\d+", raw)`. Se elimina `_ONBOARDING_HEADING_TITLE`/`_ONBOARDING_HEADING_SUBTITLE` (ya no existen). |
| `tests/step_defs/test_e14_t08.py` | crear | Step definitions pytest-bdd solo para los 4 escenarios TDD del punto 5 (parseo de edad) — mismo patrón de fake `chainlit` que `test_e14_t02.py`/`test_e14_t03.py`. El resto de escenarios quedan sin `@scenario`, documentados en el `.feature` (mismo precedente que `test_e05_t06.py`/`test_e14_t02.py`). |

## Orden de implementación TDD (punto 5 — único bloque con TDD real)

1. **Edad válida con texto adicional se reconoce** —
   `tests/features/e14_t08_onboarding_ui_polish.feature`
   - Step definitions en: `tests/step_defs/test_e14_t08.py`
   - Implementación en: `chainlit/main_family.py` (`_parse_patient_age`)
   - Notas: `re.search(r"\d+", raw)`; si no hay match, `None`. Si hay match, `int(match.group())`
     validado contra el rango existente `0 <= age <= 120`.

2. **Edad puramente numérica se sigue reconociendo (regresión)** — mismo step def, cubre que el
   cambio de `int(raw.strip())` a regex no rompe el caso ya soportado.

3. **Entrada sin ningún número se rechaza** — `re.search` devuelve `None`, la función devuelve
   `None` sin lanzar excepción.

4. **Número fuera de rango se rechaza aunque el formato sea válido** — `"150 años"` extrae `150`,
   falla la validación de rango existente, devuelve `None`.

## Secuencia de implementación (checklist manual)

No llevan TDD, se verifican en vivo (mismo criterio que E05-T05/E06-T07). Orden sugerido para no
bloquearse entre sí:

1. Reordenar `on_chat_start`: saludo + `_WELCOME_MESSAGE` (recortado) primero, siempre; mover el
   resto (`_ensure_*`) después; `_WELCOME_PROMPT` + starter actions al final.
2. Reordenar `_ensure_health_consent()` y la parte "sobre quién" de `_ensure_patient_profile()`:
   `_HEALTH_CONSENT_MESSAGE`/`_PATIENT_WHO_MESSAGE` como `cl.Message` separado, el
   `AskActionMessage` que sigue usa `_HEALTH_CONSENT_PROMPT`/`_PATIENT_WHO_PROMPT`.
3. Al principio de `_ensure_patient_profile()`, con el `profile` recién capturado: si los cuatro
   campos ya tienen valor, `return False` de inmediato (perfil completo → nada que mostrar,
   delegado a T-05).
4. Si no está completo, recorrer los cuatro campos en orden (sobre quién/nombre → diagnóstico →
   edad → contexto): si el campo ya estaba en el `profile` inicial, reproducirlo (dos
   `cl.Message`: pregunta interpolada + burbuja de respuesta con `aiip-selected-as-user-bubble`,
   "sobre quién" inferido por comparación con `full_name`, edad mostrando el entero guardado); si
   no, preguntarlo en vivo como hoy, marcando `answered_live = True` si hay respuesta. Al final,
   `return answered_live and <perfil completo tras esta llamada>`.
5. Añadir `_onboarding_complete_title()` y el envío condicional en `on_chat_start` según ese
   booleano.
6. `custom.js`: función de tagging de `aiip-heading-title` con la lista de matchers actualizada
   (saludo + "Todo listo"), actualizar las 4 reglas de `style.css`.
7. `custom.js`: función de tagging de `aiip-selected-as-user-bubble` (respuestas de botón en vivo
   y burbujas de replay de campos ya guardados) y su regla en `style.css`, verificando en vivo el
   mecanismo exacto de alineación a la derecha.
8. `custom.js`: función de tagging de `aiip-centered-actions` y su regla en `style.css`.
9. `custom.js`: función de foco automático de la caja de texto al terminar de escribir el
   agente — investigar en vivo la señal fiable de "fin de streaming" (no reutilizar
   `isThinking`/`stopThinking` tal cual, detectan el inicio) y el selector exacto del
   `<textarea>` dentro de `#message-composer`.
10. QA manual en vivo de los casos: (a) perfil vacío/consentimiento rechazado — saludo+bienvenida+
   chips directo, sin nada más; (b) onboarding completo en una sola sesión (perfil vacío al
   empezar) — con título de cierre; (c) perfil incompleto en sesión nueva — replay literal de lo
   ya guardado + solo se pregunta en vivo lo que falta + título de cierre si se completa; (d)
   perfil ya completo en sesión nueva — nada extra, sin resumen ni título; (e) botones centrados
   y burbuja de usuario en las respuestas de botón en vivo y en las burbujas de replay.

## Restricciones a respetar

- Prompts/textos de UI no van embebidos sin constante — mismo patrón que el resto de
  `main_family.py` (`_ASK_NAME_MESSAGE`, `_HEALTH_CONSENT_MESSAGE`, etc.).
- El orden relativo entre `_ensure_health_consent` → `_ensure_full_name` → `_ensure_patient_profile`
  no cambia (D-009: el gate de consentimiento va antes que cualquier dato de salud) — lo único que
  cambia es que el saludo y la bienvenida ahora los preceden a los tres, en vez de ir después.
- No investigar el hallazgo abierto de D-090 sobre `patient_diagnosis` tras refresco — fuera de
  esta tarea.
- El replay de campos ya guardados no debe disparar ninguna escritura nueva a Supabase (son datos
  ya guardados, solo se re-muestran) — `update_profile` solo se llama para campos recién
  respondidos en vivo, igual que hoy.
- El cambio de esta cuarta ronda afecta únicamente al caso de perfil ya completo (ahí se quita
  todo lo que se mostraba antes, sin sustituirlo por nada). El caso de perfil incompleto no
  cambia respecto al diseño de la Ronda 2: se mantiene el replay literal de la conversación
  anterior tal cual estaba.

## Lo que queda fuera de esta tarea

- Parseo de edades en palabras ("doce años").
- Cualquier resumen o vista de los datos de perfil cuando ya está completo — se delega
  enteramente a T-05 (edición de perfil desde `cl.ChatSettings`).
- Cualquier cambio en la alineación de los starter chips (T-05) o los iconos de copiar/editar
  mensaje — comparten wrapper con los botones de onboarding pero no se tocan.
- Investigación del bug de `patient_diagnosis` tras refresco (hallazgo abierto de D-090).
- Resumen personalizado de `patient_context` en el propio texto de bienvenida (idea aparte,
  aplazada — ver conversación de task-start, a retomar en T-04/T-06).
