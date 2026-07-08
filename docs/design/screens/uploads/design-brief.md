# Design Brief — AIIP Visual Identity

> Input document for E-02 (Visual Identity). To be used as context for Claude Design / v0 or similar tools.
> This is a brief, not a spec — the goal is to inform, not constrain.

---

## Product

**AIIP** — conversational assistant for Primary Immunodeficiencies (PID).
Two distinct profiles sharing a common visual base, differentiated by tone and accent color.

---

## Audience

| Profile | Who | Emotional context |
|---|---|---|
| Family | Parent/caregiver with no medical background | Uncertainty, concern, need for reassurance |
| Professional | Immunologist or specialist nursing staff | Need for density, references, technical credibility |

---

## Visual tone

Dark mode. Elegant, not aggressive. Trustworthy without clinical coldness. Sophisticated but accessible.

The family profile leans warmer and more human. The professional profile leans denser and more technical. Both share the same typographic system and logo.

---

## Exploratory reference (Lovable v1.8 prototype)

A first visual exploration was built in Lovable and reviewed by the collaborating immunologist. Use as a starting point, not a constraint — alternative proposals are welcome.

**What to keep:**
- Dark mode base — works well for both profiles
- Serif display typography for H1 — adds warmth and elegance
- Triangular "A" logomark on a rounded container — recognizable, simple
- Amber/orange for safety warnings — critical UI element for the Zero False Negative principle
- Profile differentiation via accent color (blue family / green professional)

**What to reconsider:**
- The dark blue and dark green bases are very similar in feel — explore whether a stronger differentiation makes sense, or whether a single shared base with accent-only differentiation is cleaner
- The logo is a placeholder — a more refined version is welcome

**Live prototype URLs (for reference):**
- Family: https://aiip-familly-app.lovable.app/
- Professional: https://aiip-professional-app.lovable.app/

## UI inspiration reference

**Google Stitch** (https://stitch.withgoogle.com) — dark interface with frosted glass / backdrop-filter blur effects on input areas. The prompt input box uses a glassmorphism treatment that feels modern and premium without being heavy.

Potential application for AIIP: the chat input box could use a similar frosted glass effect — a subtle `backdrop-filter: blur()` with a semi-transparent background, giving depth to the input area without distracting from the conversation. This is a design idea to explore, not a requirement.

Use as visual inspiration for UI surface treatments, not as a layout or color reference.

---

## Deliverables

All tokens expressed as CSS custom properties in `public/tokens.css`.

### Color tokens

```css
/* Base */
--color-bg
--color-surface
--color-surface-raised
--color-border

/* Text */
--color-text-primary
--color-text-secondary
--color-text-muted

/* Accent — shared base + profile variants */
--color-accent
--color-accent-hover
--color-accent-family
--color-accent-professional

/* Semantic */
--color-warning          /* safety alerts — Zero False Negative */
--color-warning-bg
--color-success
--color-error
```

### Typography tokens

```css
--font-display            /* serif — H1, H2 */
--font-body               /* sans-serif — body, UI */
--font-mono               /* monospace — code, references */

--text-xs / --text-sm / --text-base / --text-lg / --text-xl / --text-2xl
--font-weight-normal / --font-weight-medium / --font-weight-bold
--line-height-tight / --line-height-base / --line-height-relaxed
```

### Spacing & radius tokens

```css
--radius-sm / --radius-md / --radius-lg / --radius-xl
--space-1 through --space-12  (4px base scale)
```

### Logo

AIIP is an informational tool for families and professionals dealing with Primary Immunodeficiencies — a rare, chronic condition affecting the immune system, primarily in children. The logo should carry semantic weight that reflects this context.

**Values to express:**
- **Protection** — the immune system as a shield; the tool as a safety net for families navigating uncertainty
- **Medical trust** — rigour, validated sources, clear limits; not a diagnostic tool
- **Human warmth** — a companion for families in difficult moments, not a cold clinical interface
- **Clarity** — information, not diagnosis; transparency about what the tool does and doesn't do

**Design direction:**
The Lovable prototype uses a triangle with a stylized "A" — legible but generic. Explore richer visual metaphors that reference the medical/immunological domain while remaining accessible and warm: a simplified antibody or cell structure, a shield with human resonance, an abstract form suggesting protection and connection. Avoid overly clinical or cold iconography.

The logo must work as a single-color SVG at small sizes (32px header) and read clearly at larger sizes (64px landing). A refined placeholder is acceptable for TFM delivery — the mark should feel considered, not temporary.

- SVG exportable, single color (uses `--color-accent`)
- Two sizes: 32px (UI header) and 64px (landing page)

---

## Technical constraints

- No build dependencies — native CSS only
- Must work as theming in **Chainlit** via `public/style.css` (overrides Chainlit CSS variables)
- Must work in **Supabase Auth UI** via `auth/style.css` (overrides Supabase theme variables)
- Responsive from day one — mobile-first

---

## Token consumption architecture

```
public/tokens.css        ← single source of truth
    ↓
public/style.css         ← Chainlit theming (maps tokens to Chainlit CSS vars)
auth/style.css           ← Supabase Auth UI theming (maps tokens to Supabase vars)
```

---

*Created: june 2026 — E-02 Visual Identity*
