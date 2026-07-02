"""Detección de idioma y generación de instrucción de idioma para el prompt."""

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

MIN_LENGTH_FOR_DETECTION = 10

_LANGUAGE_NAMES = {
    "es": "castellano",
    "en": "inglés",
    "ca": "catalán",
}


def detect_language(text: str, default: str = "es") -> str:
    """Detecta el idioma del texto. Devuelve `default` si el texto es demasiado corto o no detectable."""
    if len(text.strip()) < MIN_LENGTH_FOR_DETECTION:
        return default
    try:
        return detect(text)
    except LangDetectException:
        return default


def build_language_instruction(language: str) -> str:
    """Devuelve la instrucción de idioma para incluir en el system prompt."""
    name = _LANGUAGE_NAMES.get(language)
    if name:
        return f"Responde siempre en {name}."
    return f"Responde siempre en el idioma con código '{language}'."
