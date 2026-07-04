from rag.embeddings import get_embeddings
from rag.generator import RAGGenerator
from rag.language import detect_language
from rag.retriever import get_retriever
from rag.safety import apply_safety_filter, check_alarm_signals

_DEFAULT_COLLECTION = "familias"


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
        return apply_safety_filter(response, has_alarm)
