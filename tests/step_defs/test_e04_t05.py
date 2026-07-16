"""Step definitions — E-04 T-05 Módulo de seguridad: Falso Negativo Cero."""

import json
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e04_t05_safety_module.feature")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TRIGGERS_PATH = _REPO_ROOT / "config" / "alarm_triggers.json"


# ── Background ────────────────────────────────────────────────────────────────

@given("el módulo de seguridad está inicializado")
def safety_module_initialized():
    from rag import safety  # noqa: F401 — confirma que el módulo es importable


@given('los triggers de alarma están cargados desde "config/alarm_triggers.json"')
def triggers_loaded_from_config():
    assert _TRIGGERS_PATH.exists(), f"Fichero de triggers no encontrado: {_TRIGGERS_PATH}"


# ── Scenarios 1 & 2: Detección — fixtures de query ───────────────────────────

@given('el usuario describe "mi hijo tiene 40 grados de fiebre desde hace dos días"', target_fixture="query")
def query_fiebre_alta():
    return "mi hijo tiene 40 grados de fiebre desde hace dos días"


@given('el usuario describe "tiene dificultad para respirar y los labios azulados"', target_fixture="query")
def query_dificultad_respiratoria():
    return "tiene dificultad para respirar y los labios azulados"


# ── Scenario 3: Sin alarma — query informativa ────────────────────────────────

@given('el usuario pregunta "¿qué es la agammaglobulinemia de Bruton?"', target_fixture="query")
def query_informativa_bruton():
    return "¿qué es la agammaglobulinemia de Bruton?"


# ── When compartido: check_alarm_signals ─────────────────────────────────────

@when("se evalúa la query con check_alarm_signals", target_fixture="alarm_result")
def evalua_query_alarm(query):
    from rag.safety import check_alarm_signals
    return check_alarm_signals(query)


# ── Then: resultado de detección ──────────────────────────────────────────────

@then("se detecta una señal de alarma")
def se_detecta_alarma(alarm_result):
    assert alarm_result is True, (
        f"Se esperaba alarma pero check_alarm_signals devolvió: {alarm_result!r}"
    )


@then("no se detecta ninguna señal de alarma")
def no_se_detecta_alarma(alarm_result):
    assert alarm_result is False, (
        f"Se esperaba sin alarma pero check_alarm_signals devolvió: {alarm_result!r}"
    )


# ── Scenarios 4, 5, 6: Filtro de seguridad ───────────────────────────────────

@given("se ha detectado una señal de alarma en la query", target_fixture="has_alarm")
def alarm_detected_in_query():
    return True


@given("no se ha detectado señal de alarma en la query", target_fixture="has_alarm")
def no_alarm_detected_in_query():
    return False


@given(
    'el LLM ha generado la respuesta "Puede tratarse de un episodio febril. Descansa e hidrátate bien."',
    target_fixture="llm_response",
)
def llm_response_febril():
    return "Puede tratarse de un episodio febril. Descansa e hidrátate bien."


@given(
    'el LLM ha generado una respuesta que contiene "no es grave, no te preocupes"',
    target_fixture="llm_response",
)
def llm_response_tranquilizadora():
    return "Sobre estos síntomas: no es grave, no te preocupes, suele resolverse solo."


@given(
    'el LLM ha generado una respuesta informativa sobre "la agammaglobulinemia de Bruton"',
    target_fixture="llm_response",
)
def llm_response_informativa_bruton():
    return (
        "La agammaglobulinemia de Bruton (XLA) es una inmunodeficiencia primaria congénita "
        "caracterizada por la ausencia de linfocitos B maduros en sangre periférica."
    )


@when("se aplica el filtro de seguridad a la respuesta", target_fixture="filtered_response")
def aplica_filtro_seguridad(llm_response, has_alarm):
    from rag.safety import apply_safety_filter
    return apply_safety_filter(llm_response, has_alarm)


@then("la respuesta final incluye una derivación explícita a consulta médica")
def respuesta_incluye_derivacion(filtered_response):
    markers = ["médico", "médica", "especialista", "consulta"]
    assert any(m in filtered_response.lower() for m in markers), (
        f"La respuesta no incluye derivación médica: {filtered_response!r}"
    )


@then("la respuesta final sustituye o matiza la afirmación tranquilizadora")
def respuesta_matiza_tranquilizadora(filtered_response, llm_response):
    assert len(filtered_response) > len(llm_response), (
        "El filtro no modificó la respuesta tranquilizadora — se esperaba texto adicional"
    )


@then("la respuesta final se mantiene informativa")
def respuesta_mantiene_informativa(filtered_response):
    assert "Bruton" in filtered_response or "inmunodeficiencia" in filtered_response.lower(), (
        f"El contenido informativo no se preservó en la respuesta: {filtered_response!r}"
    )


@then("no se añade alarmismo innecesario")
def no_se_añade_alarmismo(filtered_response):
    # "cuanto antes" es el marcador distinctive de la frase de derivación añadida por el módulo.
    assert "cuanto antes" not in filtered_response, (
        f"Se añadió derivación innecesaria a una respuesta informativa: {filtered_response!r}"
    )


# ── Scenario 7: Triggers cargados desde fichero ───────────────────────────────

@given('existe el fichero "config/alarm_triggers.json"', target_fixture="triggers_file_path")
def fichero_triggers_existe():
    assert _TRIGGERS_PATH.exists(), f"Fichero no encontrado: {_TRIGGERS_PATH}"
    return _TRIGGERS_PATH


@when("se inicializa el módulo de seguridad", target_fixture="file_load_result")
def se_inicializa_modulo(triggers_file_path, tmp_path):
    from rag.safety import check_alarm_signals

    unique_keyword = "señaltestúnicaxyz123456"
    test_triggers_path = tmp_path / "test_triggers.json"
    test_triggers_path.write_text(
        json.dumps({
            "meta": {},
            "triggers": [{"id": "t_test", "text": unique_keyword, "category": "test", "source": "test"}],
        }),
        encoding="utf-8",
    )

    detected_via_test_file = check_alarm_signals(unique_keyword, triggers_path=test_triggers_path)
    detected_via_prod_file = check_alarm_signals(unique_keyword, triggers_path=triggers_file_path)

    return {
        "detected_via_test_file": detected_via_test_file,
        "detected_via_prod_file": detected_via_prod_file,
    }


@then("los triggers se cargan desde el fichero JSON, no están hardcodeados en el código")
def triggers_cargados_desde_fichero(file_load_result):
    assert file_load_result["detected_via_test_file"] is True, (
        "El trigger del fichero de test no fue detectado — ¿se ignora el path inyectado?"
    )
    assert file_load_result["detected_via_prod_file"] is False, (
        "El trigger de test fue detectado en el fichero de producción — podría estar hardcodeado"
    )
