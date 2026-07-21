"""Citación duplicada de fuentes — consistencia y contraste con instrucción reforzada
(E-11 T-07, Ronda 2 / D-071).

La Ronda 1 de T-07 reveló un hallazgo no buscado al leer las transcripciones completas
(`tests/eval/results/e11_t04_transcripcion_pre_fix.json`,
`tests/eval/results/e11_t04_transcripcion.json`,
`tests/eval/results/e11_t07_t05_regression_check.json`, 11 de 17 casos): el LLM genera
intermitentemente su propio bloque "Fuentes consultadas:" en texto plano dentro de la
respuesta, duplicando el bloque determinista que añade
`rag/pipeline.py::_build_sources_section` (D-026), pese a que `[FUENTES]` ya instruye
"No cites el nombre del documento ni de la sección dentro de la respuesta". Confirmado
que no lo causó T-04/T-05 (ya aparecía pre-fix).

Este script investiga dos cosas por separado, sin aplicar ningún fix a
`prompts/system_prompt_family.txt` (D-071, mismo patrón que D-059/T-03):

- **Parte B — consistencia por pregunta**: repite `ling_07` 3 veces contra
  `RAGPipeline.query()` real de producción, sin cambiar nada, para saber si la
  duplicación es una propiedad de la pregunta/contexto o de una tirada concreta del LLM.
- **Parte C — variante de instrucción reforzada**: un `RAGGenerator` alternativo con
  `_system_prompt` mutado en memoria (nunca escrito a fichero, mismo patrón que
  `scripts/run_e11_t03_grounding_investigation.py::_build_lax_generator`), donde el
  párrafo `[FUENTES]` se reemplaza por una versión más explícita con contraejemplo
  concreto, sobre las mismas 10 preguntas ya usadas en el Bloque 0 (Ronda 1) de este
  plan (7 `ling_XX` + 3 `t05_regr_XX`).

Detección de duplicación: `response.count("Fuentes consultadas") >= 2` (bloque propio
del LLM + bloque determinista real), mismo criterio ya usado en la lectura manual de
Cowork sobre la Ronda 1.

Investigación pura (D-071): no modifica `prompts/system_prompt_family.txt`. Vuelca el
resultado completo a
`tests/eval/results/e11_t07_citation_duplication_investigation.json` para que Marcos
decida en Cowork si la variante reforzada reduce la tasa lo suficiente para proponerla
como ajuste de prompt. No es un test automatizado (D-050): sin asserts.

Uso:
    python scripts/run_e11_t07_citation_duplication_investigation.py
"""

import json
import sys
from pathlib import Path

# `python scripts/run_e11_t07_citation_duplication_investigation.py` no añade la raíz
# del repo a sys.path (solo scripts/); se añade explícitamente para poder importar `rag`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import load_rag_config
from rag.generator import RAGGenerator
from rag.language import detect_language
from rag.pipeline import RAGPipeline, _build_sources_section
from rag.safety import apply_safety_filter, check_alarm_signals

_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "eval"
    / "results"
    / "e11_t07_citation_duplication_investigation.json"
)

_DUPLICATION_MARKER = "Fuentes consultadas"

# Ronda 1 de este mismo plan (7 preguntas de scripts/run_e11_t04_linguistic_review.py +
# 3 preguntas de scripts/run_e11_t07_t05_regression_check.py). Texto reutilizado tal
# cual — mismas preguntas, no se recalcula el hallazgo original de Ronda 1 con este
# script.
_LING_07_QUESTION = "¿Cómo se clasifican los distintos tipos de inmunodeficiencias primarias?"

_TEN_QUESTIONS = [
    {
        "id": "ling_01",
        "question": (
            "¿En qué consiste el trasplante de médula ósea para tratar una "
            "inmunodeficiencia primaria?"
        ),
    },
    {
        "id": "ling_02",
        "question": (
            "¿Qué implica el proceso de acondicionamiento antes de un trasplante de "
            "médula y cómo afecta a las defensas del niño mientras se recupera?"
        ),
    },
    {
        "id": "ling_03",
        "question": (
            "¿Cómo actúa el tratamiento con inmunoglobulinas para proteger frente a "
            "infecciones?"
        ),
    },
    {
        "id": "ling_04",
        "question": (
            "¿Qué pruebas de laboratorio se utilizan para diagnosticar una "
            "inmunodeficiencia primaria?"
        ),
    },
    {
        "id": "ling_05",
        "question": (
            "¿En qué consiste el cribado neonatal para detectar una inmunodeficiencia "
            "combinada grave nada más nacer?"
        ),
    },
    {
        "id": "ling_06",
        "question": (
            "¿Qué es la hipogammaglobulinemia y qué relación tiene con las "
            "inmunodeficiencias primarias?"
        ),
    },
    {"id": "ling_07", "question": _LING_07_QUESTION},
    {"id": "t05_regr_01", "question": "¿A quién llamo si es fin de semana?"},
    {
        "id": "t05_regr_02",
        "question": "¿Cómo puedo cuidar el día a día de mi familiar?",
    },
    {
        "id": "t05_regr_03",
        "question": "¿A partir de cuánta fiebre tengo que acudir al médico?",
    },
]

# Producción observada en Ronda 1 (lectura manual de Cowork sobre las 17 transcripciones
# completas de e11_t04_transcripcion_pre_fix.json + e11_t04_transcripcion.json +
# e11_t07_t05_regression_check.json).
_PRODUCTION_RATE_COWORK = "11/17"

# Variante SOLO para esta investigación — nunca se escribe a
# prompts/system_prompt_family.txt (D-071, mismo patrón que D-059/T-03). Reemplaza el
# párrafo [FUENTES] completo, no lo añade, para no dejar la instrucción original
# ambigua conviviendo con la reforzada.
_REINFORCED_FUENTES_BLOCK = """[FUENTES]
Basa todas tus respuestas exclusivamente en los documentos proporcionados como contexto.
No generes NUNCA un encabezado ni una lista con nombres de fichero dentro de tu
respuesta — ni "Fuentes consultadas:", ni "Fuentes:", ni ningún equivalente. El sistema
añade automáticamente ese listado después de tu respuesta; si tú también lo generas,
aparecerá duplicado. Incorrecto (NO hagas esto):
"...consulta con tu equipo médico.

Fuentes consultadas:
- documento.pdf"
Correcto: termina tu respuesta en el párrafo de cierre, sin ningún bloque de fuentes
propio.
Si la información no está en el contexto, indícalo explícitamente.
"""

_FUENTES_MARKER = "[FUENTES]"
_TONO_MARKER = "\n[TONO — PERFIL FAMILIAR]"


def _build_reinforced_generator(rag_config: dict) -> RAGGenerator:
    generator = RAGGenerator(rag_config)
    prompt = generator._system_prompt
    start = prompt.index(_FUENTES_MARKER)
    end = prompt.index(_TONO_MARKER)
    generator._system_prompt = (
        prompt[:start] + _REINFORCED_FUENTES_BLOCK + prompt[end:]
    )
    return generator


def _query_with_generator(pipeline: RAGPipeline, generator: RAGGenerator, question: str) -> str:
    """Reproduce RAGPipeline.query() pero con un RAGGenerator alternativo.

    Mismo flujo que rag/pipeline.py::RAGPipeline.query() (retrieval, generación,
    apply_safety_filter, sección de fuentes determinista) para que la comparación de
    tasa de duplicación sea contra el mismo mecanismo end-to-end, no solo el texto
    crudo del LLM.
    """
    language = detect_language(question)
    raw_results = pipeline.retrieve(question)
    context = "\n\n".join(doc.page_content for doc, _ in raw_results)
    has_alarm = check_alarm_signals(question)
    raw_response = generator.generate(question=question, context=context, language=language)
    response = apply_safety_filter(raw_response, has_alarm)
    sources_section = _build_sources_section(raw_results, language)
    if sources_section:
        response = f"{response}\n\n{sources_section}"
    return response


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)

    # Parte B — consistencia por pregunta: ling_07 x3, producción real, sin cambios.
    print(f"Parte B — repitiendo ling_07 3 veces (producción real): {_LING_07_QUESTION!r}")
    ling_07_runs = []
    for run_index in (1, 2, 3):
        response = pipeline.query(_LING_07_QUESTION)
        duplicated = response.count(_DUPLICATION_MARKER) >= 2
        print(f"  Run {run_index}: duplicado={duplicated}")
        ling_07_runs.append({"run": run_index, "response": response, "duplicated": duplicated})
    ling_07_duplication_count = sum(1 for r in ling_07_runs if r["duplicated"])
    print(
        f"Parte B — ling_07 duplicó en {ling_07_duplication_count}/3 ejecuciones "
        "(producción real, sin cambios)."
    )

    # Parte C — variante de instrucción reforzada sobre las 10 preguntas de Ronda 1.
    print("\nParte C — construyendo generador con [FUENTES] reforzado (solo en memoria)...")
    reinforced_generator = _build_reinforced_generator(rag_config)

    reinforced_runs = []
    for item in _TEN_QUESTIONS:
        print(f"[{item['id']}] ejecutando (variante reforzada): {item['question']!r}")
        response = _query_with_generator(pipeline, reinforced_generator, item["question"])
        duplicated = response.count(_DUPLICATION_MARKER) >= 2
        print(f"  duplicado={duplicated}")
        reinforced_runs.append(
            {
                "id": item["id"],
                "question": item["question"],
                "response": response,
                "duplicated": duplicated,
            }
        )
    reinforced_duplication_count = sum(1 for r in reinforced_runs if r["duplicated"])
    print(
        f"\nParte C — variante reforzada duplicó en {reinforced_duplication_count}/"
        f"{len(reinforced_runs)} preguntas."
    )

    output = {
        "duplication_marker": _DUPLICATION_MARKER,
        "part_b_ling_07_consistency": {
            "question": _LING_07_QUESTION,
            "mechanism": "RAGPipeline.query() — prompt de producción, sin cambios",
            "runs": ling_07_runs,
            "duplication_count": f"{ling_07_duplication_count}/3",
        },
        "part_c_reinforced_variant": {
            "reinforced_fuentes_block": _REINFORCED_FUENTES_BLOCK,
            "mechanism": (
                "RAGGenerator alternativo con [FUENTES] reemplazado en _system_prompt "
                "(en memoria, nunca escrito a prompts/system_prompt_family.txt)"
            ),
            "cases": reinforced_runs,
            "duplication_count": f"{reinforced_duplication_count}/{len(reinforced_runs)}",
        },
        "production_rate_ronda1_cowork_reading": _PRODUCTION_RATE_COWORK,
        "conclusion_manual": None,
    }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print(
        "\nParada explícita (paso 8): 'conclusion_manual' se completa tras la lectura "
        "manual en Cowork. No se aplica la instrucción reforzada a "
        "prompts/system_prompt_family.txt desde este script."
    )


if __name__ == "__main__":
    main()
