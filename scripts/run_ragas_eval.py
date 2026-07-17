"""RAGAS Faithfulness + Answer Relevancy + Context Precision/Recall (E-07 T-02 / E-09 T-02).

Ejecuta `RAGPipeline` real (sin mocks) sobre los 27 casos informativos del
dataset parcial (`tests/eval/dataset_partial.json`, is_alarm=false) y calcula
Faithfulness y Answer Relevancy con RAGAS, usando el mismo `LLM_MODEL` de
producción como evaluador y `rag.embeddings.get_embeddings()` (BAAI/bge-m3)
para Answer Relevancy. Decisiones de diseño: D-050/D-051 (task-start),
detalle de implementación en tasks/E07-T02-plan.md.

E-09 T-02 (D-055) añade Context Precision y Context Recall sobre el
subconjunto `category in ("informativo", "otro_idioma")` (32 casos) del
mismo `dataset_partial.json`, ya ampliado a cobertura completa (72 casos,
E-09 T-01), reutilizando el mismo `evaluator_llm`. Resultado en fichero
independiente (`tests/eval/results/e09_t02_ragas_full_scores.json`), sin
tocar el histórico de E-07 T-02. Detalle en tasks/E09-T02-plan.md.

No es un test automatizado (D-050, mismo patrón que
scripts/smoke_test_rag.py, E-06 T-07): no hay asserts, solo instrumentación
y volcado a fichero para revisión manual de Marcos. Ver
tests/eval/e07_t02_ragas_faithfulness_relevancy.feature y
tests/eval/e09_t02_ragas_context_metrics.feature.

La ejecución es incremental: cada caso ya presente en el fichero de
resultados correspondiente se salta, así que una interrupción a mitad de
ejecución (p. ej. 429 de cuota de Gemini) no pierde el progreso ya hecho ni
repite llamadas.

Uso:
    python scripts/run_ragas_eval.py
"""

import json
import sys
import types
from pathlib import Path

# `python scripts/run_ragas_eval.py` no añade la raíz del repo a sys.path
# (solo scripts/), y aquí no hay setup.py/pyproject que instale el proyecto
# en modo editable. Se añade explícitamente para poder importar `rag`/`evaluation`.
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
    / "e09_t02_ragas_full_scores.json"
)

# LLM_MAX_TOKENS (1024, rag/config.py) está calibrado para respuestas de chat
# concisas (RAGGenerator), no para las llamadas internas de RAGAS: Faithfulness
# le pide al LLM listar y juzgar cada afirmación de la respuesta (statement +
# reason + verdict) en un único JSON, que con 1024 tokens queda truncado a
# mitad del último elemento y rompe el parseo. El resto de parámetros de
# inferencia (modelo, temperatura, top_p) sí se reutilizan tal cual de la
# config real.
_EVALUATOR_MAX_TOKENS = 8192


def _load_existing_results() -> dict:
    if not _RESULTS_PATH.exists():
        return {"cases": []}
    return json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))


def _clean_response(pipeline: RAGPipeline, question: str, raw_results) -> str:
    """Respuesta clínica sin el bloque de fuentes concatenado (D-026/D-041).

    `pipeline.query()` no expone la respuesta pura por contrato (rag/pipeline.py,
    E-04 T-06); se recalcula el mismo bloque de fuentes con la función
    determinista que usa `query()` internamente y se recorta si está presente,
    en lugar de reimplementar la generación fuera de la clase.
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
    # D-055: subconjunto con expected_answer clínico grounded en los chunks
    # recuperados (requisito de Context Precision/Recall) — excluye
    # diagnostico, limite, prompt_injection y alarma.
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
            # Caso informativo/otro_idioma (is_alarm=false en el dataset) que
            # disparó el filtro de seguridad de forma inesperada: no es un
            # bug de este script, pero es una señal relevante para el
            # informe de T-04.
            result["unexpected_alarm"] = True
        output["cases"].append(result)
        _write_output()

    _write_output()
    print(f"\nResultados escritos en {_RESULTS_PATH}")


if __name__ == "__main__":
    main()
