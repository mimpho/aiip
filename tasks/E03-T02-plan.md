# Plan — E-03 T-02 Esquema Supabase: tabla profiles + RLS

## Contexto técnico

**supabase-py v2.31.0** está instalado. API relevante:

- `create_client(url, SUPABASE_ANON_KEY)` — cliente anónimo, sujeto a RLS
- `create_client(url, SUPABASE_SERVICE_KEY)` — cliente admin, bypass RLS — usar
  solo en fixtures de test para crear/borrar usuarios y perfiles
- `client.auth.sign_in_with_password({"email": ..., "password": ...})` — devuelve
  `AuthResponse` con `.session.access_token`
- Para queries autenticadas con RLS activo: crear un cliente con anon key y
  llamar a `client.postgrest.auth(access_token)` antes de la query
- Admin API: `create_client(url, SERVICE_KEY).auth.admin.create_user({...})`

**Migración SQL:** Supabase ejecuta los ficheros de `supabase/migrations/` en
orden alfabético. Convención de nombre: `YYYYMMDDHHMMSS_descripcion.sql`.

**Trigger `updated_at`:** PostgreSQL no actualiza `updated_at` solo. Hay que
crear una función y un trigger en la propia migración:
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

## Ficheros a crear / modificar

| Fichero | Acción | Propósito |
|---|---|---|
| `supabase/migrations/YYYYMMDDHHMMSS_create_profiles.sql` | crear | Tabla profiles, RLS, trigger updated_at |
| `auth/supabase_client.py` | crear | Cliente Supabase + get_or_create_profile |
| `tests/step_defs/test_e03_t02.py` | crear | Step definitions para e03_t02_profiles_schema.feature |
| `tests/conftest.py` | crear | Fixtures compartidas: clientes Supabase, usuarios de test |

## Orden de implementación TDD

Sigue este orden exacto. Cada ítem = un ciclo rojo→verde antes de pasar al siguiente.

1. **La tabla profiles tiene el esquema correcto**
   - Step defs en: `tests/step_defs/test_e03_t02.py`
   - Implementación en: `supabase/migrations/YYYYMMDDHHMMSS_create_profiles.sql`
   - Notas: la migración crea la tabla con id (FK+PK a auth.users), role (CHECK),
     created_at (default now()), updated_at (default now()), trigger updated_at,
     y habilita RLS. Aplicar con `supabase db push` o desde el dashboard de Supabase.
     El test verifica la estructura consultando `information_schema.columns`.

2. **updated_at se actualiza automáticamente**
   - Implementación: el trigger de la migración del paso anterior
   - Notas: el test actualiza un campo del perfil con service key y compara
     updated_at antes y después.

3. **RLS bloquea lectura del perfil de otro usuario**
   - Notas: fixture crea usuarios A y B con admin API. El test autentica A,
     obtiene su access_token, crea cliente con `postgrest.auth(token)` e intenta
     leer el perfil de B. Espera error de RLS (código 42501 o resultado vacío).

4. **RLS bloquea escritura en el perfil de otro usuario**
   - Notas: mismo patrón — usuario A intenta UPDATE en el perfil de B.

5. **RLS permite leer y escribir el propio perfil**
   - Notas: usuario A lee y actualiza su propio perfil con su token. Ambas
     operaciones deben tener éxito.

6. **get_or_create_profile crea perfil nuevo si no existe**
   - Implementación en: `auth/supabase_client.py`
   - Notas: la función usa service key internamente (necesita bypass RLS para
     crear el perfil en el momento del login). Verifica que tras la llamada
     existe exactamente un perfil con el user_id dado.

7. **get_or_create_profile devuelve perfil existente sin duplicar**
   - Notas: llama a la función dos veces con el mismo user_id. Verifica que
     el COUNT de perfiles con ese user_id es 1.

## Restricciones a respetar

- `SUPABASE_SERVICE_KEY` solo en fixtures de test y en `get_or_create_profile`
  — nunca en código de aplicación que el usuario pueda triggear directamente
- Privacy by design (D-009): la tabla profiles solo almacena id, role,
  created_at, updated_at — sin datos de salud en esta tarea
- Commits en inglés, una responsabilidad por commit

## Lo que queda fuera de esta tarea

- Signup/login real (T-03)
- Integración con Chainlit (T-05)
- Campos adicionales de perfil como nombre, tipo de IDP, historial (E-08)
- La columna `onboarding_data` o similar va en E-08, no aquí
