import os

from dotenv import load_dotenv

REQUIRED_VARS = ["GOOGLE_API_KEY", "HF_TOKEN", "CHROMA_PATH"]


def load_rag_config() -> dict:
    """Carga y valida las variables de entorno del pipeline RAG."""
    load_dotenv()
    config = {}
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value:
            raise EnvironmentError(f"Variable de entorno requerida no definida: {var}")
        config[var] = value
    config["RAG_TOP_K"] = int(os.getenv("RAG_TOP_K", "5"))
    return config
