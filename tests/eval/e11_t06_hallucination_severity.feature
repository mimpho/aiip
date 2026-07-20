# E-11 T-06 — Hallucination Rate: desglose por bandas de severidad
# Tipo: Reporting/documentación — sin TDD, con rama+PR (precedente E06-T07).
#
# Contexto (D-058, epic-start E-11 18 jul 2026; D-069, task-start T-06 20 jul 2026):
# Hallucination Rate se define como % de casos con faithfulness < 1.0 (conteo binario,
# D-058) — 93.75% (30/32 casos) post-E-09. Bandas de severidad aprobadas:
#   Grave        (< 0.5)
#   Moderada     (0.5–0.85)
#   Leve         (0.85–<1.0)   ← incluye el límite exacto 0.85 (D-069)
#   Sin desviación (1.0)
# El caso en banda Grave, sobre los scores reales post-T-02, es eval_06 (Faithfulness
# 0.385) — no eval_15, que D-068 ya cerró (Faithfulness 0.875, banda Leve). eval_06 ya
# figuraba en hallazgo B (Answer Relevancy 0.0, docs/evaluation.md §5.1) y ha caído dos
# veces (0.722 → 0.615 → 0.385) sin causa registrada, así que se investiga antes de
# cerrar T-06 (D-069), a diferencia de otros hallazgos aplazados sin investigar en esta
# épica.

Feature: Hallucination Rate — desglose por bandas de severidad

  Como responsable del proyecto AIIP
  Quiero complementar el Hallucination Rate binario con un desglose por bandas de
  severidad de Faithfulness
  Para que el informe final distinga alucinación real (contenido inventado) de matices
  de redacción que no representan un riesgo clínico

  Scenario: Las bandas de severidad quedan definidas y documentadas
    Given las bandas Grave (< 0.5), Moderada (0.5–0.85), Leve (0.85–<1.0, límite incluido)
      y Sin desviación (1.0)
    When se documentan en "docs/evaluation.md"
    Then queda explícito que las bandas se derivan del score de Faithfulness por caso, no de
      una nueva llamada a la API (mismo principio de D-058: reutilizar datos ya calculados)

  Scenario: El desglose se calcula sobre los scores ya existentes tras esta épica
    Given los scores de Faithfulness de los 32 casos informativo/otro_idioma
      (`tests/eval/results/e09_t02_ragas_full_scores.json`, post T-01/T-02/T-03/T-04/T-05,
      sin re-medición desde T-02 — D-066/D-067 no tocan retrieval ni requieren nueva RAGAS)
    When se clasifica cada caso en su banda
    Then se obtiene el conteo y porcentaje de casos por banda

  Scenario: eval_06 queda investigado antes de confirmarse como el caso Grave
    Given que eval_06 sustituye a eval_15 como único caso en banda Grave (D-069), ya
      identificado en hallazgo B (docs/evaluation.md §5.1) y con Faithfulness cayendo dos
      veces a lo largo de la épica (0.722 → 0.615 → 0.385) sin causa registrada
    When Antigravity ejecuta la investigación dirigida (tasks/E11-T06-plan.md): reproduce
      la pregunta contra el pipeline actual y captura respuesta real + contexto recuperado
    Then se documenta si la hipótesis ya existente de hallazgo B (cita inline de
      documento/páginas) explica la caída, o si aparece una causa distinta asociada a T-01
      (ampliación de KB) o T-02 (peso adaptativo de BM25)

  Scenario: El binario y el desglose conviven en el informe
    Given el Hallucination Rate binario (% de casos con faithfulness < 1.0)
    When se documenta en "docs/evaluation.md"
    Then el binario se mantiene tal cual, sin suavizarlo
    And el desglose por bandas aparece como métrica complementaria en la misma sección,
      no sustituyendo al binario

  Scenario: Marcos confirma las bandas y el resultado final
    Given el desglose calculado sobre los datos reales de esta épica y el resultado de la
      investigación de eval_06
    When Marcos lo revisa
    Then confirma si las bandas y la explicación de eval_06 son suficientes para el informe
      final (T-07), o si hace falta un ajuste adicional
