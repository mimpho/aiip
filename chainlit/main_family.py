import os

import chainlit as cl
from auth.supabase_client import login
from rag.config import load_rag_config
from rag.pipeline import RAGPipeline
from supabase_auth.errors import AuthApiError

APP_ROLE = os.environ.get("APP_ROLE", "family")

_pipeline: RAGPipeline | None = None

_ERROR_MESSAGE = (
    "Lo siento, ha ocurrido un error al generar la respuesta. "
    "Por favor, inténtalo de nuevo en unos instantes."
)

_RETRIEVAL_STEP_NAME = "Documentos consultados"
_EXCERPT_LENGTH = 200


def _get_pipeline() -> RAGPipeline:
    """Instancia el RAGPipeline en el primer uso y lo reutiliza (D-033)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline(load_rag_config())
    return _pipeline


def _format_retrieval_step(raw_results) -> str:
    """Formatea los documentos recuperados para mostrar en cl.Step (D-035).

    Por cada documento muestra:
    - source/filename (metadatos de trazabilidad, D-022/D-029)
    - Score de similitud (redondeado a 2 decimales)
    - Extracto del chunk (primeros ~200 caracteres de page_content)

    Aprobado por Marcos: extracto de ~200 chars, no el chunk completo,
    para no saturar la UI.
    """
    if not raw_results:
        return "_Sin documentos recuperados._"

    lines = []
    for doc, score in raw_results:
        source = doc.metadata.get("source", "")
        filename = doc.metadata.get("filename", "")
        label = f"{source}/{filename}" if source and filename else filename or source or "—"
        # Reemplazar saltos de línea y espacios múltiples por un solo espacio
        # para evitar que Chainlit lo interprete como bloques de código (Raw code)
        excerpt = " ".join(doc.page_content[:_EXCERPT_LENGTH].split())
        if len(doc.page_content) > _EXCERPT_LENGTH:
            excerpt += "…"
        lines.append(f"**{label}** (score: {score:.2f})\n> {excerpt}")

    return "\n\n".join(lines)


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    try:
        result = login(username, password)
        return cl.User(
            identifier=username,
            metadata={"role": result["role"], "provider": "credentials"},
        )
    except AuthApiError:
        return None


@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    role = user.metadata.get("role") if user else "unknown"
    await cl.Message(content=f"Sesión iniciada. Perfil: {role}").send()


@cl.on_message
async def on_message(message: cl.Message):
    question = message.content.strip()
    if not question:
        return

    thinking_message = cl.Message(content="")
    await thinking_message.send()

    try:
        pipeline = _get_pipeline()

        # D-035: retrieve() primero → cl.Step con los documentos →
        # aquery_stream() con los mismos resultados (sin segunda consulta).
        raw_results = pipeline.retrieve(question)
        async with cl.Step(name=_RETRIEVAL_STEP_NAME) as step:
            step.output = _format_retrieval_step(raw_results)

        async for token in pipeline.aquery_stream(question, raw_results=raw_results):
            await thinking_message.stream_token(token)
    except Exception:
        thinking_message.content = _ERROR_MESSAGE
        await thinking_message.update()
        return

    await thinking_message.update()
