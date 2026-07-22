"""Detección de idioma y generación de instrucción de idioma para el prompt."""

from lingua import Language, LanguageDetectorBuilder

MIN_LENGTH_FOR_DETECTION = 10

# D-078 (hallazgo en E-13 T-01): margen mínimo de confianza entre el idioma
# ganador y el segundo antes de confiar en la clasificación. "que es el xiap"/
# "que es xiap" (sin tilde en "qué") clasifican como catalán con un margen de
# solo 0.035-0.05 sobre español — prácticamente un empate, artefacto de que
# "xiap" en minúscula se parece ortográficamente a catalán (xarxa, xic...).
# Los 37 casos de config/alarm_triggers.json y la muestra larga es/en/ca ya
# validada (D-057) nunca bajan de 0.64 de margen — 0.2 deja margen de sobra a
# ambos lados sin tocar ningún caso ya validado.
_MIN_CONFIDENCE_MARGIN = 0.2

# E-09 T-05 (hallazgo F, D-057): sustituye langdetect — fallaba en frases
# declarativas cortas de síntomas en español (p. ej. "ha perdido mucho peso sin
# motivo" detectada como portugués). Detector construido una vez a nivel de
# módulo, restringido a los 3 idiomas del proyecto.
_detector = LanguageDetectorBuilder.from_languages(
    Language.SPANISH, Language.ENGLISH, Language.CATALAN
).build()

_ISO_CODES = {
    Language.SPANISH: "es",
    Language.ENGLISH: "en",
    Language.CATALAN: "ca",
}

_LANGUAGE_NAMES = {
    "es": "castellano",
    "en": "inglés",
    "ca": "catalán",
}


def detect_language(text: str, default: str = "es") -> str:
    """Detecta el idioma del texto.

    Devuelve `default` si el texto es demasiado corto, si lingua no logra
    detectarlo, o si el idioma ganador no supera al segundo por al menos
    `_MIN_CONFIDENCE_MARGIN` (D-078) — evita confiar en clasificaciones que
    son, en la práctica, un empate entre dos idiomas.
    """
    if len(text.strip()) < MIN_LENGTH_FOR_DETECTION:
        return default
    values = _detector.compute_language_confidence_values(text)
    if not values:
        return default
    top = values[0]
    runner_up_value = values[1].value if len(values) > 1 else 0.0
    if (top.value - runner_up_value) < _MIN_CONFIDENCE_MARGIN:
        return default
    return _ISO_CODES.get(top.language, default)


def build_language_instruction(language: str) -> str:
    """Devuelve la instrucción de idioma para incluir en el system prompt."""
    name = _LANGUAGE_NAMES.get(language)
    if name:
        return f"Responde siempre en {name}."
    return f"Responde siempre en el idioma con código '{language}'."
