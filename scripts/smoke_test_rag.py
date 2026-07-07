"""Smoke test manual del pipeline RAG con datos reales de la KB (E-06 T-07).

Ejecuta `RAGPipeline` real (sin mocks) contra un set fijo de preguntas
representativas del perfil familias, usando la colección `family` de
ChromaDB ya indexada con la KB real. Vuelca el resultado de cada pregunta
(idioma detectado, chunks recuperados con fuente y score, respuesta y si
disparó alarma) en `tests/results/e06_t07_smoke_test_results.md` para revisión
manual de Marcos.

No es un test automatizado (D-015, E-06 T-07 es configuración sin TDD):
no hay asserts, solo instrumentación y volcado a fichero para lectura
humana. Ver tests/features/e06_t07_rag_smoke_test.feature.

Uso:
    python scripts/smoke_test_rag.py
    python scripts/smoke_test_rag.py --force-reingest
"""

import argparse
import datetime
import sys
from pathlib import Path

# `python scripts/smoke_test_rag.py` no añade la raíz del repo a sys.path
# (solo scripts/), y aquí no hay setup.py/pyproject que instale el proyecto
# en modo editable. Se añade explícitamente para poder importar `rag`/`ingestion`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.config import load_ingestion_config
from ingestion.pipeline import run_ingestion_pipeline
from rag.config import load_rag_config
from rag.embeddings import get_embeddings
from rag.language import detect_language
from rag.pipeline import RAGPipeline
from rag.retriever import distance_to_similarity, get_retriever
from rag.safety import check_alarm_signals

_COLLECTION_NAME = "family"
_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "results" / "e06_t07_smoke_test_results.md"
)

# Preguntas propuestas en la revisión de T-07 (Paso 1). Editar aquí si Marcos
# quiere cambiar el enunciado exacto antes de ejecutar el smoke test.
QUESTIONS = [
    {
        "label": "Pregunta general sobre IDP",
        "text": "¿Qué es una inmunodeficiencia primaria?",
    },
    {
        "label": "Pregunta sobre una fuente específica de la KB",
        "text": "¿Qué recomendaciones de vacunación existen para pacientes con inmunodeficiencias primarias?",
    },
    {
        "label": "Cross-lingual real (inglés)",
        "text": "What is a primary immunodeficiency?",
    },
    {
        "label": "Señal de alarma (Falso Negativo Cero)",
        "text": (
            "Mi hijo tiene fiebre muy alta, de 40 grados, y le dura ya varios días. "
            "¿Es normal en una inmunodeficiencia primaria?"
        ),
    },
    {
        "label": "Fuera de contexto (no-IDP)",
        "text": "¿Cómo hago una tortilla de patatas?",
    },
]


def _collection_count(embeddings, chroma_path: str) -> int:
    vectorstore = get_retriever(embeddings, chroma_path, _COLLECTION_NAME)
    return vectorstore._collection.count()


def _ensure_kb_indexed(embeddings, rag_config: dict, force_reingest: bool) -> int:
    """Scenario 0: verifica que la colección 'family' tiene la KB real indexada.

    Si está vacía (o si `force_reingest` fuerza una reingesta completa), corre
    `run_ingestion_pipeline()` (T-05, D-024) contra `KB_RAW_DATA_PATH` real
    antes de continuar con las preguntas del smoke test.
    """
    count = _collection_count(embeddings, rag_config["CHROMA_PATH"])
    if count > 0 and not force_reingest:
        print(f"[Scenario 0] Colección '{_COLLECTION_NAME}' ya tiene {count} chunks indexados.")
        return count

    ingestion_config = load_ingestion_config()
    source_path = ingestion_config["KB_RAW_DATA_PATH"]
    print(
        f"[Scenario 0] Colección '{_COLLECTION_NAME}' vacía o reingesta forzada. "
        f"Ejecutando run_ingestion_pipeline() contra '{source_path}'..."
    )
    summary = run_ingestion_pipeline(
        source_path=source_path,
        chroma_path=rag_config["CHROMA_PATH"],
        embeddings=embeddings,
        collection_name=_COLLECTION_NAME,
        profile="family",
    )
    if summary["failures"]:
        print("[Scenario 0] Avisos del loader durante la ingesta:")
        for failure in summary["failures"]:
            print(f"  - {failure}")

    count = _collection_count(embeddings, rag_config["CHROMA_PATH"])
    print(f"[Scenario 0] Ingesta completada. Colección '{_COLLECTION_NAME}' tiene {count} chunks.")
    return count


def _run_question(pipeline: RAGPipeline, question: str) -> dict:
    """Ejecuta una pregunta contra el pipeline real, capturando instrumentación.

    Reutiliza los componentes ya construidos por `pipeline` (embeddings,
    vectorstore) para no cargar bge-m3 dos veces. `pipeline.query()` no
    expone chunks/idioma/alarma por contrato (rag/pipeline.py, E-04 T-06),
    así que aquí se recalculan con las mismas funciones públicas
    (`detect_language`, `check_alarm_signals`) para poder documentarlas.
    """
    language = detect_language(question)
    has_alarm = check_alarm_signals(question)
    raw_results = pipeline._vectorstore.similarity_search_with_score(
        question, k=pipeline._top_k
    )
    chunks = [
        {
            "source": doc.metadata.get("source", "?"),
            "filename": doc.metadata.get("filename", "?"),
            "similarity": round(distance_to_similarity(distance), 4),
            "preview": doc.page_content[:200].replace("\n", " "),
        }
        for doc, distance in raw_results
    ]
    response = pipeline.query(question)

    return {
        "language": language,
        "has_alarm": has_alarm,
        "chunks": chunks,
        "response": response,
    }


def _format_error_md(question_label: str, question_text: str, exc: Exception) -> str:
    """Entrada de resultado cuando la pregunta falla (p. ej. 429 de cuota de Gemini).

    No aborta el resto del smoke test: cada pregunta es independiente, y un
    fallo transitorio/de cuota en una no debe hacer perder el resultado ya
    obtenido de las demás (ver incidencia real de 2026-07-07, cuota diaria
    de la free tier de gemini-2.5-flash agotada a mitad de ejecución).
    """
    lines = [
        f"## {question_label}",
        "",
        f"**Pregunta:** {question_text}",
        "",
        f"**Error:** no se pudo completar esta pregunta — {type(exc).__name__}: {exc}",
        "",
        "**Revisión manual (Marcos):** _pendiente — reintentar esta pregunta cuando se resuelva el error_",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def _format_result_md(question_label: str, question_text: str, result: dict) -> str:
    lines = [
        f"## {question_label}",
        "",
        f"**Pregunta:** {question_text}",
        "",
        f"**Idioma detectado:** {result['language']}",
        f"**Señal de alarma detectada:** {'sí' if result['has_alarm'] else 'no'}",
        "",
        "**Chunks recuperados:**",
        "",
    ]
    if result["chunks"]:
        for i, chunk in enumerate(result["chunks"], start=1):
            lines.append(
                f"{i}. `{chunk['source']}/{chunk['filename']}` "
                f"(similitud: {chunk['similarity']}) — {chunk['preview']}..."
            )
    else:
        lines.append("_Sin chunks recuperados (retrieval vacío)._")
    lines.extend(
        [
            "",
            "**Respuesta generada:**",
            "",
            f"> {result['response']}",
            "",
            "**Revisión manual (Marcos):** _pendiente_",
            "",
            "---",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-reingest",
        action="store_true",
        help="Reindexa la KB real aunque la colección 'family' ya tenga contenido.",
    )
    args = parser.parse_args()

    rag_config = load_rag_config()
    embeddings = get_embeddings()

    _ensure_kb_indexed(embeddings, rag_config, args.force_reingest)

    pipeline = RAGPipeline(rag_config)

    report_sections = [
        "# E-06 T-07 — Resultados del smoke test manual del pipeline RAG",
        "",
        f"Generado: {datetime.date.today().isoformat()}",
        "",
        "Resultado de ejecutar `RAGPipeline` real (sin mocks) contra la KB real "
        "indexada en la colección `family`. Ver `tests/features/e06_t07_rag_smoke_test.feature`.",
        "",
        "Cada entrada queda pendiente de revisión manual de Marcos antes de dar "
        "por bueno el pipeline y arrancar E-05.",
        "",
        "---",
        "",
    ]

    def _write_report() -> None:
        _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _RESULTS_PATH.write_text("\n".join(report_sections), encoding="utf-8")

    # Escribe el fichero desde el principio y tras cada pregunta (no solo al
    # final): si una pregunta falla (p. ej. 429 de cuota), las anteriores ya
    # completadas quedan guardadas y no dependen de que el script termine entero.
    _write_report()

    for question in QUESTIONS:
        print(f"Ejecutando: {question['label']}...")
        try:
            result = _run_question(pipeline, question["text"])
            section = _format_result_md(question["label"], question["text"], result)
        except Exception as exc:
            print(f"  Error: {exc}")
            section = _format_error_md(question["label"], question["text"], exc)
        report_sections.append(section)
        _write_report()

    print(f"\nResultados escritos en {_RESULTS_PATH}")


if __name__ == "__main__":
    main()
