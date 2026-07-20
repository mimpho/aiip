"""Investigación dirigida: `eval_15` (Context Precision/Recall en 0.0) — E-11 T-05.

`eval_15` ("¿Podemos viajar en avión llevando la medicación de inmunoglobulinas?") se
mantiene en `context_precision` = 0.0 en las tres mediciones disponibles pese a que T-01
añadió dos fuentes que cubren justo este tema (SEICAP "50 preguntas clave" — capítulo de
viajes — e IPOPI "Can PID patients travel and live abroad?" FAQ, `docs/kb-sources.md`
líneas 43/45), y `context_recall` retrocede de 1.0 (tras T-01) a 0.0 (tras T-02) con el
peso adaptativo. Dos hipótesis a contrastar (`tasks/E11-T05-plan.md`):

1. Retrieval real: las fuentes nuevas no se recuperan en el top-k, o se recuperan pero su
   contenido no se solapa con `expected_answer`.
2. Ruido de medición del juez LLM de RAGAS (`ContextPrecision`/`ContextRecall` con
   `evaluator_llm` a `temperature=LLM_TEMPERATURE`, no determinista).

Investigación pura (D-065): no modifica `rag/retriever.py` ni prompts, no aplica ningún
fix. Vuelca la transcripción completa (retrieval real, señal léxica, contraste frase a
frase contra la referencia, y dos invocaciones del juez sobre el MISMO contexto) a
`tests/eval/results/e11_t05_eval15_investigacion.json` para que Marcos y el agente
decidan la causa raíz en Cowork. No es un test automatizado (D-050): sin asserts.

Uso:
    python scripts/run_e11_t05_eval15_investigation.py
"""

import json
import sys
import types
from pathlib import Path

# `python scripts/run_e11_t05_eval15_investigation.py` no añade la raíz del repo a
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
from ragas.metrics import ContextPrecision, ContextRecall

from evaluation.dataset import load_dataset, validate_dataset
from rag.config import load_rag_config
from rag.pipeline import RAGPipeline
from rag.retriever import (
    _NO_SIGNAL_BM25_WEIGHT,
    _NO_SIGNAL_VECTOR_WEIGHT,
    _SIGNAL_BM25_WEIGHT,
    _SIGNAL_VECTOR_WEIGHT,
    has_lexical_signal,
)

_DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "eval" / "dataset_partial.json"
)
_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "eval"
    / "results"
    / "e11_t05_eval15_investigacion.json"
)

_CASE_ID = "eval_15"

# Mismo motivo que scripts/run_ragas_eval.py: LLM_MAX_TOKENS (1024) está calibrado para
# RAGGenerator, no para las llamadas internas de RAGAS.
_EVALUATOR_MAX_TOKENS = 8192

# Fuentes añadidas en T-01 que deberían cubrir eval_15 (docs/kb-sources.md líneas 43/45).
_EXPECTED_NEW_SOURCES = {
    ("seicap", "50-preguntas-inmunodeficiencias.pdf"),
    ("ipopi", "pid-patients-travel.html"),
}

# Afirmaciones clave de `expected_answer` (tests/eval/dataset_partial.json, eval_15),
# descompuestas en claims independientes para un chequeo léxico de cobertura por chunk.
# Es una ayuda automática (mismo patrón que `mentions_barcelona`/`mentions_vic_exact_word`
# en scripts/run_e11_t03_grounding_investigation.py) — no sustituye el contraste manual
# frase a frase del paso 5 del plan, que se añade sobre el resultado real tras ejecutar.
_REFERENCE_CLAIMS = {
    "posible_viajar_con_planificacion": ["viaj", "avión", "avion", "vuelo"],
    "llevar_informe_medico": ["informe médico", "informe medico"],
    "condiciones_conservacion_frio": ["conserva", "frío", "frio", "refriger"],
    "consultar_equipo_medico_o_farmacia": ["equipo médico", "equipo medico", "farmacia"],
}


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


def _claim_coverage(chunks: list[dict]) -> dict:
    combined = "\n\n".join(c["content"] for c in chunks).lower()
    return {
        claim: any(kw in combined for kw in keywords)
        for claim, keywords in _REFERENCE_CLAIMS.items()
    }


def _new_sources_present(chunks: list[dict]) -> dict:
    found = {(c["source"], c["filename"]) for c in chunks}
    present = _EXPECTED_NEW_SOURCES & found
    return {
        "present": sorted(f"{s}/{f}" for s, f in present),
        "missing": sorted(f"{s}/{f}" for s, f in _EXPECTED_NEW_SOURCES - present),
        "actual_sources_in_topk": sorted(f"{s}/{f}" for s, f in found if s and f),
    }


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)
    case = _load_case()
    print(f"[{case.id}] {case.question!r}")

    # Paso 2 — señal léxica (D-061): determina si el peso adaptativo coincide con el
    # peso uniforme para esta pregunta, condición necesaria para que la hipótesis 2
    # (ruido del juez, no cambio real de retrieval) sea plausible.
    bm25_retriever = pipeline._retriever.retrievers[0]
    lexical_signal = has_lexical_signal(case.question, bm25_retriever)
    signal_weights = {
        "bm25": _SIGNAL_BM25_WEIGHT if lexical_signal else _NO_SIGNAL_BM25_WEIGHT,
        "vector": _SIGNAL_VECTOR_WEIGHT if lexical_signal else _NO_SIGNAL_VECTOR_WEIGHT,
    }
    print(f"Señal léxica (has_lexical_signal): {lexical_signal}")
    print(f"Pesos que corresponden según D-061: {signal_weights}")

    # Paso 3 — retrieval de producción, peso adaptativo actual (el que aplica hoy).
    raw_results = pipeline.retrieve(case.question)
    applied_weights_production = list(pipeline._retriever.weights)
    production_chunks = _dump_chunks(raw_results)
    print(f"Pesos realmente aplicados en pipeline.retrieve(): {applied_weights_production}")
    print(f"Top-{len(production_chunks)} recuperado:")
    for chunk in production_chunks:
        print(f"  - {chunk['source']}/{chunk['filename']} (score={chunk['score']:.4f})")

    # Paso 4 — ¿aparecen las fuentes nuevas de T-01 (SEICAP viajes / IPOPI FAQ viajes)?
    new_sources_check = _new_sources_present(production_chunks)
    print(f"Fuentes nuevas de T-01 presentes en el top-k: {new_sources_check['present']}")
    if not new_sources_check["present"]:
        print(f"Fuentes que ocupan esas posiciones en su lugar: {new_sources_check['actual_sources_in_topk']}")

    # Paso 5 — cobertura léxica de las afirmaciones de expected_answer (ayuda automática;
    # el contraste manual frase a frase se añade tras inspeccionar production_chunks).
    claim_coverage = _claim_coverage(production_chunks)
    print(f"Cobertura léxica de las afirmaciones de expected_answer: {claim_coverage}")

    # Paso 6 — estabilidad del juez LLM: dos invocaciones sobre el MISMO
    # retrieved_contexts obtenido en el paso 3, sin volver a llamar a retrieve().
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
    context_recall_metric = ContextRecall(llm=evaluator_llm)
    sample = SingleTurnSample(
        user_input=case.question,
        retrieved_contexts=[doc.page_content for doc, _ in raw_results],
        reference=case.expected_answer,
    )

    print("Invocando ContextPrecision/ContextRecall dos veces sobre el mismo contexto...")
    judge_runs = []
    for run_index in (1, 2):
        run_scores = {
            "context_precision": context_precision_metric.single_turn_score(sample),
            "context_recall": context_recall_metric.single_turn_score(sample),
        }
        print(f"  Run {run_index}: {run_scores}")
        judge_runs.append(run_scores)

    judge_stable = judge_runs[0] == judge_runs[1]
    print(f"¿Juez estable entre las dos ejecuciones? {judge_stable}")

    # Paso 7 — solo si el paso 2 dio señal léxica True: contraste informativo forzando
    # los pesos NO_SIGNAL sobre el MISMO EnsembleRetriever ya cacheado, para entender el
    # mecanismo. No es el peso real aplicado en producción para esta consulta.
    no_signal_contrast = None
    if lexical_signal:
        print(
            "Señal léxica True: contraste informativo con pesos NO_SIGNAL "
            f"({_NO_SIGNAL_BM25_WEIGHT}/{_NO_SIGNAL_VECTOR_WEIGHT})..."
        )
        original_weights = list(pipeline._retriever.weights)
        pipeline._retriever.weights = [_NO_SIGNAL_BM25_WEIGHT, _NO_SIGNAL_VECTOR_WEIGHT]
        no_signal_docs = pipeline._retriever.invoke(case.question)
        no_signal_chunks = _dump_chunks([(doc, 1.0 / (i + 1)) for i, doc in enumerate(no_signal_docs)])
        pipeline._retriever.weights = original_weights

        no_signal_contrast = {
            "weights_used": [_NO_SIGNAL_BM25_WEIGHT, _NO_SIGNAL_VECTOR_WEIGHT],
            "note": (
                "Contraste informativo, no es el peso que se aplica en producción para "
                "esta consulta (señal léxica True => D-061 usa el peso uniforme/SIGNAL)."
            ),
            "chunks": no_signal_chunks,
            "new_sources_present": _new_sources_present(no_signal_chunks)["present"],
        }

    # Paso 8 — volcado completo.
    output = {
        "case_id": case.id,
        "question": case.question,
        "expected_answer": case.expected_answer,
        "lexical_signal": {
            "has_lexical_signal": lexical_signal,
            "weights_expected_by_d061": signal_weights,
        },
        "production_retrieval": {
            "applied_weights": applied_weights_production,
            "chunks": production_chunks,
        },
        "new_sources_check": new_sources_check,
        "claim_coverage_lexical_aid": claim_coverage,
        "judge_stability": {
            "runs": judge_runs,
            "stable": judge_stable,
            "evaluator_model": rag_config["LLM_MODEL"],
            "evaluator_temperature": rag_config["LLM_TEMPERATURE"],
        },
        "no_signal_weight_contrast": no_signal_contrast,
        "manual_phrase_by_phrase_contrast": None,
    }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print(
        "\nParada explícita (paso 9): 'manual_phrase_by_phrase_contrast' se completa tras "
        "inspeccionar production_retrieval.chunks. El script no aplica ningún fix ni toca "
        "rag/retriever.py ni prompts. Vuelta a Cowork para decidir causa raíz "
        "(retrieval real vs. ruido de medición) y next steps (T-06/T-07)."
    )


if __name__ == "__main__":
    main()
