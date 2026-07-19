"""Investigación offline: contraste laxo vs. estricto sobre conectores no clínicos (E-11 T-03).

Genera dos respuestas para el caso sintético "¿hay algún hospital con inmunología cerca de
Vic?" (verificado contra el KB real post-T-01: los chunks indexados etiquetan Sant Joan de Déu
y Vall d'Hebron como "Barcelona", ninguno menciona "Vic"):

- **Estricta**: `RAGPipeline.query()` real, tal cual producción (ya aplica
  `apply_safety_filter` internamente, `rag/pipeline.py`).
- **Laxa**: un segundo `RAGGenerator` con `_system_prompt` mutado en memoria (nunca se escribe
  a `prompts/system_prompt_family.txt`) para añadir permiso de conectar conceptos no clínicos de
  sentido común, generando sobre el mismo contexto recuperado en el paso estricto (no se vuelve
  a recuperar). El filtro de seguridad se aplica manualmente sobre esta variante, ya que no pasa
  por `RAGPipeline.query()`.

Solo método de investigación (D-059 punto 5): ninguna de las dos respuestas se despliega a
producción. Vuelca la transcripción completa (no solo un veredicto) a
`tests/eval/results/e11_t03_investigacion_offline.json` para que Marcos y el agente redacten la
regla en el Bloque 2 (Cowork). No es un test automatizado (D-050/D-065): sin asserts.

Uso:
    python scripts/run_e11_t03_grounding_investigation.py
"""

import json
import sys
from pathlib import Path

# `python scripts/run_e11_t03_grounding_investigation.py` no añade la raíz del repo a
# sys.path (solo scripts/); se añade explícitamente para poder importar `rag`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import load_rag_config
from rag.generator import RAGGenerator
from rag.language import detect_language
from rag.pipeline import RAGPipeline
from rag.safety import apply_safety_filter, check_alarm_signals

_RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "eval"
    / "results"
    / "e11_t03_investigacion_offline.json"
)

_QUESTION = "¿hay algún hospital con inmunología cerca de Vic?"

# Variante SOLO para esta investigación offline — nunca se escribe a
# prompts/system_prompt_family.txt. Añade permiso explícito para conectores no clínicos de
# sentido común sin quitar nada de las restricciones existentes (D-059 punto 5, D-065).
_LAX_PROMPT_ADDITION = """

[PERMISO EXPERIMENTAL — SOLO INVESTIGACIÓN OFFLINE, NO PRODUCCIÓN]
Para este contraste, además de todo lo anterior, puedes conectar conceptos NO clínicos de
sentido común usando el contexto disponible (por ejemplo: geografía básica, distancias entre
localidades, relaciones temporales obvias), aunque el contexto no lo declare explícitamente
palabra por palabra.
Esto NO amplía el permiso a ningún dato clínico: sigue sin poder inferir ni añadir nombres de
fármacos o dosis, protocolos de tratamiento, ni ninguna conclusión sobre el estado clínico del
usuario, ni usar fuentes externas no indexadas en la base de conocimiento.
"""


def _build_lax_generator(rag_config: dict) -> RAGGenerator:
    lax_generator = RAGGenerator(rag_config)
    lax_generator._system_prompt = lax_generator._system_prompt + _LAX_PROMPT_ADDITION
    return lax_generator


def main() -> None:
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)
    lax_generator = _build_lax_generator(rag_config)

    print(f"Pregunta: {_QUESTION!r}")
    raw_results = pipeline.retrieve(_QUESTION)
    retrieved_chunks = [doc.page_content for doc, _ in raw_results]
    context = "\n\n".join(retrieved_chunks)

    mentions_barcelona = any("barcelona" in chunk.lower() for chunk in retrieved_chunks)
    mentions_vic = any("vic" in chunk.lower().split() for chunk in retrieved_chunks)
    print(f"Chunk(s) recuperados mencionan 'Barcelona': {mentions_barcelona}")
    print(f"Chunk(s) recuperados mencionan 'Vic' (palabra exacta): {mentions_vic}")
    if not mentions_barcelona or mentions_vic:
        print(
            "AVISO: el caso sintético no se reprodujo como se esperaba (ver "
            "tasks/E11-T03-plan.md, paso 2) — documentar el desvío, no forzar el caso."
        )

    language = detect_language(_QUESTION)
    has_alarm = check_alarm_signals(_QUESTION)

    print("Generando respuesta estricta (RAGPipeline.query, producción)...")
    strict_response = pipeline.query(_QUESTION)

    print("Generando respuesta laxa (RAGGenerator alternativo, solo investigación)...")
    lax_response_raw = lax_generator.generate(
        question=_QUESTION, context=context, language=language
    )
    lax_response = apply_safety_filter(lax_response_raw, has_alarm)

    output = {
        "question": _QUESTION,
        "has_alarm": has_alarm,
        "retrieved_chunks": retrieved_chunks,
        "retrieval_check": {
            "mentions_barcelona": mentions_barcelona,
            "mentions_vic_exact_word": mentions_vic,
        },
        "strict_response": {
            "text": strict_response,
            "mechanism": "RAGPipeline.query() — prompt de producción, apply_safety_filter interno",
        },
        "lax_response": {
            "text_before_safety_filter": lax_response_raw,
            "text_after_safety_filter": lax_response,
            "mechanism": (
                "RAGGenerator alternativo con _system_prompt + permiso experimental "
                "(en memoria, nunca escrito a prompts/system_prompt_family.txt); "
                "apply_safety_filter aplicado manualmente"
            ),
        },
    }

    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados escritos en {_RESULTS_PATH}")
    print(
        "\nBloque 1 completado. Parada explícita: el Bloque 2 (redacción de la regla + "
        "aprobación de Marcos) se retoma en Cowork, no continúa en Antigravity (D-059 punto 5)."
    )


if __name__ == "__main__":
    main()
