"""Step definitions — E-06 T-01 Setup de dependencias y estructura del módulo de ingesta."""

import importlib
import sys
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e06_t01_ingestion_setup.feature")


# ── Scenario 1: Importación correcta de módulos de ingesta ──────────────────

@given("el entorno virtual tiene las dependencias instaladas")
def entorno_con_dependencias():
    pass


@when(
    "importo los módulos de carga de documentos y de text splitting",
    target_fixture="imported_modules",
)
def importo_modulos():
    modules = ["ingestion.loader", "ingestion.chunker"]
    return [importlib.import_module(m) for m in modules]


@then("ningún módulo lanza ImportError")
def ningun_importerror(imported_modules):
    assert all(m is not None for m in imported_modules)


# ── Scenario 2: Variable de entorno de ruta de datos crudos con valor por defecto

@given("el fichero .env no define KB_RAW_DATA_PATH")
def env_sin_kb_raw_data_path(monkeypatch):
    monkeypatch.delenv("KB_RAW_DATA_PATH", raising=False)


@when(
    "inicializo la configuración del módulo de ingesta",
    target_fixture="ingestion_config",
)
def inicializo_config():
    from ingestion.config import load_ingestion_config

    return load_ingestion_config()


@then('KB_RAW_DATA_PATH toma el valor por defecto "data/raw"')
def kb_raw_data_path_por_defecto(ingestion_config):
    assert ingestion_config["KB_RAW_DATA_PATH"] == "data/raw"


# ── Scenario 3: Variable de entorno de ruta de datos crudos personalizada ───

@given("el fichero .env define KB_RAW_DATA_PATH con una ruta personalizada")
def env_con_kb_raw_data_path_personalizada(monkeypatch):
    monkeypatch.setenv("KB_RAW_DATA_PATH", "/ruta/personalizada")


@then("la configuración usa esa ruta personalizada")
def config_usa_ruta_personalizada(ingestion_config):
    assert ingestion_config["KB_RAW_DATA_PATH"] == "/ruta/personalizada"


# ── Scenario 4: Estructura de módulo ingestion/ presente ────────────────────

@given("el repositorio está correctamente clonado")
def repositorio_clonado():
    pass


@when("verifico la estructura de directorios", target_fixture="ingestion_files")
def verifico_estructura():
    root = Path(__file__).resolve().parents[2]
    ingestion_dir = root / "ingestion"
    expected = [
        "__init__.py",
        "config.py",
        "loader.py",
        "chunker.py",
        "indexer.py",
    ]
    return {name: (ingestion_dir / name) for name in expected}


@then(
    "existe el módulo ingestion/ con los ficheros __init__.py, config.py, loader.py,"
    " chunker.py e indexer.py"
)
def existen_ficheros_ingestion(ingestion_files):
    for name, path in ingestion_files.items():
        assert path.exists(), f"Fichero no encontrado: {path}"
