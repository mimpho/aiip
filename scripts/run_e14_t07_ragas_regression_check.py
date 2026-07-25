"""Regresión mecánica RAGAS del path sin perfil (E-14 T-07, D-094 — bloque 2a).

Re-ejecuta el mismo subconjunto de 32 casos (`category in ("informativo",
"otro_idioma")`) de `tests/eval/dataset_partial.json` que ya usa
`scripts/run_ragas_eval.py`, tal cual lo invoca hoy: sin pasar `profile` a
`RAGPipeline.query()` (siempre `None`). El objetivo no es medir tono/registro
(RAGAS no lo mide, D-094) sino confirmar que el cambio de prompt de T-06
(placeholder `profile_context` en `_PROMPT_TEMPLATE`, D-093) no rompió por
accidente el path mayoritario de usuarios sin perfil.

Mismo patrón que `scripts/run_ragas_eval.py` (stub de `ChatVertexAI`,
`evaluator_llm`, 4 métricas). Escribe a un fichero de resultados propio
(`tests/eval/results/e14_t07_ragas_regression_check.json`) — no toca
`e09_t02_ragas_full_scores_e13_t04_baseline.json` ni `e09_t02_ragas_full_scores.json`,
que siguen siendo los registros oficiales de E-13 T-04.

No es un test automatizado (D-050): sin asserts, solo instrumentación y
volcado a fichero para revisión manual de Marcos, comparando el `aggregate`
final contra el baseline de E-13 T-04 (ver tasks/E14-T07-plan.md).

Uso:
    python scripts/run_e14_t07_ragas_regression_check.py
"""

import json
import sys
import types
from pathlib import Path

# `python scripts/run_e14_t07_ragas_regression_check.py` no añade la raíz del
# repo a sys.path (solo scripts/); se añade explícitamente para poder
# importar `rag`/`evaluation`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mismo stub que scripts/run_ragas_eval.py: ragas importa incondicionalmente
# `langchain_community.chat_models.vertexai.ChatVertexAI`, submódulo ya
# removido de la línea moderna de langchain-community que usa el proyecto.
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _vertexai_stub = types.ModuleType("langchain_community.chat_models.vertexai")

    class _UnusedChatVertexAI:
        pass

    _vertexai_stub.ChatVertexAI = _UnusedChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = _vertexai_stub

from langchain_google_genai import ChatGoogleGenerativeAI
from ragas.dataset_schema import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import ContextPrecision, ContextRecall, Faithfulness, ResponseRelevancy

from evaluation.dataset import load_dataset, validate_dataset
from rag.config import load_rag_config
from rag.embeddings import get_embeddings
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
    / "e14_t07_ragas_regression_check.json"
)

# Mismo ajuste que run_ragas_eval.py: LLM_MAX_TOKENS de producción (1024) no
# basta para el JSON de veredictos de Faithfulness.
_EVALUATOR_MAX_TOKENS = 8192


def _load_existing_results() -> dict:
    if not _RESULTS_PATH.exists():
        return {"cases": []}
    return json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))


def _clean_response(pipeline: RAGPipeline, question: str, raw_results) -> str:
    """Respuesta clínica sin el bloque de fuentes concatenado (D-026/D-041)."""
    language = detect_language(question)
    full_response = pipeline.query(question)
    sources_section = _build_sources_section(raw_results, language)
    if sources_section and full_response.endswith(sources_section):
        return full_response[: -len(sources_section)].rstrip("\n")
    return full_response


def _aggregate(cases: list[dict]) -> dict:
    n = len(cases)
    return {
        "n_cases": n,
        "faithfulness_mean": sum(c["faithfulness"] for c in cases) / n if n else None,
        "answer_relevancy_mean": sum(c["answer_relevancy"] for c in cases) / n if n else None,
        "context_precision_mean": sum(c["context_precision"] for c in cases) / n if n else None,
        "context_recall_mean": sum(c["context_recall"] for c in cases) / n if n else None,
    }


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)

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
    evaluator_embeddings = LangchainEmbeddingsWrapper(get_embeddings())
    faithfulness_metric = Faithfulness(llm=evaluator_llm)
    relevancy_metric = ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)
    context_precision_metric = ContextPrecision(llm=evaluator_llm)
    context_recall_metric = ContextRecall(llm=evaluator_llm)

    entries = load_dataset(_DATASET_PATH)
    all_cases = validate_dataset(entries)
    target_categories = {"informativo", "otro_idioma"}
    target_cases = [c for c in all_cases if c.category in target_categories]
    print(f"Casos a evaluar (informativo + otro_idioma): {len(target_cases)}")

    output = _load_existing_results()
    scored_ids = {c["id"] for c in output["cases"]}

    def _write_output() -> None:
        output["aggregate"] = _aggregate(output["cases"])
        _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _RESULTS_PATH.write_text(
            json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    for case in target_cases:
        if case.id in scored_ids:
            print(f"[{case.id}] ya evaluado, se salta.")
            continue

        print(f"[{case.id}] evaluando: {case.question!r}")
        try:
            raw_results = pipeline.retrieve(case.question)
            has_alarm = check_alarm_signals(case.question)
            # profile=None (default): mismo comportamiento que
            # scripts/run_ragas_eval.py, sin ejercitar [PERFIL DEL PACIENTE] (D-094).
            response = _clean_response(pipeline, case.question, raw_results)

            sample = SingleTurnSample(
                user_input=case.question,
                response=response,
                retrieved_contexts=[doc.page_content for doc, _ in raw_results],
                reference=case.expected_answer,
            )
            faithfulness_score = faithfulness_metric.single_turn_score(sample)
            answer_relevancy_score = relevancy_metric.single_turn_score(sample)
            context_precision_score = context_precision_metric.single_turn_score(sample)
            context_recall_score = context_recall_metric.single_turn_score(sample)
        except Exception as exc:
            print(f"[{case.id}] error, se reintentará en la próxima ejecución: {exc}")
            continue

        result = {
            "id": case.id,
            "question": case.question,
            "faithfulness": faithfulness_score,
            "answer_relevancy": answer_relevancy_score,
            "context_precision": context_precision_score,
            "context_recall": context_recall_score,
        }
        if has_alarm:
            result["unexpected_alarm"] = True
        output["cases"].append(result)
        _write_output()

    _write_output()
    print(f"\nResultados escritos en {_RESULTS_PATH}")


if __name__ == "__main__":
    main()
