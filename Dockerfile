# Imagen de ingesta/alertas/health. Multi-stage para una imagen final pequeña.
FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[ingest]"

FROM python:3.11-slim
# Usuario no-root: buena práctica de seguridad en contenedores.
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=builder /install /usr/local
COPY config ./config
ENV PYTHONUNBUFFERED=1 MARKETPULSE_CONFIG_DIR=/app/config
USER app
# Credenciales: se inyectan en runtime (--env-file .env o secretos del orquestador).
ENTRYPOINT ["mp-ingest"]
CMD []
