"""Investigación puntual: por qué "What is a primary immunodeficiency?" produce un
rechazo autocontradictorio en inglés desde E-13 T-01 (funcionaba bien en E-11).

Resultado (D-082): confirmado que la causa es `thinking_budget=0` (D-025) en
`rag/generator.py` — 5/5 roto con el thinking desactivado, 3/3 correcto con el
thinking por defecto. Ya corregido en producción; este script se conserva como
registro de la investigación, mismo patrón que los scripts de investigación de
E-11 (`run_e11_t05_eval15_investigation.py` y similares).

Descartado sin necesidad de red, vía lectura directa de data/chroma/chroma.sqlite3:
el contenido de los 5 chunks recuperados no contiene nada sobre restringir el
idioma de respuesta, y apply_safety_filter() no reescribe la respuesta para esta
pregunta (sin alarma).

Uso:
    PYTHONPATH=. python scripts/run_e13_t03_cross_lingual_investigation.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import load_rag_config
from rag.pipeline import RAGPipeline

QUESTION = "What is a primary immunodeficiency?"


def main():
    rag_config = load_rag_config()
    pipeline = RAGPipeline(rag_config)

    print("=== Test 1: reproducibilidad (5 llamadas idénticas) ===")
    for i in range(5):
        response = pipeline.query(QUESTION)
        broken = "I can only respond in the language" in response
        print(f"[{i+1}] {'ROTO' if broken else 'OK'} — {response[:120]!r}")

    print()
    print("=== Test 2: con thinking_budget por defecto (sin D-025) ===")
    # Instancia alternativa del generador con thinking_budget=None (valor por
    # defecto de ChatGoogleGenerativeAI, sin el override de D-025) — comparar
    # si el problema desaparece al dejar que el modelo "piense". Nota: tras
    # D-082, rag/generator.py ya no pasa thinking_budget=0, así que esta
    # instancia manual es redundante con pipeline.query() en el estado actual
    # del código — se conserva para que el script siga siendo reproducible
    # como registro histórico de la investigación.
    from langchain_google_genai import ChatGoogleGenerativeAI
    from rag.generator import _PROMPT_TEMPLATE, RAGGenerator
    from rag.language import build_language_instruction, detect_language

    llm_thinking = ChatGoogleGenerativeAI(
        model=rag_config.get("LLM_MODEL", "gemini-2.5-flash"),
        temperature=rag_config.get("LLM_TEMPERATURE", 0.1),
        top_p=rag_config.get("LLM_TOP_P", 0.1),
        max_output_tokens=2048,  # margen extra por si el thinking consume tokens (D-025)
        google_api_key=rag_config["GOOGLE_API_KEY"],
    )
    raw = pipeline.retrieve(QUESTION)
    context = "\n\n".join(doc.page_content for doc, _ in raw)
    language = detect_language(QUESTION)
    generator = RAGGenerator(rag_config)
    prompt = _PROMPT_TEMPLATE.format(
        system_prompt=generator._system_prompt,
        context=context,
        question=QUESTION,
        language_instruction=build_language_instruction(language),
    )
    for i in range(3):
        resp = llm_thinking.invoke(prompt)
        broken = "I can only respond in the language" in resp.content
        print(f"[{i+1}] {'ROTO' if broken else 'OK'} — {resp.content[:120]!r}")

    print()
    print("=== Test 3: variante de pregunta en inglés (¿es específico de esta frase?) ===")
    for variant in [
        "What are primary immunodeficiencies?",
        "Can you explain what a primary immunodeficiency is?",
        "What is XIAP deficiency?",
    ]:
        response = pipeline.query(variant)
        broken = "I can only respond in the language" in response
        print(f"{'ROTO' if broken else 'OK'} [{variant!r}] — {response[:120]!r}")


if __name__ == "__main__":
    main()
