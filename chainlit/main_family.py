import os
from datetime import datetime

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

_WELCOME_MESSAGE = (
    "¡Hola! Soy AIIP, tu asistente sobre Inmunodeficiencias Primarias. "
    "Estoy aquí para acompañarte, ya sea que convivas tú mismo con una IDP o "
    "la de un familiar, y ayudarte a resolver dudas y a encontrar información "
    "de confianza.\n\n"
    "Recuerda: **AIIP acompaña e informa, nunca diagnostica**. Ante cualquier "
    "duda sobre síntomas o decisiones médicas, consulta siempre con tu "
    "equipo sanitario.\n\n"
    "¿En qué puedo ayudarte hoy?"
)

_STARTER_QUESTIONS = (
    "¿Qué es una Inmunodeficiencia Primaria?",
    "¿Cómo puedo cuidar el día a día de mi familiar?",
    "¿Cuándo deberíamos acudir a urgencias?",
    "¿Qué preguntas puedo llevar a la próxima cita médica?",
)


def _greeting() -> str:
    """Saludo por hora del día, con el nombre si hay usuario autenticado.

    "Buenos días" / "Buenas tardes" / "Buenas noches" según la hora del
    servidor — no hay zona horaria por usuario que consultar hoy.
    """
    hour = datetime.now().hour
    if hour < 6:
        greeting = "Buenas noches"
    elif hour < 12:
        greeting = "Buenos días"
    elif hour < 20:
        greeting = "Buenas tardes"
    else:
        greeting = "Buenas noches"

    user = cl.context.session.user
    if user and user.identifier:
        greeting = f"{greeting}, {user.identifier}"
    return greeting


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


async def _answer(question: str) -> None:
    """Ejecuta el pipeline RAG para `question` y envía la respuesta en streaming.

    Compartido por `on_message` y por el callback de las preguntas sugeridas
    (D-036): ambos caminos deben comportarse igual ante la misma pregunta.
    """
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


@cl.on_chat_start
async def on_chat_start():
    """Envía el mensaje de bienvenida y el recordatorio de seguridad (D-036).

    Se repite en cada apertura de chat, no solo la primera vez: no hay
    estado persistido que distinga un primer login real de sesiones
    posteriores (D-036).

    Las preguntas sugeridas se adjuntan como `cl.Action` sobre este mismo
    mensaje, no vía `cl.set_starters`: los starters nativos de Chainlit solo
    se muestran en un hilo sin mensajes, y este mensaje de bienvenida ya
    cuenta como el primer mensaje del hilo (D-036 exige enviarlo desde
    `on_chat_start`, no desde `chainlit.md`).

    El saludo (T-05) se envía como mensaje aparte, antes del de
    bienvenida — style.css lo detecta por ser el primer assistant_message
    del hilo y lo pinta como título, no como burbuja.
    """
    await cl.Message(content=_greeting()).send()

    actions = [
        cl.Action(name="starter_question", payload={"question": q}, label=q)
        for q in _STARTER_QUESTIONS
    ]
    await cl.Message(content=_WELCOME_MESSAGE, actions=actions).send()


@cl.action_callback("starter_question")
async def on_starter_question(action: cl.Action):
    question = action.payload["question"]
    await cl.Message(content=question, type="user_message").send()
    await _answer(question)


@cl.on_message
async def on_message(message: cl.Message):
    question = message.content.strip()
    if not question:
        return
    await _answer(question)
