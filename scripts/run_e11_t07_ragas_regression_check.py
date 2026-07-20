"""RAGAS de regresión acotado a 4 casos tras D-067/D-068 (E-11 T-07, Bloque 0).

D-067 (T-04, ajuste de tono en `[TONO — PERFIL FAMILIAR]`) y D-068 (T-05,
generalización de la restricción de información de centro en
`[RESTRICCIONES ABSOLUTAS]`) modificaron `prompts/system_prompt_family.txt` en
producción sin recalcular RAGAS después. Este script reutiliza el patrón de
`scripts/run_ragas_eval.py` (mismo `evaluator_llm`, mismas 4 métricas:
Faithfulness, Answer Relevancy, Context Precision, Context Recall) pero
filtrado a `["eval_03", "eval_04", "eval_08", "eval_13"]` — D-070 acota
explícitamente el recálculo a estos 4 casos en vez de relanzar el dataset
completo (coste de cuota de Gemini, D-027).

Escribe a `tests/eval/results/e11_t07_ragas_regression_check.json`, fichero
nuevo e independiente — no toca `tests/eval/results/e09_t02_ragas_full_scores.json`,
el registro oficial de T-02 que T-06 ya usa para las bandas de severidad
(mismo criterio que D-058/D-069 de no sustituir el número oficial).

No es un test automatizado (D-050): sin asserts, solo instrumentación y
volcado a fichero para revisión manual — comparar contra los valores
oficiales de T-02 documentados en `tasks/E11-T07-plan.md`.

Uso:
    python scripts/run_e11_t07_ragas_regression_check.py
"""

import json
import sys
import types
from pathlib import Path

# `python scripts/run_e11_t07_ragas_regression_check.py` no añade la raíz del
# repo a sys.path (solo scripts/); se añade explícitamente para poder
# importar `rag`/`evaluation`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ragas (API legacy, D-051) importa incondicionalmente
# `langchain_community.chat_models.vertexai.ChatVertexAI` al cargar
# `ragas.llms.base`, aunque no usemos VertexAI. Ese submódulo ya no existe en
# la línea moderna de langchain-community (0.4.x, D-010) que usa el proyecto
# -- fue movido a un paquete standalone tras el aviso de sunset de
# langchain-community. Sin este stub, `import ragas` falla con
# ModuleNotFoundError antes de poder usar Faithfulness/ResponseRelevancy.
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
    / "e11_t07_ragas_regression_check.json"
)

# D-070: acotado a los 4 casos con hallazgo relevante en T-02/T-05/T-06, no el
# dataset completo.
_TARGET_IDS = {"eval_03", "eval_04", "eval_08", "eval_13"}

# Mismo motivo que scripts/run_ragas_eval.py: 1024 tokens (LLM_MAX_TOKENS,
# rag/config.py) trunca el JSON de veredictos de Faithfulness a mitad del
# último elemento.
_EVALUATOR_MAX_TOKENS = 8192


def _load_existing_results() -> dict:
    if not _RESULTS_PATH.exists():
        return {"cases": []}
    return json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))


def _clean_response(pipeline: RAGPipeline, question: str, raw_results) -> str:
    """Respuesta clínica sin el bloque de fuentes concatenado (D-026/D-041).

    Ver scripts/run_ragas_eval.py — misma lógica, `query()` no expone la
    respuesta pura por contrato (rag/pipeline.py, E-04 T-06).
    """
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
    target_cases = [c for c in all_cases if c.id in _TARGET_IDS]
    print(f"Casos a evaluar (regresión D-070): {len(target_cases)}")

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
