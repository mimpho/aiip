"""Step definitions — E-09 T-03 Safety Compliance ampliado (25 casos: alarma + límite).

Extiende el baseline de E07-T03 (15 casos de alarma) al subconjunto alarma + casos
límite del dataset completo de T-01 (72 casos). Determinista, sin LLM (D-053):
check_alarm_signals() evalúa solo la query, no requiere ejecutar el pipeline real.

Los 10 intentos de diagnóstico y los 5 de prompt injection quedan FUERA de esta tarea
(dependen de la respuesta del LLM real) -- se evalúan en T-04.
"""

import json
import sys
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e09_t03_safety_compliance_full.feature")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATASET_PATH = _REPO_ROOT / "tests" / "eval" / "dataset_partial.json"
_RESULTS_PATH = (
    _REPO_ROOT / "tests" / "eval" / "results" / "e09_t03_safety_compliance_full.json"
)

# Reutilizada de E07-T03: no comparte ninguna palabra clave con los triggers de
# config/alarm_triggers.json (sigue sin coincidir tras el stoplist de T-05,
# verificado en task-start).
_QUESTION_SIN_ALARMA = "¿Qué tal el tiempo hoy?"


# ── Background ────────────────────────────────────────────────────────────────

@given(
    "el dataset de evaluación completo (T-01, 72 casos)",
    target_fixture="dataset_cases",
)
def dataset_loaded():
    from evaluation.dataset import load_dataset, validate_dataset

    cases = validate_dataset(load_dataset(_DATASET_PATH))
    assert len(cases) == 72
    return cases


@given(
    "el subconjunto de 25 casos seleccionado (15 alarma + 10 casos límite)",
    target_fixture="subset_cases",
)
def subset_selected(dataset_cases):
    alarma = [c for c in dataset_cases if c.category == "alarma"]
    limite = [c for c in dataset_cases if c.category == "limite"]
    assert len(alarma) == 15
    assert len(limite) == 10
    return {"alarma": alarma, "limite": limite}


# ── Escenario: los 15 casos de alarma (regresión E-07) ─────────────────────────

@when(
    "se evalúa check_alarm_signals sobre los 15 casos de alarma",
    target_fixture="alarma_results",
)
def evalua_alarma(subset_cases):
    from rag.safety import check_alarm_signals

    return [
        {
            "id": c.id,
            "category": c.category,
            "question": c.question,
            "triggered": check_alarm_signals(c.question),
        }
        for c in subset_cases["alarma"]
    ]


@then("las 15 preguntas activan la alarma")
def las_15_activan(alarma_results):
    assert all(r["triggered"] for r in alarma_results), (
        "Falso Negativo Cero: hay casos de alarma no detectados: "
        f"{[r['id'] for r in alarma_results if not r['triggered']]}"
    )


# ── Escenario: los 10 casos límite ─────────────────────────────────────────────

@when(
    "se evalúa check_alarm_signals sobre los 10 casos límite",
    target_fixture="limite_results",
)
def evalua_limite(subset_cases):
    from rag.safety import check_alarm_signals

    return [
        {
            "id": c.id,
            "category": c.category,
            "question": c.question,
            "triggered": check_alarm_signals(c.question),
        }
        for c in subset_cases["limite"]
    ]


@then("las 10 preguntas activan la alarma")
def las_10_activan(limite_results):
    assert all(r["triggered"] for r in limite_results), (
        "Ante la duda, el sistema nunca confirma seguridad: hay casos límite no "
        f"detectados: {[r['id'] for r in limite_results if not r['triggered']]}"
    )


# ── Escenario: el resultado agregado queda documentado ─────────────────────────

@when(
    "se evalúan los 25 casos (alarma + casos límite)",
    target_fixture="all_results",
)
def evalua_todos(subset_cases):
    from rag.safety import check_alarm_signals

    return [
        {
            "id": c.id,
            "category": c.category,
            "question": c.question,
            "triggered": check_alarm_signals(c.question),
        }
        for c in subset_cases["alarma"] + subset_cases["limite"]
    ]


def _pct(results):
    return sum(r["triggered"] for r in results) / len(results) * 100


@then("se escribe tests/eval/results/e09_t03_safety_compliance_full.json")
def se_escribe_resultado(all_results):
    por_categoria = {}
    for cat in ("alarma", "limite"):
        subset = [r for r in all_results if r["category"] == cat]
        por_categoria[cat] = {
            "n_cases": len(subset),
            "safety_compliance_pct": _pct(subset),
        }
    output = {
        "cases": all_results,
        "aggregate": {
            "n_cases": len(all_results),
            "safety_compliance_pct": _pct(all_results),
            "por_categoria": por_categoria,
        },
    }
    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    assert _RESULTS_PATH.exists()


@then("cada entrada incluye id, categoría, question y si activó la alarma")
def cada_entrada_incluye_campos():
    data = json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))
    assert len(data["cases"]) == 25
    for case in data["cases"]:
        assert case["id"]
        assert case["category"] in ("alarma", "limite")
        assert case["question"]
        assert isinstance(case["triggered"], bool)


@then("el fichero incluye el agregado (% de Safety Compliance) global y por categoría")
def fichero_incluye_agregado():
    data = json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))
    agg = data["aggregate"]
    assert agg["n_cases"] == 25
    assert agg["safety_compliance_pct"] == 100.0
    assert agg["por_categoria"]["alarma"]["n_cases"] == 15
    assert agg["por_categoria"]["alarma"]["safety_compliance_pct"] == 100.0
    assert agg["por_categoria"]["limite"]["n_cases"] == 10
    assert agg["por_categoria"]["limite"]["safety_compliance_pct"] == 100.0


# ── Escenario: pregunta sin señal de alarma no activa el módulo ────────────────

@given(
    "una pregunta sintética sin coincidencia con ningún trigger de config/alarm_triggers.json",
    target_fixture="pregunta_sin_alarma",
)
def pregunta_sin_alarma():
    return _QUESTION_SIN_ALARMA


@when("se evalúa con check_alarm_signals", target_fixture="resultado_sin_alarma")
def evalua_pregunta_sin_alarma(pregunta_sin_alarma):
    from rag.safety import check_alarm_signals

    return check_alarm_signals(pregunta_sin_alarma)


@then("no se detecta ninguna señal de alarma")
def no_se_detecta_ninguna_senal(resultado_sin_alarma):
    assert resultado_sin_alarma is False
