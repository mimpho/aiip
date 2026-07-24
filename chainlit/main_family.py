import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import chainlit as cl
from auth.supabase_client import (
    get_or_create_google_user,
    get_profile,
    get_user_metadata,
    login,
    request_password_reset,
    set_new_password,
    signup,
    update_profile,
    update_user_metadata,
    verify_token,
)
from chainlit.server import app
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from rag.config import load_rag_config
from rag.pipeline import RAGPipeline
from supabase_auth.errors import AuthApiError

logger = logging.getLogger(__name__)

APP_ROLE = os.environ.get("APP_ROLE", "family")

_templates = Jinja2Templates(directory=str(Path(__file__).parent / "family" / "templates"))

_ASK_NAME_MESSAGE = "¿Cómo te llamas? Así puedo dirigirme a ti por tu nombre."

_HEALTH_CONSENT_MESSAGE = (
    "Antes de continuar, necesito tu consentimiento para tratar datos de "
    "salud —por ejemplo, diagnóstico, edad o contexto del paciente— si "
    "decides compartirlos conmigo. Es una categoría especial de datos "
    "protegida por el RGPD (Art. 9) y solo se usará para adaptar mis "
    "respuestas a esa persona, nunca para otro fin.\n\n"
    "Puedes usar el chat sin darlo: seguirá funcionando igual que hasta "
    "ahora, solo que no podré personalizar las respuestas con esa "
    "información."
)

_HEALTH_CONSENT_PROMPT = "¿Aceptas el tratamiento de estos datos?"

_HEALTH_CONSENT_TIMEOUT = 300

_PATIENT_PROFILE_TIMEOUT = 120

_PATIENT_WHO_MESSAGE = (
    "¿Los datos de salud que vas a compartir son sobre ti o sobre otra "
    "persona, como un hijo o una hija?"
)

_PATIENT_WHO_PROMPT = "Elige una opción:"

_PATIENT_OTHER_NAME_MESSAGE = "¿Cómo se llama esa persona?"

_PATIENT_DIAGNOSIS_MESSAGE = "¿Qué diagnóstico tiene {patient_name}?"

_PATIENT_AGE_MESSAGE = "¿Qué edad tiene {patient_name}?"

_PATIENT_AGE_INVALID_MESSAGE = "No he entendido esa edad. Debe ser un número entre 0 y 120."

_PATIENT_CONTEXT_MESSAGE = (
    "¿Hay algo más del contexto de {patient_name} que te gustaría que tenga "
    "en cuenta (tratamiento actual, otras condiciones, rutina diaria...)?"
)

_pipeline: RAGPipeline | None = None

_ERROR_MESSAGE = (
    "Lo siento, ha ocurrido un error al generar la respuesta. "
    "Por favor, inténtalo de nuevo en unos instantes."
)

_WELCOME_MESSAGE = (
    "¡Hola! Soy AIIP, tu asistente sobre Inmunodeficiencias Primarias. "
    "Estoy aquí para acompañarte, ya sea que convivas tú mismo con una IDP o "
    "la de un familiar, y ayudarte a resolver dudas y a encontrar información "
    "de confianza.\n\n"
    "Recuerda: **AIIP acompaña e informa, nunca diagnostica**. Ante cualquier "
    "duda sobre síntomas o decisiones médicas, consulta siempre con tu "
    "equipo sanitario."
)

_WELCOME_PROMPT = "¿En qué puedo ayudarte hoy?"

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

    Usa full_name si está disponible (D-040); si no, saludo genérico sin
    nombre — no se usa identifier (email) como sustituto, resulta impersonal
    mostrar un correo en un saludo.
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
    full_name = user.metadata.get("full_name") if user else None
    if full_name:
        greeting = f"{greeting}, {full_name}"
    return greeting


def _onboarding_complete_title(full_name: str | None) -> str:
    """Título de cierre al completar el perfil EN VIVO en esta sesión (D-090, Ronda 2/4).

    Mismo patrón que _greeting(): con coma si hay full_name ("Todo listo,
    Marcos"), a secas si no ("Todo listo") — se prioriza la consistencia
    visual con el saludo sobre la redacción original de la captura de D-090.
    """
    if full_name:
        return f"Todo listo, {full_name}"
    return "Todo listo"


def _get_pipeline() -> RAGPipeline:
    """Instancia el RAGPipeline en el primer uso y lo reutiliza (D-033)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline(load_rag_config())
    return _pipeline


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    """Login y signup mergeados en el único formulario fijo de Chainlit (D-040).

    Intenta login() primero; si falla (credenciales inválidas o email sin
    cuenta previa), intenta signup() con las mismas credenciales. Con
    "Confirm email" activado, un signup recién creado no trae sesión activa
    hasta que el usuario confirma por correo — se devuelve None en ese caso,
    Chainlit ya muestra su mensaje de error genérico en español.
    """
    try:
        result = login(username, password)
        return cl.User(
            identifier=username,
            metadata={
                "role": result["role"],
                "provider": "credentials",
                "user_id": result["session"].user.id,
            },
        )
    except AuthApiError:
        pass

    try:
        result = signup(username, password, APP_ROLE)
    except AuthApiError:
        return None

    if result["session"] is None:
        return None

    return cl.User(
        identifier=username,
        metadata={
            "role": result["role"],
            "provider": "credentials",
            "user_id": result["user_id"],
        },
    )


if os.environ.get("OAUTH_GOOGLE_CLIENT_ID") and os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET"):

    @cl.oauth_callback
    async def oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: dict,
        default_app_user: cl.User,
        id_token: Optional[str] = None,
    ) -> cl.User | None:
        """Sincroniza el login de Google con Supabase Auth (D-032/D-040).

        raw_user_data es la respuesta estándar de userinfo de Google (email,
        name, ...) ya verificada por Chainlit. get_or_create_google_user es
        idempotente: logins repetidos no duplican usuario ni perfil.

        id_token tiene default None a propósito: la ruta genérica de
        Chainlit (server.py, /auth/oauth/{provider_id}/callback) invoca este
        callback con solo 4 argumentos posicionales — id_token solo se pasa
        en la ruta especial de azure-ad-hybrid. Sin default aquí, Chainlit
        traga silenciosamente el TypeError resultante (wrap_user_function) y
        el login termina en un 401 "credentialssignin" genérico, sin rastro
        del error real salvo en el log del servidor.
        """
        if provider_id != "google":
            return None

        email = raw_user_data.get("email")
        if not email:
            return None

        result = get_or_create_google_user(email, raw_user_data.get("name"), APP_ROLE)
        return cl.User(
            identifier=email,
            metadata={
                "role": APP_ROLE,
                "provider": "google",
                "user_id": result["user_id"],
            },
        )


_auth_router = APIRouter()


@_auth_router.get("/auth/forgot-password", response_class=HTMLResponse)
async def forgot_password_form(request: Request):
    return _templates.TemplateResponse(request, "forgot_password.html", {})


@_auth_router.post("/auth/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(request: Request, email: str = Form(...)):
    request_password_reset(email)
    return _templates.TemplateResponse(request, "forgot_password.html", {"sent": True})


@_auth_router.get("/auth/confirm", response_class=HTMLResponse)
async def confirm_token(request: Request, token_hash: str | None = None, type: str | None = None):
    """Verifica un token_hash de signup o recovery (D-040).

    Comparte la verificación entre los dos casos — solo cambia qué se
    muestra después: signup confirma la cuenta (enlace a /login, sin
    autenticar en Chainlit); recovery muestra el formulario de nueva
    contraseña.

    token_hash/type son opcionales en la firma (con default None) a
    propósito: si fueran obligatorios, FastAPI devuelve su JSON 422 nativo
    para una request sin query string, antes de ejecutar una sola línea de
    este cuerpo — el usuario vería un JSON crudo con detalles internos en
    vez de la pantalla de error propia. Se valida su ausencia a mano en su
    lugar, con la misma plantilla de error que un token inválido.
    """
    if not token_hash or not type:
        return _templates.TemplateResponse(request, "confirm.html", {"state": "error"})

    try:
        response = verify_token(token_hash, type)
    except AuthApiError:
        return _templates.TemplateResponse(request, "confirm.html", {"state": "error"})

    if type == "recovery":
        return _templates.TemplateResponse(
            request,
            "confirm.html",
            {
                "state": "recovery",
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            },
        )

    return _templates.TemplateResponse(request, "confirm.html", {"state": "signup"})


@_auth_router.post("/auth/confirm", response_class=HTMLResponse)
async def confirm_recovery_submit(
    request: Request,
    access_token: str = Form(...),
    refresh_token: str = Form(...),
    password: str = Form(...),
):
    try:
        set_new_password(access_token, refresh_token, password)
    except AuthApiError:
        return _templates.TemplateResponse(request, "confirm.html", {"state": "error"})

    return _templates.TemplateResponse(request, "confirm.html", {"state": "updated"})


# Chainlit registra sus propias rutas — incluida una SPA catch-all
# GET /{full_path:path} — dentro de un único APIRouter incluido en `app`
# antes de que este módulo se importe. Como Starlette resuelve rutas en
# orden de la lista y ese catch-all coincide con cualquier path, un
# @app.get/post normal (que se añade al final de app.router.routes)
# nunca llegaría a ejecutarse: el catch-all lo interceptaría antes.
# Verificado en vivo (curl a /auth/forgot-password devolvía el index.html
# de la SPA). Insertar nuestras rutas al principio de la lista les da
# prioridad sobre ese catch-all sin tocar las rutas de Chainlit.
app.router.routes[:0] = _auth_router.routes


async def _answer(question: str) -> None:
    """Ejecuta el pipeline RAG para `question` y envía la respuesta en streaming.

    Compartido por `on_message` y por el callback de las preguntas sugeridas
    (D-036): ambos caminos deben comportarse igual ante la misma pregunta.
    """
    thinking_message = cl.Message(content="")
    await thinking_message.send()

    try:
        pipeline = _get_pipeline()

        # D-035/D-041: retrieve() primero para poder reutilizar los mismos
        # resultados en aquery_stream() sin segunda consulta al vectorstore.
        # No se renderiza como cl.Step: sería redundante con el listado de
        # fuentes al final de la respuesta (D-026). Se loguea en su lugar
        # (nivel INFO, solo server-side) para debugging — útil para el
        # desarrollador, sin valor para el usuario familiar.
        raw_results = pipeline.retrieve(question)
        logger.info(
            "Retrieval para %r: %s",
            question,
            [
                (doc.metadata.get("source", ""), doc.metadata.get("filename", ""), round(score, 4))
                for doc, score in raw_results
            ],
        )
        async for token in pipeline.aquery_stream(question, raw_results=raw_results):
            await thinking_message.stream_token(token)
    except Exception:
        logger.exception("Error al generar la respuesta del pipeline RAG")
        thinking_message.content = _ERROR_MESSAGE
        await thinking_message.update()
        return

    await thinking_message.update()


async def _ensure_health_consent() -> None:
    """Muestra el gate de consentimiento de datos de salud si no está registrado (D-009).

    user_id viaja en cl.User.metadata desde auth_callback/oauth_callback.
    cl.AskActionMessage bloquea el chat hasta que el usuario pulsa un botón
    o expira el timeout (raise_on_timeout=False por defecto, devuelve None).
    Rechazar o dejar que expire no registra nada y no bloquea el resto del
    chat (Falso Negativo Cero, D-002): en chats posteriores se vuelve a
    mostrar el gate, no se asume rechazo permanente.

    Si update_profile falla (p.ej. error de red), se loguea y el flujo sigue
    igualmente — a diferencia de _ensure_full_name, aquí hay una escritura
    nueva a Supabase que antes no existía en on_chat_start.

    No devuelve `bool` (D-090, corrección Ronda 3): el título de cierre
    "Todo listo" depende solo de si _ensure_patient_profile() completó el
    perfil en vivo, no de si este gate se mostró.
    """
    user = cl.context.session.user
    if not user:
        return
    user_id = user.metadata.get("user_id")
    if not user_id:
        return

    profile = get_profile(user_id)
    if profile.get("health_data_consent_at"):
        return

    await cl.Message(content=_HEALTH_CONSENT_MESSAGE).send()

    res = await cl.AskActionMessage(
        content=_HEALTH_CONSENT_PROMPT,
        actions=[
            cl.Action(name="consent_accept", payload={}, label="Acepto"),
            cl.Action(name="consent_decline", payload={}, label="Ahora no"),
        ],
        timeout=_HEALTH_CONSENT_TIMEOUT,
    ).send()

    if res and res.get("name") == "consent_accept":
        try:
            update_profile(
                user_id,
                {"health_data_consent_at": datetime.now(timezone.utc).isoformat()},
            )
        except Exception:
            logger.exception("Error al registrar health_data_consent_at para user_id=%s", user_id)


async def _ensure_full_name() -> None:
    """Pide el nombre por chat si el usuario autenticado no lo tiene guardado (D-040).

    user_id viaja en cl.User.metadata desde auth_callback/oauth_callback.
    El resultado se guarda también en cl.context.session.user.metadata para
    que _greeting() lo use sin una segunda consulta a Supabase. Si el
    usuario no responde a tiempo (timeout de cl.AskUserMessage), se sigue
    sin nombre — no se repregunta hasta el próximo on_chat_start.

    No devuelve `bool` (D-090, corrección Ronda 3) — mismo motivo que
    _ensure_health_consent.
    """
    user = cl.context.session.user
    if not user:
        return
    user_id = user.metadata.get("user_id")
    if not user_id:
        return

    full_name = get_user_metadata(user_id).get("full_name")
    if full_name:
        user.metadata["full_name"] = full_name
        return

    res = await cl.AskUserMessage(content=_ASK_NAME_MESSAGE, timeout=120).send()
    if res and res.get("output", "").strip():
        full_name = res["output"].strip()
        update_user_metadata(user_id, {"full_name": full_name})
        user.metadata["full_name"] = full_name


def _parse_patient_age(raw: str) -> int | None:
    """Convierte `raw` a edad válida (entero entre 0 y 120) o None (D-088, D-090).

    Extrae el primer número de `raw` en vez de exigir que sea puramente
    numérico — cubre respuestas como "12 años" o "tiene 12 años", no solo
    "12". Números en palabras ("doce") quedan fuera de alcance.
    """
    match = re.search(r"\d+", raw)
    if not match:
        return None
    age = int(match.group())
    if 0 <= age <= 120:
        return age
    return None


async def _ask_patient_age(patient_name: str) -> int | None:
    """Pregunta la edad de `patient_name`, con una única repregunta si la respuesta no es válida (D-088).

    Si la segunda respuesta tampoco es válida (o no hay respuesta en
    ninguna de las dos vueltas), devuelve None sin insistir más — se
    repreguntará en el próximo `on_chat_start`, no en este mismo chat.
    """
    prompt = _PATIENT_AGE_MESSAGE.format(patient_name=patient_name)
    for attempt in range(2):
        res = await cl.AskUserMessage(content=prompt, timeout=_PATIENT_PROFILE_TIMEOUT).send()
        if not res:
            return None
        age = _parse_patient_age(res.get("output", ""))
        if age is not None:
            return age
        if attempt == 0:
            await cl.Message(content=_PATIENT_AGE_INVALID_MESSAGE).send()
    return None


async def _replay_field(question: str, answer: str) -> None:
    """Reproduce tal cual una pregunta ya respondida en una sesión anterior (D-090, Ronda 2/4).

    La respuesta se envía con el mismo prefijo "**Selected:**" que Chainlit
    usa al reescribir un AskActionMessage tras pulsar un botón (D-090, Ronda
    1) — design/public/custom.js ya detecta ese marcador, le quita el
    prefijo y lo restyla como burbuja de usuario alineada a la derecha, así
    que no hace falta un segundo marcador de contenido para este caso.
    Riesgo aceptado si `answer` empezara a coincidir con ese prefijo por sí
    mismo: mismo perfil bajo que SOURCES_HEADINGS/D-026, son datos
    controlados por nuestro propio backend, no por el usuario o el LLM.
    """
    await cl.Message(content=question).send()
    await cl.Message(content=f"**Selected:** {answer}").send()


async def _ensure_patient_profile() -> bool:
    """Pide por chat los datos del paciente que falten en el perfil (T-03, D-089).

    Solo se alcanza con consentimiento de datos de salud ya registrado
    (_ensure_health_consent() se ejecuta antes en on_chat_start, D-009) —
    no se duplica esa comprobación aquí.

    Distingue "quién chatea" (user.metadata["full_name"], D-040) de "de
    quién son los datos clínicos" (patient_name): si el usuario indica que
    los datos son sobre sí mismo, patient_name se copia de full_name
    (D-089) en vez de preguntarse aparte; si son sobre otra persona, se
    pregunta su nombre. Las preguntas de diagnóstico/edad/contexto usan
    siempre el nombre real del paciente, nunca la palabra "paciente"
    (decisión de tono de epic-start).

    Diseño final tras cuatro rondas de QA en vivo (D-090): el perfil
    inicial (`profile = get_profile(user_id)`) puede estar completo, vacío
    o incompleto.
    - Completo (los cuatro campos con valor): no se envía ningún mensaje —
      ni resumen, ni replay, ni pregunta — y se devuelve False de
      inmediato. Ver esos datos guardados se delega enteramente a T-05
      (edición de perfil desde `cl.ChatSettings`), no al chat.
    - Vacío o incompleto: cada campo se trata individualmente, en el mismo
      orden de siempre (sobre quién/nombre → diagnóstico → edad →
      contexto). Si ya estaba en el `profile` inicial, se reproduce tal
      cual con _replay_field (pregunta original + respuesta guardada, como
      burbuja de usuario) para no perder el contexto entre sesiones; si
      falta, se pregunta en vivo, igual que siempre. Si no hay respuesta a
      una pregunta en vivo del bloque "sobre quién" (timeout/None), la
      función retorna sin preguntar el resto — se repite en el próximo
      on_chat_start, mismo criterio que _ensure_full_name/
      _ensure_health_consent. Los campos diagnóstico/edad/contexto son
      independientes entre sí: no responder a uno no corta los siguientes.

    Devuelve True solo si se completó el perfil EN VIVO en esta sesión: se
    preguntó y respondió al menos un campo en esta llamada (answered_live)
    Y el perfil queda completo al terminar — on_chat_start usa este valor,
    exclusivamente, para decidir si mostrar el título de cierre "Todo
    listo". Un perfil ya completo de antes, o uno que sigue incompleto tras
    esta llamada, devuelve False.
    """
    user = cl.context.session.user
    if not user:
        return False
    user_id = user.metadata.get("user_id")
    if not user_id:
        return False

    profile = get_profile(user_id)
    if all(
        profile.get(field)
        for field in ("patient_name", "patient_diagnosis", "patient_age", "patient_context")
    ):
        return False

    answered_live = False
    patient_name = profile.get("patient_name")

    if patient_name:
        full_name = user.metadata.get("full_name")
        if full_name and patient_name == full_name:
            await _replay_field(_PATIENT_WHO_MESSAGE, "Sobre mí")
        else:
            await _replay_field(_PATIENT_WHO_MESSAGE, "Sobre otra persona")
            await _replay_field(_PATIENT_OTHER_NAME_MESSAGE, patient_name)
    else:
        await cl.Message(content=_PATIENT_WHO_MESSAGE).send()
        res = await cl.AskActionMessage(
            content=_PATIENT_WHO_PROMPT,
            actions=[
                cl.Action(name="patient_self", payload={}, label="Sobre mí"),
                cl.Action(name="patient_other", payload={}, label="Sobre otra persona"),
            ],
            timeout=_PATIENT_PROFILE_TIMEOUT,
        ).send()
        if not res:
            return False

        if res.get("name") == "patient_self":
            patient_name = user.metadata.get("full_name")
            if not patient_name:
                return False
        elif res.get("name") == "patient_other":
            name_res = await cl.AskUserMessage(
                content=_PATIENT_OTHER_NAME_MESSAGE, timeout=_PATIENT_PROFILE_TIMEOUT
            ).send()
            if not name_res or not name_res.get("output", "").strip():
                return False
            patient_name = name_res["output"].strip()
        else:
            return False

        try:
            update_profile(user_id, {"patient_name": patient_name})
        except Exception:
            logger.exception("Error al registrar patient_name para user_id=%s", user_id)
        answered_live = True

    if profile.get("patient_diagnosis"):
        await _replay_field(
            _PATIENT_DIAGNOSIS_MESSAGE.format(patient_name=patient_name),
            profile["patient_diagnosis"],
        )
    else:
        diagnosis_res = await cl.AskUserMessage(
            content=_PATIENT_DIAGNOSIS_MESSAGE.format(patient_name=patient_name),
            timeout=_PATIENT_PROFILE_TIMEOUT,
        ).send()
        if diagnosis_res and diagnosis_res.get("output", "").strip():
            profile["patient_diagnosis"] = diagnosis_res["output"].strip()
            answered_live = True
            try:
                update_profile(user_id, {"patient_diagnosis": profile["patient_diagnosis"]})
            except Exception:
                logger.exception("Error al registrar patient_diagnosis para user_id=%s", user_id)

    if profile.get("patient_age"):
        await _replay_field(
            _PATIENT_AGE_MESSAGE.format(patient_name=patient_name),
            str(profile["patient_age"]),
        )
    else:
        age = await _ask_patient_age(patient_name)
        if age is not None:
            profile["patient_age"] = age
            answered_live = True
            try:
                update_profile(user_id, {"patient_age": age})
            except Exception:
                logger.exception("Error al registrar patient_age para user_id=%s", user_id)

    if profile.get("patient_context"):
        await _replay_field(
            _PATIENT_CONTEXT_MESSAGE.format(patient_name=patient_name),
            profile["patient_context"],
        )
    else:
        context_res = await cl.AskUserMessage(
            content=_PATIENT_CONTEXT_MESSAGE.format(patient_name=patient_name),
            timeout=_PATIENT_PROFILE_TIMEOUT,
        ).send()
        if context_res and context_res.get("output", "").strip():
            profile["patient_context"] = context_res["output"].strip()
            answered_live = True
            try:
                update_profile(user_id, {"patient_context": profile["patient_context"]})
            except Exception:
                logger.exception("Error al registrar patient_context para user_id=%s", user_id)

    profile_complete = bool(patient_name) and all(
        profile.get(field) for field in ("patient_diagnosis", "patient_age", "patient_context")
    )
    return answered_live and profile_complete


@cl.on_chat_start
async def on_chat_start():
    """Envía el saludo, la bienvenida y resuelve el onboarding pendiente (D-036, D-090 Ronda 2/3).

    Se repite en cada apertura de chat, no solo la primera vez: no hay
    estado persistido que distinga un primer login real de sesiones
    posteriores (D-036).

    El saludo (T-05) y la bienvenida (_WELCOME_MESSAGE, sin la pregunta
    final) van siempre primero, antes de cualquier gate o pregunta de
    onboarding — a diferencia del orden anterior a D-090 Ronda 2, en el que
    el gate de consentimiento podía anteponerse al saludo y dejaba la
    primera impresión del chat sin contexto. style.css detecta el saludo
    por contenido (design/public/custom.js, `aiip-heading-title`), no por
    ser el primer mensaje del hilo, así que reordenarlo aquí no rompe ese
    tratamiento visual.

    _ensure_health_consent()/_ensure_full_name()/_ensure_patient_profile()
    mantienen su orden relativo de siempre (D-009: el gate de consentimiento
    va antes que cualquier dato de salud). Solo la última devuelve `bool`
    (D-090, corrección Ronda 3): el título de cierre "Todo listo"
    (_onboarding_complete_title) depende únicamente de si el perfil del
    paciente se completó EN VIVO en esta sesión — no de si el gate de
    consentimiento o la pregunta del nombre se mostraron, ni de si
    _ensure_patient_profile() solo envió el resumen de un perfil ya
    completo de antes.

    _greeting() ahora se llama antes que _ensure_full_name() (D-090 Ronda
    2), así que ya no puede apoyarse en que esta última haya resuelto
    full_name en cl.context.session.user.metadata (D-040) para un usuario
    recurrente — sin este prefetch, el saludo perdería el nombre en todo
    chat que no sea el primero (regresión real detectada al correr los
    tests de T-05 tras el reordenamiento). Lectura no interactiva
    (get_user_metadata, sin preguntar nada): _ensure_full_name() hace
    exactamente esta misma comprobación como primer paso, así que repetirla
    aquí es barata y su propio chequeo pasa a ser un no-op cuando ya está
    cacheada.
    """
    user = cl.context.session.user
    if user and "full_name" not in user.metadata:
        user_id = user.metadata.get("user_id")
        if user_id:
            full_name = get_user_metadata(user_id).get("full_name")
            if full_name:
                user.metadata["full_name"] = full_name

    await cl.Message(content=_greeting()).send()
    await cl.Message(content=_WELCOME_MESSAGE).send()

    await _ensure_health_consent()
    await _ensure_full_name()
    onboarding_completed_now = await _ensure_patient_profile()

    if onboarding_completed_now:
        user = cl.context.session.user
        full_name = user.metadata.get("full_name") if user else None
        await cl.Message(content=_onboarding_complete_title(full_name)).send()

    actions = [
        cl.Action(name="starter_question", payload={"question": q}, label=q)
        for q in _STARTER_QUESTIONS
    ]
    await cl.Message(content=_WELCOME_PROMPT, actions=actions).send()


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
