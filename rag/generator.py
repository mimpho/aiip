from pathlib import Path
from typing import AsyncIterator

from langchain_google_genai import ChatGoogleGenerativeAI

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt_family.txt"

_PROMPT_TEMPLATE = """{system_prompt}

{profile_context}[CONTEXTO]
{context}

[PREGUNTA]
{question}

[INSTRUCCIÓN DE IDIOMA]
{language_instruction}"""


def _format_profile_context(profile: dict | None) -> str:
    """Formatea el bloque [PERFIL DEL PACIENTE] a partir de `profile` (E-14 T-06, D-093).

    Devuelve "" (bloque omitido por completo, ni cabecera) si no hay `profile`
    o `patient_name` está vacío — mismo criterio de "hay onboarding" que usa
    `_ensure_patient_profile()` en chainlit/main_family.py: `patient_name` es
    el único campo que se pide siempre primero, los demás son opcionales.
    Con `patient_name` presente, cada campo restante se añade solo si tiene
    valor — nunca se inventa ni se menciona como "no disponible" (perfil
    parcial).
    """
    if not profile or not profile.get("patient_name"):
        return ""

    lines = [f"Nombre: {profile['patient_name']}"]
    diagnosis = profile.get("patient_diagnosis")
    if diagnosis:
        lines.append(f"Diagnóstico: {diagnosis}")
    age = profile.get("patient_age")
    if age:
        lines.append(f"Edad: {age} años")
    context = profile.get("patient_context")
    if context:
        lines.append(f"Contexto: {context}")

    return "[PERFIL DEL PACIENTE]\n" + "\n".join(lines) + "\n\n"


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
            max_output_tokens=config.get("LLM_MAX_TOKENS", 2048),
            google_api_key=config["GOOGLE_API_KEY"],
            # D-082 revierte thinking_budget=0 (D-025): desactivar el thinking
            # de gemini-2.5-flash producía, de forma reproducible, un rechazo
            # autocontradictorio ("solo respondo en el idioma en que escribes...
            # pregúntame en español") ante preguntas reales en inglés — hallazgo
            # de E-13 T-03 verificando el smoke test de E-06 T-07. Con el
            # thinking activado (comportamiento por defecto del modelo, sin
            # pasar thinking_budget) y LLM_MAX_TOKENS=2048 de margen, el
            # problema no se reprodujo en ninguna repetición. El problema
            # original de D-025 (respuesta visible truncada por el thinking
            # consumiendo el presupuesto con LLM_MAX_TOKENS=300) queda cubierto
            # por el margen de 2048, no por desactivar el thinking.
        )

    def _load_system_prompt(self) -> str:
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    def generate(
        self, question: str, context: str, language: str, profile: dict | None = None
    ) -> str:
        from rag.language import build_language_instruction

        prompt = _PROMPT_TEMPLATE.format(
            system_prompt=self._system_prompt,
            profile_context=_format_profile_context(profile),
            context=context,
            question=question,
            language_instruction=build_language_instruction(language),
        )
        response = self._llm.invoke(prompt)
        return response.content

    async def agenerate_stream(
        self, question: str, context: str, language: str, profile: dict | None = None
    ) -> AsyncIterator[str]:
        from rag.language import build_language_instruction

        prompt = _PROMPT_TEMPLATE.format(
            system_prompt=self._system_prompt,
            profile_context=_format_profile_context(profile),
            context=context,
            question=question,
            language_instruction=build_language_instruction(language),
        )
        async for chunk in self._llm.astream(prompt):
            yield chunk.content
