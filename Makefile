# Atajos. En Windows usa WSL o Git Bash (o copia los comandos).
PY ?= python3.11
VENV ?= .venv
BIN = $(VENV)/bin
DBT = cd dbt && ../$(BIN)/dbt
PROFILES ?= --profiles-dir .

.PHONY: help venv install lint fmt test dbt-parse dbt-build ingest backfill alerts health \
        dashboard bot docker-build docker-run zip clean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n",$$1,$$2}'

venv: ## Crea el entorno virtual
	$(PY) -m venv $(VENV)

install: venv ## Instala dependencias + paquete en modo editable
	$(BIN)/pip install -r requirements-dev.txt && $(BIN)/pip install -e ".[dashboard]"

lint: ## ruff (estilo + errores comunes)
	$(BIN)/ruff check src tests

fmt: ## Formatea código
	$(BIN)/ruff format src tests && $(BIN)/ruff check --fix src tests

test: ## Tests unitarios (sin Snowflake)
	$(BIN)/pytest -q

dbt-parse: ## Valida el proyecto dbt sin conexión
	$(DBT) parse $(PROFILES)

dbt-build: ## seeds + modelos + tests + snapshot en tu target
	$(DBT) deps $(PROFILES) && $(DBT) build $(PROFILES) && $(DBT) docs generate $(PROFILES)

ingest: ## Ingesta diaria
	$(BIN)/mp-ingest

backfill: ## Carga histórica inicial
	$(BIN)/mp-ingest --backfill

alerts: ## Evalúa y envía alertas a Telegram
	$(BIN)/mp-alerts

health: ## Registra run_results y chequea frescura/volumen
	$(BIN)/mp-health --run-results dbt/target/run_results.json

dashboard: ## Lanza Streamlit
	$(BIN)/streamlit run src/marketpulse/dashboard/app.py

bot: ## Bot interactivo (polling) opcional
	$(BIN)/mp-bot

docker-build: ## Construye la imagen de ingesta
	docker build -t marketpulse-ingest .

docker-run: ## Ejecuta la ingesta en Docker
	docker run --rm --env-file .env marketpulse-ingest

clean: ## Limpia artefactos
	rm -rf dbt/target dbt/logs .pytest_cache .ruff_cache
