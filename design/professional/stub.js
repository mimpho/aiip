/**
 * AIIP — Perfil Profesional stub
 * Inyecta el banner "En construcción" y deshabilita el formulario de login.
 * El formulario de Chainlit se renderiza dinámicamente vía React, por lo que
 * se usa MutationObserver para interceptar el DOM en cuanto aparece.
 */

function disableLoginForm() {
  document.querySelectorAll('input').forEach(el => { el.disabled = true; });
  document.querySelectorAll('button[type="submit"], button').forEach(el => { el.disabled = true; });
}

function injectBanner() {
  if (document.getElementById('aiip-stub-banner')) return;
  const banner = document.createElement('div');
  banner.id = 'aiip-stub-banner';
  banner.innerHTML = `
    <div style="
      position: fixed;
      top: 0; left: 0; right: 0;
      z-index: 9999;
      background: var(--color-surface, #171D25);
      border-bottom: 2px solid var(--color-accent-professional, #2FC18C);
      padding: 24px 32px;
      text-align: center;
      font-family: var(--font-body, system-ui, sans-serif);
    ">
      <h2 style="
        margin: 0 0 8px;
        color: var(--color-accent-professional, #2FC18C);
        font-size: 24px;
        font-weight: 600;
      ">En construcción</h2>
      <p style="
        margin: 0;
        color: var(--color-text-secondary, #A6B2BF);
        font-size: 16px;
      ">
        El perfil profesional está fuera del alcance del TFM
        y no está disponible en esta versión.
      </p>
    </div>
  `;
  document.body.prepend(banner);
}

const observer = new MutationObserver(() => {
  disableLoginForm();
  injectBanner();
});

observer.observe(document.body, { childList: true, subtree: true });

// Ejecutar también al cargar por si el DOM ya está listo
disableLoginForm();
injectBanner();
