"""Carga y validación del dataset de evaluación (E-07 T-01)."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class EvalCase(BaseModel):
    """Un caso de prueba del dataset de evaluación (Fase 1: informativo o alarma)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    question: str
    expected_answer: str
    is_alarm: bool
    profile: Literal["familiar"]
    language: Literal["es"]


def load_dataset(path: Path) -> list[dict]:
    """Carga el dataset de evaluación desde disco y devuelve la lista de casos."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["cases"]


def validate_dataset(entries: list[dict]) -> list[EvalCase]:
    """Valida cada entrada contra `EvalCase` y el dataset completo (sin duplicados)."""
    cases = []
    for entry in entries:
        try:
            cases.append(EvalCase.model_validate(entry))
        except ValidationError as exc:
            raise ValueError(f"Entrada de dataset inválida: {exc}") from exc

    questions = [c.question for c in cases]
    duplicate_questions = {q for q in questions if questions.count(q) > 1}
    if duplicate_questions:
        raise ValueError(f"Preguntas duplicadas en el dataset: {duplicate_questions}")

    ids = [c.id for c in cases]
    duplicate_ids = {i for i in ids if ids.count(i) > 1}
    if duplicate_ids:
        raise ValueError(f"Ids duplicados en el dataset: {duplicate_ids}")

    return cases
