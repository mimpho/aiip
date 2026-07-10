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

      // injectLoginHeading's badge <img> picks its theme once, at
      // insertion time (see file header) — keep it in sync so it
      // doesn't go stale relative to the toggle it sits right next to.
      var badgeLogo = document.querySelector("#aiip-login-logo-badge img");
      if (badgeLogo) {
        badgeLogo.src = "/logo?theme=" + next;
      }
    });

    render();
    positionThemeToggle(btn);

    // Corrects a wrong first guess from currentTheme()'s last resort
    // (see its comment) the moment ZVn's mount effect actually sets the
    // class — attributeFilter keeps this to just that one signal,
    // ignoring the unrelated childList churn the other observers below
    // deal with.
    new MutationObserver(render).observe(document.documentElement, {
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
