import os

from dotenv import load_dotenv


def load_ingestion_config() -> dict:
    """Carga la configuración del módulo de ingesta."""
    load_dotenv()
    config = {}
    config["KB_RAW_DATA_PATH"] = os.getenv("KB_RAW_DATA_PATH", "data/raw")
    config["RAG_CHUNK_SIZE"] = int(os.getenv("RAG_CHUNK_SIZE", "512"))
    config["RAG_CHUNK_OVERLAP"] = int(os.getenv("RAG_CHUNK_OVERLAP", "64"))
    return config
