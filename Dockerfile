# Exemplo de Dockerfile para app Python:
# - Usa build em 2 estágios para reduzir o tamanho da imagem final.
# - Instala dependências Python no estágio "builder".
# - Mantém no estágio final apenas o necessário para executar a API.

########################
# 1) Builder stage
########################
# Imagem base enxuta do Python 3.11.
FROM python:3.11-slim AS builder

# Evita prompts interativos do apt durante o build.
ENV DEBIAN_FRONTEND=noninteractive
# Diretório de trabalho usado para instalar dependências.
WORKDIR /install

# Dependências de compilação para pacotes Python com extensões nativas.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copia a lista de dependências e instala com prefixo local.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


########################
# 2) Runtime stage
########################
# Novo estágio limpo: só com runtime.
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
# Diretório onde a aplicação vai rodar dentro do container.
WORKDIR /app

# Dependências do sistema usadas em produção pela pipeline de OCR.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ghostscript \
    qpdf \
    tesseract-ocr \
    poppler-utils \
    tesseract-ocr-por \
    pngquant \
    && rm -rf /var/lib/apt/lists/*

# Copia do builder apenas os pacotes Python já instalados.
COPY --from=builder /install /usr/local

# Copia o código da aplicação para dentro da imagem.
COPY app/ .

# Porta HTTP exposta pela API.
EXPOSE 8000

# Comando padrão ao subir o container:
# uvicorn <modulo>:<objeto_app> --host 0.0.0.0 --port 8000
# Neste projeto: arquivo api.py contendo app = FastAPI(...)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
