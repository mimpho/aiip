"""Revisión cualitativa del registro lingüístico, perfil familiar (E-11 T-04).

Ejecuta una muestra dirigida de 5-8 preguntas sobre temas con vocabulario clínico
denso (trasplante de médula/acondicionamiento, inmunoglobulinas, diagnóstico
inmunológico, cribado neonatal, hipogammaglobulinemia, clasificación de
inmunodeficiencias) contra `RAGPipeline.query()` real (`rag/pipeline.py`), que ya
aplica `apply_safety_filter` internamente — a diferencia de E11 T-03, aquí no se
genera ninguna variante alternativa del prompt, solo se lee tal cual producción.

Vuelca la transcripción íntegra (pregunta + respuesta completa, no resumida) a
`tests/eval/results/e11_t04_transcripcion.json` para la lectura cualitativa manual
posterior: marcar cada término técnico no explicado en lenguaje accesible y
contrastarlo contra `[TONO — PERFIL FAMILIAR]` de `prompts/system_prompt_family.txt`.

No es un test automatizado (D-050, mismo patrón que
scripts/run_e11_t03_grounding_investigation.py): sin asserts, solo instrumentación
y volcado a fichero para revisión manual.

Uso:
    python scripts/run_e11_t04_linguistic_review.py
"""

import json
import sys
from pathlib import Path

# `python scripts/run_e11_t04_linguistic_review.py` no añade la raíz del repo a
# sys.path (solo scripts/); se añade explícitamente para poder importar `rag`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import load_rag_config
from rag.pipeline import RAGPipeline

_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "eval"
    / "results"
    / "e11_t04_transcripcion.json"
)

# Muestra dirigida (no exhaustiva) de preguntas sobre temas con vocabulario clínico
# denso. Los dos primeros temas son los ya identificados en el hallazgo original
# (backlog/ideas.md, hallazgo #3, 8 jul 2026); el resto se añadió al revisar el KB
# (data/raw/aedip/) buscando otros documentos con terminología técnica densa.
_QUESTIONS = [
    {
        "id": "ling_01",
        "topic": "trasplante de médula (progenitores hematopoyéticos)",
        "question": (
            "¿En qué consiste el trasplante de médula ósea para tratar una "
            "inmunodeficiencia primaria?"
        ),
    },
    {
        "id": "ling_02",
        "topic": "acondicionamiento pre-trasplante",
        "question": (
            "¿Qué implica el proceso de acondicionamiento antes de un trasplante de "
            "médula y cómo afecta a las defensas del niño mientras se recupera?"
        ),
    },
    {
        "id": "ling_03",
        "topic": "inmunoglobulinas",
        "question": (
            "¿Cómo actúa el tratamiento con inmunoglobulinas para proteger frente a "
            "infecciones?"
        ),
    },
    {
        "id": "ling_04",
        "topic": "diagnóstico inmunológico",
        "question": (
            "¿Qué pruebas de laboratorio se utilizan para diagnosticar una "
            "inmunodeficiencia primaria?"
        ),
    },
    {
        "id": "ling_05",
        "topic": "cribado neonatal",
        "question": (
            "¿En qué consiste el cribado neonatal para detectar una inmunodeficiencia "
            "combinada grave nada más nacer?"
        ),
    },
    {
        "id": "ling_06",
        "topic": "hipogammaglobulinemia",
        "question": (
            "¿Qué es la hipogammaglobulinemia y qué relación tiene con las "
            "inmunodeficiencias primarias?"
        ),
    },
    {
        "id": "ling_07",
        "topic": "clasificación de inmunodeficiencias",
        "question": "¿Cómo se clasifican los distintos tipos de inmunodeficiencias primarias?",
    },
]


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)

    cases = []
    for item in _QUESTIONS:
        print(f"[{item['id']}] ({item['topic']}) ejecutando: {item['question']!r}")
        response = pipeline.query(item["question"])
        cases.append(
            {
                "id": item["id"],
                "topic": item["topic"],
                "question": item["question"],
                "response": response,
            }
        )

    output = {
        "profile": "family",
        "mechanism": "RAGPipeline.query() — prompt de producción, apply_safety_filter interno",
        "cases": cases,
    }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print("\nBloque 1: transcripción lista para la lectura cualitativa manual.")


if __name__ == "__main__":
    main()
