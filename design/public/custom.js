/* AIIP — custom_js (D-040 punto 5, ampliado 10 jul 2026)
 *
 * Chainlit's fixed login form has no native "forgot password" link, so it
 * would be undiscoverable without this. Injects a link to
 * /auth/forgot-password into the label row above the password field
 * (id="password", verified against the real rendered DOM of
 * chainlit==2.11.1, same structural pattern as the mockup's "Forgot?"
 * link). The login screen is a full page load (not an SPA route change),
 * but the password input mounts asynchronously via React, so a
 * MutationObserver — not a one-shot run at script load — is what makes
 * this reliable.
 *
 * injectLoginHeading follows the exact same rationale for a second gap:
 * the reference (docs/design/standalone-html/screens-auth.html) has a
 * logo badge + title + subtitle between the logo's original spot and
 * the card ("Intelligent Assistant for Primary Immunodeficiencies" /
 * "Informational companion for families · Available 24/7"). Checked the
 * compiled login page component directly
 * (chainlit/frontend/dist/assets/index-*.js, function LKn) — there's no
 * config field (UISettings.description included) wired to that DOM
 * region; it's just the logo, nothing else. A CSS ::before/::after
 * content string was the alternative, but it can't produce real,
 * accessible, multi-line heading+subtitle markup and has no path to the
 * app's i18n strings at all — a real DOM node, inserted the same way as
 * the forgot-password link above, is the closer fit to how this app
 * already solves this exact kind of gap.
 *
 * The badge's <img> points at Chainlit's own theme-aware logo endpoint
 * (`getLogoEndpoint`/`buildEndpoint("/logo?theme=...")`, same bundle) —
 * not a hardcoded path to design/public/logo_dark.svg — so it stays
 * correct if that convention ever changes, and matches exactly what the
 * (now hidden) original top-left logo was already rendering. Theme is
 * read once at injection time from `document.documentElement`'s
 * light/dark class (same class the vite-ui-theme toggle sets, verified
 * in the bundle) — the login page is a full page load with no visible
 * theme toggle of its own, so a one-time read is enough; no need to
 * react to live theme changes here.
 *
 * injectThemeToggle (10 jul 2026) adds that missing control. Confirmed
 * by decompiling chainlit/frontend/dist/assets/index-*.js: the /login
 * route (function LKn) renders only the logo, the login form and the
 * decorative side panel — no ThemeToggle in that tree, unlike the chat
 * shell. The whole SPA is wrapped in a `ZVn` theme provider
 * (storageKey "vite-ui-theme", values "light"/"dark"/"system") whose
 * effect, on change, does three things: toggle the light/dark class on
 * <html>, persist the choice to localStorage under that key, and copy
 * `window.theme[themeName]` (the per-theme CSS custom properties
 * Chainlit injects from theme.json, same object style.css's header
 * comment references) onto `documentElement.style`. `setTheme` itself
 * is closed over private React state, not exposed on `window`, so
 * applyTheme() below reproduces those three steps by hand rather than
 * calling into the bundle — same externally-visible effect, and because
 * it writes the same storageKey/class, the choice survives the redirect
 * into the authenticated chat (ZVn re-reads localStorage on mount there
 * too).
 *
 * positionThemeToggle (10 jul 2026, revisión 2): the chat shell *does*
 * have its own toggle after all — `#theme-toggle` (component `aGn`,
 * same bundle), rendered in the header row right before the user-menu
 * avatar (`#header .flex.items-center.gap-1`, id="header" is the
 * `p.jsx("div",{...,id:"header"})` wrapper in component `tWn`). Two
 * toggles was the actual bug reported (10 jul 2026, Marcos): our button
 * was appended once to `document.body` with `position:fixed`, and
 * because custom_js runs once per full page load — not per SPA route —
 * it never got cleaned up or repositioned when client-side navigation
 * carried it from /login into the authenticated shell, so it sat fixed
 * top-right on top of the native one. Fix: hide the native `#theme-
 * toggle` outright (style.css) and always reparent *our* button next to
 * it instead — inside the header's icon row when `#theme-toggle` exists
 * in the DOM (copying its className so ours blends in as a normal flow
 * icon button, no fixed positioning), falling back to the floating
 * glass-pill treatment (`.aiip-theme-toggle--floating`) only when that
 * row isn't present, i.e. on /login. Since SPA navigation can flip
 * between those two states any number of times without a script
 * reload, this can't be a one-shot injection like the two above — a
 * dedicated MutationObserver (below, never disconnects) re-evaluates
 * `positionThemeToggle` on every DOM change instead.
 */
(function () {
  // Sized via inline `style`, not the width/height attributes alone: in
  // header mode `btn.className` is copied from Chainlit's native toggle
  // (see positionThemeToggle below), which carries a Tailwind
  // `[&_svg]:size-4` rule forcing descendant svgs to 1rem — a plain
  // attribute loses to that class rule, but the style attribute's
  // specificity beats it without needing !important (10 jul 2026,
  // Marcos: icon was rendering at 1rem instead of the intended 1.2rem).
  var ICON_STYLE = 'style="width:1.2rem;height:1.2rem"';
  var SUN_ICON =
    '<svg ' + ICON_STYLE + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path></svg>';
  var MOON_ICON =
    '<svg ' + ICON_STYLE + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';

  // The "light"/"dark" class on <html> is authoritative once React's
  // ZVn provider has run its mount effect — but custom_js executes
  // before that (see the forgot-password-link comment above on why a
  // MutationObserver is needed at all), so the very first call here can
  // land in the window where neither class is present yet. Falling
  // through to localStorage covers the common case (a returning visitor
  // — ZVn reads the very same key) without guessing; without it this
  // always defaulted to "dark" during that race, showing the wrong icon
  // on first paint for anyone actually in light mode (10 jul 2026,
  // Marcos). The remaining edge case — a first-ever visit, nothing in
  // localStorage yet — can't be resolved from here at all: the actual
  // default comes from `default_theme` in .chainlit/config.toml, a
  // server value with no client-side global to read before React mounts
  // (confirmed: index.html only inlines `window.theme`, the per-theme
  // CSS vars, not which one is default). `system`/matchMedia would be
  // the wrong guess too, since this app doesn't use ZVn's "system"
  // default — it passes its own config value as ZVn's defaultTheme
  // prop. Rather than hardcode that config value here (one more place
  // to keep in sync), render() gets one more call the moment the class
  // actually appears — see the classObserver set up in
  // injectThemeToggle() below — so a wrong first guess self-corrects
  // within a mount tick instead of staying stuck.
  function currentTheme() {
    if (document.documentElement.classList.contains("light")) {
      return "light";
    }
    if (document.documentElement.classList.contains("dark")) {
      return "dark";
    }
    var stored = localStorage.getItem("vite-ui-theme");
    if (stored === "light" || stored === "dark") {
      return stored;
    }
    // No signal at all (first-ever visit): matches config.toml's
    // default_theme, corrected within a tick by classObserver if wrong.
    return "dark";
  }

  // Mirrors ZVn's change effect (see file header) by hand: setTheme
  // itself isn't reachable from outside React, so the class toggle,
  // localStorage write and CSS-var copy it performs are reproduced here.
  function applyTheme(themeName) {
    var root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(themeName);
    localStorage.setItem("vite-ui-theme", themeName);
    var vars = window.theme && window.theme[themeName];
    if (vars) {
      Object.keys(vars).forEach(function (key) {
        root.style.setProperty(key, vars[key]);
      });
    }
  }

  // Reparents `btn` next to Chainlit's native (hidden via CSS) toggle
  // when the authenticated header is mounted, matching its className so
  // ours reads as a normal icon button in that row; otherwise falls
  // back to the fixed glass pill used on /login. See file header for
  // why this can't be a one-shot decision. insertBefore/className
  // writes are idempotent no-ops when already in the right place, so
  // this is safe to call on every mutation.
  function positionThemeToggle(btn) {
    var nativeToggle = document.getElementById("theme-toggle");
    if (nativeToggle && nativeToggle.parentNode) {
      btn.className = nativeToggle.className;
      if (btn.nextSibling !== nativeToggle || btn.parentNode !== nativeToggle.parentNode) {
        nativeToggle.parentNode.insertBefore(btn, nativeToggle);
      }
    } else {
      btn.className = "aiip-theme-toggle--floating";
      if (btn.parentNode !== document.body) {
        document.body.appendChild(btn);
      }
    }
  }

  // Chainlit's /logo endpoint (chainlit/server.py get_logo, a plain
  // route on the shared FastAPI app — not SPA-only) is what both
  // injectLoginHeading's badge and auth_base.html's static logo use to
  // stay theme-aware, since neither can rely on a hardcoded file for
  // both palettes. Called once at setup (so a page loaded already in
  // light mode doesn't show the dark-mode logo until the first click)
  // and again on every toggle click.
  function syncThemeAwareLogos(themeName) {
    var badgeLogo = document.querySelector("#aiip-login-logo-badge img");
    if (badgeLogo) {
      badgeLogo.src = "/logo?theme=" + themeName;
    }
    var authLogo = document.getElementById("aiip-auth-logo");
    if (authLogo) {
      authLogo.src = "/logo?theme=" + themeName;
    }
  }

  function injectThemeToggle() {
    var existing = document.getElementById("aiip-theme-toggle");
    if (existing) {
      positionThemeToggle(existing);
      return true;
    }

    var btn = document.createElement("button");
    btn.id = "aiip-theme-toggle";
    btn.type = "button";

    function render() {
      var target = currentTheme() === "light" ? "dark" : "light";
      btn.innerHTML = target === "light" ? SUN_ICON : MOON_ICON;
      btn.setAttribute(
        "aria-label",
        target === "light" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"
      );
    }

    btn.addEventListener("click", function () {
      var next = currentTheme() === "light" ? "dark" : "light";
      applyTheme(next);
      render();
      syncThemeAwareLogos(next);
    });

    render();
    syncThemeAwareLogos(currentTheme());
    positionThemeToggle(btn);

    // Corrects a wrong first guess from currentTheme()'s last resort
    // (see its comment) the moment ZVn's mount effect actually sets the
    // class — attributeFilter keeps this to just that one signal,
    // ignoring the unrelated childList churn the other observers below
    // deal with.
    new MutationObserver(function () {
      render();
      syncThemeAwareLogos(currentTheme());
    }).observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    return true;
  }

  function injectForgotPasswordLink() {
    if (document.getElementById("aiip-forgot-password-link")) {
      return true;
    }

    var passwordInput = document.getElementById("password");
    if (!passwordInput) {
      return false;
    }

    var fieldWrapper = passwordInput.closest("div.grid");
    var labelRow = fieldWrapper && fieldWrapper.querySelector(":scope > div:first-child");
    if (!labelRow) {
      return false;
    }

    var link = document.createElement("a");
    link.id = "aiip-forgot-password-link";
    link.href = "/auth/forgot-password";
    link.textContent = "¿Olvidaste tu contraseña?";
    labelRow.appendChild(link);
    return true;
  }

  function injectLoginHeading() {
    if (document.getElementById("aiip-login-heading")) {
      return true;
    }

    // .flex.flex-1.items-center.justify-center is the card's own
    // vertical-centering wrapper (verified in LKn, same bundle) — unique
    // to the login page, sibling of the logo above it in the same
    // column. Inserting right before it places the heading between the
    // logo and the card without touching either.
    var cardWrapper = document.querySelector(".flex.flex-1.items-center.justify-center");
    if (!cardWrapper || !cardWrapper.parentNode) {
      return false;
    }

    var heading = document.createElement("div");
    heading.id = "aiip-login-heading";

    var badge = document.createElement("div");
    badge.id = "aiip-login-logo-badge";
    var isLight = document.documentElement.classList.contains("light");
    var logoImg = document.createElement("img");
    logoImg.src = "/logo?theme=" + (isLight ? "light" : "dark");
    logoImg.alt = "AIIP";
    badge.appendChild(logoImg);

    var title = document.createElement("h2");
    title.id = "aiip-login-heading-title";
    title.textContent = "Asistente Inteligente de Inmunodeficiencias Primarias";

    var subtitle = document.createElement("p");
    subtitle.id = "aiip-login-heading-subtitle";
    subtitle.textContent = "Acompañamiento informativo para familias · Disponible 24/7";

    heading.appendChild(badge);
    heading.appendChild(title);
    heading.appendChild(subtitle);
    cardWrapper.parentNode.insertBefore(heading, cardWrapper);
    return true;
  }

  injectThemeToggle();
  // Never disconnects: unlike the one-shot injections below, the toggle
  // needs re-evaluating for as long as the page lives, since SPA
  // navigation can move it between /login and the authenticated shell
  // any number of times without a script reload (see file header).
  // Calls injectThemeToggle() rather than positionThemeToggle()
  // directly: our button lives inside React-owned DOM once docked in
  // the header row, so a React unmount there (e.g. logout) can take it
  // down too — injectThemeToggle() re-creates it in that case instead
  // of handing positionThemeToggle a null element.
  var themeToggleObserver = new MutationObserver(function () {
    injectThemeToggle();
  });
  themeToggleObserver.observe(document.body, { childList: true, subtree: true });

  var forgotDone = injectForgotPasswordLink();
  var headingDone = injectLoginHeading();
  if (forgotDone && headingDone) {
    return;
  }

  var observer = new MutationObserver(function () {
    if (!forgotDone) {
      forgotDone = injectForgotPasswordLink();
    }
    if (!headingDone) {
      headingDone = injectLoginHeading();
    }
    if (forgotDone && headingDone) {
      observer.disconnect();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();

/* AIIP — indicador de "pensando" con efecto de máquina de escribir
 * (16 jul 2026, ampliado el mismo día tras feedback de Marcos).
 *
 * main_family.py::_answer envía un cl.Message(content="") antes de
 * empezar el streaming (D-035); mientras dura eso, style.css oculta la
 * tarjeta vacía (.message-content:empty) y anima solo el avatar
 * (aiip-avatar-pulse). Eso deja la espera muda: sin texto, un pulso
 * silencioso puede leerse como que la app se ha colgado, y este es un
 * asistente sobre inmunodeficiencias primarias — quien pregunta puede
 * estar en un momento delicado, así que el texto no debe sonar clínico
 * ni generar alarma, solo dar sensación de progreso en un tono cálido
 * y de acompañamiento.
 *
 * Independiente de la IIFE de arriba (no depende de su `return`
 * temprano cuando ambas inyecciones del login ya están hechas): esta
 * función debe seguir observando durante toda la vida de la página,
 * incluida la vista de chat autenticada donde ese `return` nunca
 * llegó a importar.
 *
 * Selectores reutilizan los ya verificados en style.css
 * (`.ai-message .message-content`, `img[alt^="Avatar for"]`) — no se
 * inventan nuevos hooks de DOM aquí.
 */
(function () {
  var THINKING_MESSAGES = [
    "Buscando información fiable para acompañarte.",
    "Revisando con calma las fuentes disponibles...",
    "Cada pregunta resuelta es un paso más hacia la tranquilidad.",
    "Preparando una respuesta clara, a tu ritmo.",
    "No estás solo/a en esto: seguimos aquí, buscando lo mejor para ti.",
    "Conectando con el conocimiento que puede ayudarte hoy.",
    "Un momento — queremos darte una respuesta bien fundamentada.",
    "Organizando la información con cuidado, casi lista.",
  ];
  var TYPE_CHAR_MS = 32;
  var PAUSE_AFTER_TYPE_MS = 1600;

  // ai-message (elemento real del DOM) -> { wrapperEl, typedEl, typeTimer,
  // pauseTimer }. Un Map normal (no WeakMap) porque también se recorre
  // para purgar instancias cuyo elemento ya no está en el documento
  // (mensajes que Chainlit desmonta al cambiar de hilo).
  var instances = new Map();

  function isThinking(aiMessageEl) {
    var content = aiMessageEl.querySelector(".message-content");
    return !!content && content.childNodes.length === 0;
  }

  // Teclea `message` carácter a carácter en `inst.typedEl`; al terminar,
  // programa una pausa (cursor parpadeando sobre el texto completo,
  // legible) antes de pasar a la siguiente frase. El cursor en sí no se
  // toca desde aquí — es un <span> hermano siempre presente con su
  // propia animación CSS continua (ver .aiip-thinking-cursor).
  function typeMessage(inst, index) {
    var message = THINKING_MESSAGES[index];
    inst.typedEl.textContent = "";
    var charIndex = 0;

    inst.typeTimer = setInterval(function () {
      charIndex++;
      inst.typedEl.textContent = message.slice(0, charIndex);
      if (charIndex >= message.length) {
        clearInterval(inst.typeTimer);
        inst.typeTimer = null;
        var nextIndex = (index + 1) % THINKING_MESSAGES.length;
        inst.pauseTimer = setTimeout(function () {
          typeMessage(inst, nextIndex);
        }, PAUSE_AFTER_TYPE_MS);
      }
    }, TYPE_CHAR_MS);
  }

  function startThinking(aiMessageEl) {
    if (instances.has(aiMessageEl)) {
      return;
    }

    // .message-content no es hijo directo de .ai-message: el bundle
    // compilado de Chainlit (chainlit/frontend/dist/assets/index-*.js)
    // envuelve avatar y contenido en dos hijos flex de la fila
    // ("ai-message flex gap-4 w-full"): el avatar, y un wrapper interno
    // ("flex flex-col items-start ... flex-grow gap-2") que es quien de
    // verdad ocupa el ancho restante y contiene .message-content. Un
    // primer intento colgaba este nodo directamente de aiMessageEl —
    // eso lo convertía en un TERCER hijo de la fila exterior, compitiendo
    // por espacio con ese wrapper (que ya reclama todo lo disponible vía
    // flex-grow): el resultado visual era el texto anclado al borde
    // derecho, creciendo hacia la izquierda con cada carácter tecleado.
    // Montarlo dentro de ese mismo wrapper, justo después del
    // .message-content vacío, lo hace ocupar la posición donde
    // aparecerá el texto real — ancho fijo, ancla izquierda, sin saltos.
    var content = aiMessageEl.querySelector(".message-content");
    var mount = content && content.parentElement;
    if (!mount) {
      return;
    }

    var wrapperEl = document.createElement("div");
    wrapperEl.className = "aiip-thinking-text";
    var typedEl = document.createElement("span");
    typedEl.className = "aiip-thinking-typed";
    var cursorEl = document.createElement("span");
    cursorEl.className = "aiip-thinking-cursor";
    wrapperEl.appendChild(typedEl);
    wrapperEl.appendChild(cursorEl);
    mount.insertBefore(wrapperEl, content.nextSibling);

    var inst = { wrapperEl: wrapperEl, typedEl: typedEl, typeTimer: null, pauseTimer: null };
    instances.set(aiMessageEl, inst);

    var startIndex = Math.floor(Math.random() * THINKING_MESSAGES.length);
    typeMessage(inst, startIndex);
  }

  function stopThinking(aiMessageEl) {
    var inst = instances.get(aiMessageEl);
    if (!inst) {
      return;
    }
    if (inst.typeTimer) {
      clearInterval(inst.typeTimer);
    }
    if (inst.pauseTimer) {
      clearTimeout(inst.pauseTimer);
    }
    if (inst.wrapperEl.parentNode) {
      inst.wrapperEl.parentNode.removeChild(inst.wrapperEl);
    }
    instances.delete(aiMessageEl);
  }

  function syncThinkingIndicators() {
    document.querySelectorAll(".ai-message").forEach(function (el) {
      if (isThinking(el)) {
        startThinking(el);
      } else {
        stopThinking(el);
      }
    });
    // Mensajes desmontados del DOM (cambio de hilo, borrado) cuyos
    // timers quedarían huérfanos si no se limpian aquí explícitamente.
    instances.forEach(function (_inst, el) {
      if (!document.body.contains(el)) {
        stopThinking(el);
      }
    });
  }

  new MutationObserver(syncThinkingIndicators).observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  syncThinkingIndicators();
})();

/* AIIP — clase específica para el pie "Fuentes consultadas" (16 jul 2026)
 *
 * D-026 (rag/pipeline.py::_build_sources_section) añade, de forma
 * determinista, un encabezado + listado de enlaces al final de la
 * respuesta — nunca generado por el LLM. style.css usaba hasta ahora un
 * selector puramente estructural (`[role="article"]:last-of-type:has(+
 * ul:last-child)`, `ul:last-child`) para darle estilo, asumiendo que esa
 * lista era siempre la última cosa en .message-content. Problema real
 * (Marcos, 16 jul 2026): `:last-child` solo comprueba la posición de un
 * elemento entre sus propios hermanos, no si es lo último en
 * .message-content en general — así que cualquier lista con viñetas
 * dentro de la propia respuesta (p. ej. si el LLM termina su respuesta
 * enumerando síntomas) que resultase ser el último bloque también
 * heredaba el estilo "de pie de página", atenuándola por error.
 *
 * `_SOURCES_HEADINGS` en rag/pipeline.py es un diccionario fijo de
 * exactamente 3 strings ("Fuentes consultadas:"/"Sources consulted:"/
 * "Fonts consultades:"); `detect_language` (rag/language.py) nunca
 * produce un idioma sin entrada ahí — `_build_sources_section` cae a
 * "es" si el idioma detectado no es es/en/ca. Ese encabezado es texto
 * controlado por nuestro propio backend, no por el LLM, así que
 * emparejarlo por contenido exacto desde JS es más fiable que cualquier
 * heurística de posición en el DOM: solo se etiqueta un `<ul>` como
 * "sección de fuentes" cuando el `[role="article"]` inmediatamente
 * anterior es, carácter a carácter, uno de esos 3 encabezados.
 *
 * Reutiliza el patrón ya establecido en este fichero (MutationObserver
 * sobre document.body, idempotente vía comprobación de classList) en
 * vez de acoplarse al observer de startThinking/syncThinkingIndicators
 * de arriba — mismo motivo que ese bloque es su propia IIFE: son
 * preocupaciones independientes, cada una con su propio ciclo de vida.
 */
(function () {
  var SOURCES_HEADINGS = [
    "Fuentes consultadas:",
    "Sources consulted:",
    "Fonts consultades:",
  ];

  function tagSourcesSections() {
    document.querySelectorAll(".ai-message .message-content").forEach(function (contentEl) {
      contentEl.querySelectorAll('[role="article"]').forEach(function (article) {
        if (article.classList.contains("aiip-sources-heading")) {
          return;
        }
        var text = article.textContent.trim();
        if (SOURCES_HEADINGS.indexOf(text) === -1) {
          return;
        }
        article.classList.add("aiip-sources-heading");
        var list = article.nextElementSibling;
        if (list && list.tagName === "UL") {
          list.classList.add("aiip-sources-list");
        }
      });
    });
  }

  new MutationObserver(tagSourcesSections).observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  tagSourcesSections();
})();

/* AIIP — pulido de UI del onboarding (E-14 T-08, D-090)
 *
 * Título por contenido, no por posición: el saludo (main_family.py::
 * _greeting) dejó de ser garantizadamente el primer mensaje del hilo en
 * cuanto T-01/T-02/T-03 empezaron a anteponerle el gate de consentimiento
 * y las preguntas de perfil — style.css usaba
 * `[data-step-type="assistant_message"]:first-child` para darle su
 * tratamiento de título (gradiente, sin avatar), un selector puramente
 * posicional que dejó de ser fiable. Mismo mecanismo que
 * tagSourcesSections arriba: etiquetar por contenido. Lista de matchers
 * (HEADING_PREFIXES, todos por prefijo — ambos textos son dinámicos, con
 * o sin ", {nombre}"): el saludo ("Buenos días"/"Buenas tardes"/"Buenas
 * noches") y, desde D-090 Ronda 2, el título de cierre de onboarding
 * ("Todo listo") que main_family.py::_onboarding_complete_title envía al
 * terminar de preguntar o reproducir algún dato pendiente. La ronda 1 de
 * este fix incluía también una cabecera fija "Antes de empezar..." antes
 * del gate de consentimiento — descartada en la Ronda 2 a favor de
 * reordenar el propio saludo/bienvenida al principio de on_chat_start, así
 * que ya no hay un matcher de texto exacto para ella.
 *
 * Riesgo aceptado (mismo perfil que SOURCES_HEADINGS arriba): si una
 * respuesta del pipeline RAG empezara literalmente por uno de esos
 * prefijos, se etiquetaría como título por error. Baja probabilidad, no
 * se mitiga aquí.
 *
 * "**Selected:**..." (D-090 Ronda 1, ampliado en Ronda 2): al responder un
 * AskActionMessage, Chainlit reescribe el contenido de ese mismo paso a
 * "**Selected:** <label>" en vez de añadir un paso nuevo (a diferencia de
 * AskUserMessage, donde la pregunta se queda fija y la respuesta es un
 * paso aparte), así que la pregunta original desaparecía del hilo al
 * responder. Fix en dos partes: main_family.py ahora envía la pregunta
 * completa como su propio cl.Message ANTES del AskActionMessage (que pasa
 * a llevar solo un texto corto de llamada a la acción); y
 * tagSelectedAsUserBubble (abajo) detecta el paso reescrito, le quita el
 * prefijo "Selected:" y lo etiqueta para que se vea como una burbuja de
 * usuario normal — así la respuesta de botón queda indistinguible de una
 * respuesta escrita a mano. Nunca coincide con los matchers de heading, así
 * que tampoco hereda ese tratamiento.
 * Ronda 2 reutiliza el mismo mecanismo para las burbujas de "replay":
 * cuando `_ensure_patient_profile()` retoma un onboarding a medias en una
 * sesión nueva, reproduce cada dato ya guardado con el mismo prefijo
 * "**Selected:**" (mismo cl.Message normal, no un AskActionMessage real),
 * así que este mismo tagger las detecta y restyla sin código nuevo.
 *
 * Botones centrados: los wrappers de botones del gate de consentimiento
 * (Acepto/Ahora no) y de "sobre quién" (Sobre mí/Sobre otra persona)
 * comparten la misma clase estructural que los starter chips (T-05) y
 * los iconos de copiar/editar mensaje — no hay un selector propio para
 * "esta fila de botones es de onboarding". Igual que arriba, se
 * etiqueta por contenido: se lee la `label` de cada `<button>` hijo del
 * wrapper y, si el conjunto coincide exactamente con uno de los dos
 * pares esperados, se añade `aiip-centered-actions` solo a ese wrapper
 * — los starter chips y los iconos de mensaje nunca coinciden con esos
 * conjuntos, así que no se ven afectados.
 */
(function () {
  var HEADING_PREFIXES = ["Buenos días", "Buenas tardes", "Buenas noches", "Todo listo"];
  var BUTTON_ROW_LABEL_SETS = [
    ["Acepto", "Ahora no"],
    ["Sobre mí", "Sobre otra persona"],
  ];
  // Matches the rendered textContent of the step Chainlit rewrites after a
  // button press — markdown's "**Selected:**" bold syntax is stripped by
  // the time it reaches the DOM (the article renders <strong>Selected:</strong>),
  // so this tolerates both the rendered form and the raw markdown form,
  // rather than assuming which one actually reaches textContent.
  var SELECTED_PREFIX_RE = /^\*{0,2}Selected:\*{0,2}\s*/;

  function matchesHeadingText(text) {
    return HEADING_PREFIXES.some(function (prefix) {
      return text.indexOf(prefix) === 0;
    });
  }

  function tagHeadingTitles() {
    document.querySelectorAll('[data-step-type="assistant_message"]').forEach(function (step) {
      if (step.classList.contains("aiip-heading-title")) {
        return;
      }
      var article = step.querySelector(".message-content [role=\"article\"]");
      if (!article) {
        return;
      }
      if (matchesHeadingText(article.textContent.trim())) {
        step.classList.add("aiip-heading-title");
      }
    });
  }

  function labelSetMatches(labels, expected) {
    if (labels.length !== expected.length) {
      return false;
    }
    var sortedLabels = labels.slice().sort();
    var sortedExpected = expected.slice().sort();
    return sortedLabels.every(function (label, index) {
      return label === sortedExpected[index];
    });
  }

  function tagCenteredActionRows() {
    document.querySelectorAll(".-ml-1\\.5.flex.items-center.flex-wrap").forEach(function (wrapper) {
      if (wrapper.classList.contains("aiip-centered-actions")) {
        return;
      }
      var labels = Array.prototype.map.call(wrapper.querySelectorAll("button"), function (btn) {
        return btn.textContent.trim();
      });
      var matches = BUTTON_ROW_LABEL_SETS.some(function (expected) {
        return labelSetMatches(labels, expected);
      });
      if (matches) {
        wrapper.classList.add("aiip-centered-actions");
      }
    });
  }

  function tagSelectedAsUserBubble() {
    document.querySelectorAll('[data-step-type="assistant_message"]').forEach(function (step) {
      if (step.classList.contains("aiip-selected-as-user-bubble")) {
        return;
      }
      var article = step.querySelector(".message-content [role=\"article\"]");
      if (!article) {
        return;
      }
      var text = article.textContent.trim();
      if (!SELECTED_PREFIX_RE.test(text)) {
        return;
      }
      article.textContent = text.replace(SELECTED_PREFIX_RE, "");
      step.classList.add("aiip-selected-as-user-bubble");
    });
  }

  function tagOnboardingUi() {
    tagHeadingTitles();
    tagCenteredActionRows();
    tagSelectedAsUserBubble();
  }

  new MutationObserver(tagOnboardingUi).observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  tagOnboardingUi();
})();

/* AIIP — foco automático de la caja de texto al terminar de escribir el
 * agente (E-14 T-08, D-090 Ronda 3, quinta pieza de QA en vivo, 24 jul
 * 2026).
 *
 * Comportamiento general del chat, no específico de onboarding (se aborda
 * aquí por conveniencia, ya que este fichero se estaba tocando de todos
 * modos): al terminar de escribir el agente cualquier respuesta (RAG
 * normal u onboarding), el usuario debería poder ponerse a escribir sin
 * tener que hacer clic primero en la caja de texto.
 *
 * No basta con reutilizar isThinking()/stopThinking() (arriba en este
 * mismo fichero) tal cual: esas detectan el INICIO del streaming
 * (.message-content pasa de 0 hijos a tener contenido), no el final. La
 * señal de fin usada aquí es la desaparición del propio cursor de
 * streaming de Chainlit — `<span class="inline-block loading-cursor">`,
 * la misma clase real y verificada que restyla `.inline-block.loading-
 * cursor` en style.css (permanece en el DOM mientras llegan tokens,
 * Chainlit la retira al terminar) — en vez de inventar un debounce sobre
 * mutaciones de texto, que sería una heurística de tiempo en vez de un
 * hecho real del DOM.
 *
 * Selector del `<textarea>` (`#message-composer textarea`, `#message-
 * composer` ya confirmado en otras reglas de style.css como el wrapper
 * real del input) asumido a partir de que es un `<textarea>` estándar de
 * shadcn/Tailwind (mismo stack que el resto de la UI) — no verificado
 * contra el DOM real en vivo como el resto de selectores "verified in the
 * live DOM" de este fichero; a confirmar en QA.
 */
(function () {
  var wasStreaming = false;

  function isCurrentlyStreaming() {
    var messages = document.querySelectorAll(".ai-message");
    if (!messages.length) {
      return false;
    }
    var last = messages[messages.length - 1];
    return !!last.querySelector(".inline-block.loading-cursor");
  }

  function focusComposer() {
    var textarea = document.querySelector("#message-composer textarea");
    if (textarea) {
      textarea.focus();
    }
  }

  function syncComposerFocus() {
    var streaming = isCurrentlyStreaming();
    if (wasStreaming && !streaming) {
      focusComposer();
    }
    wasStreaming = streaming;
  }

  new MutationObserver(syncComposerFocus).observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  syncComposerFocus();
})();
