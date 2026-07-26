# E-14 T-01 — Esquema de perfil en Supabase
# Tipo: Configuración/DDL — sin TDD, mismo patrón que E11-T01/E13-T01/E06-T07
# (rama + PR igualmente, precedente feedback_task_type_no_tdd). Migración aplicada por el
# agente vía Supabase MCP (apply_migration), confirmado por Marcos en epic-start.
#
# Contexto (D-087, epic-start E-14): capa 2 de la antigua E-08 (memoria de perfil), extraída
# como épica propia. `profiles` hoy solo tiene `id`/`role` (D-009: "sin datos de salud en
# esta tabla" por diseño) — esta tarea lo cambia a propósito, ver nota en la propia migración.
#
# Decisiones de epic-start (23 jul 2026):
# - Nombres de columna en inglés, consistente con `role`/`created_at`/`updated_at` ya
#   existentes (D-008, migración 20260706214852).
# - `user_name` (quien chatea, cuenta) se separa de `patient_name` (de quién son los datos
#   clínicos, puede ser la misma persona u otra — ej. un hijo/a). Evita asumir que quien
#   escribe es el paciente (ya advertido en prompts/system_prompt_family.txt líneas 41-46).
# - "Tipo de IDP" se descarta como lista cerrada (se evaluó la clasificación IUIS 2024, pero
#   ni el propio Marcos sabría clasificar un diagnóstico conocido en su grupo IUIS) — queda
#   como `patient_diagnosis`, texto libre.
# - `health_data_consent_at`: marca de tiempo del consentimiento explícito de datos de salud
#   que implementa T-02 (D-009, gate diseñado en julio y nunca implementado hasta ahora).

Feature: Esquema de perfil en Supabase

  Como responsable técnico del proyecto AIIP
  Quiero que `profiles` tenga columnas para nombre de cuenta, datos del paciente y marca de
  consentimiento de datos de salud
  Para poder persistir el onboarding de E-14 fuera de `user_metadata`

  # Checklist de verificación manual tras aplicar la migración

  Scenario: Migración añade las columnas nuevas sin romper filas existentes
    Given la tabla "profiles" con las columnas "id", "role", "created_at", "updated_at" y filas
      ya existentes de usuarios reales
    When se aplica la migración de E-14 (Supabase MCP, apply_migration)
    Then "profiles" gana las columnas "user_name" (text), "patient_name" (text),
      "patient_diagnosis" (text), "patient_age" (integer), "patient_context" (text) y
      "health_data_consent_at" (timestamptz)
    And ninguna fila existente se pierde ni cambia su "id"/"role"/"created_at"/"updated_at"

  Scenario: Usuarios ya existentes quedan con las columnas nuevas en NULL
    Given un usuario que ya tenía perfil antes de esta migración
    When se consulta su fila tras la migración
    Then "user_name", "patient_name", "patient_diagnosis", "patient_age", "patient_context" y
      "health_data_consent_at" son NULL
    And el usuario puede seguir haciendo login sin que la migración le bloquee

  Scenario: La migración queda documentada como cambio consciente sobre D-009
    Given el comentario original en la migración de creación de "profiles" ("Privacy by
      design (D-009): sin datos de salud en esta tabla")
    When se revisa la nueva migración de E-14
    Then incluye un comentario explícito señalando que esta tarea introduce datos de salud a
      propósito, condicionado al gate de consentimiento de T-02
