"""Step definitions — E-07 T-03 Safety Compliance baseline (15 casos de alarma)."""

import json
import sys
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e07_t03_safety_compliance_baseline.feature")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATASET_PATH = _REPO_ROOT / "tests" / "eval" / "dataset_partial.json"
_RESULTS_PATH = (
    _REPO_ROOT / "tests" / "eval" / "results" / "e07_t03_safety_compliance_baseline.json"
)

# No comparte ninguna palabra clave (>= 6 caracteres) con los triggers de
# config/alarm_triggers.json (verificado manualmente, ver E07-T03-plan.md).
_QUESTION_SIN_ALARMA = "¿Qué tal el tiempo hoy?"


# ── Background ────────────────────────────────────────────────────────────────

@given(
    "el dataset parcial de evaluación cargado desde tests/eval/dataset_partial.json",
    target_fixture="dataset_entries",
)
def dataset_loaded():
    from evaluation.dataset import load_dataset

    return load_dataset(_DATASET_PATH)


@given("los 15 casos con is_alarm en true seleccionados", target_fixture="alarm_cases")
def alarm_cases_selected(dataset_entries):
    from evaluation.dataset import validate_dataset

    cases = validate_dataset(dataset_entries)
    alarm_cases = [c for c in cases if c.is_alarm]
    assert len(alarm_cases) == 15
    return alarm_cases


# ── Escenario: todos los casos de alarma activan el módulo ─────────────────────

@when(
    "se evalúa check_alarm_signals sobre cada uno de los 15 casos",
    target_fixture="alarm_results",
)
def evalua_check_alarm_signals(alarm_cases):
    from rag.safety import check_alarm_signals

    return [
        {"id": c.id, "question": c.question, "triggered": check_alarm_signals(c.question)}
        for c in alarm_cases
    ]


@then("las 15 preguntas activan la alarma")
def las_15_preguntas_activan_la_alarma(alarm_results):
    assert all(r["triggered"] for r in alarm_results), (
        "Falso Negativo Cero: hay casos de alarma no detectados: "
        f"{[r['id'] for r in alarm_results if not r['triggered']]}"
    )


@then("el Safety Compliance baseline es del 100%")
def safety_compliance_baseline_100(alarm_results):
    pct = sum(r["triggered"] for r in alarm_results) / len(alarm_results) * 100
    assert pct == 100.0


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


# ── Escenario: el resultado queda documentado para T-04 ────────────────────────

@then("se escribe tests/eval/results/e07_t03_safety_compliance_baseline.json")
def se_escribe_resultado(alarm_results):
    output = {
        "cases": alarm_results,
        "aggregate": {
            "n_cases": len(alarm_results),
            "safety_compliance_pct": sum(r["triggered"] for r in alarm_results)
            / len(alarm_results)
            * 100,
        },
    }
    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    assert _RESULTS_PATH.exists()


@then("cada entrada incluye id, question y si activó la alarma")
def cada_entrada_incluye_campos():
    data = json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))
    assert len(data["cases"]) == 15
    for case in data["cases"]:
        assert case["id"]
        assert case["question"]
        assert isinstance(case["triggered"], bool)


@then("el fichero incluye el agregado (% de Safety Compliance)")
def fichero_incluye_agregado():
    data = json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))
    assert data["aggregate"]["n_cases"] == 15
    assert data["aggregate"]["safety_compliance_pct"] == 100.0
