"""Step definitions — E-04 T-03 Detección de idioma."""

import sys
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e04_t03_language_detection.feature")


# ── Given: módulo inicializado (scenarios 1-4) ───────────────────────────────

@given("el módulo de detección de idioma está inicializado")
def modulo_inicializado():
    from rag import language  # noqa: F401


# ── Given: idioma detectado (scenario 5) ─────────────────────────────────────

@given(parsers.parse('el idioma detectado es "{lang}"'), target_fixture="language")
def idioma_detectado_given(lang):
    return lang


# ── When: analizar texto normal (scenarios 1-3) ──────────────────────────────

@when(parsers.parse('analizo el texto "{text}"'), target_fixture="detection_result")
def analizo_texto(text):
    from rag.language import detect_language

    return detect_language(text)


# ── When: analizar texto corto (scenario 4) ──────────────────────────────────

@when(
    parsers.parse('analizo un texto demasiado corto para detectar idioma como "{text}"'),
    target_fixture="short_text_result",
)
def analizo_texto_corto(text):
    from rag.language import detect_language

    try:
        return {"lang": detect_language(text), "exception": None}
    except Exception as exc:
        return {"lang": None, "exception": exc}


# ── When: construir instrucción de idioma (scenario 5) ───────────────────────

@when("construyo el prompt final para el LLM", target_fixture="language_instruction")
def construyo_prompt(language):
    from rag.language import build_language_instruction

    return build_language_instruction(language)


# ── Then: idioma detectado (scenarios 1-3) ───────────────────────────────────

@then(parsers.parse('el idioma detectado es "{expected_lang}"'))
def idioma_detectado_es(detection_result, expected_lang):
    assert detection_result == expected_lang, (
        f"Idioma esperado: {expected_lang!r}, detectado: {detection_result!r}"
    )


# ── Then: idioma resultante con fallback (scenario 4) ────────────────────────

@then(parsers.parse('el idioma resultante es "{expected_lang}"'))
def idioma_resultante_es(short_text_result, expected_lang):
    assert short_text_result["lang"] == expected_lang, (
        f"Idioma esperado: {expected_lang!r}, resultante: {short_text_result['lang']!r}"
    )


# ── And: sin excepción (scenario 4) ──────────────────────────────────────────

@then("no se lanza ninguna excepción")
def no_se_lanza_excepcion(short_text_result):
    assert short_text_result["exception"] is None, (
        f"Se lanzó excepción inesperada: {short_text_result['exception']}"
    )


# ── Then: instrucción de castellano en el prompt (scenario 5) ────────────────

@then("el prompt contiene la instrucción de responder en castellano")
def prompt_contiene_instruccion_castellano(language_instruction):
    assert "castellano" in language_instruction.lower(), (
        f"Instrucción no menciona castellano: {language_instruction!r}"
    )
