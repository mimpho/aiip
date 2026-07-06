from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt_family.txt"

_PROMPT_TEMPLATE = """{system_prompt}

[CONTEXTO]
{context}

[PREGUNTA]
{question}

[INSTRUCCIÓN DE IDIOMA]
{language_instruction}"""


class RAGGenerator:
    """Genera respuestas via Gemini Flash usando LangChain."""

    def __init__(self, config: dict):
        if not config.get("GOOGLE_API_KEY"):
            raise EnvironmentError("Variable de entorno requerida no definida: GOOGLE_API_KEY")
        self._system_prompt = self._load_system_prompt()
        self._llm = ChatGoogleGenerativeAI(
            model=config.get("LLM_MODEL", "gemini-2.5-flash"),
            temperature=config.get("LLM_TEMPERATURE", 0.1),
            top_p=config.get("LLM_TOP_P", 0.1),
            max_output_tokens=config.get("LLM_MAX_TOKENS", 300),
            google_api_key=config["GOOGLE_API_KEY"],
        )

    def _load_system_prompt(self) -> str:
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    def generate(self, question: str, context: str, language: str) -> str:
        from rag.language import build_language_instruction

        prompt = _PROMPT_TEMPLATE.format(
            system_prompt=self._system_prompt,
            context=context,
            question=question,
            language_instruction=build_language_instruction(language),
        )
        response = self._llm.invoke(prompt)
        return response.content
