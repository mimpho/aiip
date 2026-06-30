# Plan — E-03 T-06 Separación de URLs por perfil (familiar real + profesional stub)

## Contexto técnico

### Cómo deshabilitar el formulario de Chainlit

Chainlit no expone API Python para manipular el formulario de login — es un componente React compilado. El mecanismo oficial para personalizarlo es CSS + JS custom, referenciados desde `.chainlit/config.toml`:

```toml
[UI]
custom_css = "/public/style.css"
custom_js  = "/public/stub.js"
```

La app profesional usará su propio `config.toml` (en `.chainlit_profesional/`) que apunta a un JS que:
1. Inyecta el banner "En construcción" encima del formulario
2. Deshabilita todos los `<input>` y el `<button>` de submit via DOM mutation

### Separación de configs por entrypoint

Chainlit busca `.chainlit/config.toml` relativo al directorio desde el que se lanza. Para tener configuraciones distintas por app sin duplicar todo, se crean dos directorios:

```
.chainlit/              ← config familiar (ya existe o se crea aquí)
.chainlit_profesional/  ← config profesional (apunta a public_profesional/)
```

Arranque:
```bash
# Familiar
chainlit run main_familiar.py --port 8000

# Profesional (desde el mismo repo, override de config dir via CHAINLIT_CONFIG_DIR)
CHAINLIT_CONFIG_DIR=.chainlit_profesional chainlit run main_profesional.py --port 8001
```

> **Nota:** `CHAINLIT_CONFIG_DIR` no está documentado oficialmente pero es la variable de entorno que Chainlit respeta internamente para localizar el config. Si no funciona, la alternativa es lanzar la app profesional desde un subdirectorio o usar `--root-path`. Antigravity debe verificar esto al arrancar y ajustar si es necesario.

### Variables de entorno de puertos

Se añaden a `.env.example`:
```
PORT_FAMILIAR=8000
PORT_PROFESIONAL=8001
```

### Por qué la app profesional no importa auth/

`main_profesional.py` no registra `@cl.password_auth_callback` ni importa `supabase_client`. Chainlit sin ese decorator arranca en modo "sin auth" — el usuario llega directamente a la pantalla que muestre `@cl.on_chat_start`, que en este caso será el stub "En construcción" (o bien el formulario deshabilitado via JS antes de que Chainlit muestre nada).

La estrategia más robusta: registrar `@cl.password_auth_callback` que **siempre devuelve None** — así Chainlit muestra el formulario de login (que el JS deshabilita visualmente) sin que nadie pueda autenticarse. El módulo `auth/` no se importa.

---

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `main_profesional.py` | crear | Entrypoint Chainlit profesional — password_auth_callback que siempre devuelve None |
| `.chainlit/config.toml` | crear | Config Chainlit para app familiar — referencia a design/public/style.css |
| `.chainlit_profesional/config.toml` | crear | Config Chainlit para app profesional — referencia a CSS/JS del stub |
| `design/profesional/stub.js` | crear | JS que inyecta banner y deshabilita inputs del formulario de login |
| `design/profesional/style.css` | crear | CSS del stub (tokens de E-02 con accent color profesional) |
| `.env.example` | modificar | Añadir PORT_FAMILIAR y PORT_PROFESIONAL |
| `tests/step_defs/test_e03_t06.py` | crear | Step definitions pytest-bdd para T-06 |

---

## Orden de implementación TDD

Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

### 1. La app familiar no expone referencias al perfil profesional

- Scenario: `la app familiar no expone referencias al perfil profesional`
- Step definitions: `tests/step_defs/test_e03_t06.py`
- Implementación: verificar que `main_familiar.py` no contiene las strings "profesional" ni "F-01"

Notas:
- Este test es estático — lee el código fuente de `main_familiar.py` y el CSS/JS de la app familiar y busca la ausencia de las strings prohibidas.
- No requiere levantar Chainlit.
- Si en el futuro se añade alguna referencia justificada, el test documentará la excepción.

### 2. La app profesional tiene password_auth_callback que siempre devuelve None

- Scenario: `la app profesional no instancia nada del módulo auth`
- Step definitions: añadir en `tests/step_defs/test_e03_t06.py`
- Implementación: `main_profesional.py`

Notas:
- Verificar que `main_profesional.py` no importa nada de `auth/` ni de `supabase_auth`.
- Verificar que el `password_auth_callback` registrado devuelve `None` para cualquier combinación de username/password.
- El test llama directamente al callback (igual que en T-05) sin levantar Chainlit.

```python
# main_profesional.py — estructura esperada
import chainlit as cl

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    # Stub: acceso siempre bloqueado — perfil profesional fuera del alcance del TFM
    return None

@cl.on_chat_start
async def on_chat_start():
    # No debería ejecutarse nunca (auth siempre falla), pero por seguridad:
    await cl.Message(content="Perfil profesional no disponible.").send()
```

### 3. Los puertos están definidos en .env.example

- Scenario: `las dos apps arrancan en puertos distintos sin conflicto`
- Step definitions: añadir en `tests/step_defs/test_e03_t06.py`
- Implementación: modificar `.env.example`

Notas:
- Test estático: verificar que `.env.example` contiene `PORT_FAMILIAR` y `PORT_PROFESIONAL`.
- No requiere levantar ninguna app.

### 4. El stub JS deshabilita inputs y muestra banner

- Scenario: `la app profesional muestra el formulario deshabilitado`
- Step definitions: añadir en `tests/step_defs/test_e03_t06.py`
- Implementación: `design/profesional/stub.js`

Notas:
- Test estático sobre el contenido del JS: verificar que el fichero existe y contiene las palabras clave del comportamiento esperado ("disabled", "En construcción" o equivalente, y la lógica de MutationObserver o querySelector).
- No se testea el comportamiento en browser (eso sería E-05 / validación manual).

Estructura esperada de `design/profesional/stub.js`:
```javascript
// Espera a que el DOM esté listo y el formulario de Chainlit renderizado
function disableLoginForm() {
  const inputs = document.querySelectorAll('input');
  const buttons = document.querySelectorAll('button[type="submit"], button');
  inputs.forEach(el => el.disabled = true);
  buttons.forEach(el => el.disabled = true);
}

function injectBanner() {
  if (document.getElementById('aiip-stub-banner')) return;
  const banner = document.createElement('div');
  banner.id = 'aiip-stub-banner';
  banner.innerHTML = `
    <div style="...">
      <h2>En construcción</h2>
      <p>El perfil profesional está fuera del alcance del TFM y no está disponible en esta versión.</p>
    </div>
  `;
  document.body.prepend(banner);
}

// Chainlit renderiza dinámicamente — usar MutationObserver
const observer = new MutationObserver(() => {
  disableLoginForm();
  injectBanner();
});
observer.observe(document.body, { childList: true, subtree: true });
```

---

## Restricciones a respetar

- **D-007 (Separación de perfiles):** familiar y profesional son productos distintos. Ningún enlace entre ellos en la UI.
- **D-010 (Agnóstico de proveedor):** puertos en `.env`, nunca hardcodeados.
- **D-013 (Design tokens):** el CSS del stub profesional consume los mismos tokens de `design/public/tokens.css` — no duplicar variables.
- **AGENTS.md:** `main_profesional.py` no debe importar ni instanciar nada de `auth/`.

## Lo que queda fuera de esta tarea

- Theming visual completo de la app profesional (colores de accent distintos) → E-05 / F-01.
- Lógica real del perfil profesional (KB, tono, pipeline) → F-01.
- Botón "Continuar con Google" en la app familiar → E-05.
- Configuración de `redirect_to` por entorno (dev/prod) → al arrancar E-05 o en el deploy.
- Validación visual en browser del banner y formulario deshabilitado → validación manual al ejecutar la tarea.
