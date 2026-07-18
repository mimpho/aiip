"""Step definitions — E-05 T-03 Visualización de pasos intermedios del RAG."""

import asyncio
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from langchain_core.documents import Document
from pytest_bdd import given, scenarios, then, when

# ── Fake chainlit module (debe ir antes de cualquier import de main_family) ───
# El mismo patrón que test_e05_t01.py y test_e05_t02.py:
# registrar el fake, importar main_family, y luego llamar a scenarios().

_sent_messages: list["_FakeMessage"] = []
_opened_steps: list["_FakeStep"] = []


class _FakeMessage:
    def __init__(self, content: str = ""):
        self.content = content
        _sent_messages.append(self)

    async def send(self):
        return self

    async def update(self):
        return self

    async def stream_token(self, token: str):
        self.content += token
        return self


class _FakeStep:
    """Emula cl.Step como context manager async."""

    def __init__(self, name: str = "", **kwargs):
        self.name = name
        self.output = ""
        _opened_steps.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeUser:
    def __init__(self, identifier: str, metadata: dict | None = None):
        self.identifier = identifier
        self.metadata = metadata or {}


_fake_cl = types.ModuleType("chainlit")
_fake_cl.password_auth_callback = lambda f: f
_fake_cl.oauth_callback = lambda f: f
_fake_cl.on_chat_start = lambda f: f
_fake_cl.on_message = lambda f: f
_fake_cl.action_callback = lambda name: (lambda f: f)
_fake_cl.User = _FakeUser
_fake_cl.user_session = MagicMock()
_fake_cl.Message = _FakeMessage
_fake_cl.Step = _FakeStep
_fake_cl.Action = MagicMock()

sys.modules["chainlit"] = _fake_cl

# main_family.py hace `from chainlit.server import app` (E-05 T-06, D-040)
# para registrar rutas propias sobre la app de Chainlit — sin este stub,
# el import falla porque el "chainlit" fake de arriba no es un paquete de
# verdad y no tiene submódulo `server`.
_fake_server = types.ModuleType("chainlit.server")
_fake_server.app = FastAPI()
sys.modules["chainlit.server"] = _fake_server

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chainlit"))
sys.modules.pop("main_family", None)
import main_family  # noqa: E402

scenarios("../features/e05_t03_rag_steps_visualization.feature")


# ── Helpers: RAGPipeline con vectorstore y LLM mockeados ─────────────────────


def _base_config(**overrides) -> dict:
    cfg = {
        "GOOGLE_API_KEY": "test-key",
        "CHROMA_PATH": "",
        "COLLECTION_NAME": "family_test",
        "RAG_TOP_K": 3,
        "LLM_MODEL": "gemini-test-model",
        "LLM_TEMPERATURE": 0.1,
        "LLM_TOP_P": 0.1,
        "LLM_MAX_TOKENS": 300,
    }
    cfg.update(overrides)
    return cfg


def _fake_astream(chunks):
    async def _gen(prompt):
        for chunk in chunks:
            yield SimpleNamespace(content=chunk)

    return _gen


def _build_pipeline(raw_results, chunks=None):
    """RAGPipeline con retrieval y LLM controlados.

    - mock_retriever registra cuántas veces se llama a invoke() (E-09 T-05,
      hallazgo D: el retrieval pasa por el retriever híbrido EnsembleRetriever,
      que solo expone Document sin score vía invoke())
    - LLM emite `chunks` en streaming (vacío por defecto)
    """
    chunks = chunks or ["respuesta fake"]
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [doc for doc, _ in raw_results]
    with (
        patch("rag.pipeline.get_embeddings", return_value=MagicMock()),
        patch("rag.pipeline.get_retriever", return_value=MagicMock()),
        patch("rag.pipeline.get_hybrid_retriever", return_value=mock_retriever),
        patch("rag.generator.ChatGoogleGenerativeAI") as MockLLM,
    ):
        MockLLM.return_value.astream = _fake_astream(chunks)
        from rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(_base_config())
        # Guardamos el retriever fake para que los tests puedan inspeccionar llamadas.
        pipeline._mock_retriever = mock_retriever
        return pipeline


class _FakeChatMessage:
    """Emula cl.Message tal y como llega a on_message (mensaje entrante)."""

    def __init__(self, content: str):
        self.content = content


def _run_on_message(content: str):
    _sent_messages.clear()
    _opened_steps.clear()
    asyncio.run(main_family.on_message(_FakeChatMessage(content)))


# ── Scenario 1: El pipeline expone los documentos recuperados ────────────────


@given(
    'una pregunta con resultados de retrieval en la colección "family"',
    target_fixture="ctx",
)
def pregunta_con_resultados_retrieval():
    doc1 = Document(
        page_content="La inmunodeficiencia primaria es un grupo de enfermedades.",
        metadata={"source": "ipopi", "filename": "guia.pdf"},
    )
    doc2 = Document(
        page_content="Los tratamientos incluyen inmunoglobulinas.",
        metadata={"source": "esid", "filename": "tratamiento.pdf"},
    )
    raw = [(doc1, 0.92), (doc2, 0.85)]
    pipeline = _build_pipeline(raw)
    return {"question": "¿qué es una IDP?", "raw": raw, "pipeline": pipeline}


@when("se ejecuta el paso de recuperación del pipeline")
def se_ejecuta_paso_recuperacion(ctx):
    ctx["result"] = ctx["pipeline"].retrieve(ctx["question"])


@then("se devuelve la lista de documentos recuperados con su fuente y score")
def se_devuelve_lista_con_fuente_y_score(ctx):
    result = ctx["result"]
    assert isinstance(result, list), f"Se esperaba list, se obtuvo {type(result)}"
    assert len(result) == 2, f"Se esperaban 2 documentos, se obtuvieron {len(result)}"
    for doc, score in result:
        assert isinstance(doc, Document)
        assert isinstance(score, float)
        assert "source" in doc.metadata
        assert "filename" in doc.metadata


@then(
    "esa lista está disponible antes de que la generación del LLM haya terminado"
)
def lista_disponible_antes_de_generacion(ctx):
    # retrieve() es síncrono — devuelve inmediatamente sin invocar al LLM.
    # La aseveración es estructural: el resultado ya estaba en ctx al salir
    # de se_ejecuta_paso_recuperacion, antes de cualquier llamada async.
    assert ctx["result"] is not None
    assert len(ctx["result"]) == 2


# ── Scenario 2: Sin resultados no se expone un paso vacío ───────────────────


@given(
    "una pregunta sin resultados de retrieval en la colección, coherente con D-020",
    target_fixture="ctx",
)
def pregunta_sin_resultados_retrieval():
    pipeline = _build_pipeline(raw_results=[])
    return {"question": "¿qué es una IDP?", "pipeline": pipeline}


# when: "se ejecuta el paso de recuperación del pipeline" — reutilizado del Scenario 1


@then("la lista de documentos recuperados expuesta está vacía")
def lista_expuesta_esta_vacia(ctx):
    assert ctx["result"] == [], f"Se esperaba [], se obtuvo {ctx['result']!r}"


@then("no se lanza ninguna excepción por la ausencia de resultados")
def no_se_lanza_excepcion(ctx):
    # Si llegamos aquí sin excepción propagada, el escenario pasa.
    pass


# ── Scenario 3: Los metadatos coinciden con los usados en _build_sources_section


@given("una pregunta con resultados de retrieval", target_fixture="ctx")
def pregunta_con_resultados():
    doc = Document(
        page_content="Contenido relevante sobre IDP.",
        metadata={"source": "ipopi", "filename": "guia.pdf"},
    )
    raw = [(doc, 0.90)]
    pipeline = _build_pipeline(raw)
    return {"question": "¿qué es una IDP?", "raw": raw, "pipeline": pipeline}


@when(
    "se comparan los documentos expuestos como paso intermedio con los usados en _build_sources_section"
)
def se_comparan_documentos_con_sources_section(ctx):
    pipeline = ctx["pipeline"]
    mock_retriever = pipeline._mock_retriever

    # Llamada 1: retrieve() — la única que debería ocurrir.
    raw_from_retrieve = pipeline.retrieve(ctx["question"])
    ctx["raw_from_retrieve"] = raw_from_retrieve

    # Llamada a aquery_stream con raw_results inyectado — NO debe llamar de
    # nuevo al retriever híbrido.
    async def _run_stream():
        fragments = []
        async for token in pipeline.aquery_stream(
            ctx["question"], raw_results=raw_from_retrieve
        ):
            fragments.append(token)
        return fragments

    ctx["fragments"] = asyncio.run(_run_stream())
    ctx["mock_retriever"] = mock_retriever


@then(
    "ambos provienen de la misma llamada a similarity_search_with_score, "
    "sin una segunda consulta al vectorstore"
)
def ambos_provienen_de_misma_llamada(ctx):
    # invoke() del retriever híbrido debe haberse llamado exactamente una vez
    # (en retrieve()), nunca dentro de aquery_stream() cuando se pasa raw_results.
    ctx["mock_retriever"].invoke.assert_called_once()

    # Los documentos expuestos por retrieve() son los mismos objetos Document
    # que devolvió el retriever (mismo objeto Python — sin copia), en el mismo
    # orden — EnsembleRetriever no expone score, así que la comparación es
    # sobre los documentos, no sobre la tupla (doc, score) completa.
    expected_docs = ctx["mock_retriever"].invoke.return_value
    actual_docs = [doc for doc, _ in ctx["raw_from_retrieve"]]
    assert actual_docs == expected_docs
    assert all(a is e for a, e in zip(actual_docs, expected_docs))


# ── Scenario 4: El chat no muestra un paso redundante con el listado de fuentes ─


@given("una pregunta de un usuario autenticado", target_fixture="ctx")
def pregunta_usuario_autenticado():
    return {"question": "¿qué es una IDP?"}


@when("se procesa el mensaje en main_family.on_message")
def se_procesa_mensaje_on_message(ctx, monkeypatch):
    question = ctx["question"]

    fake_doc = Document(
        page_content="Contenido relevante sobre IDP. " * 10,  # >200 chars
        metadata={"source": "ipopi", "filename": "guia.pdf"},
    )
    raw_results = [(fake_doc, 0.93)]

    mock_pipeline = MagicMock()
    mock_pipeline.retrieve.return_value = raw_results

    # aquery_stream acepta keyword raw_results (D-035)
    async def _gen(question, raw_results=None):
        yield "respuesta "
        yield "streaming"

    mock_pipeline.aquery_stream = MagicMock(side_effect=_gen)

    monkeypatch.setattr(main_family, "_get_pipeline", lambda: mock_pipeline)

    ctx["pipeline"] = mock_pipeline
    ctx["raw_results"] = raw_results
    _run_on_message(question)


@then("no se abre ningún paso (cl.Step) de documentos consultados")
def no_se_abre_step_con_documentos(ctx):
    # 1. retrieve() fue llamado con la pregunta del usuario.
    ctx["pipeline"].retrieve.assert_called_once_with(ctx["question"])

    # 2. No se abrió ningún cl.Step (D-041: redundante con el listado de D-026).
    assert not _opened_steps, f"Se abrió un cl.Step inesperado: {_opened_steps}"

    # 3. El mensaje de respuesta recibió tokens del streaming.
    assert _sent_messages, "No se envió ningún mensaje al chat"
    assert _sent_messages[-1].content == "respuesta streaming"


@then(
    "el pipeline reutiliza los mismos resultados de retrieval para el streaming "
    "de la respuesta, sin una segunda consulta al vectorstore"
)
def paso_usa_mismos_resultados_sin_segunda_consulta(ctx):
    # aquery_stream debe haber recibido raw_results= con el mismo objeto
    # que devolvió retrieve().
    ctx["pipeline"].aquery_stream.assert_called_once_with(
        ctx["question"], raw_results=ctx["raw_results"]
    )
