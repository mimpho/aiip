"""Investigación dirigida: `eval_25` (banda Grave nueva, Faithfulness 0.32) — E-13 T-04.

`eval_25` ("¿Puede mi hijo marcharse de convivencias varios días?") ya figuraba en
`docs/evaluation.md` §5.4 como "sigue abierto sin investigar" (hallazgo B de E-09,
Answer Relevancy 0.0). Tras la remedición de E-13 (T-04, corpus ampliado con 40 fichas de
MedlinePlus Genetics), Faithfulness cae de 0.857 (banda Leve, pre-E-13) a 0.32 (banda
Grave) — mientras que Context Precision (0.0), Context Recall (1.0) y Answer Relevancy
(0.0) son **idénticos** antes y después. Como el retrieval no cambió (mismos scores de
Context Precision/Recall), la hipótesis de partida es que la caída es variación de
generación/juez, no un efecto real de las 40 fichas nuevas — este script lo confirma o lo
descarta, sin darlo por hecho (paso 11 de `tasks/E13-T04-plan.md`, decisión de Marcos tras
revisar `tests/eval/results/e13_t04_cierre.md`).

Reproduce el caso contra el pipeline real (KB ampliada de E-13, ya activa) y comprueba la
estabilidad del juez de Faithfulness (dos invocaciones sobre el mismo `SingleTurnSample`),
mismo patrón que `run_e11_t06_eval06_investigation.py` (D-069) y
`run_e11_t05_eval15_investigation.py` (D-068).

Investigación pura (D-065): no modifica `rag/retriever.py` ni prompts, no aplica ningún
fix. Vuelca el resultado completo a
`tests/eval/results/e13_t04_eval25_investigacion.json` para que Marcos y el agente decidan
la causa raíz en Cowork. No es un test automatizado (D-050): sin asserts.

Uso:
    PYTHONPATH=. python scripts/run_e13_t04_eval25_investigation.py
"""

import json
import sys
import types
from pathlib import Path

# `python scripts/run_e13_t04_eval25_investigation.py` no añade la raíz del repo a
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
    / "e13_t04_eval25_investigacion.json"
)

_CASE_ID = "eval_25"

# Mismo motivo que scripts/run_ragas_eval.py: LLM_MAX_TOKENS (1024) está calibrado para
# RAGGenerator, no para las llamadas internas de RAGAS.
_EVALUATOR_MAX_TOKENS = 8192


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


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)
    case = _load_case()
    print(f"[{case.id}] {case.question!r}")

    # Retrieval real de producción (KB ampliada de E-13, ya activa).
    raw_results = pipeline.retrieve(case.question)
    applied_weights = list(pipeline._retriever.weights)
    chunks = _dump_chunks(raw_results)
    print(f"Pesos realmente aplicados en pipeline.retrieve(): {applied_weights}")
    print(f"Top-{len(chunks)} recuperado:")
    for chunk in chunks:
        print(f"  - {chunk['source']}/{chunk['filename']} (score={chunk['score']:.4f})")

    # Respuesta real generada, sin el bloque de fuentes determinista.
    response = _clean_response(pipeline, case.question, raw_results)
    print(f"\nRespuesta real:\n{response}\n")
    print(f"Expected answer (referencia RAGAS):\n{case.expected_answer}\n")

    # Restricción "Falso Negativo Cero" (AGENTS.md): señal automática barata de si esta
    # pregunta informativa (is_alarm=false) disparó el filtro de seguridad de forma
    # inesperada.
    unexpected_alarm = check_alarm_signals(case.question)
    if unexpected_alarm:
        print("¡Alarma de seguridad inesperada disparada para este caso informativo!")

    # Estabilidad del juez de Faithfulness: dos invocaciones sobre el MISMO
    # SingleTurnSample (misma respuesta, mismo contexto), sin volver a llamar a
    # retrieve() ni query() — mismo patrón que D-069/D-072.
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

    output = {
        "case_id": case.id,
        "question": case.question,
        "expected_answer": case.expected_answer,
        "historical_faithfulness_scores": {
            "pre_e13_t04": 0.8571428571428571,
            "post_e13_t04_registered": 0.32,
        },
        "historical_other_metrics_unchanged": {
            "context_precision": 0.0,
            "context_recall": 1.0,
            "answer_relevancy": 0.0,
        },
        "response": response,
        "unexpected_alarm": unexpected_alarm,
        "production_retrieval": {
            "applied_weights": applied_weights,
            "chunks": chunks,
        },
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
        "\nParada explícita: 'causa_raiz_confirmada' se completa tras la lectura manual "
        "de 'response' contra 'expected_answer' y los chunks recuperados. El script no "
        "aplica ningún fix ni toca rag/retriever.py ni prompts."
    )


if __name__ == "__main__":
    main()
