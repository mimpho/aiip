"""Step definitions — E-04 T-01 Setup de dependencias y estructura del módulo RAG."""

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e04_t01_rag_setup.feature")


# ── Scenario 1: Importación correcta de módulos RAG ─────────────────────────

@given("el entorno virtual tiene las dependencias instaladas")
def entorno_con_dependencias():
    pass


@when(
    "importo los módulos langchain, chromadb y sentence_transformers",
    target_fixture="imported_modules",
)
def importo_modulos():
    modules = ["langchain", "chromadb", "sentence_transformers"]
    return [importlib.import_module(m) for m in modules]


@then("ningún módulo lanza ImportError")
def ningun_importerror(imported_modules):
    assert all(m is not None for m in imported_modules)


# ── Scenario 2: Variables de entorno requeridas presentes ───────────────────

@given(
    "el fichero .env define GOOGLE_API_KEY, HF_TOKEN y CHROMA_PATH",
    target_fixture="env_vars_completas",
)
def env_vars_completas(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("HF_TOKEN", "test-hf-token")
    monkeypatch.setenv("CHROMA_PATH", "./data/chroma")
    return True


@when(
    "inicializo la configuración del pipeline RAG",
    target_fixture="rag_config_result",
)
def inicializo_config():
    from rag.config import load_rag_config

    with patch("rag.config.load_dotenv"):
        try:
            config = load_rag_config()
            return {"config": config, "error": None}
        except EnvironmentError as e:
            return {"config": None, "error": e}


@then("no se lanza EnvironmentError")
def no_environment_error(rag_config_result):
    assert rag_config_result["error"] is None, (
        f"Se lanzó EnvironmentError inesperado: {rag_config_result['error']}"
    )
    assert rag_config_result["config"] is not None


# ── Scenario 3: Variable de entorno requerida ausente ───────────────────────

@given("el fichero .env no define GOOGLE_API_KEY", target_fixture="env_sin_google_key")
def env_sin_google_key(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "test-hf-token")
    monkeypatch.setenv("CHROMA_PATH", "./data/chroma")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    return True


@then("se lanza EnvironmentError con mensaje que menciona GOOGLE_API_KEY")
def environment_error_menciona_clave(rag_config_result):
    assert rag_config_result["error"] is not None, "Se esperaba EnvironmentError pero no se lanzó"
    assert "GOOGLE_API_KEY" in str(rag_config_result["error"])


# ── Scenario 4: Estructura de módulo rag/ presente ──────────────────────────

@given("el repositorio está correctamente clonado")
def repositorio_clonado():
    pass


@when("verifico la estructura de directorios", target_fixture="rag_files")
def verifico_estructura():
    root = Path(__file__).resolve().parents[2]
    rag_dir = root / "rag"
    expected = [
        "__init__.py",
        "pipeline.py",
        "embeddings.py",
        "retriever.py",
        "generator.py",
        "safety.py",
    ]
    return {name: (rag_dir / name) for name in expected}


@then(
    "existe el módulo rag/ con los ficheros __init__.py, pipeline.py, embeddings.py,"
    " retriever.py, generator.py y safety.py"
)
def existen_ficheros_rag(rag_files):
    for name, path in rag_files.items():
        assert path.exists(), f"Fichero no encontrado: {path}"
