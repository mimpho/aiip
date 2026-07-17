"""Detección de idioma y generación de instrucción de idioma para el prompt."""

from lingua import Language, LanguageDetectorBuilder

MIN_LENGTH_FOR_DETECTION = 10

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
    """Detecta el idioma del texto. Devuelve `default` si el texto es demasiado corto o no detectable."""
    if len(text.strip()) < MIN_LENGTH_FOR_DETECTION:
        return default
    language = _detector.detect_language_of(text)
    if language is None:
        return default
    return _ISO_CODES.get(language, default)


def build_language_instruction(language: str) -> str:
    """Devuelve la instrucción de idioma para incluir en el system prompt."""
    name = _LANGUAGE_NAMES.get(language)
    if name:
        return f"Responde siempre en {name}."
    return f"Responde siempre en el idioma con código '{language}'."
