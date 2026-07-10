from typing import AsyncIterator

from rag.embeddings import get_embeddings
from rag.generator import RAGGenerator
from rag.language import detect_language
from rag.retriever import get_retriever
from rag.safety import apply_safety_filter, check_alarm_signals

_DEFAULT_COLLECTION = "family"

_SOURCES_HEADINGS = {
    "es": "Fuentes consultadas:",
    "en": "Sources consulted:",
    "ca": "Fonts consultades:",
}


def _build_sources_section(raw_results, language: str) -> str:
    """Construye el listado de fuentes a partir de los metadatos de los chunks recuperados.

    D-026: el LLM ya no cita el documento dentro de la respuesta (evitaba una
    respuesta verbosa, citando en cada frase); el listado se genera de forma
    determinista a partir de `source`/`filename`, no del texto generado por
    el LLM. Si los chunks no traen esos metadatos (p. ej. fixtures de test
    indexadas con `add_texts`, sin metadata), no se añade ninguna sección.
    """
    seen = {}
    for doc, _ in raw_results:
        source = doc.metadata.get("source")
        filename = doc.metadata.get("filename")
        if not source or not filename:
            continue
        pair = (source, filename)
        if pair not in seen:
            seen[pair] = doc.metadata.get("url")

    if not seen:
        return ""

    heading = _SOURCES_HEADINGS.get(language, _SOURCES_HEADINGS["es"])
    lines = [heading]
    for (source, filename), url in seen.items():
        if url:
            lines.append(f"- [{filename}]({url})")
        else:
            lines.append(f"- {source}/{filename}")
    return "\n".join(lines)


class RAGPipeline:
    """Orquestador del pipeline RAG end-to-end."""

    def __init__(self, config: dict):
        self._top_k = config.get("RAG_TOP_K", 5)
        self._embeddings = get_embeddings()
        self._vectorstore = get_retriever(
            self._embeddings,
            config["CHROMA_PATH"],
            config.get("COLLECTION_NAME", _DEFAULT_COLLECTION),
            top_k=self._top_k,
        )
        self._generator = RAGGenerator(config)

    def query(self, question: str) -> str:
        """Recibe una pregunta y devuelve la respuesta generada."""
        language = detect_language(question)
        raw = self._vectorstore.similarity_search_with_score(question, k=self._top_k)
        context = "\n\n".join(doc.page_content for doc, _ in raw)
        has_alarm = check_alarm_signals(question)
        response = self._generator.generate(
            question=question, context=context, language=language
        )
        response = apply_safety_filter(response, has_alarm)

        sources_section = _build_sources_section(raw, language)
        if sources_section:
            response = f"{response}\n\n{sources_section}"
        return response

    def retrieve(self, question: str):
        """Devuelve los documentos recuperados para la pregunta dada.

        D-035: método público que encapsula similarity_search_with_score.
        Permite al llamador (e.g. main_family.on_message) obtener los
        documentos antes de iniciar el streaming y reutilizarlos en
        aquery_stream(raw_results=...) sin una segunda consulta al vectorstore.

        Returns:
            list[tuple[Document, float]]: lista de (documento, score) en el
            mismo formato que devuelve Chroma.similarity_search_with_score.
        """
        return self._vectorstore.similarity_search_with_score(
            question, k=self._top_k
        )

    async def aquery_stream(self, question: str, raw_results=None) -> AsyncIterator[str]:
        """Recibe una pregunta y emite la respuesta generada en streaming.

        D-035: acepta `raw_results` opcional (list[tuple[Document, float]]).
        Si se proporciona, reutiliza esos resultados de retrieval en lugar de
        volver a consultar el vectorstore — permite que el llamador haga una
        sola llamada a retrieve() y la comparta entre el paso de visualización
        (cl.Step) y la generación de la respuesta.

        Si `raw_results` es None (default), se comporta exactamente como antes
        (retrocompatible con todos los tests de T-01 y T-02).

        El filtro de seguridad y el listado de fuentes se aplican sobre el
        texto completo ya ensamblado (D-030): se yield-ean como fragmentos
        finales tras agotar el streaming del cuerpo, nunca intercalados.
        """
        language = detect_language(question)
        if raw_results is None:
            raw_results = self._vectorstore.similarity_search_with_score(
                question, k=self._top_k
            )
        raw = raw_results
        context = "\n\n".join(doc.page_content for doc, _ in raw)
        has_alarm = check_alarm_signals(question)

        chunks = []
        async for token in self._generator.agenerate_stream(
            question=question, context=context, language=language
        ):
            chunks.append(token)
            yield token

        full_text = "".join(chunks)
        filtered = apply_safety_filter(full_text, has_alarm)
        safety_suffix = filtered[len(full_text):]
        if safety_suffix:
            yield safety_suffix

        sources_section = _build_sources_section(raw, language)
        if sources_section:
            yield f"\n\n{sources_section}"
