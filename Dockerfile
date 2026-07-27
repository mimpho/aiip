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
    # torch de PyPI trae las dependencias CUDA/GPU completas (~7GB extra) aunque
    # este proyecto solo corre bge-m3 en CPU (D-043) — instalar la rueda CPU-only primero
    # para que el resto de requirements.txt la reutilice sin volver a bajar la de GPU.
    && pip install --no-cache-dir torch==2.12.1 --index-url https://download.pytorch.org/whl/cpu \
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
