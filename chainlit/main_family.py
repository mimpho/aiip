import os

import chainlit as cl
from auth.supabase_client import login
from supabase_auth.errors import AuthApiError

APP_ROLE = os.environ.get("APP_ROLE", "family")


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
