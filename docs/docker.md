# Docker

## Qué
`Dockerfile` multi-stage para los comandos Python (`mp-ingest` por defecto; también `mp-alerts`,
`mp-health` cambiando el entrypoint). `docker-compose.yml` con servicios `ingest`, `alerts`, `dashboard`.

```bash
docker build -t marketpulse-ingest .
docker run --rm --env-file .env marketpulse-ingest --dry-run
docker run --rm --env-file .env --entrypoint mp-alerts marketpulse-ingest
```

## Por qué
- **Reproducibilidad**: misma versión de Python y librerías en tu PC, en un servidor o en la nube.
- **Multi-stage**: la etapa de build instala; la final solo copia lo instalado → imagen más pequeña.
- **Usuario no-root** y **sin secretos en la imagen** (se pasan con `--env-file` en runtime).
- `.dockerignore` excluye `.env`, `.git`, docs y tests.

## Internos
Capas: `python:3.11-slim` → `pip install --prefix=/install .` → copia a `/usr/local`. La config
(`config/`) se copia aparte; `MARKETPULSE_CONFIG_DIR` le dice al paquete dónde está.

## Alternativas
Ejecutar directamente en GitHub Actions (lo que hace `daily.yml`, más simple); imágenes distroless;
`uv` para instalar más rápido.

## Cuándo reutilizar
Cuando el job deba correr fuera de GitHub (cron en VPS, Cloud Run Jobs, ECS, Kubernetes CronJob).
