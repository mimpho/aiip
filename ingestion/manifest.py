"""Manifest de trazabilidad de las fuentes de datos crudos (D-021)."""

import hashlib
import json
from datetime import date
from pathlib import Path


def compute_checksum(path: Path) -> str:
    """Calcula el checksum sha256 del contenido binario del fichero."""
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return f"sha256:{digest}"


def load_manifest(path: Path) -> dict:
    """Carga el manifest desde disco, o un manifest vacío si no existe."""
    path = Path(path)
    if not path.exists():
        return {"documents": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, data: dict) -> None:
    """Persiste el manifest en disco como JSON legible."""
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def sync_entry(manifest: dict, key: str, file_path: Path) -> str | None:
    """Crea o actualiza la entrada `key` del manifest a partir de `file_path`.

    Devuelve el mensaje de aviso correspondiente si la entrada se creó o
    actualizó, o None si el checksum coincide con el registrado.
    """
    checksum = compute_checksum(file_path)
    documents = manifest.setdefault("documents", {})
    entry = documents.get(key)

    if entry is None:
        documents[key] = {
            "checksum": checksum,
            "url": None,
            "fecha": date.today().isoformat(),
        }
        return "fuente nueva sin URL documentada"

    if entry["checksum"] != checksum:
        entry["checksum"] = checksum
        entry["fecha"] = date.today().isoformat()
        return "el contenido de la fuente cambió"

    return None
