########################
# Builder stage
########################
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /install

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


########################
# Runtime stage
########################
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ghostscript \
    qpdf \
    tesseract-ocr \
    poppler-utils \
    tesseract-ocr-por \
    pngquant \
    && rm -rf /var/lib/apt/lists/*

# Python packages
COPY --from=builder /install /usr/local

# Application source
COPY app/ .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]