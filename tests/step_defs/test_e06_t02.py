"""Step definitions — E-06 T-02 Loader de documentos fuente."""

import json
import sys
import warnings as warnings_module
from datetime import date
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

scenarios("../features/e06_t02_document_loader.feature")


def _make_minimal_pdf(path: Path, text: str) -> None:
    """Escribe un PDF de una página válido con `text` como contenido extraíble."""
    content = f"BT /F1 24 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        b"/MediaBox [0 0 612 792] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    buffer = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(buffer))
        buffer += f"{i} 0 obj\n".encode()
        buffer += obj
        buffer += b"\nendobj\n"
    xref_offset = len(buffer)
    buffer += f"xref\n0 {len(objects) + 1}\n".encode()
    buffer += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        buffer += f"{off:010d} 00000 n \n".encode()
    buffer += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode()
    path.write_bytes(bytes(buffer))


def _write_manifest(root: Path, documents: dict) -> None:
    (root / "manifest.json").write_text(
        json.dumps({"documents": documents}, ensure_ascii=False), encoding="utf-8"
    )


# ── Background ────────────────────────────────────────────────────────────────

@given(
    "la carpeta de datos crudos configurada en KB_RAW_DATA_PATH existe",
    target_fixture="ctx",
)
def carpeta_datos_crudos_existe(tmp_path):
    root = tmp_path / "raw"
    root.mkdir()
    return {"root": root, "source_path": str(root)}


# ── Given steps ───────────────────────────────────────────────────────────────

@given("un PDF válido en data/raw/<fuente>/")
def pdf_valido(ctx):
    source_dir = ctx["root"] / "ipopi"
    source_dir.mkdir()
    _make_minimal_pdf(source_dir / "doc.pdf", "Contenido de prueba del PDF.")
    ctx["source_name"] = "ipopi"
    ctx["file_name"] = "doc.pdf"
    ctx["expected_text"] = "Contenido de prueba del PDF."


@given("un fichero HTML válido en data/raw/<fuente>/")
def html_valido(ctx):
    source_dir = ctx["root"] / "ipopi"
    source_dir.mkdir()
    (source_dir / "doc.html").write_text(
        "<html><head><title>Doc</title></head>"
        "<body><p>Texto legible de prueba.</p></body></html>",
        encoding="utf-8",
    )
    ctx["source_name"] = "ipopi"
    ctx["file_name"] = "doc.html"
    ctx["expected_text"] = "Texto legible de prueba."


@given(
    "un fichero HTML en data/raw/<fuente>/ con varios <div> sueltos sin envoltorio"
    " <html>/<body>"
)
def html_fragmento_sin_envoltorio(ctx):
    source_dir = ctx["root"] / "aedip"
    source_dir.mkdir()
    (source_dir / "fragmento.html").write_text(
        "<div><p>Primer bloque interesante.</p></div>"
        "<div><p>Segundo bloque, nodo suelto.</p></div>",
        encoding="utf-8",
    )
    ctx["source_name"] = "aedip"
    ctx["file_name"] = "fragmento.html"


@given(
    "data/raw/<fuente>/ contiene un fichero de formato no soportado junto a"
    " ficheros válidos"
)
def formato_no_soportado_junto_validos(ctx):
    source_dir = ctx["root"] / "ipopi"
    source_dir.mkdir()
    (source_dir / "notas.txt").write_text("contenido no soportado", encoding="utf-8")
    (source_dir / "doc.html").write_text(
        "<html><body><p>Contenido válido.</p></body></html>", encoding="utf-8"
    )
    ctx["source_name"] = "ipopi"
    ctx["valid_file_name"] = "doc.html"


@given("KB_RAW_DATA_PATH apunta a una ruta que no existe")
def ruta_no_existe(ctx, tmp_path):
    ctx["source_path"] = str(tmp_path / "no_existe")


@given("la carpeta de datos crudos existe pero no contiene ninguna fuente")
def carpeta_vacia(ctx):
    pass  # el Background ya crea root vacío


@given(
    "un fichero en data/raw/<fuente>/ sin entrada correspondiente en"
    " data/raw/manifest.json"
)
def fichero_nuevo_sin_manifest_entry(ctx):
    source_dir = ctx["root"] / "ipopi"
    source_dir.mkdir()
    (source_dir / "doc.html").write_text(
        "<html><body><p>Contenido nuevo.</p></body></html>", encoding="utf-8"
    )
    ctx["source_name"] = "ipopi"
    ctx["file_name"] = "doc.html"
    ctx["manifest_key"] = "ipopi/doc.html"
    _write_manifest(ctx["root"], {})


@given(
    "un fichero en data/raw/<fuente>/ con entrada en el manifest cuyo checksum no"
    " coincide con el contenido actual"
)
def fichero_checksum_desactualizado(ctx):
    source_dir = ctx["root"] / "ipopi"
    source_dir.mkdir()
    (source_dir / "doc.html").write_text(
        "<html><body><p>Contenido actualizado.</p></body></html>", encoding="utf-8"
    )
    ctx["source_name"] = "ipopi"
    ctx["file_name"] = "doc.html"
    ctx["manifest_key"] = "ipopi/doc.html"
    _write_manifest(
        ctx["root"],
        {
            "ipopi/doc.html": {
                "checksum": "sha256:" + "0" * 64,
                "url": "https://example.org/ipopi",
                "fecha": "2025-01-01",
            }
        },
    )


@given("data/raw/manifest.json no existe")
def manifest_no_existe(ctx):
    source_dir = ctx["root"] / "ipopi"
    source_dir.mkdir()
    (source_dir / "doc.html").write_text(
        "<html><body><p>Contenido sin manifest previo.</p></body></html>",
        encoding="utf-8",
    )
    ctx["source_name"] = "ipopi"
    ctx["file_name"] = "doc.html"
    ctx["manifest_key"] = "ipopi/doc.html"


# ── When ──────────────────────────────────────────────────────────────────────

@when("se ejecuta el loader", target_fixture="load_result")
def ejecuta_loader(ctx):
    from ingestion.loader import load_documents

    with warnings_module.catch_warnings(record=True) as caught:
        warnings_module.simplefilter("always")
        try:
            documents = load_documents(ctx["source_path"])
            exception = None
        except Exception as exc:  # noqa: BLE001 - se captura para el Then
            documents = None
            exception = exc

    return {
        "documents": documents,
        "exception": exception,
        "warnings": [str(w.message) for w in caught],
    }


# ── Then steps ────────────────────────────────────────────────────────────────

@then("se extrae el texto completo del documento")
def texto_completo_extraido(load_result, ctx):
    docs = load_result["documents"]
    assert docs, "No se cargó ningún documento"
    full_text = "\n".join(d.page_content for d in docs)
    assert ctx["expected_text"] in full_text


@then('el metadato "source" refleja el nombre de la carpeta de fuente')
def metadato_source_correcto(load_result, ctx):
    docs = load_result["documents"]
    assert docs
    for doc in docs:
        assert doc.metadata["source"] == ctx["source_name"]


@then('el metadato "filename" refleja el nombre del fichero')
def metadato_filename_correcto(load_result, ctx):
    docs = load_result["documents"]
    assert docs
    for doc in docs:
        assert doc.metadata["filename"] == ctx["file_name"]


@then("se extrae el texto legible del documento sin marcado HTML")
def texto_legible_sin_html(load_result, ctx):
    docs = load_result["documents"]
    assert docs
    full_text = "\n".join(d.page_content for d in docs)
    assert ctx["expected_text"] in full_text
    assert "<p>" not in full_text
    assert "<html>" not in full_text


@then("se extrae el texto de cada nodo")
def texto_de_cada_nodo(load_result):
    docs = load_result["documents"]
    assert docs
    full_text = "\n".join(d.page_content for d in docs)
    assert "Primer bloque interesante." in full_text
    assert "Segundo bloque, nodo suelto." in full_text


@then("el texto de nodos distintos queda separado por un salto de párrafo")
def texto_separado_por_parrafo(load_result):
    docs = load_result["documents"]
    assert docs
    full_text = "\n".join(d.page_content for d in docs)
    assert "interesante.\n\nSegundo" in full_text
    assert "interesante.Segundo" not in full_text


@then("se registra un aviso indicando el fichero omitido")
def aviso_fichero_omitido(load_result):
    assert any(
        "no soportado" in w.lower() and "omitido" in w.lower()
        for w in load_result["warnings"]
    )


@then("los ficheros válidos de la misma carpeta se cargan igualmente")
def validos_cargados_igualmente(load_result, ctx):
    docs = load_result["documents"]
    assert docs
    assert any(d.metadata["filename"] == ctx["valid_file_name"] for d in docs)


@then("se lanza un error claro que indica la ruta esperada")
def error_ruta_esperada(load_result, ctx):
    exc = load_result["exception"]
    assert isinstance(exc, FileNotFoundError)
    assert ctx["source_path"] in str(exc)


@then("se lanza un error claro indicando que no hay documentos que cargar")
def error_no_hay_documentos(load_result):
    assert isinstance(load_result["exception"], ValueError)


@then("se crea una entrada nueva en el manifest con su checksum y fecha de detección")
def entrada_nueva_creada(ctx):
    manifest = json.loads((ctx["root"] / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["documents"][ctx["manifest_key"]]
    assert entry["checksum"].startswith("sha256:")
    assert entry["fecha"] == date.today().isoformat()


@then('el campo "url" de la nueva entrada queda a null')
def url_a_null(ctx):
    manifest = json.loads((ctx["root"] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["documents"][ctx["manifest_key"]]["url"] is None


@then("se registra un aviso de fuente nueva sin URL documentada")
def aviso_fuente_nueva(load_result):
    assert any(
        "fuente nueva sin url documentada" in w.lower()
        for w in load_result["warnings"]
    )


@then("el fichero se carga igualmente sin bloquear el resto del proceso")
def fichero_cargado_sin_bloqueo(load_result):
    assert load_result["exception"] is None
    assert load_result["documents"]


@then("se actualiza el checksum y la fecha de la entrada existente")
def checksum_actualizado(ctx):
    manifest = json.loads((ctx["root"] / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["documents"][ctx["manifest_key"]]
    assert entry["checksum"] != "sha256:" + "0" * 64
    assert entry["fecha"] == date.today().isoformat()
    assert entry["url"] == "https://example.org/ipopi"


@then("se registra un aviso indicando que el contenido de la fuente cambió")
def aviso_contenido_cambiado(load_result):
    assert any(
        "el contenido de la fuente cambió" in w.lower()
        for w in load_result["warnings"]
    )


@then("se crea el manifest con entradas para todos los ficheros encontrados")
def manifest_creado_con_entradas(ctx):
    manifest_path = ctx["root"] / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert ctx["manifest_key"] in manifest["documents"]


@then("se registra un aviso indicando que no había manifest previo")
def aviso_no_habia_manifest(load_result):
    assert any(
        "no había manifest previo" in w.lower() for w in load_result["warnings"]
    )


@then("todos los ficheros se cargan igualmente sin bloquear el proceso")
def todos_cargados_sin_bloqueo(load_result):
    assert load_result["exception"] is None
    assert load_result["documents"]
