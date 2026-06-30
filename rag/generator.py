class RAGGenerator:
    """Genera respuestas via Gemini Flash usando LangChain."""

    def __init__(self, config: dict):
        raise NotImplementedError

    def generate(self, question: str, context: str, language: str) -> str:
        raise NotImplementedError
