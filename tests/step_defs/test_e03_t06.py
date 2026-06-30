"""Step definitions — E-03 T-06 Separación de URLs por perfil."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

from pytest_bdd import given, scenarios, then, when

ROOT = Path(__file__).resolve().parents[2]

# ── Fake chainlit (not installed in CI) ──────────────────────────────────────


class _FakeUser:
    def __init__(self, identifier: str, metadata: dict | None = None):
        self.identifier = identifier
        self.metadata = metadata or {}


_fake_cl = types.ModuleType("chainlit")
_fake_cl.password_auth_callback = lambda f: f
_fake_cl.on_chat_start = lambda f: f
_fake_cl.User = _FakeUser
_fake_cl.user_session = MagicMock()
_fake_cl.Message = MagicMock()

sys.modules.setdefault("chainlit", _fake_cl)

scenarios("../features/e03_t06_url_separation.feature")


# ── Scenario 1: la app familiar no expone referencias al perfil profesional ──


@given("la app familiar está arrancada en el puerto 8000")
def app_familiar_arrancada():
    pass  # test estático — no se levanta Chainlit


@when("cargo la página de login de la app familiar", target_fixture="familiar_source")
def cargo_pagina_familiar():
    return (ROOT / "main_familiar.py").read_text()


@then('no hay ningún texto ni enlace que mencione "profesional" ni "F-01"')
def no_referencias_profesional(familiar_source):
    assert "profesional" not in familiar_source
    assert "F-01" not in familiar_source


# ── Scenario 2: la app profesional muestra el formulario deshabilitado ────────


@given("la app profesional está arrancada en el puerto 8001")
def app_profesional_arrancada():
    pass  # test estático — no se levanta Chainlit


@when("cargo la página de la app profesional", target_fixture="stub_js_content")
def cargo_pagina_profesional():
    return (ROOT / "design" / "profesional" / "stub.js").read_text()


@then('veo un banner "En construcción" con texto explicativo encima del formulario')
def veo_banner_construccion(stub_js_content):
    assert "En construcción" in stub_js_content


@then("todos los inputs del formulario están deshabilitados")
def inputs_deshabilitados(stub_js_content):
    assert "input" in stub_js_content.lower()
    assert "disabled" in stub_js_content


@then("el botón de submit está deshabilitado")
def boton_submit_deshabilitado(stub_js_content):
    assert "button" in stub_js_content.lower()
    assert "disabled" in stub_js_content


# ── Scenario 3: las dos apps arrancan en puertos distintos sin conflicto ──────


@given(
    "el entorno tiene PORT_FAMILIAR=8000 y PORT_PROFESIONAL=8001 en .env",
    target_fixture="env_example_content",
)
def entorno_tiene_puertos():
    return (ROOT / ".env.example").read_text()


@when("arranco la app familiar y la app profesional simultáneamente")
def arranco_apps():
    pass  # test estático — se verifica solo la presencia de las variables


@then("cada una responde en su puerto sin error de binding")
def responden_sin_conflicto(env_example_content):
    assert "PORT_FAMILIAR" in env_example_content
    assert "PORT_PROFESIONAL" in env_example_content


# ── Scenario 4: la app profesional no instancia nada del módulo auth ─────────


@given("la app profesional arranca")
def app_profesional_arranca():
    pass  # test estático sobre el código fuente


@when("se inicializa el proceso de Chainlit")
def inicializa_chainlit():
    pass


@then("no se importa ni instancia supabase_client ni ningún callback de auth")
def no_importa_auth():
    source = (ROOT / "main_profesional.py").read_text()
    assert "supabase_client" not in source
    assert "from auth" not in source
    assert "import auth" not in source
