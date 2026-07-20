"""Investigación dirigida: `eval_06` (banda Grave, Faithfulness 0.385) — E-11 T-06.

`eval_06` ("¿Con qué frecuencia hay que hacer revisiones con el inmunólogo?") cayó dos
veces sin causa registrada: 0.722 (pre-E-11, E-09 T-05) → 0.615 (tras T-01, KB ampliada)
→ 0.385 (tras T-02, peso adaptativo BM25). Ya figuraba en hallazgo B
(`tests/eval/results/e09_t05_plan_b_investigacion.md`), que documentó una fuga de cita
inline de documento/páginas en la reproducción de este caso con Faithfulness en 0.60
(antes de T-01/T-02) — esa investigación no cubre las dos caídas posteriores.

Reproduce el caso contra el pipeline real (KB ampliada + peso adaptativo, ya activos:
no es posible reconstruir el estado previo a T-01/T-02, ver tasks/E11-T06-plan.md),
contrasta la respuesta real contra la hipótesis de hallazgo B y comprueba la
estabilidad del juez de Faithfulness (dos invocaciones sobre el mismo
`SingleTurnSample`, mismo patrón que `run_e11_t05_eval15_investigation.py` para Context
Precision/Recall).

Investigación pura (D-065): no modifica `rag/retriever.py` ni prompts, no aplica ningún
fix. Vuelca el resultado completo a
`tests/eval/results/e11_t06_eval06_investigacion.json` para que Marcos y el agente
decidan la causa raíz en Cowork. No es un test automatizado (D-050): sin asserts.

Uso:
    python scripts/run_e11_t06_eval06_investigation.py
"""

import json
import re
import sys
import types
from pathlib import Path

# `python scripts/run_e11_t06_eval06_investigation.py` no añade la raíz del repo a
# sys.path (solo scripts/); se añade explícitamente para poder importar `rag`/`evaluation`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ragas (API legacy, D-051) importa incondicionalmente
# `langchain_community.chat_models.vertexai.ChatVertexAI` al cargar `ragas.llms.base`,
# que ya no existe en la línea moderna de langchain-community (0.4.x, D-010). Mismo stub
# que `scripts/run_ragas_eval.py`.
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _vertexai_stub = types.ModuleType("langchain_community.chat_models.vertexai")

    class _UnusedChatVertexAI:
        pass

    _vertexai_stub.ChatVertexAI = _UnusedChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = _vertexai_stub

from langchain_google_genai import ChatGoogleGenerativeAI
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness

from evaluation.dataset import load_dataset, validate_dataset
from rag.config import load_rag_config
from rag.language import detect_language
from rag.pipeline import RAGPipeline, _build_sources_section
from rag.safety import check_alarm_signals

_DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "eval" / "dataset_partial.json"
)
_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "eval"
    / "results"
    / "e11_t06_eval06_investigacion.json"
)

_CASE_ID = "eval_06"

# Mismo motivo que scripts/run_ragas_eval.py: LLM_MAX_TOKENS (1024) está calibrado para
# RAGGenerator, no para las llamadas internas de RAGAS.
_EVALUATOR_MAX_TOKENS = 8192

# Patrón de hallazgo B (tests/eval/results/e09_t05_plan_b_investigacion.md): el LLM cita
# el nombre del documento fuente junto con "páginas NNN" dentro del cuerpo de la
# respuesta, duplicando la sección `Fuentes consultadas:` que añade
# `_build_sources_section()` de forma determinista.
_INLINE_PAGE_CITATION_RE = re.compile(r"páginas?\s+\d+", re.IGNORECASE)


def _load_case():
    entries = load_dataset(_DATASET_PATH)
    cases = validate_dataset(entries)
    for case in cases:
        if case.id == _CASE_ID:
            return case
    raise ValueError(f"Caso {_CASE_ID!r} no encontrado en {_DATASET_PATH}")


def _dump_chunks(raw_results) -> list[dict]:
    return [
        {
            "source": doc.metadata.get("source"),
            "filename": doc.metadata.get("filename"),
            "score": score,
            "content": doc.page_content,
        }
        for doc, score in raw_results
    ]


def _clean_response(pipeline: RAGPipeline, question: str, raw_results) -> str:
    """Respuesta clínica sin el bloque de fuentes concatenado (D-026/D-041).

    Mismo patrón que `scripts/run_ragas_eval.py::_clean_response`: `pipeline.query()`
    no expone la respuesta pura por contrato (rag/pipeline.py, E-04 T-06); se recalcula
    el mismo bloque de fuentes determinista y se recorta si está presente, en lugar de
    reimplementar la generación fuera de la clase.
    """
    language = detect_language(question)
    full_response = pipeline.query(question)
    sources_section = _build_sources_section(raw_results, language)
    if sources_section and full_response.endswith(sources_section):
        return full_response[: -len(sources_section)].rstrip("\n")
    return full_response


def _finding_b_contrast(response: str, chunks: list[dict]) -> dict:
    """Contraste con la hipótesis de hallazgo B: ¿cita el texto una página inline?

    Comprueba dos señales independientes sobre el cuerpo de la respuesta (ya sin la
    sección de fuentes determinista, ver `_clean_response`):
    1. Patrón "página(s) NNN" (el que documentó hallazgo B literalmente).
    2. Mención literal del nombre de fichero de alguna de las fuentes recuperadas.
    """
    page_match = _INLINE_PAGE_CITATION_RE.search(response)
    filenames_in_chunks = sorted({c["filename"] for c in chunks if c.get("filename")})
    filenames_cited_inline = [
        filename for filename in filenames_in_chunks if filename in response
    ]

    fragment = None
    if page_match:
        start = max(0, page_match.start() - 60)
        end = min(len(response), page_match.end() + 20)
        fragment = response[start:end].strip()

    present = bool(page_match) or bool(filenames_cited_inline)
    return {
        "present": present,
        "page_pattern_match": page_match.group(0) if page_match else None,
        "filenames_cited_inline": filenames_cited_inline,
        "fragment": fragment,
    }


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)
    case = _load_case()
    print(f"[{case.id}] {case.question!r}")

    # Paso 2 — retrieval real de producción (KB ampliada + peso adaptativo, ya activos).
    raw_results = pipeline.retrieve(case.question)
    applied_weights = list(pipeline._retriever.weights)
    chunks = _dump_chunks(raw_results)
    print(f"Pesos realmente aplicados en pipeline.retrieve(): {applied_weights}")
    print(f"Top-{len(chunks)} recuperado:")
    for chunk in chunks:
        print(f"  - {chunk['source']}/{chunk['filename']} (score={chunk['score']:.4f})")

    # Paso 3 — respuesta real generada, sin el bloque de fuentes determinista.
    response = _clean_response(pipeline, case.question, raw_results)
    print(f"\nRespuesta real:\n{response}\n")

    # Restricción "Falso Negativo Cero" (AGENTS.md): señal automática barata de si esta
    # pregunta informativa (is_alarm=false) disparó el filtro de seguridad de forma
    # inesperada. No sustituye la lectura manual del tono (paso 5).
    unexpected_alarm = check_alarm_signals(case.question)
    if unexpected_alarm:
        print("¡Alarma de seguridad inesperada disparada para este caso informativo!")

    # Paso 4 — contraste con la hipótesis de hallazgo B (cita inline de documento/páginas).
    finding_b = _finding_b_contrast(response, chunks)
    print(f"Contraste hallazgo B (cita inline presente): {finding_b['present']}")
    if finding_b["fragment"]:
        print(f"  Fragmento: {finding_b['fragment']!r}")

    # Paso 6 — estabilidad del juez de Faithfulness: dos invocaciones sobre el MISMO
    # SingleTurnSample (misma respuesta, mismo contexto), sin volver a llamar a
    # retrieve() ni query().
    evaluator_llm = LangchainLLMWrapper(
        ChatGoogleGenerativeAI(
            model=rag_config["LLM_MODEL"],
            temperature=rag_config["LLM_TEMPERATURE"],
            top_p=rag_config["LLM_TOP_P"],
            max_output_tokens=_EVALUATOR_MAX_TOKENS,
            google_api_key=rag_config["GOOGLE_API_KEY"],
            thinking_budget=0,
        )
    )
    faithfulness_metric = Faithfulness(llm=evaluator_llm)
    sample = SingleTurnSample(
        user_input=case.question,
        response=response,
        retrieved_contexts=[doc.page_content for doc, _ in raw_results],
        reference=case.expected_answer,
    )

    print("Invocando Faithfulness dos veces sobre el mismo SingleTurnSample...")
    judge_runs = []
    for run_index in (1, 2):
        score = faithfulness_metric.single_turn_score(sample)
        print(f"  Run {run_index}: faithfulness={score}")
        judge_runs.append(score)

    judge_stable = judge_runs[0] == judge_runs[1]
    print(f"¿Juez estable entre las dos ejecuciones? {judge_stable}")

    # Paso 7 — volcado completo.
    output = {
        "case_id": case.id,
        "question": case.question,
        "expected_answer": case.expected_answer,
        "historical_faithfulness_scores": {
            "pre_e11_e09_t05": 0.722,
            "post_t01_e11_t02_baseline": 0.615,
            "post_t02_current": 0.385,
        },
        "response": response,
        "unexpected_alarm": unexpected_alarm,
        "production_retrieval": {
            "applied_weights": applied_weights,
            "chunks": chunks,
        },
        "finding_b_contrast": finding_b,
        "tone_note_manual": None,
        "judge_stability": {
            "runs": judge_runs,
            "stable": judge_stable,
            "evaluator_model": rag_config["LLM_MODEL"],
            "evaluator_temperature": rag_config["LLM_TEMPERATURE"],
        },
        "causa_raiz_confirmada": None,
    }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print(
        "\nParada explícita (paso 8): 'tone_note_manual' y 'causa_raiz_confirmada' se "
        "completan tras la lectura manual de 'response' en Cowork. El script no aplica "
        "ningún fix ni toca rag/retriever.py ni prompts. Vuelta a Cowork para decidir la "
        "causa raíz de las dos caídas y redactar el desglose final de T-06 "
        "(docs/evaluation.md) y el cierre de la tarea."
    )


if __name__ == "__main__":
    main()
