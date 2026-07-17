import json
import re
from pathlib import Path

_TRIGGERS_PATH = Path(__file__).resolve().parent.parent / "config" / "alarm_triggers.json"

REASSURING_PHRASES = [
    "no es grave",
    "no te preocupes",
    "no es necesario ir al médico",
    "no hace falta consulta",
    "todo está bien",
]

# E-09 T-05 (hallazgo A): palabras sin señal de alarma por sí solas — se excluyen de la
# intersección de keywords en check_alarm_signals(), no son propiedad de un trigger
# concreto sino de la función de matching en general.
MATCH_STOPLIST = [
    "después",
    "varios",
    "infusión",
]

_REFERRAL = (
    "\n\nAnte esta situación, te recomendamos consultar con tu equipo médico cuanto antes."
)

_triggers_cache: dict = {}


def _load_triggers(path: Path) -> tuple:
    if path not in _triggers_cache:
        data = json.loads(path.read_text(encoding="utf-8"))
        _triggers_cache[path] = tuple(data["triggers"])
    return _triggers_cache[path]


def _keywords(text: str) -> frozenset:
    """Palabras significativas (>= 6 caracteres) del texto, en minúsculas."""
    return frozenset(w for w in re.findall(r"\w+", text.lower()) if len(w) >= 6)


def _words(text: str) -> frozenset:
    """Todas las palabras del texto, en minúsculas, sin filtro de longitud."""
    return frozenset(re.findall(r"\w+", text.lower()))


def check_alarm_signals(query: str, triggers_path: Path = _TRIGGERS_PATH) -> bool:
    """Devuelve True si la query contiene palabras clave de algún trigger de alarma."""
    triggers = _load_triggers(triggers_path)
    query_kws = _keywords(query)
    query_words = _words(query)
    stoplist = frozenset(MATCH_STOPLIST)

    for t in triggers:
        match_kws = (_keywords(t["text"]) & query_kws) - stoplist
        if not match_kws:
            continue
        requires_context = t.get("requires_context")
        if requires_context and not (query_words & frozenset(requires_context)):
            continue
        return True
    return False


def apply_safety_filter(response: str, has_alarm: bool) -> str:
    """Postprocesa la respuesta del LLM aplicando el principio de Falso Negativo Cero."""
    response_lower = response.lower()
    needs_filter = has_alarm or any(phrase in response_lower for phrase in REASSURING_PHRASES)
    if needs_filter:
        return response + _REFERRAL
    return response
