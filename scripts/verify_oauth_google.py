"""
Verificación del Escenario 5 — E-03 T-01
Comprueba que Supabase genera una URL de autorización OAuth válida de Google.

Uso:
    python scripts/verify_oauth_google.py --app familiar
    python scripts/verify_oauth_google.py --app profesional
"""

import argparse
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

REDIRECT_URLS = {
    "familiar": "http://localhost:8000/auth/callback",
    "profesional": "http://localhost:8001/auth/callback",
}


def verify(app: str) -> None:
    redirect_to = REDIRECT_URLS[app]

    # Construye la URL que Supabase usa para iniciar el flujo OAuth
    params = urllib.parse.urlencode({
        "provider": "google",
        "redirect_to": redirect_to,
    })
    endpoint = f"{SUPABASE_URL}/auth/v1/authorize?{params}"

    print(f"\n[{app.upper()}] Solicitando URL de autorización...")
    print(f"  Endpoint: {endpoint}")

    req = urllib.request.Request(
        endpoint,
        headers={"apikey": SUPABASE_ANON_KEY},
    )

    # Supabase devuelve un redirect (302) a Google — no seguimos el redirect,
    # solo verificamos que la Location apunta a accounts.google.com
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
    opener.addheaders = []

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise urllib.error.HTTPError(newurl, code, msg, headers, fp)

    no_redirect_opener = urllib.request.build_opener(NoRedirect())

    try:
        no_redirect_opener.open(req)
        # Si no redirige, algo va mal
        print("  ❌ No se recibió redirección — revisa la configuración del provider.")
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            location = e.headers.get("Location", "")
            parsed = urllib.parse.urlparse(location)
            params_returned = urllib.parse.parse_qs(parsed.query)

            ok_host = parsed.netloc == "accounts.google.com"
            ok_client_id = "client_id" in params_returned
            ok_redirect = "redirect_uri" in params_returned

            print(f"  Location: {location[:120]}{'...' if len(location) > 120 else ''}")
            print(f"  ✅ Host Google:     {ok_host}")
            print(f"  ✅ client_id:       {ok_client_id}")
            print(f"  ✅ redirect_uri:    {ok_redirect}")

            if ok_host and ok_client_id and ok_redirect:
                print(f"\n  ✅ Escenario 5 [{app}] — PASS")
            else:
                print(f"\n  ❌ Escenario 5 [{app}] — FAIL (revisa el provider en Supabase)")
        else:
            print(f"  ❌ HTTP {e.code}: {e.reason}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--app",
        choices=["familiar", "profesional"],
        required=True,
        help="App a verificar",
    )
    args = parser.parse_args()
    verify(args.app)
