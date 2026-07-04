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


def check_alarm_signals(query: str, triggers_path: Path = _TRIGGERS_PATH) -> bool:
    """Devuelve True si la query contiene palabras clave de algún trigger de alarma."""
    triggers = _load_triggers(triggers_path)
    query_kws = _keywords(query)
    return any(bool(_keywords(t["texto"]) & query_kws) for t in triggers)


def apply_safety_filter(response: str, has_alarm: bool) -> str:
    """Postprocesa la respuesta del LLM aplicando el principio de Falso Negativo Cero."""
    response_lower = response.lower()
    needs_filter = has_alarm or any(phrase in response_lower for phrase in REASSURING_PHRASES)
    if needs_filter:
        return response + _REFERRAL
    return response
