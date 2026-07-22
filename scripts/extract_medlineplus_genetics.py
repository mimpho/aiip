"""Extracción de fichas de MedlinePlus Genetics para E-13 (D-063, D-073, D-074, D-077).

Cruza la página curada "Immune System and Disorders" (43 fichas, sección
Genetics) con el compendio XML `ghr-summaries.xml` para construir la lista
definitiva de fichas nuevas y extraer, lote a lote, el contenido clínico
relevante de cada una a `data/raw/medlineplus_genetics/`.

Descarta automáticamente el solapamiento exacto ya confirmado con
`data/raw/upiip/` (D-074): Bruton's/XLA, enfermedad granulomatosa crónica,
inmunodeficiencia variable común. Un segundo grupo de fichas "de revisión"
(subtipos de SCID, D-074, y síndrome de DiGeorge/22q11.2, hallazgo de
task-start T-01) no se descarta ni se incluye de forma automática — Marcos
las revisa ficha por ficha (escenario 2 del `.feature`) y decide si aportan
valor genuino; si se aprueban, se extraen con `--extract-one` y quedan fuera
de la numeración de lotes (no desplazan el orden alfabético inverso ya
fijado).

El rango de fichas (lote) se acepta como parámetro para poder reutilizar el
script sin reescritura en T-02/T-03 (D-073).

D-077: además del XML masivo (description + related-gene-list), cada ficha
extraída hace una petición HTTP a su página individual
(medlineplus.gov/genetics/condition/{slug}/) para incluir la sección
"Causes" — el XML no la trae, y es donde MedlinePlus explica en prosa la
relación gen→subtipo (p. ej. "XIAP gene mutations cause XLP2"), justo el
tipo de dato que D-075 ya identificó como ausente del "description". Si una
ficha no tiene sección Causes (o falla la petición), se registra un aviso y
se continúa sin ella — no rompe el lote.

Uso:
    python scripts/extract_medlineplus_genetics.py --build-list
    python scripts/extract_medlineplus_genetics.py --extract-batch 1 13
    python scripts/extract_medlineplus_genetics.py --extract-one 22q112-deletion-syndrome
    python scripts/extract_medlineplus_genetics.py --fill-manifest-urls
"""

import argparse
import sys
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

# `python scripts/extract_medlineplus_genetics.py` no añade la raíz del repo a
# sys.path (solo scripts/); se añade explícitamente para poder importar `ingestion`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.manifest import load_manifest, save_manifest

CURATED_PAGE_URL = "https://medlineplus.gov/immunesystemanddisorders.html"
SUMMARIES_XML_URL = "https://medlineplus.gov/download/ghr-summaries.xml"
CONDITION_PAGE_URL_TEMPLATE = "https://medlineplus.gov/genetics/condition/{slug}/"
_XML_NS = {
    "g": "https://medlineplus.gov/download/ghr-summaries-20250602.xsd",
    "html": "http://www.w3.org/1999/xhtml",
}

SOURCE_NAME = "medlineplus_genetics"
OUTPUT_DIR = Path("data/raw") / SOURCE_NAME
MANIFEST_PATH = Path("data/raw/manifest.json")

# Solapamiento exacto confirmado con data/raw/upiip/ (D-074) — se descarta
# siempre de la lista definitiva, sin pasar por revisión ficha por ficha.
EXACT_OVERLAP_SLUGS = {
    "x-linked-agammaglobulinemia": "upiip/06_Malaltia_de_Bruton_ES.pdf",
    "chronic-granulomatous-disease": "upiip/07_Malaltia_Granulomatosa_Cronica_ES.pdf",
    "common-variable-immune-deficiency": "upiip/03_Immunodeficiencia_Comuna_Variable_ES.pdf",
}

# Fichas que se comparan ficha por ficha contra un documento genérico ya
# indexado (D-074 para SCID; DiGeorge/22q11.2 es hallazgo de task-start T-01,
# mismo criterio — ver decisions.md). No se descartan ni se incluyen solas:
# Marcos decide, y si se aprueban se extraen con --extract-one, fuera de la
# numeración de lotes.
REVIEW_CANDIDATE_SLUGS = {
    "22q112-deletion-syndrome": "upiip/09_Sindrome_DiGeorge_ES.pdf",
    "jak3-deficient-severe-combined-immunodeficiency": "upiip/04_Immunodeficiencia_Combinada_Greu_ES.pdf",
    "x-linked-severe-combined-immunodeficiency": "upiip/04_Immunodeficiencia_Combinada_Greu_ES.pdf",
    "zap70-related-severe-combined-immunodeficiency": "upiip/04_Immunodeficiencia_Combinada_Greu_ES.pdf",
}


def _slug_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def fetch_curated_conditions() -> list[dict]:
    """Descarga la página curada y devuelve las fichas de la sección Genetics.

    Cada entrada: {"slug", "title", "url"}. Ordenadas tal como aparecen en la
    página (ya alfabético ascendente en origen).
    """
    response = requests.get(CURATED_PAGE_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    conditions = []
    seen_slugs = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/genetics/condition/" not in href:
            continue
        title = link.get_text(strip=True)
        if not title.endswith(": MedlinePlus Genetics"):
            continue
        title = title[: -len(": MedlinePlus Genetics")]
        slug = _slug_from_url(href)
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        conditions.append({"slug": slug, "title": title, "url": href.rstrip("/")})
    return conditions


def fetch_summaries_by_slug() -> dict[str, dict]:
    """Descarga ghr-summaries.xml e indexa cada health-condition-summary por slug.

    Devuelve {slug: {"title", "url", "paragraphs": [...]}}.
    """
    response = requests.get(SUMMARIES_XML_URL, timeout=120)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    by_slug = {}
    for record in root.findall("g:health-condition-summary", _XML_NS):
        ghr_page = record.findtext("g:ghr-page", namespaces=_XML_NS)
        if not ghr_page or "/genetics/condition/" not in ghr_page:
            continue
        slug = _slug_from_url(ghr_page)
        name = record.findtext("g:name", namespaces=_XML_NS)

        paragraphs = []
        for text_block in record.findall("./g:text-list/g:text", _XML_NS):
            role = text_block.findtext("g:text-role", namespaces=_XML_NS)
            if role != "description":
                continue
            html_el = text_block.find("g:html", _XML_NS)
            if html_el is None:
                continue
            for p in html_el.findall("html:p", _XML_NS):
                paragraph = "".join(p.itertext()).strip()
                if paragraph:
                    paragraphs.append(paragraph)

        genes = [
            g.text.strip()
            for g in record.findall(
                "./g:related-gene-list/g:related-gene/g:gene-symbol", _XML_NS
            )
            if g.text and g.text.strip()
        ]

        by_slug[slug] = {
            "title": name,
            "url": ghr_page.rstrip("/"),
            "paragraphs": paragraphs,
            "genes": genes,
        }
    return by_slug


def fetch_causes_paragraphs(slug: str) -> list[str]:
    """Descarga la página individual de la ficha y extrae la sección "Causes" (D-077).

    El compendio XML solo trae "description" — la relación en prosa entre un
    gen concreto y un subtipo de la enfermedad (p. ej. "XIAP gene mutations
    cause XLP2") vive únicamente en esta sección de la página HTML. Estructura
    real: `<div data-bookmark="causes"><h2>Causes</h2><section><div
    class="mp-content">...párrafos...</div></section><section>...caja "Learn
    more about the genes..."...</section></div>` — se toma solo el primer
    `div.mp-content` (la prosa), no la caja de enlaces a genes.

    No lanza excepción si la ficha no tiene sección Causes o falla la
    petición — registra un aviso y devuelve una lista vacía, para no romper
    el lote completo por una ficha suelta.
    """
    url = CONDITION_PAGE_URL_TEMPLATE.format(slug=slug)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[aviso] {slug}: no se pudo descargar {url} para la sección Causes ({exc})")
        return []

    # response.content (bytes) en vez de response.text: requests adivina mal el
    # encoding de esta página para caracteres fuera de ASCII (letras griegas en
    # nombres de proteínas como "p110δ"/"p85α", o el nbsp de "The\xa0PIK3CD..."),
    # decodificándolos como Latin-1 y produciendo mojibake ("p110Î´"). Pasar los
    # bytes crudos deja que BeautifulSoup detecte el encoding real (UTF-8) a
    # partir del contenido/meta charset, en vez de la cabecera HTTP poco fiable.
    soup = BeautifulSoup(response.content, "html.parser")
    causes_section = soup.find("div", attrs={"data-bookmark": "causes"})
    if causes_section is None:
        print(f"[aviso] {slug}: sin sección Causes en la página, se omite")
        return []

    content = causes_section.find("div", class_="mp-content")
    if content is None:
        print(f"[aviso] {slug}: sección Causes sin contenido reconocible, se omite")
        return []

    # " ".join(...split()): get_text(strip=True) hace strip() por nodo de texto y
    # descarta los que quedan vacíos tras el strip — incluye los nodos que son solo
    # el espacio entre un texto y un <i>/<a> anidado (p. ej. nombres de gen en
    # cursiva), así que las palabras quedan pegadas ("theXIAPgene"). split()+join
    # normaliza sin perder los separadores.
    paragraphs = [
        " ".join(p.get_text().split())
        for p in content.find_all("p")
        if p.get_text(strip=True)
    ]
    if not paragraphs:
        print(f"[aviso] {slug}: sección Causes vacía tras el parseo, se omite")
    return paragraphs


def _sort_key(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    return "".join(c for c in normalized if not unicodedata.combining(c)).upper()


def build_definitive_list() -> list[dict]:
    """Cruza la página curada con el compendio XML y clasifica cada ficha.

    Devuelve la lista de las 43 fichas curadas, ordenadas alfabéticamente de
    forma inversa (Z→A), cada una con su categoría:
    - "exact_overlap": descartada automáticamente (D-074).
    - "review_candidate": pendiente de revisión ficha por ficha (D-074 + T-01).
    - "base": ficha nueva de base, numerada dentro de los lotes.
    """
    curated = fetch_curated_conditions()
    summaries = fetch_summaries_by_slug()

    entries = []
    for condition in curated:
        slug = condition["slug"]
        summary = summaries.get(slug)
        if summary is None:
            raise ValueError(
                f"Ficha curada sin entrada en ghr-summaries.xml: {slug} "
                f"({condition['title']})"
            )
        if slug in EXACT_OVERLAP_SLUGS:
            category = "exact_overlap"
        elif slug in REVIEW_CANDIDATE_SLUGS:
            category = "review_candidate"
        else:
            category = "base"
        entries.append(
            {
                "slug": slug,
                "title": summary["title"] or condition["title"],
                "url": summary["url"],
                "category": category,
                "paragraphs": summary["paragraphs"],
                "genes": summary["genes"],
            }
        )

    entries.sort(key=lambda e: _sort_key(e["title"]), reverse=True)

    base_entries = [e for e in entries if e["category"] == "base"]
    for position, entry in enumerate(base_entries, start=1):
        entry["batch_position"] = position

    return entries


def _print_list_summary(entries: list[dict]) -> None:
    total = len(entries)
    exact = [e for e in entries if e["category"] == "exact_overlap"]
    review = [e for e in entries if e["category"] == "review_candidate"]
    base = [e for e in entries if e["category"] == "base"]

    print(f"Total fichas curadas (sección Genetics de Immune System and Disorders): {total}")
    print(f"  - Descartadas por solapamiento exacto con upiip/ ({len(exact)}):")
    for e in exact:
        print(f"      [{e['slug']}] {e['title']}  ->  {EXACT_OVERLAP_SLUGS[e['slug']]}")
    print(f"  - Pendientes de revisión ficha por ficha ({len(review)}):")
    for e in review:
        print(f"      [{e['slug']}] {e['title']}  ->  {REVIEW_CANDIDATE_SLUGS[e['slug']]}")
    print(f"  - Base (nuevas, numeradas en lotes) ({len(base)}):")
    for e in base:
        print(f"      {e['batch_position']:>2}. [{e['slug']}] {e['title']}")


def _write_html(entry: dict, output_path: Path) -> None:
    # El párrafo "description" del XML describe la enfermedad clínicamente pero no
    # siempre nombra el gen causante (vive aparte, en <related-gene-list>) — el caso
    # que originó E-13 (D-063) es justo una consulta literal por el símbolo del gen
    # ("xiap"), así que se añade aquí para que quede indexado en el texto del chunk.
    # La sección Causes (D-077, solo en la página HTML individual, no en el XML) es
    # donde MedlinePlus explica en prosa la relación gen→subtipo (p. ej. "XIAP gene
    # mutations cause XLP2") — se añade antes de la línea compacta de genes.
    paragraphs = list(entry["paragraphs"])
    paragraphs.extend(fetch_causes_paragraphs(entry["slug"]))
    if entry["genes"]:
        paragraphs.append(f"Related gene(s): {', '.join(entry['genes'])}.")
    body = "\n".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
    html = f"<h1>{entry['title']}</h1>\n{body}\n"
    output_path.write_text(html, encoding="utf-8")


def extract_batch(start: int, end: int) -> list[Path]:
    """Extrae las fichas de base en el rango [start, end] (1-indexado, incluido)."""
    entries = build_definitive_list()
    base_by_position = {e["batch_position"]: e for e in entries if e["category"] == "base"}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for position in range(start, end + 1):
        entry = base_by_position.get(position)
        if entry is None:
            raise ValueError(f"No hay ficha de base en la posición {position}")
        output_path = OUTPUT_DIR / f"{entry['slug']}.html"
        _write_html(entry, output_path)
        written.append(output_path)
        print(f"[{position}] {entry['title']} -> {output_path}")
    return written


def extract_one(slug: str) -> Path:
    """Extrae una única ficha de revisión aprobada (fuera de la numeración de lotes)."""
    entries = build_definitive_list()
    matches = [e for e in entries if e["slug"] == slug]
    if not matches:
        raise ValueError(f"Slug no encontrado en la lista curada: {slug}")
    entry = matches[0]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{entry['slug']}.html"
    _write_html(entry, output_path)
    print(f"[revisión aprobada] {entry['title']} -> {output_path}")
    return output_path


def fill_manifest_urls() -> None:
    """Rellena la URL real de cada ficha ya indexada de medlineplus_genetics.

    Se ejecuta después de `python scripts/smoke_test_rag.py --force-reingest`
    (que crea las entradas nuevas con `url: null`, D-021). Lee la URL real
    directamente del <ghr-page> de cada ficha en ghr-summaries.xml — no
    modifica `ingestion/manifest.py::sync_entry()` (D-073).
    """
    summaries = fetch_summaries_by_slug()
    manifest = load_manifest(MANIFEST_PATH)
    documents = manifest.setdefault("documents", {})

    updated = 0
    for filename in sorted(p.name for p in OUTPUT_DIR.glob("*.html")):
        slug = filename[: -len(".html")]
        summary = summaries.get(slug)
        if summary is None:
            print(f"[aviso] sin URL en ghr-summaries.xml para {filename}, se omite")
            continue
        key = f"{SOURCE_NAME}/{filename}"
        entry = documents.get(key)
        if entry is None:
            print(f"[aviso] {key} no está en el manifest (¿falta reingesta?), se omite")
            continue
        if entry.get("url") != summary["url"]:
            entry["url"] = summary["url"]
            updated += 1

    save_manifest(MANIFEST_PATH, manifest)
    print(f"URLs actualizadas en el manifest: {updated}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--build-list", action="store_true",
        help="Descarga las fuentes y muestra la lista definitiva clasificada",
    )
    group.add_argument(
        "--extract-batch", nargs=2, type=int, metavar=("START", "END"),
        help="Extrae las fichas de base en el rango [START, END] (1-indexado)",
    )
    group.add_argument(
        "--extract-one", metavar="SLUG",
        help="Extrae una ficha de revisión aprobada por su slug (fuera de los lotes)",
    )
    group.add_argument(
        "--fill-manifest-urls", action="store_true",
        help="Rellena la URL real de las fichas ya indexadas (tras --force-reingest)",
    )
    args = parser.parse_args()

    if args.build_list:
        _print_list_summary(build_definitive_list())
    elif args.extract_batch:
        start, end = args.extract_batch
        extract_batch(start, end)
    elif args.extract_one:
        extract_one(args.extract_one)
    elif args.fill_manifest_urls:
        fill_manifest_urls()


if __name__ == "__main__":
    main()
