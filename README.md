# RRHH - Smart Candidate Filtering POC

Proyecto de ejemplo para generación, parsing y ranking de CVs contra JDs con explicación y mini-assessment.

## Estructura

- `smart-filtering-poc/`: código principal, UI Streamlit, CLI y tests.
- `PLAN.md`: plan de trabajo.

### Estructura detallada (smart-filtering-poc)

- `config/default.yaml`: rutas de datos/outputs, modelo de embeddings, peso extra de skills.
- `requirements.txt` / `pyproject.toml`: dependencias (incluye extras dev, ruff/black/pytest).
- `app/ui_streamlit/app.py`: UI Streamlit; ranking, filtros, explicación y export CSV.
- `src/smart_filtering/`
  - `config.py`: carga YAML de config y resuelve rutas.
  - `generator/`: datos sintéticos.
    - `cv_generator.py`: genera CVs (ids, skills, experiencia, ubicación).
    - `jd_generator.py`: genera JDs por rol (must/nice, pesos, ubicación).
    - `run_generation.py`: escribe CVs en DOCX.
    - `run_jd_generation.py`: escribe JDs en DOCX.
  - `normalizer/skills_taxonomy.py`: catálogo de skills, sinónimos, helpers.
  - `embedder/embed.py`: wrapper de SentenceTransformer; modo offline devuelve ceros.
  - `parser/docx_parser.py`: parsea CV/JD DOCX → dict enriquecido con coords.
  - `ranker/features.py`: similitud semántica, experiencia, cobertura must-have, distancia geográfica.
  - `ranker/score.py`: pondera features según JD, aplica factores de cobertura/experiencia y skill_alignment.
  - `explainer/explain.py`: texto de explicación/KO en castellano con desglose.
  - `assessor/questions.py`: banco básico de preguntas por skill.
  - `assessor/grade.py`: “grader” simplificado por keywords, produce score/100.
  - `cli.py`: comandos generate-cv/generate-jd/rank.
  - `__main__.py`: permite `python -m smart_filtering`.
- `tests/`: pruebas básicas de parser y scoring.
- `data/`: placeholder (`.gitkeep`); los datos generados en `data/raw`, `data/processed`, `data/outputs` están ignorados en git.

## Cómo arrancar la app (local)

```bash
git clone git@github.com:dvcaba/rrhh.git
cd rrhh/smart-filtering-poc
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m smart_filtering.generator.run_generation
python -m smart_filtering.generator.run_jd_generation
streamlit run app/ui_streamlit/app.py
```

Notas:
- Para entornos sin red o despliegues ligeros, exporta `SMART_FILTERING_EMBEDDER_MODE=offline` antes de lanzar Streamlit (usa embeddings cero y evita descargar el modelo).
- Los datos generados se guardan en `smart-filtering-poc/data/raw/` y se ignoran en git.

## Despliegue rápido (Streamlit Cloud)

1) Conecta el repo `dvcaba/rrhh` en https://share.streamlit.io.
2) App path: `smart-filtering-poc/app/ui_streamlit/app.py`.
3) Añade el secret/env `SMART_FILTERING_EMBEDDER_MODE=offline` si no quieres descargar el modelo.
4) Deploy y comparte la URL pública.

## Qué hace

- Genera CVs/JDs sintéticos (DOCX) y los parsea a diccionarios.
- Calcula features (skills, similitud semántica, experiencia, ubicación), los pondera y produce un score 0–1.
- Explica el score/KO en texto y permite un mini-assessment simulado.
- UI Streamlit para ajustar pesos de skills, filtrar KOs, ver ranking con `cv_id` y exportar CSV.
