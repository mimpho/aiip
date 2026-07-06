-- Refactor: nombres de rol de perfil a inglés (family/professional).
-- La tabla profiles está vacía en el momento de esta migración (sin backfill de datos).
-- Ver refactor/E06-family-professional-naming.

ALTER TABLE profiles DROP CONSTRAINT profiles_role_check;

ALTER TABLE profiles
  ADD CONSTRAINT profiles_role_check CHECK (role IN ('family', 'professional'));
