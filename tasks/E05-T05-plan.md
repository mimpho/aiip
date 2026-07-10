# Plan — E-05 T-05 Theming completo (tokens E-02) + responsive del chat

## Contexto técnico

### Resumen del hallazgo (D-038)

`design/public/style.css` (E-02) define variables `--cl-color-*` y clases `.cl-*`
que no existen en el Chainlit real (verificado contra el CSS compilado de
`chainlit==2.11.1` instalado en `.venv`). El origen es que esas clases se
inventaron para los comps estáticos de `docs/design/screens/` (canvas de
diseño, no HTML renderizado por Chainlit) y se llevaron sin verificar a
`design/public/style.css`. Esta tarea corrige eso.

### Mecanismo real: `public/theme.json`

Confirmado contra la documentación oficial
([docs.chainlit.io/customisation/theme](https://docs.chainlit.io/customisation/theme)):
Chainlit lee un fichero `theme.json` en el directorio `public/` y lo inyecta
como `window.theme` para fijar variables CSS con esquema shadcn. Estructura:

```json
{
  "custom_fonts": ["<url de Google Fonts>"],
  "variables": {
    "light": { "--background": "...", "--foreground": "...", "--primary": "...", ... },
    "dark":  { "--background": "...", "--foreground": "...", "--primary": "...", ... }
  }
}
```

Claves completas por modo (`light`/`dark`): `--font-sans`, `--font-mono`,
`--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`,
`--popover-foreground`, `--primary`, `--primary-foreground`, `--secondary`,
`--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`,
`--accent-foreground`, `--destructive`, `--destructive-foreground`,
`--border`, `--input`, `--ring`, `--radius` (solo en `light` según el ejemplo
oficial, se hereda en dark si no se repite), `--sidebar-background`,
`--sidebar-foreground`, `--sidebar-primary`, `--sidebar-primary-foreground`,
`--sidebar-accent`, `--sidebar-accent-foreground`, `--sidebar-border`,
`--sidebar-ring`.

**⚠️ Restricción no obvia, confirmada en la doc oficial: los colores van en
HSL, no en hex** — formato `"H S% L%"` (sin `hsl()`, sin comas). Es
obligatorio, no una preferencia de estilo.

### Conversión hex → HSL de los tokens principales (ya calculada, verificar el resto con la misma fórmula)

Calculado programáticamente desde `design/public/tokens.css`
(`colorsys.rgb_to_hls`, redondeado):

| Token AIIP | Hex | Variable Chainlit sugerida | HSL |
|---|---|---|---|
| `--color-bg` (dark) | `#0F1419` | `--background` (dark) | `210 25% 8%` |
| `--color-surface` (dark) | `#171D25` | `--card` / `--sidebar-background` (dark) | `214 23% 12%` |
| `--color-surface-raised` (dark) | `#1F2731` | `--popover` (dark) | `213 23% 16%` |
| `--color-border` (dark) | `#2B343F` | `--border` / `--input` (dark) | `213 19% 21%` |
| `--color-text-primary` (dark) | `#EEF2F7` | `--foreground` (dark) | `213 36% 95%` |
| `--color-text-secondary` (dark) | `#A6B2BF` | `--muted-foreground` (dark) | `211 16% 70%` |
| `--color-accent-family` (dark) | `#6E8BFF` | `--primary` / `--ring` (dark) | `228 100% 72%` |
| `--color-error` | `#E5565B` | `--destructive` (light y dark) | `358 73% 62%` |
| `--color-bg` (light) | `#F4F6F9` | `--background` (light) | `216 29% 97%` |
| `--color-surface` (light) | `#FFFFFF` | `--card` (light) | `0 0% 100%` |
| `--color-surface-raised` (light) | `#F8FAFC` | `--popover` (light) | `210 40% 98%` |
| `--color-border` (light) | `#E2E7ED` | `--border` / `--input` (light) | `213 23% 91%` |
| `--color-text-primary` (light) | `#1A2129` | `--foreground` (light) | `212 22% 13%` |
| `--color-text-secondary` (light) | `#5A6573` | `--muted-foreground` (light) | `214 12% 40%` |
| `--color-accent-family` (light) | `#5570E8` | `--primary` / `--ring` (light) | `229 76% 62%` |

Faltan por convertir con la misma fórmula (no bloqueante, mecánico):
`--color-warning`, `--color-success`, `--color-surface-raised` →
`--secondary`/`--muted`/`--accent` (shadcn distingue varios niveles de gris
donde AIIP solo tiene `surface`/`surface-raised`/`border` — usar buen juicio
para no aplanar la jerarquía visual, ej. `--muted` y `--secondary` pueden
compartir el mismo valor que `--surface-raised` si no hace falta más matiz).
`--radius` se pasa directamente en `rem`/`px` (no es un color, no lleva HSL):
usar `--radius-lg` de `tokens.css` (`14px` ≈ `0.875rem`).

`--font-sans` / `--font-mono`: usar `var(--font-body)` / `var(--font-mono)`
de `tokens.css` no funciona dentro de `theme.json` (es JSON estático, no CSS
vivo) — poner directamente `"'Hanken Grotesk', system-ui, sans-serif"` y
`"'JetBrains Mono', 'Courier New', monospace"`. `custom_fonts` lleva la URL
de Google Fonts ya usada en `style.css` (Spectral + Hanken Grotesk +
JetBrains Mono).

### Perfil profesional no aplica a esta tarea

`tokens.css` define `[data-profile="professional"]` para intercambiar el
accent, pensado para una sola app con selector — pero D-007 ya fijó URLs
separadas por perfil (no un selector runtime), y no hay nada en el código
actual que setee ese atributo. Para T-05 (solo app familiar), `theme.json`
codifica directamente el accent de familia como `--primary`. El accent
profesional es un theme.json propio de la futura app profesional (F-01),
fuera de esta tarea.

### Selectores de componentes reales — a identificar en Antigravity

`theme.json` resuelve la paleta base (colores, radios, fuentes), pero los
selectores específicos que hoy usa `style.css` para componentes concretos
(`.cl-message-user`, `.cl-input-wrapper` con el borde animado, `.cl-sidebar`,
`.cl-source-reference`, `.cl-suggestion-chip`, `.cl-alert-warning`) no
existen y hay que sustituirlos por selectores reales. El frontend de
Chainlit es Tailwind + shadcn compilado — no siempre hay clases semánticas.
Pistas encontradas en el bundle JS (`grep` sobre
`chainlit/frontend/dist/assets/index-*.js`): existen los strings
`"message-composer"`, `"chat-input"`, `"assistant_message"`, `"step"`,
`"data-step-type"` — probablemente ids/`data-testid`/atributos de datos, no
confirmado como selector CSS válido sin inspección en vivo. **Este punto se
resuelve en Antigravity**: arrancar el servidor Chainlit local, abrir
devtools, e identificar el selector real de cada componente antes de
escribirlo en `style.css`. No inventar selectores por analogía sin
verificarlos en el DOM renderizado.

### Verificar primero: cómo resuelve Chainlit `public_dir`

`chainlit/config.py`: `public_dir = os.path.join(APP_ROOT, "public")` y
`APP_ROOT = os.getenv("CHAINLIT_APP_ROOT", os.getcwd())`. El repo no tiene
documentado en ningún sitio (`README.md`, `docs/tech-spec.md`,
`.env.example`) el comando exacto para levantar `chainlit/main_family.py` de
forma que `/public/style.css` (referenciado en
`chainlit/family/config.toml`) resuelva a `design/public/`. Es plausible que
esto nunca se haya verificado — coherente con la hipótesis de D-038 de que
el theming de E-02 nunca se aplicó. **Primer paso de implementación:**
arrancar la app localmente, comprobar en la pestaña Network si
`/public/style.css` devuelve 200 con el contenido esperado o 404; si falla,
fijar `CHAINLIT_APP_ROOT` (o mover/symlinkear `design/public` a donde
resuelva `APP_ROOT`) y documentar el comando de arranque correcto — no
existe hoy en el repo y hace falta para que cualquier persona pueda levantar
la app con el theming aplicado.

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `design/public/theme.json` | crear | Mapea `tokens.css` al esquema real de Chainlit (light/dark, HSL) |
| `design/public/style.css` | modificar | Elimina el bloque `:root { --cl-color-*: ... }` (redundante con theme.json) y reescribe los selectores de componente sobre clases reales verificadas en devtools. Conserva la lógica del borde animado del input y el scrollbar, adaptando el selector. |
| `chainlit/family/config.toml` | verificar, modificar si hace falta | Confirmar que `custom_css = "/public/style.css"` sigue siendo correcto una vez resuelto `public_dir`; no necesita tocar `theme.json` (Chainlit lo autodetecta en `public/`) |
| Documentación del comando de arranque (README.md o docs/tech-spec.md, a decidir en Antigravity si no existe ya) | crear/ampliar | Deja constancia de cómo se lanza `main_family.py` para que `/public/` resuelva a `design/public/` |

No se toca `design/public/tokens.css` (sigue siendo la fuente de verdad de
valores) ni `design/auth/style.css` (fuera de alcance, D-031/T-06).

## Orden de implementación

Sin TDD — validación manual contra los escenarios de
`tests/features/e05_t05_theming_responsive.feature`, en este orden:

1. **Prerrequisito — arrancar la app y confirmar `public_dir`.** Sin esto,
   ningún cambio de CSS será visible. Documentar el hallazgo.
2. **Escenario 1 — `theme.json` se carga.** Crear `design/public/theme.json`
   con la tabla de conversión de arriba (completar los valores que faltan
   con la misma fórmula). Verificar en devtools que `--primary`,
   `--background`, etc. reflejan los valores de AIIP, no los defaults de
   Chainlit.
3. **Escenario 2 — desktop coincide con tokens/comp de referencia.**
   Reescribir `style.css` sobre selectores reales (mensajes, input, sidebar,
   chips, alerta warning). Comparar visualmente con
   `docs/design/screens/AIIP Phase 2 - Chat.dc.html` (variante Family ·
   Dark) — es referencia de diseño, no de selectores.
4. **Escenario 3 — responsive en viewport móvil (375px).** Añadir
   media queries donde haga falta; Chainlit ya es responsive por defecto
   (D-007), esto es sobre todo verificar que las adiciones de `style.css`
   no rompen ese comportamiento nativo.
5. **Escenario 4 — `cl.Step` respeta el theming.** Verificar que el paso
   "Documentos consultados" (D-035, T-03) hereda el theming general sin
   necesitar CSS adicional; si Chainlit lo pinta con un estilo por defecto
   no coherente, identificar su selector real y ajustarlo.

## Restricciones a respetar

- **D-013:** `tokens.css` sigue siendo la única fuente de verdad de valores;
  `theme.json`/`style.css` son traducciones, no un segundo lugar donde fijar
  valores nuevos.
- **D-007:** diseño responsive desde el inicio — Chainlit ya lo soporta
  nativamente, no introducir un framework CSS adicional (sin Tailwind
  propio, sin Shadcn/ui en el lado Python — D-013 ya lo descartó).
- **Reparto git:** rama `task/E05-T05-theming-responsive-chat` ya creada por
  Marcos. El agente en Antigravity no hace `push`/`merge`.
- **No tocar** `rag/`, `chainlit/main_family.py` (lógica), ni
  `design/auth/style.css`.

## Lo que queda fuera de esta tarea

- Theme.json / theming del perfil profesional (F-01).
- `design/auth/style.css` (Supabase Auth UI) — D-031/T-06.
- Iconografía custom de `cl.Step` o avatares — Chainlit los gestiona de
  forma nativa.
- Cambios de contenido o lógica de `chainlit/main_family.py` — esta tarea es
  solo CSS/JSON de theming.
