"""Step definitions — E-07 T-01 Dataset de evaluación parcial."""

import sys
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../eval/e07_t01_partial_eval_dataset.feature")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATASET_PATH = _REPO_ROOT / "tests" / "eval" / "dataset_partial.json"


# ── Background ────────────────────────────────────────────────────────────────

@given("el fichero tests/eval/dataset_partial.json existe")
def dataset_file_exists():
    assert _DATASET_PATH.exists(), f"Fichero de dataset no encontrado: {_DATASET_PATH}"


# ── Given: entradas a validar ────────────────────────────────────────────────

@given(
    "el dataset parcial de evaluación cargado desde tests/eval/dataset_partial.json",
    target_fixture="dataset_entries",
)
def dataset_loaded():
    from evaluation.dataset import load_dataset

    return load_dataset(_DATASET_PATH)


@given("una entrada de dataset sin el campo expected_answer", target_fixture="dataset_entries")
def entry_without_expected_answer():
    return [
        {
            "id": "eval_test_invalid",
            "question": "¿Pregunta de prueba sin expected_answer?",
            "is_alarm": False,
            "profile": "familiar",
            "language": "es",
        }
    ]


# ── When compartido: validate_dataset ────────────────────────────────────────

@when("se valida su estructura", target_fixture="validation_result")
def valida_estructura(dataset_entries):
    from evaluation.dataset import validate_dataset

    try:
        return {"cases": validate_dataset(dataset_entries), "error": None}
    except ValueError as exc:
        return {"cases": None, "error": exc}


# ── Then: conteo total y por categoría ───────────────────────────────────────

@then("contiene exactamente 42 entradas")
def contiene_42_entradas(validation_result):
    assert len(validation_result["cases"]) == 42


@then("27 entradas corresponden a consultas informativas")
def entradas_informativas(validation_result):
    informativas = [c for c in validation_result["cases"] if not c.is_alarm]
    assert len(informativas) == 27


@then("15 entradas tienen is_alarm en true")
def entradas_alarma(validation_result):
    alarma = [c for c in validation_result["cases"] if c.is_alarm]
    assert len(alarma) == 15


# ── Then: schema obligatorio ─────────────────────────────────────────────────

@then("cada entrada incluye id, question, expected_answer, is_alarm, profile y language")
def cada_entrada_incluye_campos_obligatorios(validation_result):
    for case in validation_result["cases"]:
        assert case.id
        assert case.question
        assert case.expected_answer
        assert isinstance(case.is_alarm, bool)
        assert case.profile
        assert case.language


@then("ninguna entrada incluye el campo relevant_chunks")
def ninguna_entrada_incluye_relevant_chunks(validation_result):
    from evaluation.dataset import EvalCase

    for case in validation_result["cases"]:
        assert "relevant_chunks" not in EvalCase.model_fields
        assert not hasattr(case, "relevant_chunks")


@then('profile es "familiar" y language es "es" en todas las entradas')
def profile_y_language_correctos(validation_result):
    for case in validation_result["cases"]:
        assert case.profile == "familiar"
        assert case.language == "es"


# ── Then: unicidad ────────────────────────────────────────────────────────────

@then("no hay dos entradas con el mismo texto de question")
def sin_preguntas_duplicadas(validation_result):
    questions = [c.question for c in validation_result["cases"]]
    assert len(questions) == len(set(questions))


@then("no hay dos entradas con el mismo id")
def sin_ids_duplicados(validation_result):
    ids = [c.id for c in validation_result["cases"]]
    assert len(ids) == len(set(ids))


# ── Then: validación negativa ─────────────────────────────────────────────────

@then("la validación falla indicando qué campo obligatorio falta")
def validacion_falla_por_campo_ausente(validation_result):
    assert validation_result["cases"] is None
    assert validation_result["error"] is not None
    assert "expected_answer" in str(validation_result["error"]), (
        f"El error no identifica el campo ausente: {validation_result['error']!r}"
    )
