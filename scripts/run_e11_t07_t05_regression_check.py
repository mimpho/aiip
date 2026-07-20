"""Regresión post-fix D-068 sobre `guia_antibiotics_esp_0.pdf` (E-11 T-07, Bloque 0).

D-067/D-068 modificaron `prompts/system_prompt_family.txt` en producción
(generalización de `[RESTRICCIONES ABSOLUTAS]` a cualquier información operativa
de un centro concreto, T-05) sin re-ejecutar después ninguna verificación. Este
script reproduce las 3 preguntas ya documentadas en `backlog/ideas.md`
("Hallazgos del RAG", punto 1, actualizaciones 10/18 jul) contra
`RAGPipeline.query()` real (`rag/pipeline.py`), que ya aplica el prompt de
producción tal cual — sin mocks, mismo mecanismo que
`scripts/run_e11_t04_linguistic_review.py`.

Vuelca la transcripción íntegra (pregunta + respuesta completa) a
`tests/eval/results/e11_t07_t05_regression_check.json`, marcando si
`guia_antibiotics_esp_0.pdf` aparece entre las fuentes citadas, para la lectura
manual posterior: de las dos preguntas que antes citaban el documento sin
salvedad (`e11_t05_cierre.md` §3 — "a quién llamo" y "cuánta fiebre"), ¿aparece
ahora la salvedad de información específica de un centro? La tercera ("día a
día") no se espera que cambie — la cita ya era correcta antes del fix.

No es un test automatizado (D-050, mismo patrón que
scripts/run_e11_t04_linguistic_review.py): sin asserts, solo instrumentación y
volcado a fichero para revisión manual.

Uso:
    python scripts/run_e11_t07_t05_regression_check.py
"""

import json
import sys
from pathlib import Path

# `python scripts/run_e11_t07_t05_regression_check.py` no añade la raíz del
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
    / "e11_t07_t05_regression_check.json"
)

_ANTIBIOTICS_GUIDE_FILENAME = "guia_antibiotics_esp_0.pdf"

# Las 3 preguntas exactas de `backlog/ideas.md` ("Hallazgos del RAG", punto 1).
_QUESTIONS = [
    {
        "id": "t05_regr_01",
        "origin": "10 jul 2026, smoke test E-05 T-07 CU-05",
        "question": "¿A quién llamo si es fin de semana?",
    },
    {
        "id": "t05_regr_02",
        "origin": "18 jul 2026",
        "question": "¿Cómo puedo cuidar el día a día de mi familiar?",
    },
    {
        "id": "t05_regr_03",
        "origin": "18 jul 2026",
        "question": "¿A partir de cuánta fiebre tengo que acudir al médico?",
    },
]


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)

    cases = []
    for item in _QUESTIONS:
        print(f"[{item['id']}] ejecutando: {item['question']!r}")
        response = pipeline.query(item["question"])
        cites_antibiotics_guide = _ANTIBIOTICS_GUIDE_FILENAME in response
        cases.append(
            {
                "id": item["id"],
                "origin": item["origin"],
                "question": item["question"],
                "response": response,
                "cites_antibiotics_guide": cites_antibiotics_guide,
            }
        )

    output = {
        "profile": "family",
        "mechanism": "RAGPipeline.query() — prompt de producción post D-067/D-068",
        "cases": cases,
    }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print("\nTranscripción lista para la lectura manual de la salvedad de centro concreto.")


if __name__ == "__main__":
    main()
