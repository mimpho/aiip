import chainlit as cl


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    # Stub: acceso siempre bloqueado — perfil profesional fuera del alcance del TFM
    return None


@cl.on_chat_start
async def on_chat_start():
    # No debería ejecutarse nunca (auth siempre falla), pero por seguridad:
    await cl.Message(content="Perfil profesional no disponible.").send()
