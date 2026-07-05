"""Loader de documentos fuente (E-06 T-02)."""

import warnings
from pathlib import Path

from langchain_community.document_loaders import BSHTMLLoader, PyPDFLoader

from ingestion.manifest import load_manifest, save_manifest, sync_entry


def _load_pdf(file_path: Path):
    return PyPDFLoader(str(file_path)).load()


def _load_html(file_path: Path):
    return BSHTMLLoader(
        str(file_path), bs_kwargs={"features": "html.parser"}
    ).load()


_LOADERS_BY_SUFFIX = {
    ".pdf": _load_pdf,
    ".html": _load_html,
    ".htm": _load_html,
}


def load_documents(source_path: str):
    """Carga documentos PDF y HTML desde el path de datos crudos de la KB.

    Cada subcarpeta directa de `source_path` se trata como una fuente:
    su nombre sobrescribe metadata["source"] y metadata["filename"] se
    añade a partir del nombre del fichero. Sincroniza cada fichero
    cargado contra data/raw/manifest.json (ver ingestion.manifest).
    """
    root = Path(source_path)
    if not root.exists():
        raise FileNotFoundError(
            f"La carpeta de datos crudos no existe: {source_path}"
        )

    source_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    if not source_dirs:
        raise ValueError(
            f"No hay documentos que cargar: {source_path} no contiene ninguna fuente"
        )

    manifest_path = root / "manifest.json"
    manifest_existed = manifest_path.exists()
    manifest = load_manifest(manifest_path)
    if not manifest_existed:
        warnings.warn("No había manifest previo, se crea uno nuevo", UserWarning)

    documents = []
    for source_dir in source_dirs:
        for file_path in sorted(p for p in source_dir.iterdir() if p.is_file()):
            load_fn = _LOADERS_BY_SUFFIX.get(file_path.suffix.lower())
            if load_fn is None:
                warnings.warn(
                    f"Formato no soportado, omitido: {file_path}", UserWarning
                )
                continue

            manifest_key = f"{source_dir.name}/{file_path.name}"
            manifest_warning = sync_entry(manifest, manifest_key, file_path)
            if manifest_warning is not None:
                warnings.warn(f"{manifest_warning}: {manifest_key}", UserWarning)

            loaded_docs = load_fn(file_path)
            for doc in loaded_docs:
                doc.metadata["source"] = source_dir.name
                doc.metadata["filename"] = file_path.name
            documents.extend(loaded_docs)

    save_manifest(manifest_path, manifest)
    return documents
