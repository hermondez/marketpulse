# Layout `src/` y `pyproject.toml`

## Qué
El código vive en `src/marketpulse/` y se instala como paquete (`pip install -e .`).
`pyproject.toml` declara dependencias, extras (`dashboard`, `dbt`, `dev`), comandos (`mp-ingest`,
`mp-alerts`, `mp-health`, `mp-bot`) y configuración de ruff/pytest.

## Por qué
- **Evita imports "accidentales"**: con layout plano, `import marketpulse` funciona desde la raíz aunque
  el paquete no esté instalado, y los tests pueden pasar en tu máquina y fallar en Docker/CI. Con `src/`
  los tests importan el paquete *instalado*, igual que en producción.
- **Un solo archivo de configuración** (PEP 621) en lugar de `setup.py` + `setup.cfg` + `requirements`.
- **Comandos de consola**: `mp-ingest` funciona igual en local, Docker y CI.

## Cómo funciona
`[tool.setuptools.packages.find] where = ["src"]` le dice a setuptools dónde buscar.
Modo editable (`-e`) enlaza el código: cambias un archivo y no necesitas reinstalar.
`requirements-pipeline.txt` fija versiones exactas para builds reproducibles (CI/Docker) y
`requirements.txt` (`-e .[dashboard]`) instala solo el dashboard en Streamlit Cloud; `pyproject.toml`
también las fija aquí porque es una aplicación, no una librería.

## Alternativas
`poetry` o `uv` (gestionan lockfile automáticamente; `uv` es muy rápido). Layout plano para scripts
pequeños.

## Cuándo reutilizar
Siempre que el código tenga tests, Docker o se ejecute en más de un lugar.
