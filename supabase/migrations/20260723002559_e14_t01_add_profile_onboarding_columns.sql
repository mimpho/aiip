-- E-14 T-01 — Amplía profiles con datos de onboarding de perfil y consentimiento de salud
-- Privacy by design (D-009): la migración original de `profiles` (20260628021829_create_profiles.sql)
-- declaraba explícitamente "sin datos de salud en esta tabla". Esta migración introduce datos de
-- salud a propósito, condicionado al gate de consentimiento de T-02 (D-009, actualización del
-- 9 de julio de 2026): health_data_consent_at se registra una única vez, siempre vía service key
-- (mismo patrón que role/user_metadata hoy), no por el cliente autenticado. Sin restricción de
-- columna adicional ni CHECK de rango en patient_age (D-088): sin ruta de cliente directo contra
-- Supabase en el stack actual (Chainlit backend Python), validación de rango se deja a la capa de
-- aplicación (T-03).

ALTER TABLE profiles
  ADD COLUMN user_name text,
  ADD COLUMN patient_name text,
  ADD COLUMN patient_diagnosis text,
  ADD COLUMN patient_age integer,
  ADD COLUMN patient_context text,
  ADD COLUMN health_data_consent_at timestamptz;
