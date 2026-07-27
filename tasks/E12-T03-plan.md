# Plan — E-12 T-03 Despliegue público (perfil familiar)

## Contexto (ya decidido en Cowork, no se re-discute en Antigravity)

- **Origen:** D-007 (jun 2026) comprometió una URL pública para el 10 jul; quedó documentado como
  análisis pendiente de ejecutar en `backlog/ideas.md` ("Despliegue online del perfil familias") y
  se aparcó sin dueño cuando E-10 salió de Fase 1.5 (D-087). E-12 lo retoma como T-03, en paralelo
  a T-02, sin workflow completo de `epic-start`/`task-start` (sin Gherkin, sin gates) dado el
  margen de 2-3 días hasta el 29 de julio — decisión ya tomada, ver `backlog/epics.md` sección E-12.
- **Alcance:** solo el perfil **familiar** (`chainlit/main_family.py`). El perfil profesional es
  un stub sin RAG conectado (backlog F-01), no se despliega.
- **Objetivo:** que el tribunal del TFM pueda abrir una URL y usar el chat real (login, RAG,
  citación de fuentes, derivación de seguridad) sin depender de que nadie tenga el repo en local.

## Decisión de plataforma: HF Spaces (revertido desde Fly.io, 27 jul 2026)

Este plan eligió originalmente **Fly.io** por un motivo técnico concreto (ver histórico en git):
`fly deploy` construye desde el filesystem local, así que `data/chroma/` (gitignored, ~94MB)
viaja en la imagen sin tocar `.gitignore` de GitHub. HF Spaces, en cambio, despliega vía git push
a un repo propio del Space, lo que exige forzar la inclusión de `data/chroma/` con git-lfs — un
paso extra que el plan original quería evitar.

**Verificación del tier gratuito (pedida explícitamente antes de implementar) invalidó esa
decisión.** Comprobado contra la documentación oficial de Fly.io (`fly.io/docs/about/pricing`,
27 jul 2026):

- **Fly.io ya no ofrece tier gratuito a cuentas nuevas** ("Fly.io no longer offers plans to new
  customers") — pay-as-you-go puro, tarjeta de crédito obligatoria desde el alta.
- Solo cuentas *legacy* (anteriores al cambio de política, 2024) conservan una asignación
  gratuita: hasta 3 VMs `shared-cpu-1x` de **256MB RAM**.
- Aunque esa cuenta legacy existiera, 256MB es insuficiente: `bge-m3` en CPU necesita ~1.2-2.5GB
  solo para inferencia (float16), sin contar PyTorch + ChromaDB + Chainlit. La máquina mínima
  viable serían 1-2GB RAM, **~6-11€/mes** — no hay ruta gratuita real en Fly.io hoy.
- Se descartaron también Render.com (free tier: 512MB RAM / 0.1 CPU, insuficiente, además de
  dormir a los 15 min) y Railway.app (no es un tier gratuito permanente: trial de 30 días con 5$
  de crédito, luego plan de pago).

**HF Spaces (Docker SDK, hardware "CPU Basic") sí es gratis de verdad**: 2 vCPU, 16GB RAM, sin
tarjeta de crédito, sin límite de tiempo (se duerme tras ~48h sin tráfico y arranca solo con la
siguiente visita). Es más que suficiente para bge-m3+torch+ChromaDB+Chainlit. Se acepta el coste
que el plan original quería evitar (git-lfs para `data/chroma/`) porque es un problema resuelto
una sola vez, no recurrente como el coste de Fly.io — ver mecánica en el paso 4 más abajo.

## Decisión de plataforma (segunda corrección): Google Cloud Run (revertido desde HF Spaces, 27 jul 2026, misma tarde)

Con el Dockerfile ya validado de punta a punta en local (ver paso 3 más abajo), Marcos fue a crear
el Space en la web de HF y descubrió que **el SDK Docker está tras muro de pago** desde hace ~3
semanas (cambio no anunciado oficialmente, reportado en el foro de HF desde el 8 jul 2026,
agravado el 24 jul: *"Add billing to your account (credits or subscribe to PRO) to unlock Docker
Spaces"*). Confirmado visualmente en la UI de creación de Space: **Docker** aparece marcado
`Paid`, y en "Space hardware" **CPU Basic** aparece deshabilitado — solo queda seleccionable
ZeroGPU (pensado para demos Gradio con cuota de GPU diaria, no para un backend de chat
persistente). Static y Gradio siguen gratis; Docker no. Esto invalida la decisión de HF Spaces
tomada horas antes en este mismo documento — no hay tier gratuito real para un despliegue Docker
en HF tampoco.

En este punto ni Fly.io ni HF Spaces ofrecen ya una ruta Docker gratuita. Se evaluaron 3 opciones:
Fly.io de pago (~6-11€/mes, ya descartado arriba), HF PRO de pago (9$/mes, mantiene la complejidad
de git-lfs), y **Google Cloud Run**, elegido finalmente. Verificado contra la documentación oficial
(`docs.cloud.google.com/free/docs/free-cloud-features`, 27 jul 2026):

- **Always Free, permanente (no un trial de tiempo limitado)**: 2 millones de requests/mes,
  360.000 GB-segundos de memoria + 180.000 vCPU-segundos de cómputo/mes, 1GB de salida de datos.
  A diferencia de Fly.io/HF (que facturan por tiempo de máquina encendida), Cloud Run solo
  descuenta cuota mientras el contenedor procesa una request activa — en reposo no consume nada.
  Para el tráfico esperado de una demo de TFM (unas pocas sesiones cortas), el consumo real queda
  muy por debajo de la cuota — coste esperado: **0€**.
- Sí exige un billing account de GCP con tarjeta de crédito dada de alta (verificación, no cargo
  esperado dado el volumen) — misma fricción que Fly.io/HF, pero sin expectativa real de cobro.
- Memoria configurable por instancia: hasta 8GiB (de sobra para bge-m3+torch+ChromaDB+Chainlit,
  que necesitan ~2-4GB).
- **`gcloud run deploy --source .` construye desde el filesystem local vía Cloud Build** — mismo
  mecanismo que el Fly.io original (build context local), **sin el lío de git-lfs** que exigía HF
  Spaces. `data/chroma/` viaja en la imagen automáticamente, igual que en la decisión inicial.
- Se descartó Oracle Cloud Always Free (VMs ARM gratis de verdad, 24GB RAM) por riesgo de
  capacidad/provisioning agotada en muchas regiones — friction real de horas/días, incompatible
  con el margen de ~2 días hasta el 29 de julio.

El Dockerfile del paso 1 y el build validado en el paso 3 **no cambian** — Cloud Run consume el
mismo Dockerfile tal cual (el patrón de usuario no-root UID 1000, pensado originalmente para HF
Spaces, es inocuo aquí y se mantiene). Solo cambian los pasos de despliegue (4 en adelante).

## Requisitos previos (los haces tú, fuera de Antigravity)

1. Cuenta de Google Cloud + crear (o reutilizar) un **proyecto de GCP**, y habilitar **billing**
   (tarjeta de crédito, sin cargo esperado dado el volumen — ver "Decisión de plataforma" arriba).
2. Instalar `gcloud` CLI (`brew install --cask google-cloud-sdk` en macOS), autenticar
   (`gcloud auth login`) y fijar el proyecto (`gcloud config set project <project-id>`).
3. Habilitar las APIs necesarias: `gcloud services enable run.googleapis.com
   cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com`.
4. Tener a mano los valores reales de tu `.env` — se usan para crear los secrets en Secret
   Manager (paso 5).
5. En **Google Cloud Console** (mismo proyecto OAuth de D-014 — puede ser un proyecto GCP distinto
   al de este despliegue, Cloud Run y el proyecto OAuth no tienen que coincidir), añadir a
   "Authorized redirect URIs" la URL de Cloud Run una vez conocida tras el primer deploy (paso 6,
   patrón `https://<service>-<hash>.<region>.run.app/auth/oauth/google/callback` o el dominio
   `.a.run.app` equivalente — Cloud Run muestra la URL exacta al terminar `gcloud run deploy`).
   Sin este paso el login de Google falla en producción aunque funcione en local (mismo patrón que
   ya vimos con `redirect_uri_mismatch` en el smoke test local).

**Hallazgo adicional (28 jul, smoke test contra la URL real):** dar de alta la URI exacta en
Google Cloud Console no fue suficiente — el `redirect_uri_mismatch` persistía. Causa real:
Chainlit construye el `redirect_uri` que manda a Google con `get_user_facing_url()`
(`chainlit/server.py:439`), cuya propia documentación dice literalmente *"Handles deployment with
proxies (like cloud run)"* — sin la variable de entorno `CHAINLIT_URL` explícita, usa la URL
interna que ve el proceso detrás del proxy de Cloud Run (previsiblemente `http://` o un host
distinto al público), no la URL pública real. `CHAINLIT_URL` no estaba en `.env.example` porque
en local no hace falta (la URL interna y la pública coinciden). Fix: añadir
`CHAINLIT_URL=https://<url-real-de-cloud-run>` a las variables de entorno del deploy (paso 6) —
no es un secret, va en `cloudrun-env-vars.yaml` junto a `SUPABASE_URL` y el resto.

## Pasos para Antigravity

### 1. Crear `Dockerfile` en la raíz del repo

HF Spaces ejecuta el contenedor con UID 1000, no root — hay que crear el usuario explícitamente y
`chown` en cada `COPY`/`ADD` (si no, falla por permisos al escribir cachés de HF/torch en runtime).

```dockerfile
FROM python:3.12-slim

# build-essential: compila dependencias nativas de torch/sentence-transformers.
# libgomp1: requerido en runtime por torch (OpenMP), no solo en build.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces corre el contenedor como UID 1000, no root.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

# chainlit/family/public y chainlit/family/.chainlit/translations son symlinks en el repo
# (a design/public/ y ../../../.chainlit/translations). docker build local los preserva, pero
# `gcloud run deploy --source .` empaqueta el código para Cloud Build de otra forma y los
# convierte en directorios vacíos — se resuelven aquí de forma explícita para que el Dockerfile
# funcione igual sea cual sea el mecanismo de build.
RUN rm -rf chainlit/family/public && cp -r design/public chainlit/family/public \
    && rm -rf chainlit/family/.chainlit/translations \
    && cp -r .chainlit/translations chainlit/family/.chainlit/translations

ENV CHAINLIT_APP_ROOT=$HOME/app/chainlit/family
ENV PYTHONPATH=$HOME/app

EXPOSE 8000

# Sin -w (esa flag es solo para desarrollo con autoreload)
CMD ["chainlit", "run", "chainlit/main_family.py", "--host", "0.0.0.0", "--port", "8000"]
```

**Verificado en Cloud Run (27 jul 2026, tras el primer deploy real):** `chainlit/family/public` y
`chainlit/family/.chainlit/translations` son symlinks (a `design/public/` y a
`../../../.chainlit/translations` respectivamente). En el smoke test local con `docker build`
directo se resolvían bien (mismo filesystem local como build context), pero **`gcloud run deploy
--source .` los rompió**: llegaron a la imagen como directorios reales vacíos, no como symlinks —
el mecanismo de subida de fuentes de Cloud Build no los preserva igual que un `docker build`
local. Síntoma en producción: la app cargaba pero sin `style.css`/`custom.js`/`theme.json`
(404 en `/public/*`, tema por defecto de Chainlit en vez del de AIIP). Diagnosticado extrayendo la
imagen exacta desplegada (`docker pull` + `docker run --entrypoint sh` + `ls -la`) y comparando
con el comportamiento local. Fix aplicado arriba: en vez de depender de que el symlink sobreviva,
se `rm -rf` + `cp -r` el contenido real dentro del propio build — funciona igual sin importar el
mecanismo de subida del código (local, Cloud Build, o cualquier otro futuro).

### 2. Crear `.dockerignore` en la raíz (no existe todavía)

```
.venv/
.git/
__pycache__/
*.pyc
.pytest_cache/
tests/
tasks/
docs/
data/raw/
!data/raw/manifest.json
.env
.DS_Store
.claude/
```

Importante: **no** excluir `data/chroma/` aquí — a diferencia de git, el build de Docker sí debe
incluirlo (es la base vectorial ya indexada que hace funcionar el RAG en producción).

### 3. Probar la imagen en local antes de tocar la nube (válido para cualquier plataforma)

```bash
docker build -t aiip-family-test .
docker run --rm -p 8010:8000 --env-file .env aiip-family-test
```

El contenedor sigue escuchando en el puerto 8000 interno (coherente con el `Dockerfile`); el
mapeo de host usa **8010**, no 8000 ni 8001 — 8000 puede estar ocupado por un `chainlit run -w`
local de desarrollo (frecuente en este proyecto) y 8001 está reservado a `PORT_PROFESSIONAL`
(`.env.example`, D-010).

Abrir `http://localhost:8010` y verificar: login (email/password y Google), una pregunta al chat
con respuesta y fuente citada, y un caso de alarma (ver
`tests/features/e04_t05_safety_module.feature` para un ejemplo de query). Si algo falla aquí, es
mucho más barato depurarlo en local que en un build remoto en la nube.

**Verificado en local (27 jul 2026, build real con Docker Desktop en macOS):**

- Primer build con `torch==2.12.1` directo de PyPI: **10.8GB** — muy por encima de la estimación
  original (">3GB"). Causa real, no la imagen base: la rueda de PyPI de `torch` incluye las
  dependencias CUDA/GPU completas (`nvidia-cublas`, `nvidia-cudnn-cu13`, `triton`,
  `cuda-toolkit`...), aunque este proyecto solo corre `bge-m3` en CPU (D-043) — el `python:3.12-slim`
  de base no era el problema, como suponía una versión anterior de este plan.
- Fix aplicado (ya incorporado en el Dockerfile del punto 1): instalar la rueda CPU-only de
  `torch` desde `https://download.pytorch.org/whl/cpu` antes de `pip install -r requirements.txt`.
  Resultado: **4.05GB** — dentro de cualquier límite razonable de HF Spaces (50GB de storage
  efímero en build/runtime para el hardware "CPU Basic").
- Contenedor arrancado con `--env-file .env`: arranca limpio (un único log
  `Your app is available at http://0.0.0.0:8000`, sin errores de permisos ni de symlinks). `curl`
  a `/`, `/login`, `/public/style.css`, `/public/custom.js` y `/auth/config` devuelven 200 con
  contenido real — confirma que los symlinks (punto 1) y el usuario no-root (UID 1000) funcionan
  bien dentro de la imagen, y que `/auth/config` expone `"oauthProviders":["google"]`, es decir
  que las credenciales de Google OAuth del `.env` se leyeron bien.
- Pipeline RAG probado directamente dentro del contenedor (`RAGPipeline(load_rag_config()).retrieve(...)`,
  sin pasar por la UI): carga de `bge-m3` desde cero (~2.2GB descargados vía `HF_TOKEN`) +
  `retrieve()` sobre ChromaDB con el hybrid retriever, **65s en total la primera vez** (carga de
  modelo incluida, no es el tiempo por request), 10 resultados devueltos sin error. Confirma que
  el mayor riesgo técnico del plan (bge-m3 en CPU dentro del contenedor) funciona de extremo a
  extremo.
- Test manual en navegador (Marcos, 27 jul): el contenedor de prueba se movió a **puerto de host
  8010** (no 8000: choca con un `chainlit run -w --port 8000` de desarrollo que llevaba >1 día
  corriendo; no 8001: reservado a `PORT_PROFESSIONAL`). Login email/password contra el contenedor
  confirmado en los logs (`POST .../auth/v1/token?grant_type=password` → 400 con credenciales que
  no correspondían a password real, seguido del fallback a `signup` de `auth_callback`, D-040 —
  comportamiento esperado, no bug) — prueba que el contenedor habla correctamente con el Supabase
  real (`diyvhfujdxigtxqxfocm.supabase.co`, el mismo del `.env`, no otra base de datos). Login
  Google dio `Error 400: redirect_uri_mismatch` — **esperado**, Google Cloud Console solo tiene de
  alta la redirect URI del puerto 8000 habitual, no la 8010 de esta prueba puntual; confirma la
  ruta exacta (`/auth/oauth/google/callback`, `chainlit/server.py:644`) que ya usa el requisito
  previo 5. Decisión: no dar de alta 8010 solo para esto — se verifica Google OAuth de verdad en
  el paso 7, contra la URL real de HF Spaces (que de todas formas necesita su propia alta).
- Pendiente de verificación manual (requiere navegador, no automatizable desde aquí): una pregunta
  real en el chat con fuente citada y un caso de alarma, con login por email/password.
  **Completado (Marcos, 27 jul):** pregunta informativa ("¿Cómo puedo cuidar el día a día de mi
  familiar?" y "que es el xiap?") con retrieval + fuentes citadas reales (`idf`, `upiip`,
  `medlineplus_genetics`) y respuesta generada por Gemini sin error; caso de alarma ("mi hijo
  tiene 40 grados de fiebre desde hace dos días", ejemplo de
  `tests/features/e04_t05_safety_module.feature`) procesado igualmente sin error en retrieval ni
  en la llamada al LLM. **Checklist local del paso 3 completo** — el `Dockerfile` queda validado
  de extremo a extremo antes de tocar HF Spaces.

Fallos esperables que siguen abiertos, por orden de probabilidad:
- `bge-m3` se descarga la primera vez que se usa (ya verificado arriba, ~2.2GB, ~65s en esta
  máquina) — el primer mensaje de chat en producción será lento. Aceptable para una demo, pero
  avisar a quien pruebe la herramienta de que la primera respuesta puede tardar más.
- El login con Google no se ha podido probar en local del todo (el redirect de OAuth apunta a un
  dominio real) — se prueba de verdad en el paso 7, contra la URL pública de HF Spaces.

### 4. Crear los secrets en Secret Manager

A diferencia de Fly.io (`fly secrets set`) o HF Spaces (web UI), Cloud Run referencia secrets ya
creados en **Secret Manager** — un paso de alta por secret, luego se referencian por nombre en el
deploy (paso 6). Solo los valores realmente sensibles; el resto va como `--set-env-vars` normal.

```bash
# Desde la raíz de este repo, con los valores reales de tu .env:
echo -n "TU_SUPABASE_SERVICE_KEY" | gcloud secrets create SUPABASE_SERVICE_KEY --data-file=-
echo -n "TU_GOOGLE_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-
echo -n "TU_HF_TOKEN" | gcloud secrets create HF_TOKEN --data-file=-
echo -n "TU_CHAINLIT_AUTH_SECRET" | gcloud secrets create CHAINLIT_AUTH_SECRET --data-file=-
echo -n "TU_OAUTH_GOOGLE_CLIENT_SECRET" | gcloud secrets create OAUTH_GOOGLE_CLIENT_SECRET --data-file=-
```

`SUPABASE_ANON_KEY` y `OAUTH_GOOGLE_CLIENT_ID` no son secretos de verdad (van al cliente/redirect
público) — se pueden pasar como `--set-env-vars` normal en el paso 6, no hace falta darlos de alta
aquí. `CHAINLIT_URL` tampoco es secret — ver hallazgo en el requisito previo 5 (necesaria para que
el login de Google use la URL pública real, no la interna del proxy de Cloud Run).

### 5. Crear `.gcloudignore` — hallazgo crítico, corrige una asunción errónea de este plan

**Esta suposición inicial era incorrecta y causó el fallo más grave de todo el despliegue:**
"Cloud Build usa el mismo mecanismo que `docker build`, el filesystem local como contexto,
respetando `.dockerignore`". Falso. `gcloud run deploy --source .` tiene un **paso de subida de
fuentes previo y separado** al build de Docker: decide qué sube a Cloud Build usando
`.gcloudignore` si existe, y **si no existe, hereda automáticamente las reglas de `.gitignore`**
del repo (documentado por `gcloud`, no un comportamiento nuestro). Como `data/chroma/` está en
`.gitignore` (a propósito, para que no viaje a GitHub), **nunca llegó a Cloud Build** — la imagen
se construyó con `data/chroma/` completamente ausente. `.dockerignore` no importa aquí: nunca
llega a evaluarse sobre un fichero que ya se excluyó en la subida.

**Síntoma en producción, sin ningún error visible:** la app funcionaba (login, chat, respuesta
generada) pero `retrieve()` devolvía siempre `[]` — el LLM respondía sin ningún contexto de la
KB real, sin fuentes citadas. Al principio se sospechó una condición de carrera entre instancias
concurrentes de Cloud Run (ver Riesgos conocidos), pero un test aislado (mismo build, sin presión
de memoria/concurrencia, `docker run --platform linux/amd64` en local sobre la imagen exacta
desplegada) confirmó `n_results: 0` de forma determinista — y una inspección directa
(`chromadb.PersistentClient(path='./data/chroma').list_collections()` dentro de la imagen) mostró
`collections: []` y `ls data/chroma/` con "No such file or directory". Diagnóstico confirmado.

**Fix:**

```
# Sin este fichero, `gcloud run deploy --source .` hereda .gitignore para decidir qué subir a
# Cloud Build — y .gitignore excluye data/chroma/ (a propósito, para GitHub). Este fichero rompe
# esa herencia explícitamente; data/chroma/ NO debe excluirse aquí, es la base vectorial del RAG.
.venv/
.git/
__pycache__/
*.pyc
.pytest_cache/
tests/
tasks/
docs/
data/raw/
!data/raw/manifest.json
.env
.DS_Store
.claude/
```

Mismo contenido que `.dockerignore` (paso 2), en un fichero nuevo `.gcloudignore` en la raíz —
crearlo es suficiente para que `gcloud` deje de heredar `.gitignore` y `data/chroma/` viaje.

**Lección para futuros despliegues con `gcloud run deploy --source .` (o cualquier mecanismo de
subida de fuentes de GCP) sobre un repo con `.gitignore`:** verificar siempre `.gcloudignore`
explícitamente — nunca asumir que el mecanismo de subida de fuentes se comporta como un
`docker build` local, aunque el resultado final use el mismo `Dockerfile`.

### 6. Desplegar

```bash
gcloud run deploy aiip-family \
  --source . \
  --region europe-west1 \
  --port 8000 \
  --memory 8Gi \
  --cpu 2 \
  --concurrency 4 \
  --allow-unauthenticated \
  --env-vars-file=cloudrun-env-vars.yaml \
  --set-secrets="SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,HF_TOKEN=HF_TOKEN:latest,CHAINLIT_AUTH_SECRET=CHAINLIT_AUTH_SECRET:latest,OAUTH_GOOGLE_CLIENT_SECRET=OAUTH_GOOGLE_CLIENT_SECRET:latest"
```

**Comando definitivo (27 jul, tras converger todos los fixes de esta sección) — este es el que
hay que reutilizar para futuros redeploys** (cambios de código, actualización de `data/chroma/`
tras reingesta, etc.): memoria 8Gi (no 4Gi ni 6Gi, ambos insuficientes — ver Riesgos conocidos),
`--concurrency 4`, y requiere que exista `.gcloudignore` en la raíz (paso 5) o `data/chroma/`
no viajará. `cloudrun-env-vars.yaml` es un fichero local (fuera del repo, con los valores no
sensibles del `.env`) — recrearlo si se despliega desde otra máquina, mismo contenido que la
lista de variables del paso 6 original. Los secrets de Secret Manager (paso 4) ya existen en el
proyecto GCP y se reutilizan tal cual — no hace falta recrearlos en cada redeploy, esa referencia
(`:latest`) recoge automáticamente si se actualiza algún valor con `gcloud secrets versions add`.
No hace falta repetir `gcloud services enable` ni la concesión de IAM sobre los secrets (paso 4.5,
`gcloud secrets add-iam-policy-binding`) — ya quedan concedidos a nivel de proyecto/secret.

Notas:
- `--region`: cualquier región cercana sirve; `europe-west1` (Bélgica) es razonable dado que
  Supabase también está en EU (D-014). No afecta la cuota Always Free (aplica en "regiones EE.UU.
  seleccionadas" para el tráfico de salida gratuito, pero el cómputo Always Free de Cloud Run no
  está limitado a EE.UU. — verificar si aparece algún cargo inesperado de red tras el primer
  deploy, debería ser mínimo dado el volumen).
- `--memory 6Gi --cpu 2`: **corregido tras el primer deploy real** — con `--memory 4Gi` el
  contenedor murió por OOM (`Memory limit of 4096 MiB exceeded with 4155 MiB used`, visible en
  `gcloud logging read`) al cargar `bge-m3` bajo carga real, justo por encima de lo observado en
  el smoke test local (~2-4GB). 6Gi da margen sin acercarse al máximo de Cloud Run (8GiB).
- `--allow-unauthenticated`: necesario para que el tribunal acceda sin credenciales de GCP — el
  control de acceso real lo sigue haciendo Chainlit (Supabase auth), no IAM de GCP.
- `DRIVE_BASE_PATH`, `KB_RAW_DATA_PATH`, `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP` no hacen falta en
  producción — solo se usan en el pipeline de ingesta (Colab/local), no al servir el chat.
- El comando construye la imagen vía Cloud Build (usa el `Dockerfile` de la raíz) y despliega en
  un solo paso — la primera vez tarda varios minutos (build completo, sin caché remota todavía).
  Al terminar, `gcloud` imprime la URL del servicio (`https://aiip-family-<hash>.<region>.run.app`
  o el dominio `.a.run.app` equivalente) — esa es la URL para el requisito previo 5 (Google Cloud
  Console) y el smoke test del paso 7.

### 7. Smoke test sobre la URL real

Repetir el mismo checklist del paso 3 (login email/password, login Google, pregunta con fuente
citada, caso de alarma) pero contra la URL real que imprimió `gcloud run deploy`. Si el login de
Google falla con `redirect_uri_mismatch` (ya visto en el smoke test local), revisar el requisito
previo 5 — la URI exacta debe coincidir carácter a carácter, incluyendo el `https://` y el path
`/auth/oauth/google/callback`.

Nota sobre arranque en frío: la primera visita tras el deploy (o tras un periodo largo sin
tráfico, ver Riesgos) tardará más en el primer mensaje del chat por la descarga de `bge-m3`
(~65s, ya medido en el smoke test local) — normal, no es un fallo.

### 8. Actualizar documentación (vuelta a Cowork, no en Antigravity)

Una vez la URL esté verificada y funcionando:
- `README.md` sección 0.4 (Ficha del proyecto) y 2.4 (Infraestructura y despliegue): sustituir el
  aviso de "pendiente" por la URL real y el estado real del despliegue (Google Cloud Run,
  incluyendo el recorrido Fly.io → HF Spaces → Cloud Run y por qué en cada paso — verificación de
  tier gratuito, ver sección "Decisión de plataforma" arriba — para que quede como parte trazable
  de la metodología del TFM, no solo como nota interna).
- `backlog/epics.md`: marcar T-03 como ✅ Completada, con nota del recorrido de plataforma.
- Valorar con Marcos si hace falta una T-04 de cierre final de E-12 (pendiente de decidir, ver
  nota en `backlog/epics.md`).

## Riesgos conocidos (no bloquean el arranque, pero avisar si aparecen)

- Cloud Run escala a cero tras un periodo sin tráfico (equivalente al "sueño" de HF Spaces/otros
  PaaS) — la siguiente visita tiene arranque en frío: descarga de `bge-m3` de nuevo si el
  contenedor es una instancia nueva (~65s ya medido en el smoke test local, reproducido también
  ahí al recrear el contenedor de prueba). Mitigación barata: visitar la URL uno mismo el día
  antes de la defensa.
- **Límite conocido, aceptado explícitamente (27 jul, tras smoke test real en producción):** bajo
  tráfico simultáneo, Cloud Run puede levantar **varias instancias en paralelo** (autoscaling por
  defecto), cada una cargando su propia copia de `bge-m3` de forma independiente y sin caché
  compartida entre instancias. Observado en logs reales: OOM incluso a 6GiB de memoria (`Memory
  limit of 6144 MiB exceeded with 6248-6545 MiB used`) — probablemente la causa de un fallo
  puntual del login de Google durante el smoke test (la petición cayó en una instancia
  muerta/no lista). Nota: en el mismo smoke test también se observó `retrieve()` devolviendo
  `[]` de forma constante, pero esa parte **no era este problema** — era el bug de
  `data/chroma/` ausente de la imagen por herencia de `.gitignore` (ver paso 5, ya corregido con
  `.gcloudignore`); quedan aquí solo el OOM/autoscaling como riesgo real todavía sin eliminar
  del todo. Mitigado parcialmente subiendo a
  `--memory 8Gi` y `--concurrency 4` (limita cuántas peticiones pesadas procesa una misma
  instancia a la vez), pero **no se activa `--min-instances=1`** (que eliminaría el problema del
  todo manteniendo una instancia siempre caliente) porque el despliegue puede quedar publicado
  semanas sin supervisión activa, y `--min-instances=1` implica coste real y recurrente mientras
  esté activo (~3-7€ según el tiempo que quede levantado, verificado contra
  `cloud.google.com/run/pricing`: \$0.000024/vCPU-seg + \$0.0000025/GiB-seg más allá de la cuota
  Always Free) — decisión explícita de Marcos: aceptar el riesgo de una posible respuesta lenta o
  fallida bajo picos de tráfico simultáneo, a cambio de mantener el despliegue realmente gratuito
  y sin mantenimiento activo a medio plazo. Si el tribunal prueba la herramienta con varias
  personas a la vez, hay una probabilidad real (no cuantificada) de un fallo puntual — mitigación
  si ocurre: recargar la página/reintentar, la siguiente request debería caer en una instancia ya
  estable.
- `bge-m3` en CPU puede ir lento en el primer request incluso con instancia ya caliente — no hay
  presupuesto de tiempo aquí para optimizar, solo para que funcione.
- Facturación: aunque el volumen esperado cae muy por debajo de la cuota Always Free (verificado
  arriba), Cloud Run sí exige billing account activo con tarjeta — si el tribunal genera tráfico
  inesperadamente alto (poco probable), podría haber cargo real, a diferencia de HF Spaces gratis
  sin tarjeta. Revisar el dashboard de facturación de GCP tras la defensa por higiene, no porque
  se espere ningún cargo.
- Riesgo de proceso, no técnico: los secrets creados en Secret Manager (paso 4) quedan en el
  proyecto de GCP, no en este repo — si se repite el despliegue en otra máquina/sesión, hay que
  recrearlos o reutilizar los existentes con `gcloud secrets versions access latest --secret=...`
  en vez de volver a hacer `gcloud secrets create` (que fallaría si el secret ya existe;
  usar `gcloud secrets versions add` para actualizar un valor).
- **Resuelto con fix de código (28 jul), no solo de configuración:** `auth/supabase_client.py`
  (`sign_up()`, `reset_password_for_email()`) no pasaba ninguna URL de redirect explícita — el
  enlace del email de confirmación de signup y de recuperación de contraseña lo construía
  **Supabase** con su Site URL de dashboard por defecto (Authentication → URL Configuration), no
  algo derivado de la petición como sí hace Chainlit para el OAuth de Google (ver hallazgo de
  `CHAINLIT_URL` arriba) — con el mismo problema de fondo: local y producción no pueden compartir
  un único Site URL fijo. En vez de alternar el Site URL a mano según el entorno (lo que exigiría
  el requisito previo original, D-014), se añadió `_confirm_redirect_url()` en
  `auth/supabase_client.py`: lee `CHAINLIT_URL` (la misma variable que ya usa Chainlit) y, si está
  presente, pasa `options={"email_redirect_to": ...}` a `sign_up()` y
  `options={"redirect_to": ...}` a `reset_password_for_email()`, apuntando a `/auth/confirm` (la
  ruta ya existente, `chainlit/main_family.py`). Sin `CHAINLIT_URL` (caso local), `options` no se
  pasa y Supabase cae a su Site URL de dashboard como siempre — local y producción funcionan a la
  vez sin alternar nada a mano. 29 tests de `tests/step_defs/test_e05_t06.py` y relacionados siguen
  en verde (mockean `signup()`/`request_password_reset()` como caja negra, no los argumentos
  internos a `client.auth.sign_up`). Único requisito previo real que queda: añadir la URL de Cloud
  Run a la lista de "Redirect URLs" en el dashboard de Supabase (whitelist, distinta del Site
  URL) — Supabase rechaza cualquier `email_redirect_to`/`redirect_to` que no esté en esa lista,
  aunque se pase explícitamente por código.

**Segunda vuelta, smoke test real de recuperación de contraseña (28 jul):** el email seguía
enlazando a `localhost` pese al fix — causa: D-040 (punto 4) ya documentaba que las plantillas de
email de Supabase ("Confirm signup"/"Reset password") estaban reescritas a mano a
`{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=signup|recovery` (patrón deliberado,
no el `{{ .ConfirmationURL }}` por defecto — necesario porque la app expone su propia ruta
`/auth/confirm` que espera `token_hash`+`type` directamente, no el endpoint `/verify` que genera
`.ConfirmationURL`). `{{ .SiteURL }}` es un valor fijo de dashboard, no varía con el `redirect_to`
que pasa la API por mucho que el código lo mande — de ahí que siguiera enlazando a local. Primer
intento de arreglo (cambiar la plantilla a `{{ .ConfirmationURL }}`) **incorrecto**, habría roto
el patrón de ruta propia de D-040. Fix real, verificado contra la documentación oficial de
Supabase (`supabase.com/docs/guides/auth/auth-email-templates`): existe una variable
`{{ .RedirectTo }}` — *"contains the redirect URL passed when signUp/resetPasswordForEmail/... is
called"*, con fallback documentado al Site URL cuando no se pasa nada o el valor no está en la
whitelist de Redirect URLs. Aplicado en dos sitios:
- Plantillas de Supabase: `{{ .SiteURL }}` → `{{ .RedirectTo }}`, resto del patrón sin cambios
  (Marcos, dashboard).
- `auth/supabase_client.py`, `_confirm_redirect_url()`: bug propio detectado antes de desplegarlo
  — devolvía `f"{CHAINLIT_URL}/auth/confirm"`, pero la plantilla ya añade `/auth/confirm?...`
  ella misma; habría duplicado la ruta (`/auth/confirm/auth/confirm?...`). Corregido a devolver
  solo el dominio base.
29 tests siguen en verde tras el fix (no tocan la lógica interna de construcción de URL).
