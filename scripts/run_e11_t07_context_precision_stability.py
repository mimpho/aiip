"""Estabilidad del juez de Context Precision en `eval_08`/`eval_13` (E-11 T-07, Ronda 2 / D-071).

La Ronda 1 de T-07 (`tests/eval/results/e11_t07_ragas_regression_check.json`) encontró
dos caídas de Context Precision por encima del umbral orientativo (~0.10):
`eval_08` (0.500 → 0.200, Δ−0.300) y `eval_13` (0.143 → 0.000, Δ−0.143), frente al
registro oficial de T-02 (`tests/eval/results/e09_t02_ragas_full_scores.json`). D-071
decide investigar si la varianza viene de la generación (la respuesta de hoy es
distinta a la de T-02) o del juez LLM antes de decidir si es ruido conocido
(D-058/D-069/T-05) o una regresión real.

Para cada caso, una única reproducción real (`pipeline.retrieve()` +
`_clean_response()`, mismo patrón que `scripts/run_ragas_eval.py`) construye un único
`SingleTurnSample`, y `ContextPrecision.single_turn_score()` se invoca dos veces sobre
ESE MISMO sample — sin repetir retrieval ni generación entre las dos invocaciones,
mismo patrón exacto que el paso 6 de `scripts/run_e11_t06_eval06_investigation.py`
para Faithfulness. Si los dos scores del juez coinciden entre sí pero no con T-02, la
varianza está en la generación. Si difieren entre sí, la varianza está en el juez.

Investigación pura (D-071, mismo patrón que D-065/T-06): no modifica
`prompts/system_prompt_family.txt` ni `rag/retriever.py`, no aplica ningún fix. Vuelca
el resultado completo a
`tests/eval/results/e11_t07_context_precision_stability.json` (campo
`interpretacion: null` por caso, para completar en Cowork tras la lectura manual). No
es un test automatizado (D-050): sin asserts.

Uso:
    python scripts/run_e11_t07_context_precision_stability.py
"""

import json
import sys
import types
from pathlib import Path

# `python scripts/run_e11_t07_context_precision_stability.py` no añade la raíz del
# repo a sys.path (solo scripts/); se añade explícitamente para poder importar
# `rag`/`evaluation`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ragas (API legacy, D-051) importa incondicionalmente
# `langchain_community.chat_models.vertexai.ChatVertexAI` al cargar `ragas.llms.base`,
# que ya no existe en la línea moderna de langchain-community (0.4.x, D-010). Mismo
# stub que `scripts/run_ragas_eval.py`.
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _vertexai_stub = types.ModuleType("langchain_community.chat_models.vertexai")

    class _UnusedChatVertexAI:
        pass

    _vertexai_stub.ChatVertexAI = _UnusedChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = _vertexai_stub

from langchain_google_genai import ChatGoogleGenerativeAI
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import ContextPrecision

from evaluation.dataset import load_dataset, validate_dataset
from rag.config import load_rag_config
from rag.language import detect_language
from rag.pipeline import RAGPipeline, _build_sources_section

_DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "eval" / "dataset_partial.json"
)
_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "eval"
    / "results"
    / "e11_t07_context_precision_stability.json"
)

# Valores oficiales de T-02 (e09_t02_ragas_full_scores.json) y de la Ronda 1 de T-07
# (e11_t07_ragas_regression_check.json), documentados en tasks/E11-T07-plan.md.
_TARGET_CASES = {
    "eval_08": {"t02_context_precision": 0.500, "ronda1_context_precision": 0.19999999998},
    "eval_13": {"t02_context_precision": 0.143, "ronda1_context_precision": 0.0},
}

# Mismo motivo que scripts/run_ragas_eval.py: LLM_MAX_TOKENS (1024) está calibrado
# para RAGGenerator, no para las llamadas internas de RAGAS.
_EVALUATOR_MAX_TOKENS = 8192


def _load_target_cases():
    entries = load_dataset(_DATASET_PATH)
    all_cases = validate_dataset(entries)
    by_id = {case.id: case for case in all_cases if case.id in _TARGET_CASES}
    missing = _TARGET_CASES.keys() - by_id.keys()
    if missing:
        raise ValueError(f"Casos no encontrados en {_DATASET_PATH}: {sorted(missing)}")
    return [by_id[case_id] for case_id in _TARGET_CASES]


def _clean_response(pipeline: RAGPipeline, question: str, raw_results) -> str:
    """Respuesta clínica sin el bloque de fuentes concatenado (D-026/D-041).

    Mismo patrón que `scripts/run_ragas_eval.py::_clean_response`.
    """
    language = detect_language(question)
    full_response = pipeline.query(question)
    sources_section = _build_sources_section(raw_results, language)
    if sources_section and full_response.endswith(sources_section):
        return full_response[: -len(sources_section)].rstrip("\n")
    return full_response


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)
    cases = _load_target_cases()

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
    context_precision_metric = ContextPrecision(llm=evaluator_llm)

    results = []
    for case in cases:
        print(f"[{case.id}] {case.question!r}")

        # Única reproducción real: retrieval + generación, sin repetir entre las dos
        # invocaciones del juez.
        raw_results = pipeline.retrieve(case.question)
        retrieved_contexts = [doc.page_content for doc, _ in raw_results]
        response = _clean_response(pipeline, case.question, raw_results)
        print(f"  Respuesta real:\n{response}\n")

        sample = SingleTurnSample(
            user_input=case.question,
            response=response,
            retrieved_contexts=retrieved_contexts,
            reference=case.expected_answer,
        )

        print(f"  Invocando ContextPrecision dos veces sobre el mismo SingleTurnSample...")
        judge_runs = []
        for run_index in (1, 2):
            score = context_precision_metric.single_turn_score(sample)
            print(f"    Run {run_index}: context_precision={score}")
            judge_runs.append(score)
        judge_stable = judge_runs[0] == judge_runs[1]
        print(f"  ¿Juez estable entre las dos ejecuciones? {judge_stable}")

        results.append(
            {
                "case_id": case.id,
                "question": case.question,
                "expected_answer": case.expected_answer,
                "historical_context_precision": _TARGET_CASES[case.id],
                "retrieved_contexts": retrieved_contexts,
                "response": response,
                "judge_stability": {
                    "runs": judge_runs,
                    "stable": judge_stable,
                    "evaluator_model": rag_config["LLM_MODEL"],
                    "evaluator_temperature": rag_config["LLM_TEMPERATURE"],
                },
                "interpretacion": None,
            }
        )

    output = {"cases": results}
    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print(
        "\nParada explícita: 'interpretacion' se completa tras la lectura manual en "
        "Cowork. El script no aplica ningún fix ni toca rag/retriever.py ni prompts."
    )


if __name__ == "__main__":
    main()
