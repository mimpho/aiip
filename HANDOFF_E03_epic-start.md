# Handoff — E-03 epic-start en curso

> Nota de traspaso para continuar en Cowork. Fichero temporal, no forma parte
> de la documentación del repo — bórralo cuando E-03 esté cerrada o el Paso 1
> quede aprobado y volcado a `tests/features/`.
> Generado: 27 junio 2026.

---

## Contexto

Se invocó `/epic-start` para arrancar **E-03 — Autenticación y separación de
perfiles** (antes E-02; renumerada cuando se insertó E-02 = Identidad visual,
ya completada). Sigue el proceso definido en `skills/epic-start/SKILL.md`
(3 pasos con gates: descomposición → formalización Gherkin → ramas).

Antes de arrancar la épica se corrigieron restos de la renumeración anterior
(ya commiteado y pusheado a `main` en `930e615`):
- `backlog/epics.md` — Fase 1.5: `E-08`→`E-09`, `E-09`→`E-10`
- `docs/tech-spec.md` §13 — IDs de decisión y referencias de épica
- `AGENTS.md` — el proceso de 6 pasos arranca en "E-03 en adelante" (E-02 fue
  diseño, no código)

---

## Estado actual: Paso 1 (descomposición en tareas) — GATE ABIERTO

**T-01 ya está aprobada, revisada y registrada** — es la única que avanzó más allá del chat:
- Fichero: [`tests/features/e03_t01_oauth_google.feature`](tests/features/e03_t01_oauth_google.feature)
- Tipo: configuración (estilo E-01) — sin rama, sin PR. Checklist manual + script de verificación (pendiente de escribir cuando se ejecute la tarea).
- Decisión de arquitectura asociada: **D-014** en `decisions.md` — Supabase es el único broker de identidad OAuth (Chainlit nunca usa su `@cl.oauth_callback` nativo). Ya commiteada en el working tree (ver más abajo, *pendiente de push*).

Revisión crítica hecha sobre T-01 (por si se quiere aplicar el mismo nivel de rigor a T-02–T-06):
1. Ambigüedad de quién hace de broker OAuth (resuelta → D-014)
2. Faltaba el consent screen de Google y su modo "Testing" (con test users)
3. Faltaba la allowlist de Redirect URLs en Supabase (no basta con activar el provider)
4. La redirect URI debía ser el valor concreto, no una descripción genérica
5. Riesgo de confundir las credenciales OAuth con `GOOGLE_API_KEY` (Gemini) — nunca van en `.env`
6. Un solo Client ID de Google compartido por las dos apps (familiar/profesional)

**T-02 a T-06 siguen solo en esta conversación, sin fichero.** Para cada una, lanzar `task-start` desde Cowork — la skill incluye revisión crítica, resolución de puntos abiertos, `.feature` formal (pytest-bdd) y plan de implementación en `tasks/`. No hay paso previo de aprobación separado; el gate está dentro de la propia skill.

### T-02 — Esquema Supabase: tabla `profiles` + RLS

Como desarrollador del proyecto AIIP
Quiero una tabla `profiles` con políticas RLS
Para almacenar el rol (familiar/profesional) ligado a `auth.users` de forma segura

Criterios:
- Dado que aplico la migración, entonces existe `profiles` con `id` (FK a `auth.users`), `role` (CHECK familiar/profesional), `created_at`, `updated_at`.
- Dado un usuario A autenticado, cuando intenta leer el perfil de un usuario B, entonces RLS lo bloquea.
- Dado un usuario autenticado, cuando lee/escribe su propio perfil, entonces RLS lo permite.

Notas: migración SQL en `supabase/migrations/`. Bloquea T-03 y T-04.

### T-03 — Registro y login con email/password, rol fijo por app

Como usuario (familiar o profesional)
Quiero registrarme e iniciar sesión con email y contraseña
Para acceder a AIIP sin depender de una cuenta de Google

Criterios:
- Dado que me registro desde la app familiar, cuando se completa el signup, entonces mi perfil se crea con `role="familiar"`.
- Dado que me registro desde la app profesional, cuando se completa el signup, entonces mi perfil se crea con `role="profesional"`.
- Dado que ya tengo cuenta, cuando inicio sesión con credenciales correctas, entonces obtengo sesión válida con rol recuperable.
- Dado que introduzco credenciales incorrectas, entonces recibo un error claro y no se crea sesión.

Notas: `auth/supabase_client.py` (signup/login/get_or_create_profile). El rol viene de una constante `APP_ROLE` por instancia, nunca de un selector visible. Depende de T-02.

### T-04 — Login con Google OAuth, rol fijo por app

Como usuario (familiar o profesional)
Quiero iniciar sesión con mi cuenta de Google
Para acceder sin crear una contraseña nueva

Criterios:
- Dado que inicio sesión con Google desde la app familiar por primera vez, entonces se crea mi perfil con `role="familiar"`.
- Dado que ya tengo perfil y repito login con Google, entonces no se duplica el perfil ni se sobrescribe el rol existente.

Notas: depende de T-01, T-02. Reutiliza `get_or_create_profile` de T-03. Usa `supabase.auth.sign_in_with_oauth` (NO el `@cl.oauth_callback` nativo de Chainlit — ver D-014).

### T-05 — Integración de autenticación en Chainlit

Como usuario autenticado
Quiero que Chainlit reconozca mi sesión y mi rol
Para que el pipeline futuro (E-04) sepa qué KB y tono aplicar

Criterios:
- Dado que inicio sesión vía el formulario de Chainlit (`password_auth_callback`) con credenciales válidas, entonces se crea una sesión `cl.User` con el rol incluido.
- Dado que inicio sesión vía Google, entonces la sesión de Chainlit incluye el rol igualmente (el flujo OAuth lo dispara y resuelve Supabase, no el callback nativo de Chainlit).
- Dado que las credenciales son inválidas, entonces Chainlit rechaza el acceso sin crear sesión.

Notas: depende de T-03, T-04. Define la app familiar base (`main_familiar.py`) sobre la que clonar la profesional en T-06.

### T-06 — Separación de URLs por perfil (familiar real + profesional stub)

Como usuario familiar
Quiero que no haya ninguna referencia visible a una versión profesional
Para no generar confusión sobre el alcance del producto

Como usuario profesional
Quiero acceder a una ruta separada
Para una futura evolución (F-01) sin afectar a la experiencia familiar

Criterios:
- Dado que accedo a la app familiar, entonces no hay ningún enlace ni texto que mencione un perfil profesional.
- Dado que accedo a la app profesional, cuando inicio sesión, entonces veo una pantalla "en construcción" sin KB ni RAG.
- ⚠️ **PUNTO ABIERTO sin resolver:** si un usuario con `role="profesional"` se autentica en la app familiar (o viceversa) — ¿se bloquea con error, o se deja pasar porque cada app ya filtra por su propio `APP_ROLE`? Decidir antes de aprobar esta tarea.

Notas: depende de T-05. Dos entrypoints Chainlit compartiendo `auth/`.

---

## Cambios sin commitear en el working tree

```
decisions.md       — nueva entrada D-014 (Supabase como broker OAuth) + índice + footer renumerado (D-015/16/17)
docs/tech-spec.md  — §13 sincronizado con la renumeración anterior de D-014/15/16
```

Marcos confirmó el contenido pero **aún no ha confirmado el push a `main`** — preguntar antes de commitear si se retoma desde Cowork.

---

## Próximo paso al retomar

1. Rama `epic/E03-auth` ya creada. PR de T-01 (script de verificación) → `epic/E03-auth` pendiente de merge.
2. Para T-02 en adelante: lanzar `skills/task-start/SKILL.md` desde Cowork para cada tarea en orden.
   - La skill revisa la definición, resuelve puntos abiertos (incluido el ⚠️ de T-06), genera el `.feature` y el plan en `tasks/`.
   - Cada tarea de código va en rama `task/E03-TXX-nombre` desde `epic/E03-auth`.

Referencia: `skills/task-start/SKILL.md`.
