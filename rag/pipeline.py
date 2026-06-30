class RAGPipeline:
    """Orquestador del pipeline RAG end-to-end."""

    def __init__(self, config: dict):
        raise NotImplementedError

    def query(self, question: str) -> str:
        """Recibe una pregunta y devuelve la respuesta generada."""
        raise NotImplementedError
