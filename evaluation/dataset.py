"""Carga y validación del dataset de evaluación (E-07 T-01, ampliado en E-09 T-01)."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator


class EvalCase(BaseModel):
    """Un caso de prueba del dataset de evaluación (D-054: cobertura completa)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    question: str
    expected_answer: str
    is_alarm: bool
    profile: Literal["familiar"]
    language: Literal["es", "en", "ca"]
    category: Literal[
        "informativo", "alarma", "diagnostico", "limite", "otro_idioma", "prompt_injection"
    ]
    attack_type: str | None = None
    expected_behavior: str | None = None
    expected_safety_trigger: bool | None = None

    @model_validator(mode="after")
    def _category_is_alarm_coherente(self) -> "EvalCase":
        if self.category == "alarma" and not self.is_alarm:
            raise ValueError(
                f"Incoherencia category/is_alarm en '{self.id}': category='alarma' "
                "exige is_alarm=True"
            )
        if self.category == "informativo" and self.is_alarm:
            raise ValueError(
                f"Incoherencia category/is_alarm en '{self.id}': category='informativo' "
                "exige is_alarm=False"
            )
        return self

    @model_validator(mode="after")
    def _campos_prompt_injection_obligatorios(self) -> "EvalCase":
        if self.category == "prompt_injection":
            faltantes = [
                campo
                for campo in ("attack_type", "expected_behavior", "expected_safety_trigger")
                if getattr(self, campo) is None
            ]
            if faltantes:
                raise ValueError(
                    f"Entrada '{self.id}' con category='prompt_injection' sin campos "
                    f"obligatorios: {faltantes}"
                )
        return self


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
