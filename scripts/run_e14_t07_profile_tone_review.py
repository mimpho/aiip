"""Revisión manual dirigida del path con perfil, tono/registro (E-14 T-07, D-094 — bloque 2b).

Ejecuta 8 preguntas fijas contra `RAGPipeline.query()` real (`rag/pipeline.py`),
cada una con un `profile` distinto (D-093, T-06), para inspeccionar a mano si la
respuesta generada: usa el nombre real del paciente en vez de "el paciente", no
reintroduce el diagnóstico como si fuera información nueva, y simplifica el
registro cuando la edad del paciente es baja. `tone_06` es el caso de control
(perfil vacío) — debe producir una respuesta indistinguible del pipeline previo
a E-14 (sin bloque `[PERFIL DEL PACIENTE]`).

Ronda 2 (D-095): `tone_07`/`tone_08` son casos nuevos de categoría alarma con
perfil, añadidos tras el hallazgo de la Ronda 1 (`tone_05` se cortaba a media
palabra, sin el bloque `[CIERRE OBLIGATORIO]`, por el mismo mecanismo de D-082 —
el bloque `[PERFIL DEL PACIENTE]` reduce el margen de `LLM_MAX_TOKENS` disponible
para la respuesta visible). Verifican, con `LLM_MAX_TOKENS=3072` ya vigente
(`rag/config.py`), que un corte silencioso no comprometa Falso Negativo Cero en
el escenario real donde sí importaría: una pregunta de alarma con perfil.

RAGAS no mide tono/registro (D-094): esto no es una métrica automática, es una
transcripción para lectura manual, mismo patrón que
`scripts/run_e11_t04_linguistic_review.py` (sin mocks, prompt de producción,
`apply_safety_filter` interno).

No es un test automatizado (D-050): sin asserts, solo instrumentación y volcado
a fichero. El campo `revision_manual` de cada caso se rellena a mano tras leer
la respuesta.

Uso:
    python scripts/run_e14_t07_profile_tone_review.py
"""

import json
import sys
from pathlib import Path

# `python scripts/run_e14_t07_profile_tone_review.py` no añade la raíz del
# repo a sys.path (solo scripts/); se añade explícitamente para poder
# importar `rag`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import load_rag_config
from rag.pipeline import RAGPipeline

_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "eval"
    / "results"
    / "e14_t07_profile_tone_review.json"
)

_CASES = [
    {
        "id": "tone_01",
        "profile": {
            "patient_name": "Marcos",
            "patient_diagnosis": "XLA",
            "patient_age": 34,
            "patient_context": None,
        },
        "question": "¿Qué vacunas debería evitar?",
    },
    {
        "id": "tone_02",
        "profile": {
            "patient_name": "Lucía",
            "patient_diagnosis": "SCID",
            "patient_age": 2,
            "patient_context": None,
        },
        "question": "¿Qué vacunas debería evitar?",
    },
    {
        "id": "tone_03",
        "profile": {
            "patient_name": "Iker",
            "patient_diagnosis": "CVID",
            "patient_age": 8,
            "patient_context": "acude al colegio",
        },
        "question": "¿Puede hacer educación física con normalidad?",
    },
    {
        "id": "tone_04",
        "profile": {
            "patient_name": "Marcos",
            "patient_diagnosis": "XLA",
            "patient_age": 34,
            "patient_context": None,
        },
        "question": "¿A qué especialista debo acudir para revisión?",
    },
    {
        "id": "tone_05",
        "profile": {
            "patient_name": "Iker",
            "patient_diagnosis": None,
            "patient_age": 8,
            "patient_context": None,
        },
        "question": "¿Qué es una inmunodeficiencia primaria?",
    },
    {
        "id": "tone_06",
        "profile": {
            "patient_name": None,
            "patient_diagnosis": None,
            "patient_age": None,
            "patient_context": None,
        },
        "question": "¿Qué es una inmunodeficiencia primaria?",
    },
    {
        "id": "tone_07",
        "profile": {
            "patient_name": "Iker",
            "patient_diagnosis": "CVID",
            "patient_age": 8,
            "patient_context": "acude al colegio",
        },
        "question": "Mi hijo tiene 39°C de fiebre y está muy decaído, ¿es urgente?",
    },
    {
        "id": "tone_08",
        "profile": {
            "patient_name": "Lucía",
            "patient_diagnosis": "SCID",
            "patient_age": 2,
            "patient_context": None,
        },
        "question": "Le ha salido un sarpullido con la vacuna de ayer, ¿qué hago?",
    },
]


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)

    cases = []
    for item in _CASES:
        print(f"[{item['id']}] perfil={item['profile']} ejecutando: {item['question']!r}")
        response = pipeline.query(item["question"], profile=item["profile"])
        cases.append(
            {
                "id": item["id"],
                "profile": item["profile"],
                "question": item["question"],
                "response": response,
                "revision_manual": None,
            }
        )

    output = {
        "mechanism": "RAGPipeline.query(question, profile=...) — prompt de producción, apply_safety_filter interno",
        "cases": cases,
    }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print("\nTranscripción lista para la lectura cualitativa manual (campo revision_manual).")


if __name__ == "__main__":
    main()
