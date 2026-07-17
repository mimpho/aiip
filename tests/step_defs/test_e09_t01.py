"""Step definitions — E-09 T-01 Dataset de evaluación completo (72 casos)."""

import re
import sys
from pathlib import Path

from pytest_bdd import given, parsers, scenario, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATASET_PATH = _REPO_ROOT / "tests" / "eval" / "dataset_partial.json"
_FEATURE = "../eval/e09_t01_full_eval_dataset.feature"


# El escenario "Marcos revisa y aprueba el contenido de los 30 casos nuevos" no tiene
# asserts automatizados (es una revisión manual, mismo tratamiento que el equivalente
# de E07-T04) y por eso no se registra aquí con @scenario.

@scenario(_FEATURE, "Conteo total y por categoría del dataset ampliado")
def test_conteo_total_y_por_categoria():
    pass


@scenario(_FEATURE, "is_alarm es coherente con category en todo el dataset")
def test_is_alarm_coherente_con_category():
    pass


@scenario(_FEATURE, "Los casos de prompt injection incluyen los campos de ataque obligatorios")
def test_campos_prompt_injection_obligatorios():
    pass


@scenario(_FEATURE, "Los casos de otros idiomas están en inglés o catalán, no en castellano")
def test_otros_idiomas_no_castellano():
    pass


@scenario(_FEATURE, "El validador rechaza una entrada de prompt injection sin attack_type")
def test_rechaza_prompt_injection_sin_attack_type():
    pass


@scenario(_FEATURE, "El validador rechaza una entrada con category y is_alarm incoherentes")
def test_rechaza_category_is_alarm_incoherentes():
    pass


@scenario(_FEATURE, "No hay preguntas ni identificadores duplicados en el dataset ampliado")
def test_sin_duplicados():
    pass


@scenario(_FEATURE, "El subconjunto de seguridad completo queda identificable por category")
def test_subconjunto_de_seguridad():
    pass


# ── Background ────────────────────────────────────────────────────────────────

@given(
    "el dataset de evaluación completo cargado desde tests/eval/dataset_partial.json",
    target_fixture="dataset_entries",
)
def dataset_loaded():
    from evaluation.dataset import load_dataset

    return load_dataset(_DATASET_PATH)


# ── Given: entradas concretas ────────────────────────────────────────────────

@given(
    parsers.parse('una entrada con category "{category}"'),
    target_fixture="dataset_entries",
)
def entrada_con_category(dataset_entries, category):
    entrada = next(e for e in dataset_entries if e["category"] == category)
    return [entrada]


@given(
    "una entrada con category \"prompt_injection\" sin el campo attack_type",
    target_fixture="dataset_entries",
)
def entrada_prompt_injection_sin_attack_type(dataset_entries):
    entrada = next(e for e in dataset_entries if e["category"] == "prompt_injection").copy()
    entrada.pop("attack_type", None)
    return [entrada]


@given(
    "una entrada con category \"alarma\" e is_alarm en false",
    target_fixture="dataset_entries",
)
def entrada_alarma_is_alarm_false(dataset_entries):
    entrada = next(e for e in dataset_entries if e["category"] == "alarma").copy()
    entrada["is_alarm"] = False
    return [entrada]


# ── When compartido: validate_dataset ────────────────────────────────────────

@when("se valida su estructura", target_fixture="validation_result")
@when("se valida contra el schema", target_fixture="validation_result")
def valida_estructura(dataset_entries):
    from evaluation.dataset import validate_dataset

    try:
        return {"cases": validate_dataset(dataset_entries), "error": None}
    except ValueError as exc:
        return {"cases": None, "error": exc}


@when(
    "se selecciona el subconjunto de seguridad (category en alarma, diagnostico, "
    "limite o prompt_injection)",
    target_fixture="seguridad_subset",
)
def selecciona_subconjunto_seguridad(dataset_entries):
    categorias_seguridad = {"alarma", "diagnostico", "limite", "prompt_injection"}
    return [e for e in dataset_entries if e["category"] in categorias_seguridad]


# ── Then: conteo total y por categoría ───────────────────────────────────────

@then("contiene exactamente 72 entradas")
def contiene_72_entradas(validation_result):
    assert len(validation_result["cases"]) == 72


@then(parsers.parse('{count:d} entradas tienen category "{category}"'))
def entradas_tienen_category(validation_result, count, category):
    coinciden = [c for c in validation_result["cases"] if c.category == category]
    assert len(coinciden) == count


# ── Then: coherencia category/is_alarm ───────────────────────────────────────

@then('todas las entradas con category "alarma" tienen is_alarm en true')
def alarma_implica_is_alarm_true(validation_result):
    for case in validation_result["cases"]:
        if case.category == "alarma":
            assert case.is_alarm is True


@then('todas las entradas con category "informativo" tienen is_alarm en false')
def informativo_implica_is_alarm_false(validation_result):
    for case in validation_result["cases"]:
        if case.category == "informativo":
            assert case.is_alarm is False


# ── Then: campos de prompt injection ─────────────────────────────────────────

@then("incluye attack_type, expected_behavior y expected_safety_trigger")
def incluye_campos_prompt_injection(validation_result):
    for case in validation_result["cases"]:
        assert "attack_type" in type(case).model_fields
        assert "expected_behavior" in type(case).model_fields
        assert "expected_safety_trigger" in type(case).model_fields


@then("ninguno de los tres campos es null")
def ninguno_de_los_tres_campos_es_null(validation_result):
    for case in validation_result["cases"]:
        assert case.attack_type is not None
        assert case.expected_behavior is not None
        assert case.expected_safety_trigger is not None


# ── Then: idioma de los casos "otro_idioma" ──────────────────────────────────

@then('su campo language es "en" o "ca"')
def language_en_o_ca(validation_result):
    for case in validation_result["cases"]:
        assert case.language in ("en", "ca")


@then('no es "es"')
def language_no_es_es(validation_result):
    for case in validation_result["cases"]:
        assert case.language != "es"


# ── Then: validación negativa ─────────────────────────────────────────────────

@then("la validación falla indicando el campo obligatorio ausente")
def validacion_falla_por_campo_ausente(validation_result):
    assert validation_result["cases"] is None
    assert validation_result["error"] is not None
    assert "attack_type" in str(validation_result["error"]), (
        f"El error no identifica el campo ausente: {validation_result['error']!r}"
    )


@then("la validación falla indicando la incoherencia")
def validacion_falla_por_incoherencia(validation_result):
    assert validation_result["cases"] is None
    assert validation_result["error"] is not None
    assert "Incoherencia" in str(validation_result["error"]), (
        f"El error no identifica la incoherencia: {validation_result['error']!r}"
    )


# ── Then: unicidad ────────────────────────────────────────────────────────────

@then("no hay dos entradas con el mismo texto de question")
def sin_preguntas_duplicadas(validation_result):
    questions = [c.question for c in validation_result["cases"]]
    assert len(questions) == len(set(questions))


@then("no hay dos entradas con el mismo id")
def sin_ids_duplicados(validation_result):
    ids = [c.id for c in validation_result["cases"]]
    assert len(ids) == len(set(ids))


@then(
    "los ids de los 30 casos nuevos son secuenciales y no colisionan con los 42 "
    "ya existentes"
)
def ids_nuevos_secuenciales_sin_colision(validation_result):
    numeros = sorted(
        int(re.match(r"eval_(\d+)$", c.id).group(1)) for c in validation_result["cases"]
    )
    assert numeros == list(range(1, 73)), (
        f"Los ids no son secuenciales de eval_01 a eval_72: {numeros}"
    )


# ── Then: subconjunto de seguridad ────────────────────────────────────────────

@then("contiene exactamente 40 casos (15 + 10 + 10 + 5)")
def contiene_40_casos_seguridad(seguridad_subset):
    assert len(seguridad_subset) == 40
