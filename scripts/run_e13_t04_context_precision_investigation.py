"""Investigación dirigida: caída de Context Precision (−3.7pp) en la remedición de E-13
T-04 — desglose de los 3 casos sin explicar tras el análisis local de D-086.

D-086 (`decisions.md`) ya descartó dilución generalizada comparando
`e09_t02_ragas_full_scores_pre_e13_t04.json` contra `e09_t02_ragas_full_scores.json`
(32 casos): 26 no cambian, 1 mejora, y solo 5 empeoran, con la caída agregada concentrada
en esos 5. `eval_08` ya está resuelto (mismo patrón bimodal de ruido del juez que D-072,
0.5/0.2). `eval_20` (delta −0.025) es demasiado pequeño para investigar. Quedan 3 casos sin
explicación: `eval_22`, `eval_10`, `eval_63` (el único caso `otro_idioma`, en inglés — mismo
idioma que las 40 fichas nuevas de MedlinePlus, candidato más plausible a dilución real).

Este script (paso 13 de `tasks/E13-T04-plan.md`, D-086) comprueba, para cada uno de los 3
casos, contra el pipeline real (KB ampliada de E-13, ya activa):
1. Si algún chunk de `medlineplus_genetics` aparece en el contexto recuperado (evidencia
   necesaria, no suficiente, de dilución — un chunk nuevo presente no implica que desplace
   contenido más relevante, hay que revisar el contenido).
2. Estabilidad del juez de Context Precision (dos invocaciones sobre el mismo
   `SingleTurnSample`, mismo patrón que D-069/D-072/D-085) — si varía, es ruido del
   evaluador, no del retrieval.

Investigación pura (D-065): no modifica `rag/retriever.py` ni prompts, no aplica ningún
fix. Vuelca el resultado completo a
`tests/eval/results/e13_t04_context_precision_investigacion.json` para que Marcos y el
agente decidan la lectura final en Cowork. No es un test automatizado (D-050): sin
asserts.

Uso:
    PYTHONPATH=. python scripts/run_e13_t04_context_precision_investigation.py
"""

import json
import sys
import types
from pathlib import Path

# `python scripts/run_e13_t04_context_precision_investigation.py` no añade la raíz del
# repo a sys.path (solo scripts/); se añade explícitamente para poder importar
# `rag`/`evaluation`.
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
from ragas.metrics import ContextPrecision

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
    / "e13_t04_context_precision_investigacion.json"
)

_CASE_IDS = ("eval_22", "eval_10", "eval_63")

# Historial de Context Precision de D-086 (pre-E-13 vs. fichero vigente post-E-13), para
# que el volcado quede autocontenido sin tener que cruzar con los ficheros de resultados.
_HISTORICAL_CONTEXT_PRECISION = {
    "eval_22": {"pre_e13_t04": 0.917, "post_e13_t04": 0.500},
    "eval_10": {"pre_e13_t04": 1.000, "post_e13_t04": 0.700},
    "eval_63": {"pre_e13_t04": 0.804, "post_e13_t04": 0.650},
}

# Mismo motivo que scripts/run_ragas_eval.py: LLM_MAX_TOKENS (1024) está calibrado para
# RAGGenerator, no para las llamadas internas de RAGAS.
_EVALUATOR_MAX_TOKENS = 8192


def _load_cases():
    entries = load_dataset(_DATASET_PATH)
    cases = validate_dataset(entries)
    by_id = {case.id: case for case in cases if case.id in _CASE_IDS}
    return [by_id[case_id] for case_id in _CASE_IDS]


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
    cases = _load_cases()

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

    results = {}
    for case in cases:
        print(f"\n=== [{case.id}] {case.question!r} ===")

        raw_results = pipeline.retrieve(case.question)
        chunks = _dump_chunks(raw_results)
        medlineplus_chunks = [
            c for c in chunks if c.get("source") == "medlineplus_genetics"
        ]
        print(f"Top-{len(chunks)} recuperado:")
        for chunk in chunks:
            flag = " <-- medlineplus_genetics" if chunk in medlineplus_chunks else ""
            print(f"  - {chunk['source']}/{chunk['filename']} (score={chunk['score']:.4f}){flag}")
        print(f"¿Chunks de medlineplus_genetics presentes? {bool(medlineplus_chunks)}")

        response = _clean_response(pipeline, case.question, raw_results)
        print(f"\nRespuesta real:\n{response}\n")

        unexpected_alarm = check_alarm_signals(case.question)
        if unexpected_alarm:
            print("¡Alarma de seguridad inesperada disparada para este caso informativo!")

        sample = SingleTurnSample(
            user_input=case.question,
            response=response,
            retrieved_contexts=[doc.page_content for doc, _ in raw_results],
            reference=case.expected_answer,
        )

        print("Invocando ContextPrecision dos veces sobre el mismo SingleTurnSample...")
        judge_runs = []
        for run_index in (1, 2):
            score = context_precision_metric.single_turn_score(sample)
            print(f"  Run {run_index}: context_precision={score}")
            judge_runs.append(score)
        judge_stable = judge_runs[0] == judge_runs[1]
        print(f"¿Juez estable entre las dos ejecuciones? {judge_stable}")

        results[case.id] = {
            "case_id": case.id,
            "question": case.question,
            "expected_answer": case.expected_answer,
            "historical_context_precision": _HISTORICAL_CONTEXT_PRECISION[case.id],
            "response": response,
            "unexpected_alarm": unexpected_alarm,
            "production_retrieval": {
                "chunks": chunks,
                "medlineplus_chunks_present": bool(medlineplus_chunks),
                "medlineplus_chunk_count": len(medlineplus_chunks),
            },
            "judge_stability": {
                "runs": judge_runs,
                "stable": judge_stable,
                "evaluator_model": rag_config["LLM_MODEL"],
                "evaluator_temperature": rag_config["LLM_TEMPERATURE"],
            },
            "causa_probable_confirmada": None,
        }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print(
        "\nParada explícita: 'causa_probable_confirmada' se completa tras la lectura "
        "manual de 'response' y 'production_retrieval.chunks' en Cowork. El script no "
        "aplica ningún fix ni toca rag/retriever.py ni prompts."
    )


if __name__ == "__main__":
    main()
