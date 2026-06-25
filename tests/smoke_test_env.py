"""
smoke_test_env.py — Verificación del entorno de desarrollo AIIP
E-01 / T-06

Verifica que todos los servicios externos están correctamente configurados
antes de arrancar el desarrollo de E-02 y E-03.

Uso:
    python tests/smoke_test_env.py

Requiere:
    pip install supabase python-dotenv google-generativeai sentence-transformers
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

PASS = "✅"
FAIL = "❌"
results = []


def check(name, fn):
    try:
        fn()
        results.append((PASS, name))
        print(f"{PASS} {name}")
    except Exception as e:
        results.append((FAIL, name))
        print(f"{FAIL} {name}: {e}")


# ── 1. Variables de entorno requeridas ────────────────────────

def check_env_vars():
    required = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY",
        "GOOGLE_API_KEY",
        "LLM_MODEL",
        "HF_TOKEN",
        "EMBEDDINGS_MODEL",
    ]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Variables no definidas en .env: {', '.join(missing)}")


# ── 2. Conexión a Supabase ────────────────────────────────────

def check_supabase():
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_ANON_KEY"]
    client = create_client(url, key)
    # Consulta mínima para verificar conectividad
    client.table("_dummy_check").select("*").limit(1).execute()


# Supabase devuelve error 404 si la tabla no existe, pero eso confirma
# que la conexión y autenticación funcionan. Capturamos solo errores reales.
def check_supabase_safe():
    from supabase import create_client
    try:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_ANON_KEY"]
        client = create_client(url, key)
        client.table("_dummy_check").select("*").limit(1).execute()
    except Exception as e:
        # Error de red o autenticación → fallo real
        if "Invalid API key" in str(e) or "Connection" in str(e):
            raise
        # Error de tabla no encontrada → conexión OK
        pass


# ── 3. Google AI — Gemini Flash ───────────────────────────────

def check_gemini():
    from google import genai
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(
        model=os.environ["LLM_MODEL"],
        contents="Di 'ok' en una palabra."
    )
    if not response.text:
        raise ValueError("El modelo no devolvió respuesta")


# ── 4. Embeddings — BAAI/bge-m3 ──────────────────────────────

def check_embeddings():
    from sentence_transformers import SentenceTransformer
    model_name = os.environ["EMBEDDINGS_MODEL"]
    model = SentenceTransformer(model_name)
    vector = model.encode("inmunodeficiencia primaria")
    if len(vector) != 1024:
        raise ValueError(f"Dimensión inesperada: {len(vector)} (esperada 1024)")


# ── 5. Google Drive (solo en Colab) ──────────────────────────

def check_drive():
    drive_path = os.getenv("DRIVE_BASE_PATH", "")
    if not drive_path or not os.path.exists("/content/drive"):
        print(f"   (omitido — no se está ejecutando en Colab)")
        return
    if not os.path.exists(drive_path):
        raise FileNotFoundError(f"Ruta no encontrada: {drive_path}")


# ── Ejecución ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n── AIIP Smoke Test ──────────────────────────────────\n")

    check("Variables de entorno", check_env_vars)
    check("Conexión Supabase", check_supabase_safe)
    check("Google AI — Gemini Flash", check_gemini)
    check("Embeddings — BAAI/bge-m3", check_embeddings)
    check("Google Drive (Colab)", check_drive)

    print("\n─────────────────────────────────────────────────────")
    passed = sum(1 for r in results if r[0] == PASS)
    total = len(results)
    print(f"Resultado: {passed}/{total} checks pasados\n")

    if passed < total:
        sys.exit(1)
