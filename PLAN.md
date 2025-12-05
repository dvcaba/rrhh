# Plan de implementación

## Objetivos
- Empaquetar el proyecto como módulo instalable y evitar hacks de `sys.path`.
- Separar código, datos y artefactos generados.
- Externalizar configuración (rutas, pesos, modelo de embeddings, seeds).
- Declarar dependencias y añadir pruebas automatizadas.
- Exponer entrypoints claros (CLI + UI).

## Estructura propuesta
- `pyproject.toml` con dependencias (`streamlit`, `pandas`, `numpy`, `sentence-transformers`, `python-docx`, etc.) y extras de desarrollo (`pytest`, `ruff`, `black`).
- `src/smart_filtering/` con módulos: `generator/`, `parser/`, `normalizer/`, `embedder/`, `ranker/`, `assessor/`, `explainer/`.
- `scripts/` o `cli/` con comandos `generate-cv`, `generate-jd`, `rank`, `launch-ui`.
- `app/streamlit/app.py` importando el paquete instalado (sin `sys.path`).
- `config/` para `default.yaml` (rutas de datos, pesos de ranking, modelo de embeddings, seeds).
- `data/raw/{cvs,jds}`, `data/processed/`, `data/outputs/` (excluidos de git).
- `tests/` con `pytest` (parser, ranker, assessor).
- `.gitignore` para `__pycache__`, `*.docx` generados, `.venv`, etc.
- `README.md` actualizado con setup, comandos y flujo.

## Fases de trabajo
1) **Housekeeping**: mover código a `src/smart_filtering`, añadir `.gitignore`, mover `CVs/` y `JDs/` a `data/raw`, ajustar imports.
2) **Dependencias & build**: crear `pyproject.toml`/`requirements.txt`, fijar versiones mínimas, incluir extras dev.
3) **Config**: añadir `config/default.yaml` y loader; parametrizar rutas, pesos y modelo.
4) **CLI**: crear entrypoints (`python -m smart_filtering.cli generate-cv --n 20 --out data/raw/cvs`, etc.).
5) **UI**: adaptar Streamlit a la nueva ruta de imports y config; parametrizar rutas y modelo.
6) **Tests**: `pytest` para `parse_docx_cv/jd`, score determinista con fixtures, grading básico.
7) **Validación**: smoke test del CLI y UI; documentar comandos en `README.md`.
8) **(Opcional) CI**: workflow simple (lint + tests) en GitHub Actions.

## Criterios de salida
- `pip install -e .` funciona sin `sys.path` hacks.
- `pytest` pasa.
- CLI genera CV/JD y rankea sin rutas hardcodeadas.
- Streamlit carga usando la config y datos en `data/raw`.
- `README.md` al día con setup, uso y estructura.
