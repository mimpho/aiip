/* AIIP — custom_js (D-040 punto 5)
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
 */
(function () {
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

  if (injectForgotPasswordLink()) {
    return;
  }

  var observer = new MutationObserver(function () {
    if (injectForgotPasswordLink()) {
      observer.disconnect();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
