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


def _get_pipeline() -> RAGPipeline:
    """Instancia el RAGPipeline en el primer uso y lo reutiliza (D-033)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline(load_rag_config())
    return _pipeline


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
        async for token in pipeline.aquery_stream(question):
            await thinking_message.stream_token(token)
    except Exception:
        thinking_message.content = _ERROR_MESSAGE
        await thinking_message.update()
        return

    await thinking_message.update()
